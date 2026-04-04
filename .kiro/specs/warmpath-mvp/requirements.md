# Requirements Document

## Introduction

WarmPath is a hackathon MVP (1-week scope) that helps job seekers turn their first-degree LinkedIn connections into ranked referral opportunities and personalized outreach recommendations. A user uploads a LinkedIn connections CSV, enters job preferences (target role, preferred location, company-type preference), and receives a ranked list of companies with the best contact at each, a path-strength label, a relevance score, an explanation, a next-action recommendation, and a draft outreach message.

## Glossary

- **Dashboard**: The single-page React/Next.js frontend that provides the upload area, preferences form, and ranked results view.
- **CSV_Parser**: The backend module responsible for reading, validating, and normalizing a LinkedIn connections CSV file.
- **Connection_Record**: A normalized data object representing one LinkedIn connection, containing first name, last name, profile URL, email address (optional), company name, position title, and connected-on date.
- **Preferences**: A user-supplied object containing target role keywords, preferred location, and company-type preference (e.g., startup, mid-size, enterprise, any).
- **Company_Grouper**: The backend module that groups Connection_Records by normalized company name.
- **Contact_Selector**: The backend module that selects the single best contact at each company based on title relevance to the user's target role and connection recency.
- **Ranker**: The backend module that scores and sorts companies by relevance to the user's Preferences.
- **Path_Labeler**: The backend module that assigns a path-strength label (Warm Path, Stretch Path, or Explore) to each company based on its relevance score.
- **LLM_Advisor**: The backend module that calls an LLM to generate a reasoning explanation, a next-action recommendation, and an outreach message draft for a given company result.
- **Company_Result**: The output object for one company containing: company name, best contact (name + title), path label, score, explanation, next-action recommendation, and outreach message draft.
- **API**: The Python FastAPI backend that orchestrates all processing modules and serves results to the Dashboard.

## Requirements

### Requirement 1: Upload LinkedIn Connections CSV

**User Story:** As a job seeker, I want to upload my LinkedIn connections CSV file, so that the system can analyze my network for referral opportunities.

#### Acceptance Criteria

1. WHEN the user selects a CSV file through the Dashboard, THE Dashboard SHALL send the file to the API for processing.
2. WHEN the API receives a CSV file, THE CSV_Parser SHALL accept files that contain the columns: First Name, Last Name, URL, Email Address, Company, Position, Connected On.
3. IF the uploaded file is not a valid CSV or is missing required columns, THEN THE API SHALL return a descriptive error message identifying the missing columns or format problem.
4. WHEN a valid CSV is parsed, THE CSV_Parser SHALL produce a list of Connection_Records with trimmed whitespace on all string fields.
5. WHEN a CSV row has an empty Company field, THE CSV_Parser SHALL exclude that row from further processing.
6. WHEN a CSV row has an empty Email Address field, THE CSV_Parser SHALL retain the Connection_Record with the email field set to null.
7. THE CSV_Parser SHALL parse the Connected On field into a standard date format (ISO 8601).
8. AFTER successful parsing, THE API SHALL return a parsing summary including: total rows processed, valid connections retained, excluded rows (with reason), and unique companies identified.

### Requirement 2: Enter Job Preferences

**User Story:** As a job seeker, I want to enter my target role, preferred location, and company-type preference, so that the system can rank my connections by relevance to my goals.

#### Acceptance Criteria

1. THE Dashboard SHALL provide a form with fields for target role keywords (free text), preferred location (free text), and company-type preference (dropdown: startup, mid-size, enterprise, any).
2. WHEN the user submits the preferences form, THE Dashboard SHALL send the Preferences object to the API.
3. IF the target role keywords field is empty, THEN THE API SHALL return an error message stating that target role is required.
4. WHEN the preferred location field is empty, THE API SHALL treat location as unspecified and skip location-based scoring adjustments.
5. WHEN the company-type preference is set to "any", THE API SHALL skip company-type scoring adjustments.

### Requirement 3: Group Connections by Company

**User Story:** As a job seeker, I want my connections grouped by company, so that I can see all my contacts at each organization in one place.

