# WarmPath MVP

Turn your LinkedIn connections into a ranked referral strategy.

Upload a LinkedIn connections CSV, enter your target role, and get a ranked list of companies with the best contact at each — scored, labeled, and ready for outreach.

## Live Demo

https://warm-path-beta.vercel.app

Test it using the included `Connections.csv` file or upload your own LinkedIn export.
Note: The app may take a few seconds to load initially as the backend is hosted on a free tier.

---

## 1. Problem

Job seekers are often advised to "network more" and get referrals, but a LinkedIn connections list does not translate into a clear strategy.

- Students and early professionals rely heavily on LinkedIn due to limited access to in-person networking
- Job boards are saturated, and many opportunities (especially startups) are not visible there
- People may have hundreds of connections but lack clarity on:
  - which companies to prioritize
  - which contacts are most relevant
  - how to initiate outreach

WarmPath addresses this gap by turning a static connections list into an actionable plan.

---

## 2. Solution

WarmPath converts your first-degree LinkedIn network into:

- Ranked companies based on relevance to your target role
- A single best contact per company
- Path strength labels:
  - **Warm Path** (strong referral opportunity)
  - **Stretch Path** (moderate opportunity)
  - **Explore** (low signal)
- Outreach-ready messages (AI-assisted or fallback)

---

## 3. What the MVP Does

1. Upload a LinkedIn connections CSV
2. Enter job preferences (target role, location, company type)
3. WarmPath:
   - groups connections by company
   - selects the most relevant contact per company
   - ranks companies using a deterministic scoring model (0–100)
4. Click a company to view:
   - explanation of relevance
   - recommended next action
   - outreach message

---

## 4. Data Source

### 4.1 Current MVP Uses

LinkedIn first-degree connections export (CSV)

### 4.2 Columns Used

- First Name
- Last Name
- URL
- Email Address
- Company
- Position
- Connected On

### 4.3 How This Data Is Accessed

- manually exported from LinkedIn
- no scraping
- no LinkedIn API integration
- no second-degree network access

This ensures transparency, user control, and reproducibility.

---

## 5. How to Try It

### 5.1 Option 1 — Use Demo Data

Use the included `Connections.csv`.

Steps:

1. Upload the file
2. Enter:
   - Target role: `software engineer`
   - Company type: `enterprise`
3. Click **Analyze**

Expected behavior:

- ~23 valid connections, ~3 excluded (missing company)
- ~21 unique companies ranked by relevance
- Warm Path / Stretch Path / Explore labels visible
- Expand any company to see explanation, next action, and outreach draft

### 5.2 Option 2 — Use Your Own LinkedIn Data

1. Go to LinkedIn → Settings → Data Privacy → Download my data → Download larger data archive
2. Request the Connections export
3. Download the CSV
4. Upload it into WarmPath

---

## 6. How It Works

**Pipeline:**

```
CSV → Normalize → Group by Company → Select Best Contact → Rank → Label → Display
```

- Core pipeline is fully deterministic
- LLM is used only on demand (not in ranking)
- System works without external dependencies via fallback responses

---

## 7. Ranking Logic (Simplified)

Each company is scored (0–100) using:

- Title relevance (0–60) → strongest signal
- Title category bonus (0–15)
- Company type:
  - match: +15
  - mismatch (known companies): -5
- Location match: +10 (only when signal exists)
- Email availability: +5

Then labeled:

- ≥70 → **Warm Path**
- 40–69 → **Stretch Path**
- <40 → **Explore**

Note:

- Ranking is deterministic (no LLM involvement)
- Filters (company type, location) act as **adjustments**, not overrides

---

## 8. AI-Assisted Outreach

WarmPath generates:

- Explanation (why this is relevant)
- Next action recommendation
- Personalized outreach message

### Configuration

```bash
export LLM_API_KEY=your_openai_key
export LLM_MODEL=gpt-4o-mini
```

| Behavior | Result |
|---|---|
| With API key | AI-generated responses |
| Without API key | Fallback deterministic templates |

This ensures the product remains usable in all environments.

---

## 9. Architecture

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript (Vite) |
| Backend | FastAPI |
| Data processing | Deterministic pipeline |
| LLM | Optional, invoked on demand |

Deployment:

- Frontend → Vercel
- Backend → Render

---

## 10. Project Structure

```
backend/
  main.py
  api.py
  models.py
  csv_parser.py
  normalizer.py
  title_categorizer.py
  grouper.py
  contact_selector.py
  ranker.py
  path_labeler.py
  llm_advisor.py
  requirements.txt

frontend/
  src/
    App.tsx
    api.ts
    components.tsx
    types.ts
    main.tsx
  package.json
  vite.config.ts
  tsconfig.json
  index.html

Connections.csv
README.md
```

---

## 11. Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 12. Limitations (MVP)

- Only first-degree connections
- Requires manual CSV upload
- No real-time job data integration
- No second-degree network analysis
- Limited company-type mapping (static lookup)
- Location signal is heuristic (no explicit location field in CSV)

---

## 13. Future Direction

WarmPath is designed to evolve into a network intelligence system.

Planned improvements:

- Direct authenticated data import (removing CSV dependency)
- Second-degree connection path discovery
- Startup and hidden opportunity discovery beyond job boards
- Personalized ranking using user behavior
- Outreach tracking and follow-up recommendations
- Integration with job signals and hiring data

---

## 14. Demo Flow

1. Upload CSV
2. Enter target role
3. View ranked companies
4. Expand a company
5. Copy outreach message

---

## 15. Summary

WarmPath helps move from:

> "I have connections"

to:

> "I know exactly who to reach out to, where, and why."
