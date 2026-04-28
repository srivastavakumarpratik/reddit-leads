"""
Reddit Lead Gen — Configuration
Pain phrases, filters, scoring, and domain tagging.
"""

# ─────────────────────────────────────────────
# Pain Phrase Queries
# Each entry: (query_string, track, domain_hint)
# track: "karma" or "authority"
# domain_hint: default domain tag if subreddit doesn't override
# ─────────────────────────────────────────────

QUERIES = [
    # ── Track 1: Karma (broad, high-volume) ──
    ("Excel too slow", "karma", "General"),
    ("Google Sheets limit rows", "karma", "General"),
    ("combine multiple spreadsheets", "karma", "General"),
    ("automate report every week", "karma", "Automation"),
    ("dashboard recommendation beginner", "karma", "General"),
    ("XLOOKUP not working", "karma", "General"),
    ("Power Query combine files", "karma", "General"),
    ("pivot table help", "karma", "General"),

    # ── Track 2: Domain Pain (buyer signals) ──
    # Finance
    ("budget vs actual reporting", "authority", "Finance"),
    ("consolidate financial reports multiple companies", "authority", "Finance"),
    ("multi-entity finance dashboard", "authority", "Finance"),
    ("cash flow forecasting dashboard", "authority", "Finance"),
    ("FP&A reporting problem", "authority", "Finance"),

    # E-commerce
    ("Shopify reporting too many spreadsheets", "authority", "E-commerce"),
    ("Amazon seller dashboard", "authority", "E-commerce"),
    ("track ROAS across channels", "authority", "E-commerce"),
    ("e-commerce margin tracking", "authority", "E-commerce"),

    # Healthcare
    ("healthcare KPI dashboard", "authority", "Healthcare"),
    ("patient reporting NHS", "authority", "Healthcare"),
    ("clinical data reporting", "authority", "Healthcare"),

    # Construction / Engineering
    ("construction project tracker dashboard", "authority", "Construction"),
    ("equipment hire dashboard", "authority", "Construction"),
    ("manpower planning dashboard", "authority", "Construction"),

    # PMO / Project Management
    ("PMO dashboard Power BI", "authority", "PMO"),
    ("project milestone tracker", "authority", "PMO"),
    ("executive KPI dashboard", "authority", "PMO"),

    # Real Estate
    ("real estate portfolio dashboard", "authority", "Real Estate"),
    ("rent roll reporting", "authority", "Real Estate"),

    # Education
    ("student performance dashboard", "authority", "Education"),
    ("tutoring business reporting", "authority", "Education"),

    # Marketing
    ("marketing dashboard manual reporting", "authority", "Marketing"),
    ("campaign performance reporting", "authority", "Marketing"),
    ("PPC reporting across platforms", "authority", "Marketing"),

    # Tech / SaaS / Startups
    ("investor dashboard startup", "authority", "Tech/SaaS"),
    ("SaaS metrics dashboard", "authority", "Tech/SaaS"),
    ("cohort analysis reporting", "authority", "Tech/SaaS"),
    ("burn rate tracking", "authority", "Tech/SaaS"),

    # HR / People Analytics
    ("headcount dashboard", "authority", "HR/People"),
    ("attrition dashboard HR", "authority", "HR/People"),
    ("people analytics reporting", "authority", "HR/People"),

    # Automation-specific
    ("send report email automatically Power BI", "authority", "Automation"),
    ("Power Automate PDF report", "authority", "Automation"),
    ("automate SharePoint reporting", "authority", "Automation"),
    ("n8n reporting workflow", "authority", "Automation"),
    ("scheduled report email", "authority", "Automation"),

    # Technical Authority (r/powerbi core)
    ("DAX calculate filter context", "authority", "General"),
    ("star schema Power BI", "authority", "General"),
    ("Power BI slow performance", "authority", "General"),
    ("Power Query M multiple files folder", "authority", "General"),
    ("measures vs calculated column", "authority", "General"),
    ("TMDL Tabular Editor", "authority", "General"),
    ("Deneb custom visual Power BI", "authority", "General"),
    ("Power BI data model best practice", "authority", "General"),
]

