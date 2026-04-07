"""Tests for grouper.py"""

import pytest
from datetime import date
from models import ConnectionRecord
from grouper import group_by_company, _normalize_company_name


def _record(company, first="Alice", last="Smith", position="Engineer"):
    return ConnectionRecord(
        first_name=first, last_name=last, full_name=f"{first} {last}",
        url="", email=None, company=company, position=position,
        connected_on=date(2024, 1, 1),
    )


# ── _normalize_company_name ───────────────────────────────────────────────────

@pytest.mark.parametrize("name,expected", [
    ("Google", "google"),
    ("Google Inc.", "google"),
    ("Google Inc", "google"),
    ("Microsoft Corp", "microsoft"),
    ("Microsoft Corp.", "microsoft"),
    ("Acme LLC", "acme"),
    ("Acme Ltd", "acme"),
    ("Big Corp.", "big"),
    ("Startup Co", "startup"),
    ("Startup Company", "startup"),
    ("Some LP", "some"),
    ("Some PLC", "some"),
    ("OpenAI", "openai"),                    # no suffix to strip
    ("  Trimmed Name  ", "trimmed name"),    # whitespace stripped
])
def test_normalize_company_name(name, expected):
    assert _normalize_company_name(name) == expected


# ── group_by_company ──────────────────────────────────────────────────────────

def test_single_record_single_group():
    records = [_record("Acme Corp")]
    groups = group_by_company(records)
    assert len(groups) == 1
    assert "acme" in groups


def test_same_company_different_casing_grouped():
    records = [_record("Acme Corp"), _record("ACME CORP")]
    groups = group_by_company(records)
    assert len(groups) == 1


def test_legal_suffix_variants_grouped():
    """'Google Inc.' and 'Google LLC' both normalize to 'google'."""
    records = [_record("Google Inc."), _record("Google LLC")]
    groups = group_by_company(records)
    assert len(groups) == 1
    assert "google" in groups


def test_different_companies_separate_groups():
    records = [_record("Acme Corp"), _record("Beta Inc")]
    groups = group_by_company(records)
    assert len(groups) == 2


def test_display_name_from_first_record():
    """Display name uses original casing from the first record seen."""
    records = [_record("Acme Corp"), _record("acme corp")]
    groups = group_by_company(records)
    assert groups["acme"].display_name == "Acme Corp"


def test_contacts_aggregated_in_group():
    records = [
        _record("Acme Corp", first="Alice"),
        _record("Acme Corp", first="Bob"),
        _record("Acme Corp", first="Carol"),
    ]
    groups = group_by_company(records)
    assert len(groups["acme"].contacts) == 3


def test_empty_records_returns_empty_groups():
    assert group_by_company([]) == {}


def test_normalized_name_stored_on_group():
    records = [_record("Google Inc.")]
    groups = group_by_company(records)
    assert groups["google"].normalized_name == "google"
