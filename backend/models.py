"""Data models for WarmPath MVP."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class ConnectionRecord:
    """One normalized LinkedIn connection."""

    first_name: str
    last_name: str
    full_name: str  # "{first_name} {last_name}"
    url: str  # LinkedIn profile URL
    email: str | None  # None if not provided
    company: str  # Original company name (trimmed)
    position: str  # Original position title (trimmed)
    connected_on: date  # Parsed from "DD Mon YYYY"
    title_category: str = "unknown"  # technical, recruiting, leadership, student, unknown


@dataclass
class Preferences:
    """User-supplied job search parameters."""

    target_role: str  # Free text, required
    location: str = ""  # Free text, optional (empty = unspecified)
    company_type: str = "any"  # startup, mid-size, enterprise, any


@dataclass
class CompanyGroup:
    """Internal grouping structure."""

    normalized_name: str  # Lowercased, suffix-stripped key
    display_name: str  # Original casing from first record
    contacts: list[ConnectionRecord] = field(default_factory=list)


@dataclass
class ContactSelection:
    """Result of best-contact selection for one company."""

    contact: ConnectionRecord
    selection_score: float  # Internal score used for selection


@dataclass
class LLMDetails:
    """Response from the LLM Advisor."""

    explanation: str  # 2–3 sentences
    next_action: str  # 1 sentence
    outreach_draft: str  # 3–5 sentences


@dataclass
class CompanyResult:
    """Output object for one company in the ranked results."""

    company_name: str  # Display name
    contact_name: str  # Best contact full name
    contact_title: str  # Best contact position
    contact_url: str  # Best contact LinkedIn URL
    contact_email: str | None  # Nullable
    path_label: str  # "Warm Path" | "Stretch Path" | "Explore"
    score: int  # 0–100
    contact_count: int  # Number of connections at this company


@dataclass
class ExcludedRow:
    """A row excluded during CSV parsing."""

    row_number: int
    reason: str  # e.g., "Empty company field"


@dataclass
class ParsingSummary:
    """Statistics returned after CSV processing."""

    total_rows: int  # Total data rows in CSV (excluding header/notes)
    valid_connections: int  # Rows that produced a ConnectionRecord
    excluded_rows: int  # Rows excluded (with reasons)
    exclusion_reasons: list[ExcludedRow] = field(default_factory=list)
    unique_companies: int = 0  # Distinct normalized company names
