"""API routes for WarmPath MVP."""

import io
import json
from dataclasses import asdict

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from contact_selector import select_best_contact
from csv_parser import parse_csv
from grouper import group_by_company
from llm_advisor import classify_company_types
from models import Preferences, ParsingSummary
from normalizer import normalize_connections
from ranker import rank_companies, get_unknown_companies
from title_categorizer import categorize_all_contacts

router = APIRouter(prefix="/api")


@router.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    preferences: str = Form(...),
):
    """Main pipeline endpoint.

    Accepts multipart form:
      - file: LinkedIn connections CSV
      - preferences: JSON string with target_role, location, company_type

    Returns:
      { parsing_summary: {...}, results: [...] }
    """
    # --- Parse preferences JSON ---
    try:
        prefs_data = json.loads(preferences)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=422, detail="Invalid preferences format")

    target_role = prefs_data.get("target_role", "").strip()
    if not target_role:
        raise HTTPException(status_code=400, detail="Target role is required")

    prefs = Preferences(
        target_role=target_role,
        location=prefs_data.get("location", "").strip(),
        company_type=prefs_data.get("company_type", "any").strip(),
    )

    # --- Parse CSV ---
    try:
        contents = await file.read()
        rows, total_rows = parse_csv(io.BytesIO(contents))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # --- Normalize ---
    valid_records, excluded_rows = normalize_connections(rows)

    # --- Categorize all contacts (explicit preprocessing step) ---
    categorize_all_contacts(valid_records)

    # --- Group by company ---
    groups = group_by_company(valid_records)

    # --- Select best contact per company ---
    target_keywords = [w.lower() for w in prefs.target_role.split() if w.strip()]
    selections = {}
    for norm_name, group in groups.items():
        selections[norm_name] = select_best_contact(group, target_keywords)

    # --- Rank and label ---
    # Enrich unknown companies with LLM classification (if API key is set)
    # Only when user has a company type preference — skip the LLM call for "any"
    enriched_types: dict[str, str] = {}
    if prefs.company_type != "any":
        unknown = get_unknown_companies(groups)
        if unknown:
            enriched_types = await classify_company_types(unknown)

    results = rank_companies(groups, selections, prefs, enriched_types)

    # --- Build parsing summary ---
    summary = ParsingSummary(
        total_rows=total_rows,
        valid_connections=len(valid_records),
        excluded_rows=len(excluded_rows),
        exclusion_reasons=excluded_rows,
        unique_companies=len(groups),
    )

    return JSONResponse(content={
        "parsing_summary": asdict(summary),
        "results": [asdict(r) for r in results],
    })


@router.post("/details")
async def details(body: dict):
    """LLM-powered details for a selected company.

    Accepts JSON: { company_result: {...}, preferences: {...} }
    Always returns 200 with explanation, next_action, outreach_draft.
    Falls back to static content on any error.
    """
    from dataclasses import asdict as _asdict

    from llm_advisor import generate_details
    from models import CompanyResult, LLMDetails

    try:
        cr_data = body.get("company_result", {})
        pr_data = body.get("preferences", {})

        company_result = CompanyResult(
            company_name=cr_data.get("company_name", ""),
            contact_name=cr_data.get("contact_name", ""),
            contact_title=cr_data.get("contact_title", ""),
            contact_url=cr_data.get("contact_url", ""),
            contact_email=cr_data.get("contact_email"),
            path_label=cr_data.get("path_label", "Explore"),
            score=cr_data.get("score", 0),
            contact_count=cr_data.get("contact_count", 1),
        )

        prefs = Preferences(
            target_role=pr_data.get("target_role", ""),
            location=pr_data.get("location", ""),
            company_type=pr_data.get("company_type", "any"),
        )

        result = await generate_details(company_result, prefs)
        return _asdict(result)

    except Exception:
        # Never fail to the client
        return {
            "explanation": "Relevance based on your preferences.",
            "next_action": "Reach out via LinkedIn message.",
            "outreach_draft": "Hi, I noticed we're connected on LinkedIn. Would you be open to a quick chat?",
        }
