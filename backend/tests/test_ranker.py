"""Tests for ranker.py"""

import pytest
from datetime import date
from models import CompanyGroup, ConnectionRecord, ContactSelection, Preferences
from ranker import (
    _is_technical_role,
    _title_relevance_score,
    _title_category_bonus,
    _location_adjustment,
    _company_type_adjustment,
    _email_bonus,
    get_unknown_companies,
    rank_companies,
)


def _record(
    position="Software Engineer",
    email=None,
    title_category="technical",
    first="Alice",
    company="Acme Corp",
):
    return ConnectionRecord(
        first_name=first, last_name="Smith", full_name=f"{first} Smith",
        url="", email=email, company=company, position=position,
        connected_on=date(2024, 1, 1),
        title_category=title_category,
    )


def _group(norm_name, display_name, *records):
    return CompanyGroup(normalized_name=norm_name, display_name=display_name, contacts=list(records))


def _selection(record):
    return ContactSelection(contact=record, selection_score=5.0)


# ── _is_technical_role ────────────────────────────────────────────────────────

@pytest.mark.parametrize("role,expected", [
    ("software engineer", True),
    ("data scientist", True),
    ("frontend developer", True),
    ("devops", True),
    ("product manager", False),
    ("marketing specialist", False),
    ("recruiter", False),
])
def test_is_technical_role(role, expected):
    assert _is_technical_role(role) == expected


# ── _title_relevance_score ────────────────────────────────────────────────────

def test_title_relevance_full_match():
    assert _title_relevance_score("software engineer", ["software", "engineer"]) == 60


def test_title_relevance_partial_match():
    score = _title_relevance_score("software developer", ["software", "engineer"])
    assert score == 30  # 1/2 matches → 30


def test_title_relevance_no_match():
    assert _title_relevance_score("Marketing Director", ["software", "engineer"]) == 0


def test_title_relevance_recruiter_minimum():
    """Recruiters always get at least 5 even with no keyword match."""
    score = _title_relevance_score("Talent Recruiter", ["software", "engineer"])
    assert score >= 5


def test_title_relevance_no_keywords_returns_zero():
    assert _title_relevance_score("Engineer", []) == 0


# ── _title_category_bonus ─────────────────────────────────────────────────────

def test_category_bonus_tech_role_recruiting():
    assert _title_category_bonus("Recruiter", is_tech_role=True) == 15


def test_category_bonus_tech_role_technical():
    assert _title_category_bonus("Software Engineer", is_tech_role=True) == 10


def test_category_bonus_tech_role_leadership():
    assert _title_category_bonus("Director of Engineering", is_tech_role=True) == 5


def test_category_bonus_tech_role_unknown():
    assert _title_category_bonus("Accountant", is_tech_role=True) == 0


def test_category_bonus_nonttech_role_leadership():
    assert _title_category_bonus("VP of Marketing", is_tech_role=False) == 10


def test_category_bonus_nontech_role_technical():
    assert _title_category_bonus("Software Engineer", is_tech_role=False) == 5


# ── _location_adjustment ──────────────────────────────────────────────────────

def test_location_no_preference():
    assert _location_adjustment("New York Corp", "Engineer NYC", "") == 0


def test_location_match_in_company_name():
    assert _location_adjustment("Seattle Startup", "Engineer", "seattle") == 10


def test_location_match_in_position():
    assert _location_adjustment("Acme Corp", "NYC Engineer", "nyc") == 10


def test_location_no_match():
    assert _location_adjustment("Boston Corp", "Remote Engineer", "seattle") == 0


def test_location_never_penalizes():
    """Location score is always >= 0."""
    score = _location_adjustment("Company X", "position Y", "z")
    assert score >= 0


# ── _company_type_adjustment ──────────────────────────────────────────────────

def test_company_type_match_enterprise():
    assert _company_type_adjustment("google", "enterprise") == 15


def test_company_type_mismatch():
    assert _company_type_adjustment("google", "startup") == -5


def test_company_type_unknown_company():
    assert _company_type_adjustment("unknown_startup_xyz", "startup") == 0


def test_company_type_any_preference():
    assert _company_type_adjustment("google", "any") == 0


