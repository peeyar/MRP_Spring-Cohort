"""Connection Normalizer — converts raw CSV rows into ConnectionRecord objects."""

from datetime import datetime

from models import ConnectionRecord, ExcludedRow


def _parse_date(date_str: str) -> datetime:
    """Parse LinkedIn date format 'DD Mon YYYY' (e.g., '18 Mar 2026')."""
    return datetime.strptime(date_str.strip(), "%d %b %Y").date()


def normalize_connections(
    rows: list[dict[str, str]],
) -> tuple[list[ConnectionRecord], list[ExcludedRow]]:
    """Normalize raw CSV row dicts into ConnectionRecord objects.

    - Trims whitespace on all string fields
    - Parses Connected On into datetime.date
    - Sets email to None when empty
    - Excludes rows with empty Company (after trimming)
    - Tracks excluded rows with reasons

    Returns:
        (valid_records, excluded_rows)
    """
    valid: list[ConnectionRecord] = []
    excluded: list[ExcludedRow] = []

    for i, row in enumerate(rows, start=1):
        first_name = row.get("First Name", "").strip()
        last_name = row.get("Last Name", "").strip()
        url = row.get("URL", "").strip()
        email_raw = row.get("Email Address", "").strip()
        company = row.get("Company", "").strip()
        position = row.get("Position", "").strip()
        connected_on_raw = row.get("Connected On", "").strip()

        # Exclude rows with empty company
        if not company:
            excluded.append(ExcludedRow(row_number=i, reason="Empty company field"))
            continue

        # Parse date — exclude on failure
        try:
            connected_on = _parse_date(connected_on_raw)
        except (ValueError, AttributeError):
            excluded.append(
                ExcludedRow(row_number=i, reason=f"Invalid date format: '{connected_on_raw}'")
            )
            continue

        full_name = f"{first_name} {last_name}".strip()
        email = email_raw if email_raw else None

        valid.append(
            ConnectionRecord(
                first_name=first_name,
                last_name=last_name,
                full_name=full_name,
                url=url,
                email=email,
                company=company,
                position=position,
                connected_on=connected_on,
            )
        )

    return valid, excluded
