"""API routes for WarmPath MVP."""

import asyncio
import io
import json
import logging
import time
from dataclasses import asdict

from opentelemetry import context as otel_context

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from contact_selector import select_best_contact
from csv_parser import parse_csv
from grouper import group_by_company
from llm_advisor import classify_company_types, prefetch_details_background
from models import Preferences, ParsingSummary
from normalizer import normalize_connections
from ranker import rank_companies, get_unknown_companies
from title_categorizer import categorize_all_contacts

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)


@router.post("/analyze")
async def analyze(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    preferences: str = Form(...),
):
    t0 = time.perf_counter()

    def log_step(step: str):
        logger.info("[analyze] %s — %.2fs elapsed", step, time.perf_counter() - t0)

    log_step("start")

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
    log_step("prefs parsed")

    # --- Parse CSV ---
    try:
        contents = await file.read()
        rows, total_rows = parse_csv(io.BytesIO(contents))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    log_step(f"CSV parsed — {total_rows} rows")

    # --- Normalize ---
    valid_records, excluded_rows = normalize_connections(rows)
    log_step(f"normalized — {len(valid_records)} valid records")

    # --- Categorize ---
    categorize_all_contacts(valid_records)
    log_step("categorized")

    # --- Group by company ---
    groups = group_by_company(valid_records)
    log_step(f"grouped — {len(groups)} companies")

    # --- Select best contact per company ---
    target_keywords = [w.lower() for w in prefs.target_role.split() if w.strip()]
    selections = {}
    for norm_name, group in groups.items():
        selections[norm_name] = select_best_contact(group, target_keywords)
    log_step("contacts selected")

    # --- Classify unknown companies (capped at 5s to stay non-blocking) ---
    enriched_types: dict[str, str] = {}
    if prefs.company_type != "any":
        unknown = get_unknown_companies(groups)
        if unknown:
            log_step(f"classifying {len(unknown)} unknown companies")
            try:
                enriched_types = await asyncio.wait_for(
                    classify_company_types(unknown), timeout=5.0
                )
            except asyncio.TimeoutError:
                logger.warning("[analyze] classify_company_types timed out — skipping enrichment")
    log_step("enrichment done")

    results = rank_companies(groups, selections, prefs, enriched_types)
    log_step(f"ranked — {len(results)} results")

    # --- Kick off background LLM prefetch for top 10, linked to this trace ---
    # Capture the current trace context so background spans appear as children
    # of this HTTP request span in Phoenix, not as orphaned traces.
    captured_ctx = otel_context.get_current()

    async def _prefetch_with_trace_context():
        token = otel_context.attach(captured_ctx)
        try:
            await prefetch_details_background(results, prefs)
        finally:
            otel_context.detach(token)

    background_tasks.add_task(_prefetch_with_trace_context)
    log_step("background task queued")

    # --- Build parsing summary ---
    summary = ParsingSummary(
        total_rows=total_rows,
        valid_connections=len(valid_records),
        excluded_rows=len(excluded_rows),
        exclusion_reasons=excluded_rows,
        unique_companies=len(groups),
    )

    log_step("returning response")
    return JSONResponse(content={
        "parsing_summary": asdict(summary),
        "results": [asdict(r) for r in results],
    })


@router.post("/details")
async def details(body: dict):
    """Check server cache first; call LLM if not yet cached."""
    import cache
    from llm_advisor import generate_details, _build_fallback
    from models import CompanyResult

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

        cached = cache.get(company_result.contact_url)
        if cached:
            logger.info("[details] cache hit for %s", company_result.company_name)
            return asdict(cached)

        logger.info("[details] cache miss — calling LLM for %s", company_result.company_name)
        result = await generate_details(company_result, prefs)
        cache.set(company_result.contact_url, result)
        return asdict(result)

    except Exception as e:
        logger.error("[details] unexpected error: %s", e)
        return {
            "explanation": "Relevance based on your preferences.",
            "next_action": "Reach out via LinkedIn message.",
            "outreach_draft": "Hi, I noticed we're connected on LinkedIn. Would you be open to a quick chat?",
        }