def test_company_type_enriched_types():
    enriched = {"mynewco": "startup"}
    assert _company_type_adjustment("mynewco", "startup", enriched) == 15
    assert _company_type_adjustment("mynewco", "enterprise", enriched) == -5


# ── _email_bonus ──────────────────────────────────────────────────────────────

def test_email_bonus_with_email():
    assert _email_bonus("user@example.com") == 5


def test_email_bonus_without_email():
    assert _email_bonus(None) == 0


# ── get_unknown_companies ─────────────────────────────────────────────────────

def test_get_unknown_companies():
    groups = {
        "google": _group("google", "Google"),
        "unknownco": _group("unknownco", "Unknown Co"),
    }
    unknowns = get_unknown_companies(groups)
    assert "unknownco" in unknowns
    assert "google" not in unknowns


# ── rank_companies ────────────────────────────────────────────────────────────

def test_rank_companies_basic():
    rec = _record(position="Software Engineer", email="a@b.com")
    rec.title_category = "technical"
    groups = {"acme": _group("acme", "Acme Corp", rec)}
    selections = {"acme": _selection(rec)}
    prefs = Preferences(target_role="software engineer")

    results = rank_companies(groups, selections, prefs)

    assert len(results) == 1
    assert results[0].company_name == "Acme Corp"
    assert results[0].score > 0
    assert results[0].path_label in ("Warm Path", "Stretch Path", "Explore")


def test_rank_companies_sorted_descending():
    r1 = _record(position="Software Engineer", first="Alice")
    r2 = _record(position="Accountant", first="Bob")
    groups = {
        "acme": _group("acme", "Acme Corp", r1),
        "beta": _group("beta", "Beta Corp", r2),
    }
    selections = {"acme": _selection(r1), "beta": _selection(r2)}
    prefs = Preferences(target_role="software engineer")

    results = rank_companies(groups, selections, prefs)
    assert results[0].score >= results[1].score


def test_rank_companies_alphabetical_tiebreak():
    r1 = _record(position="Accountant", first="Alice")
    r2 = _record(position="Accountant", first="Bob")
    groups = {
        "zeta": _group("zeta", "Zeta Corp", r2),
        "alpha": _group("alpha", "Alpha Corp", r1),
    }
    selections = {"zeta": _selection(r2), "alpha": _selection(r1)}
    prefs = Preferences(target_role="accountant")

    results = rank_companies(groups, selections, prefs)
    assert results[0].company_name == "Alpha Corp"
    assert results[1].company_name == "Zeta Corp"


def test_rank_companies_score_clamped_to_100():
    """Score components can sum > 100; result is clamped."""
    r = _record(position="Software Engineer Recruiter", email="a@b.com")
    r.title_category = "recruiting"
    groups = {"google": _group("google", "Google", r)}
    selections = {"google": _selection(r)}
    prefs = Preferences(
        target_role="software engineer",
        company_type="enterprise",
        location="google",
    )

    results = rank_companies(groups, selections, prefs)
    assert results[0].score <= 100


def test_rank_companies_score_clamped_to_zero():
    """Negative raw score (mismatch penalty) is clamped to 0."""
    r = _record(position="Accountant", email=None)
    r.title_category = "unknown"
    groups = {"google": _group("google", "Google", r)}
    selections = {"google": _selection(r)}
    prefs = Preferences(target_role="software engineer", company_type="startup")

    results = rank_companies(groups, selections, prefs)
    assert results[0].score >= 0


def test_rank_companies_contact_count():
    r1 = _record(first="Alice")
    r2 = _record(first="Bob")
    r3 = _record(first="Carol")
    groups = {"acme": _group("acme", "Acme Corp", r1, r2, r3)}
    selections = {"acme": _selection(r1)}
    prefs = Preferences(target_role="engineer")

    results = rank_companies(groups, selections, prefs)
    assert results[0].contact_count == 3


def test_rank_skips_groups_without_selection():
    r = _record()
    groups = {
        "acme": _group("acme", "Acme Corp", r),
        "beta": _group("beta", "Beta Corp", r),
    }
    selections = {"acme": _selection(r)}  # beta has no selection

    results = rank_companies(groups, selections, Preferences(target_role="engineer"))
    assert len(results) == 1
    assert results[0].company_name == "Acme Corp"
