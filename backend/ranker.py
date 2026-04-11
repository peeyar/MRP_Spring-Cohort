"""Ranker — computes 0–100 relevance scores for companies. Fully deterministic."""

from models import CompanyGroup, CompanyResult, ContactSelection, Preferences
from path_labeler import label_path
from title_categorizer import categorize_title

# Small static lookup: normalized company name → company type.
# Keys must match the output of grouper._normalize_company_name (lowercase, legal suffixes stripped).
_COMPANY_TYPE_LOOKUP: dict[str, str] = {
    "accenture": "enterprise",
    "ada developers academy": "startup",
    "adobe": "enterprise",
    "akvelon, inc.": "mid-size",
    "alphabet": "enterprise",
    "amazon": "enterprise",
    "amazon web services": "enterprise",
    "anthropic": "startup",
    "apple": "enterprise",
    "apptad inc.": "startup",
    "ask consulting": "startup",
    "astronomer": "startup",
    "at&t": "enterprise",
    "atlassian": "mid-size",
    "aumovio": "startup",
    "aws": "enterprise",
    "bank of america": "enterprise",
    "big river steel": "mid-size",
    "bloomberg": "enterprise",
    "boeing": "enterprise",
    "business needs inc.": "startup",
    "capital one": "enterprise",
    "chewy": "enterprise",
    "ciena": "mid-size",
    "cisco": "enterprise",
    "citi": "enterprise",
    "citi india": "enterprise",
    "cloudflare": "mid-size",
    "confluent": "mid-size",
    "creatorsagi inc": "startup",
    "credit acceptance": "mid-size",
    "datadog": "mid-size",
    "decked": "startup",
    "dexian": "mid-size",
    "digicert": "mid-size",
    "e-it": "startup",
    "easidoo": "startup",
    "elastic": "mid-size",
    "european centre for medium-range weather forecasts": "enterprise",
    "figma": "startup",
    "fusion life sciences technologies llc": "startup",
    "gen": "mid-size",
    "google": "enterprise",
    "gusto": "mid-size",
    "harvey nash": "mid-size",
    "hashicorp": "mid-size",
    "hireeazy": "startup",
    "humana": "enterprise",
    "ibm": "enterprise",
    "intel": "enterprise",
    "jpmorgan chase": "enterprise",
    "konecta": "mid-size",
    "linear": "startup",
    "ltm": "startup",
    "mansio": "startup",
    "marshall technologies inc": "startup",
    "mastercard": "enterprise",
    "meta": "enterprise",
    "meta platforms": "enterprise",
    "microsoft": "enterprise",
    "mongodb": "mid-size",
    "my code club": "startup",
    "netflix": "enterprise",
    "notion": "startup",
    "oasis equity group": "startup",
    "omdena": "startup",
    "onepay": "startup",
    "openai": "startup",
    "oracle": "enterprise",
    "pagerduty": "mid-size",
    "parametric": "mid-size",
    "pastures": "startup",
    "previse solutions": "startup",
    "puget sound energy": "mid-size",
    "reckitt": "enterprise",
    "relentless": "startup",
    "retool": "startup",
    "rlx (regional livestock exchanges)": "startup",
    "s piper staffing llc": "startup",
    "salesforce": "enterprise",
    "snowflake": "mid-size",
    "spectraforce": "mid-size",
    "stand 8 technology consulting": "startup",
    "stefanini latam": "mid-size",
    "stripe": "startup",
    "striveworks": "startup",
    "supabase": "startup",
    "t-mobile": "enterprise",
    "technosphere, inc.": "startup",
    "twilio": "mid-size",
    "uber": "enterprise",
    "university of maryland": "enterprise",
    "vercel": "startup",
    "visa": "enterprise",
    "walmart": "enterprise",
    "zillion technologies, inc.": "startup",
}

# Technical keywords used to determine if target role is technical
_TECHNICAL_ROLE_KEYWORDS = {
    "engineer", "developer", "architect", "data", "scientist",
    "analyst", "sde", "swe", "devops", "qa", "software", "ml",
    "machine learning", "backend", "frontend", "fullstack",
}


def _is_technical_role(target_role: str) -> bool:
    """Check if the target role contains technical keywords."""
    words = set(target_role.lower().split())
    return bool(words & _TECHNICAL_ROLE_KEYWORDS)


