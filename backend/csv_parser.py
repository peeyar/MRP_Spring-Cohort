"""CSV Parser — reads LinkedIn connections CSV, skips preamble, validates columns."""

import csv
import io
from typing import BinaryIO

REQUIRED_COLUMNS = {
    "First Name",
    "Last Name",
    "URL",
    "Email Address",
    "Company",
    "Position",
    "Connected On",
}


def parse_csv(file: BinaryIO) -> tuple[list[dict[str, str]], int]:
    """Parse a LinkedIn connections CSV file.

    Skips the LinkedIn "Notes:" preamble, finds the header row,
    validates required columns, and returns raw row dicts.

    Returns:
        (rows, total_row_count) where rows is a list of dicts keyed by column name.

    Raises:
        ValueError: If required columns are missing or file has no data.
    """
    content = file.read()
    if isinstance(content, bytes):
        content = content.decode("utf-8-sig")  # handle BOM

    # Find the header row — skip LinkedIn "Notes:" preamble
    lines = content.splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("First Name"):
            header_idx = i
            break

    if header_idx is None:
        raise ValueError(
            "Could not find CSV header row. Expected a row starting with 'First Name'."
        )

    # Rejoin from header onward and parse as CSV
    csv_text = "\n".join(lines[header_idx:])
    reader = csv.DictReader(io.StringIO(csv_text))

    # Validate required columns
    found_columns = set(reader.fieldnames or [])
    missing = REQUIRED_COLUMNS - found_columns
    if missing:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")

    rows = list(reader)
    total_row_count = len(rows)

    # Zero data rows is valid — the pipeline will return success with empty results.
    # Only truly invalid files (missing header, missing columns) raise errors above.
    return rows, total_row_count
