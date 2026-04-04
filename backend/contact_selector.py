"""Contact Selector — picks the single best contact from a company group.

Assumes title_category has already been set on all contacts
via categorize_all_contacts() before this module is called.
"""

from models import CompanyGroup, ConnectionRecord, ContactSelection

# Categories that get a bonus when selecting contacts
_PREFERRED_CATEGORIES = {"recruiting", "technical"}


def _title_relevance_score(position: str, target_keywords: list[str]) -> float:
    """Score 0–10 based on keyword overlap between position and target role."""
    if not target_keywords:
        return 0.0

    position_words = set(position.lower().split())
    matches = sum(1 for kw in target_keywords if kw in position_words)
    return round((matches / len(target_keywords)) * 10, 2)


def select_best_contact(
    group: CompanyGroup,
    target_role_keywords: list[str],
) -> ContactSelection:
    """Select the best contact from a company group.

    Scoring per contact:
      1. Title relevance (0–10): keyword overlap with target role (dominant signal)
      2. Title category bonus (+2): if category is recruiting or technical
      3. Email bonus (+1): if email is non-null
      4. Tie-breaker: more recent connected_on date wins

    Returns:
        ContactSelection with the chosen contact and its composite score.
    """
    best_contact: ConnectionRecord | None = None
    best_score: float = -1.0
    best_date = None

    for contact in group.contacts:
        # 1. Title relevance (dominant signal, 0–10)
        score = _title_relevance_score(contact.position, target_role_keywords)

        # 2. Title category bonus (+2, modest)
        if contact.title_category in _PREFERRED_CATEGORIES:
            score += 2.0

        # 3. Email bonus (+1, small)
        if contact.email:
            score += 1.0

        # 4. Recency tie-breaker
        is_better = (
            score > best_score
            or (score == best_score and best_date is not None and contact.connected_on > best_date)
        )

        if is_better:
            best_contact = contact
            best_score = score
            best_date = contact.connected_on

    return ContactSelection(contact=best_contact, selection_score=best_score)