def _title_relevance_score(position: str, target_keywords: list[str]) -> int:
    """Score 0–60 based on keyword overlap. Primary ranking signal."""
    if not target_keywords:
        return 0

    position_words = set(position.lower().split())
    matches = sum(1 for kw in target_keywords if kw in position_words)
    raw = round((matches / len(target_keywords)) * 60)

    # Minimum 5 for recruiters (always somewhat relevant)
    category = categorize_title(position)
    if category == "recruiting" and raw < 5:
        raw = 5

    return raw


def _title_category_bonus(position: str, is_tech_role: bool) -> int:
    """Score 0–15 based on contact's title category relative to target role.

    Recruiting gets the highest bonus, but capped at 15 so it can't
    overpower a strong direct technical match (which scores up to 60).
    """
    category = categorize_title(position)

    if is_tech_role:
        return {"recruiting": 15, "technical": 10, "leadership": 5}.get(category, 0)
    else:
        return {"recruiting": 15, "leadership": 10, "technical": 5}.get(category, 0)


def _location_adjustment(company_name: str, position: str, preferred_location: str) -> int:
    """Score 0 or 10. Checks if preferred location appears in company name or position.

    LinkedIn CSV has no dedicated location column, so this is a best-effort
    heuristic. Returns 0 cleanly when no location preference is set or when
    no signal is found — never penalizes.
    """
    if not preferred_location:
        return 0
    loc = preferred_location.lower()
    haystack = f"{company_name} {position}".lower()
    if loc in haystack:
        return 10
    return 0


def _company_type_adjustment(
    normalized_company: str, preferred_type: str,
    enriched_types: dict[str, str] | None = None,
) -> int:
    """Score -5 to +15. Static lookup first, then LLM-enriched fallback.

    +15 if company matches preferred type (meaningful boost).
    -5  if company is in a lookup but is a different type (mild penalty).
     0  if company is unknown or preference is 'any'.
    """
    if preferred_type == "any" or not preferred_type:
        return 0
    # Check static lookup first, then enriched types
    known_type = _COMPANY_TYPE_LOOKUP.get(normalized_company)
    if known_type is None and enriched_types:
        known_type = enriched_types.get(normalized_company)
    if known_type is None:
        return 0  # Unknown company — no signal, no penalty
    if known_type == preferred_type:
        return 15
    return -5


def _email_bonus(email: str | None) -> int:
    """Score 0 or 5."""
    return 5 if email else 0


def get_unknown_companies(groups: dict[str, "CompanyGroup"]) -> list[str]:
    """Return normalized company names not in the static lookup."""
    return [name for name in groups if name not in _COMPANY_TYPE_LOOKUP]


def rank_companies(
    groups: dict[str, CompanyGroup],
    selections: dict[str, ContactSelection],
    preferences: Preferences,
    enriched_types: dict[str, str] | None = None,
) -> list[CompanyResult]:
    """Score and rank companies. Returns sorted list of CompanyResult.

    Score composition (0–100):
      - Title relevance:       0–60  (dominant signal)
      - Title category bonus:  0–15  (modest)
      - Company-type match:   -5–15  (meaningful when known)
      - Location adjustment:   0–10  (optional heuristic)
      - Email availability:    0–5   (small bonus)
      - Clamped to 0–100

    enriched_types: optional dict from LLM classification for companies
    not in the static lookup. Keys are normalized company names.

    Sorting: descending by score, alphabetically by company name on ties.
    """
    target_keywords = [w.lower() for w in preferences.target_role.split() if w.strip()]
    is_tech_role = _is_technical_role(preferences.target_role)

    results: list[CompanyResult] = []

    for norm_name, group in groups.items():
        selection = selections.get(norm_name)
        if not selection or not selection.contact:
            continue

        contact = selection.contact

        # Compute each scoring component independently — no hidden dependencies
        title_rel = _title_relevance_score(contact.position, target_keywords)
        cat_bonus = _title_category_bonus(contact.position, is_tech_role)
        loc_adj = _location_adjustment(group.display_name, contact.position, preferences.location)
        type_adj = _company_type_adjustment(norm_name, preferences.company_type, enriched_types)
        email_pts = _email_bonus(contact.email)

        raw_score = title_rel + cat_bonus + loc_adj + type_adj + email_pts
        score = max(0, min(100, raw_score))

        results.append(
            CompanyResult(
                company_name=group.display_name,
                contact_name=contact.full_name,
                contact_title=contact.position,
                contact_url=contact.url,
                contact_email=contact.email,
                path_label=label_path(score),
                score=score,
                contact_count=len(group.contacts),
            )
        )

    # Sort: descending score, then alphabetically on ties
    results.sort(key=lambda r: (-r.score, r.company_name))
    return results
