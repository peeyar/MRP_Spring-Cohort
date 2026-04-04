# Implementation Plan: WarmPath MVP

## Overview

Build a thin end-to-end working version first (backend pipeline → minimal frontend → LLM polish → optional tests). Each phase produces a demoable increment. Python FastAPI backend, React frontend.

## Tasks

### Phase 1: Backend Core Pipeline

- [x] 1. Set up backend project structure and data models
  - [x] 1.1 Create FastAPI project skeleton with `backend/` directory, `main.py`, `requirements.txt` (fastapi, uvicorn, python-multipart, python-dateutil)
    - _Requirements: 9.1_
  - [x] 1.2 Define all data model dataclasses in `backend/models.py`: `ConnectionRecord`, `Preferences`, `CompanyGroup`, `ContactSelection`, `CompanyResult`, `ParsingSummary`, `ExcludedRow`, `LLMDetails`
    - _Requirements: 1.4, 9.3_

- [x] 2. Implement CSV Parser and Connection Normalizer
  - [x] 2.1 Implement `backend/csv_parser.py` — `parse_csv(file)` that skips LinkedIn "Notes:" preamble, finds the header row, validates required columns, returns list of raw row dicts and total row count. Raise `ValueError` on missing columns listing which ones are absent.
    - _Requirements: 1.2, 1.3_
  - [x] 2.2 Implement `backend/normalizer.py` — `normalize_connections(rows)` that trims whitespace, parses `Connected On` ("DD Mon YYYY") to `datetime.date`, sets email to `None` when empty, excludes rows with empty Company, tracks excluded rows with reasons. Returns `(list[ConnectionRecord], list[ExcludedRow])`.
    - _Requirements: 1.4, 1.5, 1.6, 1.7_

- [x] 3. Implement Company Grouper and Title Categorizer
  - [x] 3.1 Implement `backend/grouper.py` — `group_by_company(records)` that normalizes company names (lowercase, strip whitespace, remove trailing legal suffixes from safe set: inc, llc, ltd, corp, corporation, co, company, plc, lp). Returns `dict[str, CompanyGroup]` with display name from first record seen.
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  - [x] 3.2 Implement `backend/title_categorizer.py` — `categorize_title(position)` using keyword matching to return one of: technical, recruiting, leadership, student, unknown.
    - _Requirements: 4.5_

- [x] 4. Implement Contact Selector
  - [x] 4.1 Implement `backend/contact_selector.py` — `select_best_contact(group, target_role_keywords)` that scores each contact by title-relevance keyword overlap (0–10), title category bonus (+2), email bonus (+1), and uses recency as tie-breaker. Returns `ContactSelection`.
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.6_

- [x] 5. Implement Ranker and Path Labeler
  - [x] 5.1 Implement `backend/ranker.py` — `rank_companies(groups, selections, preferences)` computing 0–100 score: title relevance (0–60), title category bonus (0–15), location adjustment (0–10), company-type adjustment (0–5 via small static lookup), email bonus (0–5). Clamp to 0–100. Sort descending by score, alphabetically on ties. Returns `list[CompanyResult]`.
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_
  - [x] 5.2 Implement `backend/path_labeler.py` — `label_path(score)` returning "Warm Path" (≥70), "Stretch Path" (40–69), "Explore" (<40).
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 6. Implement POST /api/analyze endpoint
  - [x] 6.1 Implement `backend/api.py` with `POST /api/analyze` that accepts multipart form (CSV file + JSON preferences string), validates target role is non-empty, orchestrates: csv_parser → normalizer → grouper → title_categorizer → contact_selector → ranker → path_labeler. Returns `{ parsing_summary, results }` JSON. Handle errors with appropriate HTTP status codes (400, 422, 500).
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 1.8, 2.3, 2.4, 2.5_
  - [x] 6.2 Wire `backend/main.py` to mount the API router with CORS middleware enabled for frontend dev server origin.
    - _Requirements: 9.1_

- [ ] 7. Checkpoint — Backend pipeline end-to-end verification
  - [ ] 7.1 Send `POST /api/analyze` with the sample `Connections.csv` and verify: response is valid JSON with `parsing_summary` and `results` keys, `parsing_summary.total_rows == valid_connections + excluded_rows`, results are sorted by score descending, each result contains all required fields (company_name, contact_name, contact_title, contact_url, contact_email, path_label, score, contact_count).
    - _Requirements: 9.2, 9.3, 1.8_

### Phase 2: Frontend MVP UI

- [x] 8. Set up React frontend project
  - [x] 8.1 Create React app in `frontend/` directory (Vite + React + TypeScript). Install axios for API calls. Define TypeScript interfaces matching backend response models (`CompanyResult`, `ParsingSummary`, `Preferences`).
    - _Requirements: 8.1_

- [x] 9. Implement Upload Area and Preferences Form
  - [x] 9.1 Create `UploadArea` component — file input that accepts `.csv` files and stores the selected file in parent state.
    - _Requirements: 1.1_
  - [x] 9.2 Create `PreferencesForm` component — target role (text input, required), location (text input, optional), company type (dropdown: startup, mid-size, enterprise, any). Validate target role is non-empty before enabling submit. On submit, send CSV + preferences to `POST /api/analyze`.
    - _Requirements: 2.1, 2.2_

