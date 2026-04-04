---
inclusion: always
---

# WarmPath — Project Context

## What is WarmPath?
WarmPath is a hackathon project (1-week scope) that helps job seekers turn their first-degree LinkedIn connections into ranked referral opportunities and outreach recommendations.

## Problem
Students and early-career job seekers are told to "network more" and "get referrals," but they lack equal access to in-person events, insider circles, or strong alumni introductions. A LinkedIn connections list doesn't automatically become a job-search strategy. Many people also miss smaller companies and startups that aren't top-of-mind.

## MVP Goal
Allow a user to upload a LinkedIn first-degree connections CSV and enter job preferences. The system then:
- Parses and normalizes connections
- Groups contacts by company
- Identifies the best contact at each company
- Ranks companies by relevance to the user's target role, location, and company type preference
- Labels each result with a path strength (Warm Path, Stretch Path, or Explore)
- Recommends the next best action
- Generates a concise outreach draft for the selected contact

## Key Constraints
- MVP uses only first-degree connections (no second-degree graph)
- No live LinkedIn scraping
- No automatic message sending
- Email addresses may be missing for many contacts
- Must be demo-friendly and completable in 1 week

## Output Per Company
- Company name
- Best contact (name + title)
- Path label (Warm Path / Stretch Path / Explore)
- Score
- Explanation
- Next action recommendation
- Outreach message draft

## Architecture Preferences
- Frontend: React or Next.js (simple dashboard with upload + preferences + ranked results)
- Backend: Python FastAPI
- Storage: Local JSON or SQLite
- Modular components for incremental implementation

## Design Principles
- Deterministic logic first for parsing, grouping, ranking, and best-contact selection
- LLM only for reasoning summaries, next-action suggestions, and outreach drafting
- Simple, demo-friendly workflow
- Keep scope realistic for a hackathon

## Available CSV Columns
- First Name, Last Name, URL, Email Address, Company, Position, Connected On
