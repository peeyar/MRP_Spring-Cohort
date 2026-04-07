"""Tests for normalizer.py"""

import pytest
from datetime import date
from normalizer import normalize_connections, _parse_date


def _row(**kwargs):
    """Helper: create a row dict with sensible defaults."""
    defaults = {
        "First Name": "Alice",
        "Last Name": "Smith",
        "URL": "https://li/alice",
        "Email Address": "alice@ex.com",
        "Company": "Acme Corp",
        "Position": "Engineer",
        "Connected On": "01 Jan 2024",
    }
    return {**defaults, **kwargs}


# ── _parse_date ───────────────────────────────────────────────────────────────

def test_parse_date_valid():
    assert _parse_date("01 Jan 2024") == date(2024, 1, 1)
    assert _parse_date("18 Mar 2023") == date(2023, 3, 18)
    assert _parse_date("31 Dec 2022") == date(2022, 12, 31)


def test_parse_date_strips_whitespace():
    assert _parse_date("  01 Jan 2024  ") == date(2024, 1, 1)


def test_parse_date_invalid_raises():
    with pytest.raises(ValueError):
        _parse_date("not-a-date")
    with pytest.raises(ValueError):
        _parse_date("2024-01-01")


# ── normalize_connections ─────────────────────────────────────────────────────

def test_valid_row_becomes_connection_record():
    records, excluded = normalize_connections([_row()])
    assert len(records) == 1
    assert len(excluded) == 0
    r = records[0]
    assert r.first_name == "Alice"
    assert r.last_name == "Smith"
    assert r.full_name == "Alice Smith"
    assert r.company == "Acme Corp"
    assert r.position == "Engineer"
    assert r.connected_on == date(2024, 1, 1)
    assert r.email == "alice@ex.com"


def test_empty_email_becomes_none():
    records, _ = normalize_connections([_row(**{"Email Address": ""})])
    assert records[0].email is None


def test_whitespace_only_email_becomes_none():
    records, _ = normalize_connections([_row(**{"Email Address": "   "})])
    assert records[0].email is None


def test_empty_company_excluded():
    _, excluded = normalize_connections([_row(**{"Company": ""})])
    assert len(excluded) == 1
    assert "Empty company field" in excluded[0].reason


def test_whitespace_company_excluded():
    _, excluded = normalize_connections([_row(**{"Company": "   "})])
    assert len(excluded) == 1
    assert "Empty company field" in excluded[0].reason


def test_invalid_date_excluded():
    _, excluded = normalize_connections([_row(**{"Connected On": "not-a-date"})])
    assert len(excluded) == 1
    assert "Invalid date format" in excluded[0].reason


def test_excluded_row_number_is_1_indexed():
    _, excluded = normalize_connections([_row(**{"Company": ""})])
    assert excluded[0].row_number == 1


def test_whitespace_trimmed_from_fields():
    records, _ = normalize_connections([_row(**{
        "First Name": "  Alice  ",
        "Company": "  Acme Corp  ",
        "Position": "  Engineer  ",
    })])
    assert records[0].first_name == "Alice"
    assert records[0].company == "Acme Corp"
    assert records[0].position == "Engineer"


def test_mixed_valid_and_excluded_rows():
    rows = [
        _row(),                              # valid
        _row(**{"Company": ""}),             # excluded: empty company
        _row(**{"Connected On": "bad"}),     # excluded: bad date
        _row(**{"First Name": "Bob", "Last Name": "Jones"}),  # valid
    ]
    records, excluded = normalize_connections(rows)
    assert len(records) == 2
    assert len(excluded) == 2


def test_full_name_concatenation():
    records, _ = normalize_connections([_row(**{"First Name": "John", "Last Name": "Doe"})])
    assert records[0].full_name == "John Doe"


def test_default_title_category_is_unknown():
    records, _ = normalize_connections([_row()])
    assert records[0].title_category == "unknown"