# ─────────────────────────────────────────────
# Negative Keywords (discard post if any match)
# Matched against title + selftext, case-insensitive
# ─────────────────────────────────────────────

NEGATIVE_KEYWORDS = [
    "homework",
    "assignment",
    "class project",
    "coursework",
    "school project",
    "hiring",
    "job posting",
    "we're looking for",
    "we are hiring",
    "job opening",
    "ELI5",
    "explain like",
    "meme",
    "shitpost",
    "interview prep",
    "certification exam",
    "PL-300 exam",
    "practice test",
    "exam question",
    "upvote if",
    "karma farming",
    "onlyfans",
]

# ─────────────────────────────────────────────
# Org-Size Signal Phrases
# If any match in post body → org_signal = True
# ─────────────────────────────────────────────

ORG_SIGNAL_PHRASES = [
    "our company",
    "our team",
    "our department",
    "our organization",
    "our organisation",
    "we have",
    "my team",
    "my department",
    "my company",
    "employees",
    "headcount",
    "our clients",
    "our customers",
    "business owner",
    "my business",
    "our business",
    "my firm",
    "our firm",
    "multiple locations",
    "multiple stores",
    "multiple branches",
    "franchises",
    "subsidiaries",
    "group of companies",
    "parent company",
]

# ─────────────────────────────────────────────
# Subreddit → Domain Override
# If post is from a known subreddit, override domain_hint
# ─────────────────────────────────────────────

SUBREDDIT_DOMAIN_MAP = {
    "ecommerce": "E-commerce",
    "shopify": "E-commerce",
    "FulfillmentByAmazon": "E-commerce",
    "AmazonSeller": "E-commerce",
    "FPandA": "Finance",
    "accounting": "Finance",
    "CFO": "Finance",
    "financialmodelling": "Finance",
    "startups": "Tech/SaaS",
    "SaaS": "Tech/SaaS",
    "EntrepreneurRideAlong": "Tech/SaaS",
    "marketing": "Marketing",
    "PPC": "Marketing",
    "analytics": "Marketing",
    "projectmanagement": "PMO",
    "humanresources": "HR/People",
    "peopleanalytics": "HR/People",
    "realestateinvesting": "Real Estate",
    "CommercialRealEstate": "Real Estate",
    "healthIT": "Healthcare",
    "Construction": "Construction",
    "nocode": "Automation",
    "zapier": "Automation",
    "n8n": "Automation",
    "Automate": "Automation",
    "powerbi": "General",
    "BusinessIntelligence": "General",
    "datascience": "General",
    "excel": "General",
    "googlesheets": "General",
    "learnpython": "General",
    "dashboards": "General",
}

# ─────────────────────────────────────────────
# Persona Selection
# subreddit → persona, with track as tiebreaker
# ─────────────────────────────────────────────

KARMA_SUBREDDITS = {
    "excel", "googlesheets", "dashboards",
    "learnpython", "Automate",
}

DIAGNOSTIC_SUBREDDITS = {
    "powerbi", "BusinessIntelligence",
    "datascience", "analytics",
}

AUTOMATION_SUBREDDITS = {
    "nocode", "zapier", "n8n",
}

# Everything else in Track 2 → Business Translator

# ─────────────────────────────────────────────
# Scoring Thresholds
# ─────────────────────────────────────────────

# Post must have at least this score to not be auto-discarded
MIN_POST_SCORE = 1

# Priority H: org_signal OR (comments < this AND score > SCORE_FLOOR AND domain specific)
HIGH_PRIORITY_MAX_COMMENTS = 5
HIGH_PRIORITY_MIN_SCORE = 3

# Priority M: domain specific AND comments below this
MEDIUM_PRIORITY_MAX_COMMENTS = 15

# ─────────────────────────────────────────────
# Reddit Search Settings
# ─────────────────────────────────────────────

SEARCH_SORT = "new"
SEARCH_TIME_FILTER = "day"
SEARCH_LIMIT_PER_QUERY = 25
RATE_LIMIT_DELAY_SECONDS = 1.5

# PRAW user agent (username injected at runtime)
USER_AGENT_TEMPLATE = "python:betterbi-reddit-leads:v1.0 (by /u/{username})"
