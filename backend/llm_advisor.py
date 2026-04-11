"""LLM Advisor — generates explanation, next action, outreach draft, and company type classification via OpenAI."""

import asyncio
import json
import logging
import os

from models import CompanyResult, LLMDetails, Preferences

logger = logging.getLogger(__name__)

_VALID_TYPES = {"startup", "mid-size", "enterprise"}

_CLASSIFY_PROMPT = """Classify each company below as exactly one of: startup, mid-size, enterprise.

Rules:
- startup: <1000 employees or founded in last ~10 years and still growing
- mid-size: ~1000–10000 employees
- enterprise: >10000 employees or a well-known Fortune 500 / large public company

Companies:
{company_list}

Respond as JSON only — a single object mapping company name to type.
Example: {{"Acme Corp": "startup", "Big Bank": "enterprise"}}"""


def _get_client():
    """Return an AsyncOpenAI client, or None if no API key is set."""
    from openai import AsyncOpenAI
    api_key = os.environ.get("LLM_API_KEY", "")
    if not api_key:
        return None
    base_url = os.environ.get("LLM_BASE_URL", "").strip() or None
    return AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=60.0)


async def classify_company_types(company_names: list[str]) -> dict[str, str]:
    """Classify unknown companies via a single LLM call.

    Returns a dict mapping normalized company name → type (startup/mid-size/enterprise).
    Returns empty dict on any failure (no API key, network error, bad response).
    """
    if not company_names:
        return {}

    client = _get_client()
    if not client:
        return {}

    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
    prompt = _CLASSIFY_PROMPT.format(
        company_list="\n".join(f"- {name}" for name in company_names)
    )

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        parsed = json.loads(content)
        result: dict[str, str] = {}
        for name, ctype in parsed.items():
            ctype_lower = ctype.strip().lower()
            if ctype_lower in _VALID_TYPES:
                result[name.strip().lower()] = ctype_lower
        return result

    except Exception as e:
        logger.error("Company classification LLM call failed: %s", e)
        return {}


_PROMPT_TEMPLATE = """You are a career networking advisor. Given the following context, produce three outputs.

Context:
- Job seeker's target role: {target_role}
- Preferred location: {location}
- Company type preference: {company_type}
- Company: {company_name}
- Contact: {contact_name}, {contact_title}
- Path strength: {path_label} (score: {score}/100)
- Email available: {has_email}

Produce:
1. EXPLANATION (2-3 sentences): Why this company/contact is relevant.
2. NEXT ACTION (1 sentence): The recommended next step, considering whether email is available.
3. OUTREACH DRAFT (3-5 sentences): A personalized message to the contact.

Format your response as JSON: {{"explanation": "...", "next_action": "...", "outreach_draft": "..."}}"""


def _build_fallback(result: CompanyResult, prefs: Preferences) -> LLMDetails:
    """Return personalized fallback content based on available company/contact data."""
    contact = result.contact_name
    title = result.contact_title or "professional"
    company = result.company_name
    role = prefs.target_role

    if result.path_label == "Warm Path":
        explanation = (
            f"{contact}'s role as {title} at {company} aligns closely with your target of {role}. "
            f"With a score of {result.score}/100, this is a high-priority connection worth reaching out to promptly. "
            f"A warm introduction here could fast-track your job search."
        )
        next_action = (
            f"Send {contact} a personalized LinkedIn message referencing your shared connection "
            f"and your interest in {role} opportunities at {company}."
        )
    elif result.path_label == "Stretch Path":
        explanation = (
            f"{contact} is a {title} at {company} — a worthwhile stretch connection for your {role} search. "
            f"Their insider perspective could surface unadvertised openings or referral opportunities. "
            f"A brief, genuine outreach has a good chance of getting a response."
        )
        next_action = (
            f"Reach out to {contact} on LinkedIn with a concise note about your {role} search "
            f"and ask if they'd be open to a 15-minute informational chat about {company}."
        )
    else:
        explanation = (
            f"{contact} works at {company} as {title}. "
            f"While this is an exploratory connection, they may have visibility into {role} openings "
            f"or be able to refer you to the right person internally."
        )
        next_action = (
            f"Send {contact} a brief, casual LinkedIn message to get on their radar "
            f"for future {role} opportunities at {company}."
        )

    if result.contact_email:
        outreach = (
            f"Hi {contact},\n\n"
            f"I hope you're doing well! I'm currently exploring {role} opportunities "
            f"and came across your profile — I'd love to hear about your experience at {company}. "
            f"Would you be open to a quick 15-minute call at your convenience?\n\n"
            f"Thanks so much,\n[Your name]"
        )
    else:
        outreach = (
            f"Hi {contact}, I noticed we're connected on LinkedIn and that you're at {company}. "
            f"I'm currently exploring {role} opportunities and would love to learn about your experience there. "
            f"Would you be open to a quick chat? Happy to work around your schedule."
        )

    return LLMDetails(explanation=explanation, next_action=next_action, outreach_draft=outreach)


async def generate_details(result: CompanyResult, prefs: Preferences) -> LLMDetails:
    """Call OpenAI to generate details. Falls back on any error."""
    client = _get_client()
    if not client:
        logger.warning("LLM_API_KEY not set — returning fallback content")
        return _build_fallback(result, prefs)

    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
    prompt = _PROMPT_TEMPLATE.format(
        target_role=prefs.target_role,
        location=prefs.location or "Not specified",
        company_type=prefs.company_type,
        company_name=result.company_name,
        contact_name=result.contact_name,
        contact_title=result.contact_title,
        path_label=result.path_label,
        score=result.score,
        has_email="Yes" if result.contact_email else "No",
    )

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        parsed = json.loads(content)
        fallback = _build_fallback(result, prefs)
        return LLMDetails(
            explanation=parsed.get("explanation", fallback.explanation),
            next_action=parsed.get("next_action", fallback.next_action),
            outreach_draft=parsed.get("outreach_draft", fallback.outreach_draft),
        )

    except Exception as e:
        logger.error("LLM call failed: %s", e)
        return _build_fallback(result, prefs)


async def prefetch_details_background(
    results: list[CompanyResult], prefs: Preferences
) -> None:
    """Background task: generate and cache details for ranks 1–10 only.

    Runs after the /analyze response is sent. Ranks 11+ are generated on-demand
    via /details when the user clicks a card.
    """
    import cache

    sem = asyncio.Semaphore(3)

    async def _fetch_and_cache(r: CompanyResult) -> None:
        async with sem:
            try:
                details = await generate_details(r, prefs)
                cache.set(r.contact_url, details)
                logger.info("Background prefetch done: %s", r.company_name)
            except Exception as e:
                logger.error("Background prefetch failed for %s: %s", r.company_name, e)

    batch = results[:10]
    if batch:
        await asyncio.gather(*[_fetch_and_cache(r) for r in batch])
