"""Tests for title_categorizer.py"""

import pytest
from title_categorizer import categorize_title, categorize_all_contacts


# ── categorize_title ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("title,expected", [
    ("Software Engineer", "technical"),
    ("Senior Developer", "technical"),
    ("Data Scientist", "technical"),
    ("QA Analyst", "technical"),
    ("DevOps Engineer", "technical"),
    ("Programmer", "technical"),
    ("Recruiter", "recruiting"),
    ("Talent Acquisition Specialist", "recruiting"),
    ("HR Manager", "recruiting"),  # "hr" keyword
    ("Human Resources Business Partner", "recruiting"),
    ("Director of Engineering", "leadership"),
    ("VP of Product", "leadership"),
    ("Vice President, Sales", "leadership"),
    ("CEO", "leadership"),
    ("CTO", "leadership"),
    ("Head of Design", "leadership"),
    ("Engineering Manager", "leadership"),  # leadership beats technical
    ("Team Lead", "leadership"),
    ("Principal Engineer", "leadership"),  # "principal" before "engineer"
    ("Student", "student"),
    ("Software Engineering Intern", "student"),  # "intern" beats "engineer"
    ("Fellow", "student"),
    ("Graduate Assistant", "student"),
    ("", "unknown"),
    ("Marketing Specialist", "unknown"),
    ("Accountant", "unknown"),
    ("Teacher", "unknown"),
])
def test_categorize_title(title, expected):
    assert categorize_title(title) == expected


def test_categorize_title_case_insensitive():
    assert categorize_title("SOFTWARE ENGINEER") == "technical"
    assert categorize_title("recruiter") == "recruiting"
    assert categorize_title("DIRECTOR") == "leadership"


def test_categorize_title_recruiting_priority_over_technical():
    """Recruiting is checked before technical; 'hiring engineer' → recruiting via 'hiring'."""
    assert categorize_title("Hiring Manager") == "recruiting"


# ── categorize_all_contacts ───────────────────────────────────────────────────

def test_categorize_all_contacts_mutates_records():
    """categorize_all_contacts sets title_category on each record in-place."""
    from models import ConnectionRecord
    from datetime import date

    def make_record(position):
        return ConnectionRecord(
            first_name="A", last_name="B", full_name="A B",
            url="", email=None, company="Acme", position=position,
            connected_on=date(2024, 1, 1),
        )

    records = [make_record("Software Engineer"), make_record("Recruiter")]
    categorize_all_contacts(records)

    assert records[0].title_category == "technical"
    assert records[1].title_category == "recruiting"
