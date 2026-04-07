"""Tests for llm_advisor.py — all LLM calls are mocked via unittest.mock."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date

from models import CompanyResult, Preferences
from llm_advisor import classify_company_types, generate_details, _build_fallback


def _make_result(**kwargs):
    defaults = dict(
        company_name="Acme Corp",
        contact_name="Alice Smith",
        contact_title="Software Engineer",
        contact_url="https://li/alice",
        contact_email=None,
        path_label="Stretch Path",
        score=55,
        contact_count=1,
    )
    return CompanyResult(**{**defaults, **kwargs})


def _make_prefs(**kwargs):
    defaults = dict(target_role="software engineer", location="", company_type="any")
    return Preferences(**{**defaults, **kwargs})


def _mock_httpx_response(content: str):
    """Return a mock httpx response object with the given content string."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": content}}]
    }
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


# ── classify_company_types ────────────────────────────────────────────────────

async def test_classify_no_api_key(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    result = await classify_company_types(["acme"])
    assert result == {}


async def test_classify_empty_list(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    result = await classify_company_types([])
    assert result == {}


async def test_classify_valid_response(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    response_json = json.dumps({"Acme Corp": "startup", "Big Corp": "enterprise"})
    mock_client = _mock_httpx_response(response_json)

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await classify_company_types(["acme corp", "big corp"])

    assert result.get("acme corp") == "startup"
    assert result.get("big corp") == "enterprise"


async def test_classify_strips_markdown_fences(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    content = '```json\n{"acme": "startup"}\n```'
    mock_client = _mock_httpx_response(content)

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await classify_company_types(["acme"])

    assert result.get("acme") == "startup"


async def test_classify_filters_invalid_types(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    response_json = json.dumps({"acme": "unicorn", "beta": "startup"})
    mock_client = _mock_httpx_response(response_json)

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await classify_company_types(["acme", "beta"])

    assert "acme" not in result  # "unicorn" is not a valid type
    assert result.get("beta") == "startup"


async def test_classify_invalid_json_returns_empty(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    mock_client = _mock_httpx_response("not valid json at all")

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await classify_company_types(["acme"])

    assert result == {}


async def test_classify_network_error_returns_empty(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=Exception("network error"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await classify_company_types(["acme"])

    assert result == {}


# ── _build_fallback ───────────────────────────────────────────────────────────

def test_build_fallback_fills_placeholders():
    result = _make_result(company_name="Stripe", contact_name="Bob Jones")
    prefs = _make_prefs(target_role="backend engineer")
    fallback = _build_fallback(result, prefs)

    assert "Bob Jones" in fallback.outreach_draft
    assert "backend engineer" in fallback.outreach_draft
    assert "Stripe" in fallback.outreach_draft


# ── generate_details ──────────────────────────────────────────────────────────

async def test_generate_details_no_api_key_returns_fallback(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    details = await generate_details(_make_result(), _make_prefs())
    assert details.explanation
    assert details.next_action
    assert details.outreach_draft


async def test_generate_details_valid_response(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    payload = json.dumps({
        "explanation": "Great match.",
        "next_action": "Send a message.",
        "outreach_draft": "Hi Alice, let's connect.",
    })
    mock_client = _mock_httpx_response(payload)

    with patch("httpx.AsyncClient", return_value=mock_client):
        details = await generate_details(_make_result(), _make_prefs())

    assert details.explanation == "Great match."
    assert details.next_action == "Send a message."
    assert details.outreach_draft == "Hi Alice, let's connect."


async def test_generate_details_strips_markdown_fences(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    content = '```json\n{"explanation": "Good.", "next_action": "Go.", "outreach_draft": "Hi."}\n```'
    mock_client = _mock_httpx_response(content)

    with patch("httpx.AsyncClient", return_value=mock_client):
        details = await generate_details(_make_result(), _make_prefs())

    assert details.explanation == "Good."


async def test_generate_details_invalid_json_returns_fallback(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    mock_client = _mock_httpx_response("not json")

    with patch("httpx.AsyncClient", return_value=mock_client):
        details = await generate_details(_make_result(), _make_prefs())

    assert details.explanation
    assert details.outreach_draft


async def test_generate_details_network_error_returns_fallback(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=Exception("timeout"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        details = await generate_details(_make_result(), _make_prefs())

    assert details.explanation