- [x] 10. Implement Parsing Summary and Ranked Results List
  - [x] 10.1 Create `ParsingSummary` component — displays total rows, valid connections, excluded rows count, unique companies. Shown after successful analysis.
    - _Requirements: 8.8_
  - [x] 10.2 Create `ResultsList` component with `CompanyResultCard` sub-component — scrollable list showing company name, contact name + title, path label text, and score for each result. Initially show top 25 with "Show More" button.
    - _Requirements: 8.1, 8.2, 8.3_

- [x] 11. Add loading indicator and error handling
  - [x] 11.1 Create `LoadingIndicator` component shown while API call is in progress. Create `ErrorAlert` component for displaying API error messages.
    - _Requirements: 8.7, 8.9_

- [ ] 12. Checkpoint — Demoable end-to-end flow
  - [ ] 12.1 Verify: uploading CSV and submitting preferences renders the parsing summary bar and a ranked results list with company names, contact info, path labels, and scores. Verify error alert appears when target role is left empty. Verify loading indicator shows during API call.
    - _Requirements: 8.1, 8.2, 8.3, 8.7, 8.8, 8.9_

### Phase 3: LLM Details and UX Polish

- [x] 13. Implement LLM Advisor and POST /api/details endpoint
  - [x] 13.1 Implement `backend/llm_advisor.py` — `generate_details(company_result, preferences)` that constructs a structured prompt, calls OpenAI API (model via `LLM_MODEL` env var, key via `LLM_API_KEY`), parses JSON response into `LLMDetails`. On any error/timeout (15s), return static fallback content.
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_
  - [x] 13.2 Add `POST /api/details` endpoint to `backend/api.py` — accepts JSON with `company_result` + `preferences`, calls LLM Advisor, returns `{ explanation, next_action, outreach_draft }`. Always returns 200 (fallback on error).
    - _Requirements: 7.1, 7.5_

- [x] 14. Implement expandable Detail View in frontend
  - [x] 14.1 Create `DetailView` component — expanded panel below `CompanyResultCard` on click. Triggers `POST /api/details` on first expand (lazy load). Displays explanation, next action, and outreach draft. Cache results so re-expanding doesn't re-call API.
    - _Requirements: 8.5_

- [x] 15. Add copy-to-clipboard and color-coded path labels
  - [x] 15.1 Add copy-to-clipboard button for outreach draft text in `DetailView`.
    - _Requirements: 8.6_
  - [x] 15.2 Add color-coded path label badges in `CompanyResultCard`: green for Warm Path, yellow for Stretch Path, gray for Explore.
    - _Requirements: 8.4_

- [ ] 16. Checkpoint — Full feature demo-ready
  - [ ] 16.1 Verify full flow: upload CSV → enter preferences → see ranked results → click a company → detail view expands with explanation, next action, and outreach draft → copy-to-clipboard works → path labels are color-coded (green/yellow/gray). Verify fallback content appears when LLM_API_KEY is not set.
    - _Requirements: 8.4, 8.5, 8.6, 7.5_

### Phase 4: Minimal QA and Cleanup

- [ ]* 17. Backend smoke test and key unit tests
  - [ ]* 17.1 Write one backend smoke test for `POST /api/analyze` — upload a small CSV fixture, verify 200 response with valid `parsing_summary` and non-empty `results` array, verify each result has all required fields.
    - _Requirements: 9.2, 9.3_
  - [ ]* 17.2 Write unit tests for ranker score boundaries and path label thresholds — verify scores at 39, 40, 69, 70 produce correct path labels ("Explore", "Stretch Path", "Stretch Path", "Warm Path"). Verify scores are clamped to 0–100.
    - _Requirements: 5.1, 6.1, 6.2, 6.3, 6.4_
  - [ ]* 17.3 Write unit test for LLM advisor fallback — mock a failed LLM call and verify static fallback content is returned (explanation, next_action, outreach_draft all non-empty strings).
    - _Requirements: 7.5_

- [ ]* 18. README and final demo verification
  - [ ]* 18.1 Add `README.md` with setup instructions: how to install backend dependencies, start the FastAPI server, install frontend dependencies, start the React dev server, and configure `LLM_API_KEY` / `LLM_MODEL` env vars.
  - [ ]* 18.2 Final manual demo walkthrough: upload `Connections.csv`, enter preferences, verify ranked results, expand a company detail, copy outreach message. Confirm the app is demo-ready.

## Notes

- Phase 1 + 2 produce a demoable MVP without any LLM dependency
- Phase 3 adds LLM-powered details and visual polish
- Phase 4 tasks marked with `*` are optional and can be skipped for faster MVP delivery
- Frontend is a single page — no routing, no heavy styling framework
- Ranking uses the documented baseline scoring; no time spent on score tuning
- Company-type lookup is a small static dict (~20–50 entries), not a live API
- Ranking is fully deterministic — no LLM in the scoring pipeline
