"""Integration tests for API routes using FastAPI TestClient."""

import json
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# ── CSV fixtures ──────────────────────────────────────────────────────────────

VALID_CSV = (
    "First Name,Last Name,URL,Email Address,Company,Position,Connected On\n"
    "Alice,Smith,https://li/alice,alice@ex.com,Acme Corp,Software Engineer,01 Jan 2024\n"
    "Bob,Jones,https://li/bob,,Beta Inc,Talent Recruiter,15 Mar 2023\n"
)

EMPTY_CSV = "First Name,Last Name,URL,Email Address,Company,Position,Connected On\n"

MISSING_COMPANY_CSV = (
    "First Name,Last Name,URL,Email Address,Company,Position,Connected On\n"
    "Alice,Smith,https://li/alice,alice@ex.com,,Software Engineer,01 Jan 2024\n"
)

NO_HEADER_CSV = "col1,col2\nval1,val2\n"

MISSING_COLUMN_CSV = "First Name,Last Name\nAlice,Smith\n"


def _post_analyze(csv_content: str, preferences: dict):
    return client.post(
        "/api/analyze",
        files={"file": ("connections.csv", csv_content.encode(), "text/csv")},
        data={"preferences": json.dumps(preferences)},
    )


# ── /health ───────────────────────────────────────────────────────────────────

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ── /api/analyze — success ────────────────────────────────────────────────────

def test_analyze_valid_csv():
    with patch("api.classify_company_types", new_callable=AsyncMock, return_value={}):
        resp = _post_analyze(VALID_CSV, {"target_role": "software engineer"})
    assert resp.status_code == 200
    body = resp.json()
    assert "parsing_summary" in body
    assert "results" in body


def test_analyze_parsing_summary_counts():
    with patch("api.classify_company_types", new_callable=AsyncMock, return_value={}):
        resp = _post_analyze(VALID_CSV, {"target_role": "software engineer"})
    summary = resp.json()["parsing_summary"]
    assert summary["total_rows"] == 2
    assert summary["valid_connections"] == 2
    assert summary["unique_companies"] == 2


def test_analyze_results_structure():
    with patch("api.classify_company_types", new_callable=AsyncMock, return_value={}):
        resp = _post_analyze(VALID_CSV, {"target_role": "software engineer"})
    results = resp.json()["results"]
    assert len(results) > 0
    r = results[0]
    assert "company_name" in r
    assert "contact_name" in r
    assert "path_label" in r
    assert "score" in r
    assert r["path_label"] in ("Warm Path", "Stretch Path", "Explore")
    assert 0 <= r["score"] <= 100


def test_analyze_empty_csv_returns_empty_results():
    with patch("api.classify_company_types", new_callable=AsyncMock, return_value={}):
        resp = _post_analyze(EMPTY_CSV, {"target_role": "software engineer"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["results"] == []
    assert body["parsing_summary"]["total_rows"] == 0


def test_analyze_row_with_empty_company_excluded():
    with patch("api.classify_company_types", new_callable=AsyncMock, return_value={}):
        resp = _post_analyze(MISSING_COMPANY_CSV, {"target_role": "engineer"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["parsing_summary"]["valid_connections"] == 0
    assert body["parsing_summary"]["excluded_rows"] == 1


def test_analyze_company_type_any_skips_llm():
    """When company_type is 'any', classify_company_types should NOT be called."""
    with patch("api.classify_company_types", new_callable=AsyncMock) as mock_classify:
        _post_analyze(VALID_CSV, {"target_role": "engineer", "company_type": "any"})
    mock_classify.assert_not_called()


def test_analyze_company_type_filter_calls_llm():
    """When company_type is specified and not 'any', classify_company_types IS called."""
    with patch("api.classify_company_types", new_callable=AsyncMock, return_value={}) as mock_classify:
        _post_analyze(VALID_CSV, {"target_role": "engineer", "company_type": "startup"})
    mock_classify.assert_called_once()


# ── /api/analyze — error cases ────────────────────────────────────────────────

def test_analyze_missing_target_role_returns_400():
    resp = _post_analyze(VALID_CSV, {"location": "NYC"})
    assert resp.status_code == 400
    assert "Target role" in resp.json()["detail"]


def test_analyze_empty_target_role_returns_400():
    resp = _post_analyze(VALID_CSV, {"target_role": "   "})
    assert resp.status_code == 400


def test_analyze_invalid_preferences_json_returns_422():
    resp = client.post(
        "/api/analyze",
        files={"file": ("connections.csv", VALID_CSV.encode(), "text/csv")},
        data={"preferences": "not-valid-json"},
    )
    assert resp.status_code == 422


def test_analyze_csv_no_header_returns_400():
    resp = _post_analyze(NO_HEADER_CSV, {"target_role": "engineer"})
    assert resp.status_code == 400


def test_analyze_csv_missing_columns_returns_400():
    resp = _post_analyze(MISSING_COLUMN_CSV, {"target_role": "engineer"})
    assert resp.status_code == 400


# ── /api/details ──────────────────────────────────────────────────────────────

def test_details_always_returns_200():
    """Details endpoint never fails — falls back to static content on any error."""
    with patch("api.details.__wrapped__" if hasattr(client, "__wrapped__") else "llm_advisor.generate_details",
               new_callable=AsyncMock,
               return_value=None):
        resp = client.post("/api/details", json={
            "company_result": {
                "company_name": "Acme Corp",
                "contact_name": "Alice Smith",
                "contact_title": "Software Engineer",
                "contact_url": "https://li/alice",
                "contact_email": None,
                "path_label": "Stretch Path",
                "score": 55,
                "contact_count": 1,
            },
            "preferences": {
                "target_role": "software engineer",
                "location": "",
                "company_type": "any",
            },
        })
    assert resp.status_code == 200


def test_details_returns_expected_fields():
    with patch("llm_advisor.generate_details", new_callable=AsyncMock) as mock_gen:
        from models import LLMDetails
        mock_gen.return_value = LLMDetails(
            explanation="Great match.",
            next_action="Send a message.",
            outreach_draft="Hi Alice.",
        )
        resp = client.post("/api/details", json={
            "company_result": {
                "company_name": "Acme Corp",
                "contact_name": "Alice Smith",
                "contact_title": "Engineer",
                "contact_url": "",
                "contact_email": None,
                "path_label": "Explore",
                "score": 30,
                "contact_count": 1,
            },
            "preferences": {"target_role": "engineer", "location": "", "company_type": "any"},
        })
    assert resp.status_code == 200
    body = resp.json()
    assert "explanation" in body
    assert "next_action" in body
    assert "outreach_draft" in body


def test_details_fallback_on_bad_body():
    """Malformed body doesn't crash — falls back to static content."""
    resp = client.post("/api/details", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert "explanation" in body