#### Acceptance Criteria

1. WHEN the CSV_Parser produces a list of Connection_Records, THE Company_Grouper SHALL group records by normalized company name.
2. THE Company_Grouper SHALL normalize company names using light normalization: trimming whitespace, lowercasing for matching, and optionally removing a limited safe set of common legal suffixes (e.g., Inc, LLC, Ltd, Corp) only when clearly present at the end of the name.
3. WHEN two or more Connection_Records share the same normalized company name, THE Company_Grouper SHALL place them in a single group.
4. THE Company_Grouper SHALL produce one group per unique normalized company name, each containing one or more Connection_Records.

### Requirement 4: Select Best Contact per Company

**User Story:** As a job seeker, I want the system to identify the single best contact at each company, so that I know exactly who to reach out to.

#### Acceptance Criteria

1. WHEN a company group contains one or more Connection_Records, THE Contact_Selector SHALL select exactly one Connection_Record as the best contact.
2. THE Contact_Selector SHALL score each Connection_Record based on title relevance to the user's target role keywords.
3. WHEN two Connection_Records have equal title-relevance scores, THE Contact_Selector SHALL prefer the more recently connected contact (later Connected On date).
4. WHEN a Connection_Record has a non-null email address, THE Contact_Selector SHALL add a small bonus to that contact's selection score.
5. THE Contact_Selector SHALL categorize contact titles into broad groups such as technical, recruiting, leadership, student, and unknown, and MAY use these categories as additional deterministic scoring signals.
6. THE Contact_Selector SHALL return the selected contact's full name, position title, profile URL, and email address (if available).

### Requirement 5: Rank Companies by Relevance

**User Story:** As a job seeker, I want companies ranked by how relevant they are to my job goals, so that I can prioritize my outreach efforts.

#### Acceptance Criteria

1. WHEN the Company_Grouper and Contact_Selector have produced results, THE Ranker SHALL compute a relevance score (0–100) for each company.
2. THE Ranker SHALL factor in the best contact's title relevance to the target role keywords as the primary scoring signal.
3. WHEN the user specifies a preferred location, THE Ranker MAY apply a small heuristic score adjustment if location-related text is present in the contact's position field or in an optional company metadata dataset. IF no location signal is available, THEN the Ranker SHALL skip location scoring for that company.
4. Company-type matching for MVP SHALL rely only on a small static lookup or simple deterministic heuristics. WHEN the user specifies a company-type preference other than "any", THE Ranker SHALL increase the score for companies matching that type. IF no company-type information is available for a company, THEN the Ranker SHALL skip company-type scoring for that company.
5. THE Ranker SHALL sort companies in descending order by relevance score.
6. WHEN two companies have the same relevance score, THE Ranker SHALL sort them alphabetically by company name.
7. THE Ranker SHALL use deterministic logic only; the Ranker SHALL NOT call an LLM.

### Requirement 6: Label Path Strength

**User Story:** As a job seeker, I want each company labeled with a path strength (Warm Path, Stretch Path, or Explore), so that I can quickly gauge how strong each referral opportunity is.

#### Acceptance Criteria

1. WHEN the Ranker assigns a relevance score to a company, THE Path_Labeler SHALL assign exactly one label from: Warm Path, Stretch Path, Explore.
2. WHEN the relevance score is 70 or above, THE Path_Labeler SHALL assign the label "Warm Path".
3. WHEN the relevance score is between 40 and 69 (inclusive), THE Path_Labeler SHALL assign the label "Stretch Path".
4. WHEN the relevance score is below 40, THE Path_Labeler SHALL assign the label "Explore".
5. THE Path_Labeler SHALL use deterministic threshold logic only; the Path_Labeler SHALL NOT call an LLM.

### Requirement 7: Generate Explanation, Next Action, and Outreach Draft

**User Story:** As a job seeker, I want a brief explanation of why a company is relevant, a recommended next action, and a ready-to-send outreach message, so that I can act on each opportunity without starting from scratch.

#### Acceptance Criteria

