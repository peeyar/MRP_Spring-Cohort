"""Title Categorizer — maps position strings to broad categories via keyword matching."""

# Keywords per category, checked in priority order.
# Leadership checked before technical so "Engineering Manager" → leadership, not technical.
_CATEGORY_KEYWORDS: list[tuple[str, list[str]]] = [
    ("recruiting", [
        "recruiter", "talent", "hiring", "staffing",
        "hr", "human resources",
    ]),
    ("leadership", [
        "director", "vp", "vice president", "president",
        "ceo", "cto", "cfo", "coo", "cio",
        "head of", "manager", "lead", "principal",
    ]),
    ("student", [
        "student", "intern", "fellow", "apprentice",
        "graduate assistant",
    ]),
    ("technical", [
        "engineer", "developer", "architect",
        "data", "scientist", "analyst",
        "sde", "swe", "devops", "qa",
        "programmer", "software",
    ]),
]


def categorize_title(position: str) -> str:
    """Categorize a position title into one of:
    technical, recruiting, leadership, student, unknown.

    Uses simple case-insensitive keyword matching.
    First matching category wins (priority order above).
    """
    if not position:
        return "unknown"

    lower = position.lower()

    for category, keywords in _CATEGORY_KEYWORDS:
        for kw in keywords:
            if kw in lower:
                return category

    return "unknown"


def categorize_all_contacts(records):
    """Explicit preprocessing step: set title_category on every ConnectionRecord.

    Call this once after normalization, before grouping/selection/ranking.
    This avoids hidden side effects in downstream modules.
    """
    for record in records:
        record.title_category = categorize_title(record.position)
