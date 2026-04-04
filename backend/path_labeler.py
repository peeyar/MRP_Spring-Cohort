"""Path Labeler — assigns path-strength labels based on deterministic score thresholds."""


def label_path(score: int) -> str:
    """Return a path label based on the relevance score.

    - Score >= 70 → "Warm Path"
    - Score 40–69 → "Stretch Path"
    - Score < 40  → "Explore"
    """
    if score >= 70:
        return "Warm Path"
    if score >= 40:
        return "Stretch Path"
    return "Explore"