1. THE system SHALL generate LLM-based explanation, next action, and outreach details only for a user-selected Company_Result, or for a limited number of top-ranked results, to keep response time suitable for the MVP.
2. WHEN LLM generation is triggered, THE LLM_Advisor SHALL generate a concise explanation (2–3 sentences) of why the company is relevant to the user's Preferences.
3. WHEN LLM generation is triggered, THE LLM_Advisor SHALL generate a next-action recommendation (one sentence) appropriate to the path label and whether an email address is available.
4. WHEN LLM generation is triggered, THE LLM_Advisor SHALL generate an outreach message draft (3–5 sentences) personalized with the contact's name, title, company, and the user's target role.
5. IF the LLM_Advisor call fails or times out, THEN THE API SHALL return a fallback explanation ("Relevance based on your preferences"), a fallback next action ("Reach out via LinkedIn message"), and a fallback outreach template with placeholders.
6. THE LLM_Advisor SHALL be the only module that calls an external LLM; all other modules SHALL use deterministic logic.

### Requirement 8: Display Ranked Results

**User Story:** As a job seeker, I want to see a ranked list of companies with their scores, labels, best contacts, and outreach details, so that I can take action on my strongest referral paths.

#### Acceptance Criteria

1. WHEN the API returns ranked Company_Results, THE Dashboard SHALL initially display only the top N ranked companies, where N is configurable (default N = 25 for MVP).
2. THE Dashboard SHALL display the results in a scrollable list ordered by descending relevance score.
3. THE Dashboard SHALL display for each Company_Result: company name, best contact name, best contact title, path label, and relevance score.
4. THE Dashboard SHALL visually distinguish path labels using color coding: green for Warm Path, yellow for Stretch Path, gray for Explore.
5. WHEN the user clicks on a Company_Result, THE Dashboard SHALL show the explanation, next-action recommendation, and outreach message draft in an expanded detail view.
6. THE Dashboard SHALL provide a copy-to-clipboard button for the outreach message draft.
7. WHILE the API is processing the uploaded CSV and Preferences, THE Dashboard SHALL display a loading indicator.
8. AFTER processing completes, THE Dashboard SHALL display the parsing summary (total rows processed, valid connections retained, excluded rows, unique companies identified) above the results list.
9. IF the API returns an error, THEN THE Dashboard SHALL display the error message in a visible alert area.

### Requirement 9: API Orchestration

**User Story:** As a developer, I want a single API endpoint that accepts the CSV and preferences and returns ranked results, so that the frontend has a simple integration point.

#### Acceptance Criteria

1. THE API SHALL expose a POST endpoint that accepts a CSV file upload and a Preferences JSON object.
2. WHEN the API receives a valid request, THE API SHALL invoke the CSV_Parser, Company_Grouper, Contact_Selector, Ranker, and Path_Labeler in sequence and return the list of Company_Results.
3. THE API SHALL return Company_Results as a JSON array, each element containing: company name, best contact name, best contact title, best contact profile URL, best contact email (nullable), path label, and relevance score. The response SHALL also include the parsing summary object.
4. IF any processing step fails, THEN THE API SHALL return an HTTP error response with a descriptive message and appropriate status code.
5. THE deterministic processing pipeline (excluding LLM calls) SHALL handle typical LinkedIn connection exports with responsive performance suitable for MVP demo usage.

## Assumptions

- Users export their LinkedIn connections CSV using LinkedIn's standard data export feature, which produces the columns listed in the Glossary.
- The MVP does not persist user data between sessions; each upload is a fresh analysis.
- Company-type classification (startup, mid-size, enterprise) in the MVP relies on simple heuristics or a static lookup rather than a live data source.
- The LLM provider API key is configured as an environment variable on the backend.
- The system runs locally or on a single server; no multi-tenant or scaling concerns for the MVP.

## Out of Scope

- Second-degree connection analysis
- Live LinkedIn API scraping or OAuth integration
- Automatic message sending (email or LinkedIn)
- User authentication or account management
- Persistent storage of user data across sessions
- Mobile-responsive design (desktop-first for demo)
- Batch processing of multiple CSV files
- Integration with job boards or applicant tracking systems
