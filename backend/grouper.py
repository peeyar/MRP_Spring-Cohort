"""Company Grouper — groups ConnectionRecords by normalized company name."""

import re

from models import CompanyGroup, ConnectionRecord

# Legal suffixes to strip (only when they appear as the last word)
_LEGAL_SUFFIXES = {
    "inc", "llc", "ltd", "corp", "corporation",
    "co", "company", "plc", "lp",
}

# Pattern: optional comma/period, then a suffix word, then optional trailing period/comma, at end of string
_SUFFIX_PATTERN = re.compile(
    r"[,.]?\s+(" + "|".join(_LEGAL_SUFFIXES) + r")\.?,?\s*$",
    re.IGNORECASE,
)


def _normalize_company_name(name: str) -> str:
    """Normalize a company name for grouping.

    - Strip whitespace
    - Lowercase
    - Remove trailing legal suffix from safe set
    """
    normalized = name.strip().lower()
    normalized = _SUFFIX_PATTERN.sub("", normalized).strip()
    return normalized


def group_by_company(
    records: list[ConnectionRecord],
) -> dict[str, CompanyGroup]:
    """Group ConnectionRecords by normalized company name.

    Returns:
        Dict mapping normalized company name to CompanyGroup.
        Display name comes from the first record seen for each group.
    """
    groups: dict[str, CompanyGroup] = {}

    for record in records:
        key = _normalize_company_name(record.company)

        if key not in groups:
            groups[key] = CompanyGroup(
                normalized_name=key,
                display_name=record.company,
                contacts=[record],
            )
        else:
            groups[key].contacts.append(record)

    return groups
