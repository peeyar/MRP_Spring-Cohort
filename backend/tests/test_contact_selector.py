"""Tests for contact_selector.py"""

import pytest
from datetime import date
from models import CompanyGroup, ConnectionRecord
from contact_selector import select_best_contact, _title_relevance_score


def _record(
    position="Engineer",
    email=None,
    title_category="unknown",
    connected_on=None,
    first="Alice",
):
    return ConnectionRecord(
        first_name=first, last_name="Smith", full_name=f"{first} Smith",
        url="", email=email, company="Acme", position=position,
        connected_on=connected_on or date(2024, 1, 1),
        title_category=title_category,
    )


def _group(*records):
    return CompanyGroup(
        normalized_name="acme", display_name="Acme Corp", contacts=list(records)
    )


# ── _title_relevance_score ────────────────────────────────────────────────────

def test_title_relevance_no_keywords():
    assert _title_relevance_score("Software Engineer", []) == 0.0


def test_title_relevance_full_match():
    assert _title_relevance_score("software engineer", ["software", "engineer"]) == 10.0


def test_title_relevance_partial_match():
    score = _title_relevance_score("software developer", ["software", "engineer"])
    assert score == 5.0  # 1/2 keywords matched


def test_title_relevance_no_match():
    assert _title_relevance_score("Marketing Director", ["software", "engineer"]) == 0.0


def test_title_relevance_capped_at_ten():
    score = _title_relevance_score("software engineer data", ["software", "engineer"])
    assert score <= 10.0


# ── select_best_contact ───────────────────────────────────────────────────────

def test_single_contact_selected():
    contact = _record(position="Software Engineer")
    result = select_best_contact(_group(contact), ["software", "engineer"])
    assert result.contact is contact


def test_higher_relevance_wins():
    low = _record(position="Marketing Director", first="Low")
    high = _record(position="Software Engineer", first="High")
    result = select_best_contact(_group(low, high), ["software", "engineer"])
    assert result.contact is high


def test_category_bonus_for_recruiting():
    base = _record(position="Product Manager", title_category="unknown", first="Base")
    recruiter = _record(position="Talent Recruiter", title_category="recruiting", first="Rec")
    result = select_best_contact(_group(base, recruiter), [])
    assert result.contact is recruiter  # recruiting gets +2 bonus


def test_category_bonus_for_technical():
    base = _record(position="Operations", title_category="unknown", first="Base")
    tech = _record(position="Software Engineer", title_category="technical", first="Tech")
    result = select_best_contact(_group(base, tech), [])
    assert result.contact is tech


def test_email_bonus():
    no_email = _record(email=None, first="NoEmail")
    has_email = _record(email="a@b.com", first="HasEmail")
    result = select_best_contact(_group(no_email, has_email), [])
    assert result.contact is has_email


def test_recency_tiebreaker():
    older = _record(connected_on=date(2022, 1, 1), first="Older")
    newer = _record(connected_on=date(2024, 6, 1), first="Newer")
    result = select_best_contact(_group(older, newer), [])
    assert result.contact is newer


def test_selection_score_is_returned():
    contact = _record(
        position="Software Engineer",
        title_category="technical",
        email="a@b.com",
    )
    result = select_best_contact(_group(contact), ["software", "engineer"])
    # relevance (10) + category bonus (2) + email bonus (1) = 13
    assert result.selection_score == 13.0
