"""Tests for csv_parser.py"""

import io
import pytest
from csv_parser import parse_csv, REQUIRED_COLUMNS


def _make_csv(*data_rows, preamble=None):
    """Helper: assemble a CSV bytes object with optional LinkedIn preamble."""
    header = "First Name,Last Name,URL,Email Address,Company,Position,Connected On"
    lines = list(preamble or []) + [header] + list(data_rows)
    return io.BytesIO("\n".join(lines).encode("utf-8"))


# ── happy path ────────────────────────────────────────────────────────────────

def test_parse_single_valid_row():
    f = _make_csv("Alice,Smith,https://li/alice,alice@ex.com,Acme Corp,Engineer,01 Jan 2024")
    rows, total = parse_csv(f)
    assert total == 1
    assert len(rows) == 1
    assert rows[0]["First Name"] == "Alice"
    assert rows[0]["Company"] == "Acme Corp"
    assert rows[0]["Position"] == "Engineer"


def test_parse_multiple_rows():
    f = _make_csv(
        "Alice,Smith,https://li/alice,,Acme Corp,Engineer,01 Jan 2024",
        "Bob,Jones,https://li/bob,,Beta Inc,Manager,15 Mar 2023",
    )
    rows, total = parse_csv(f)
    assert total == 2
    assert rows[0]["First Name"] == "Alice"
    assert rows[1]["First Name"] == "Bob"


def test_parse_with_linkedin_preamble():
    """LinkedIn exports include a 'Notes:' preamble before the header row."""
    f = _make_csv(
        "Alice,Smith,https://li/alice,,Acme Corp,Engineer,01 Jan 2024",
        preamble=["Notes:", "-- You can include up to 3,000 notes here.", ""],
    )
    rows, total = parse_csv(f)
    assert total == 1
    assert rows[0]["First Name"] == "Alice"


def test_parse_empty_csv_is_valid():
    """Header-only CSV has zero data rows — pipeline returns empty results."""
    f = _make_csv()
    rows, total = parse_csv(f)
    assert total == 0
    assert rows == []


def test_parse_all_required_columns_present():
    f = _make_csv("Alice,Smith,https://li/alice,a@b.com,Acme Corp,Engineer,01 Jan 2024")
    rows, _ = parse_csv(f)
    for col in REQUIRED_COLUMNS:
        assert col in rows[0], f"Column '{col}' missing from parsed row"


def test_parse_bom_stripped():
    """UTF-8 BOM at start of file is stripped transparently."""
    header = "First Name,Last Name,URL,Email Address,Company,Position,Connected On"
    content = "\ufeff" + header + "\nAlice,Smith,,,Acme Corp,Engineer,01 Jan 2024"
    f = io.BytesIO(content.encode("utf-8"))
    rows, total = parse_csv(f)
    assert total == 1


# ── error cases ───────────────────────────────────────────────────────────────

def test_parse_missing_first_name_header():
    """File with no 'First Name' header row raises ValueError."""
    f = io.BytesIO(b"col1,col2,col3\nval1,val2,val3")
    with pytest.raises(ValueError, match="Could not find CSV header row"):
        parse_csv(f)


def test_parse_missing_required_columns():
    """Header found but required columns absent raises ValueError."""
    f = io.BytesIO(b"First Name,Last Name\nAlice,Smith")
    with pytest.raises(ValueError, match="Missing columns"):
        parse_csv(f)


def test_parse_empty_file():
    f = io.BytesIO(b"")
    with pytest.raises(ValueError, match="Could not find CSV header row"):
        parse_csv(f)
