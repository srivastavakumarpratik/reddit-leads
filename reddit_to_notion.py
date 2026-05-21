#!/usr/bin/env python3
"""
Reddit -> Notion lead fetcher.

Searches Reddit for posts matching pain-phrase queries, scores them, and
inserts new ones into a Notion database. Dedup is by URL against Notion.

Setup:
    pip install praw notion-client

Env vars:
    REDDIT_CLIENT_ID
    REDDIT_CLIENT_SECRET
    REDDIT_USER_AGENT       (any string, e.g. "betterbi-leads:v1")
    NOTION_TOKEN            (integration token from notion.so/my-integrations)
    NOTION_DATABASE_ID      (the 32-char UUID of your Reddit Leads database)

Run:
    python reddit_to_notion.py
"""

import os
import sys
import time
from datetime import datetime, timezone

import praw
from notion_client import Client as Notion


# ── Queries: (query, track, domain_hint) ─────────────────────────────────────

QUERIES = [
    ("Excel too slow", "Karma", "General"),
    ("Google Sheets limit rows", "Karma", "General"),
    ("combine multiple spreadsheets", "Karma", "General"),
    ("automate report every week", "Karma", "Automation"),
    ("dashboard recommendation beginner", "Karma", "General"),
    ("XLOOKUP not working", "Karma", "General"),
    ("Power Query combine files", "Karma", "General"),
    ("pivot table help", "Karma", "General"),
    ("budget vs actual reporting", "Authority", "Finance"),
    ("consolidate financial reports multiple companies", "Authority", "Finance"),
    ("multi-entity finance dashboard", "Authority", "Finance"),
    ("cash flow forecasting dashboard", "Authority", "Finance"),
    ("FP&A reporting problem", "Authority", "Finance"),
    ("Shopify reporting too many spreadsheets", "Authority", "E-commerce"),
    ("Amazon seller dashboard", "Authority", "E-commerce"),
    ("track ROAS across channels", "Authority", "E-commerce"),
    ("e-commerce margin tracking", "Authority", "E-commerce"),
    ("healthcare KPI dashboard", "Authority", "Healthcare"),
    ("patient reporting NHS", "Authority", "Healthcare"),
    ("clinical data reporting", "Authority", "Healthcare"),
    ("construction project tracker dashboard", "Authority", "Construction"),
    ("equipment hire dashboard", "Authority", "Construction"),
    ("manpower planning dashboard", "Authority", "Construction"),
    ("PMO dashboard Power BI", "Authority", "PMO"),
    ("project milestone tracker", "Authority", "PMO"),
    ("executive KPI dashboard", "Authority", "PMO"),
    ("real estate portfolio dashboard", "Authority", "Real Estate"),
    ("rent roll reporting", "Authority", "Real Estate"),
    ("student performance dashboard", "Authority", "Education"),
    ("tutoring business reporting", "Authority", "Education"),
    ("marketing dashboard manual reporting", "Authority", "Marketing"),
    ("campaign performance reporting", "Authority", "Marketing"),
    ("PPC reporting across platforms", "Authority", "Marketing"),
    ("investor dashboard startup", "Authority", "Tech/SaaS"),
    ("SaaS metrics dashboard", "Authority", "Tech/SaaS"),
    ("cohort analysis reporting", "Authority", "Tech/SaaS"),
    ("burn rate tracking", "Authority", "Tech/SaaS"),
    ("headcount dashboard", "Authority", "HR/People"),
    ("attrition dashboard HR", "Authority", "HR/People"),
    ("people analytics reporting", "Authority", "HR/People"),
    ("send report email automatically Power BI", "Authority", "Automation"),
    ("Power Automate PDF report", "Authority", "Automation"),
    ("automate SharePoint reporting", "Authority", "Automation"),
    ("n8n reporting workflow", "Authority", "Automation"),
    ("scheduled report email", "Authority", "Automation"),
    ("DAX calculate filter context", "Authority", "General"),
    ("star schema Power BI", "Authority", "General"),
    ("Power BI slow performance", "Authority", "General"),
    ("Power Query M multiple files folder", "Authority", "General"),
    ("measures vs calculated column", "Authority", "General"),
    ("TMDL Tabular Editor", "Authority", "General"),
    ("Deneb custom visual Power BI", "Authority", "General"),
    ("Power BI data model best practice", "Authority", "General"),
]

NEGATIVE_KEYWORDS = [
    "homework", "assignment", "class project", "coursework", "school project",
    "hiring", "job posting", "we're looking for", "we are hiring", "job opening",
    "ELI5", "explain like", "meme", "shitpost", "interview prep",
    "certification exam", "PL-300 exam", "practice test", "exam question",
    "upvote if", "karma farming", "onlyfans",
]

ORG_SIGNAL_PHRASES = [
    "our company", "our team", "our department", "our organization",
    "our organisation", "we have", "my team", "my department", "my company",
    "employees", "headcount", "our clients", "our customers", "business owner",
    "my business", "our business", "my firm", "our firm", "multiple locations",
    "multiple stores", "multiple branches", "franchises", "subsidiaries",
    "group of companies", "parent company",
]

SUBREDDIT_DOMAIN_MAP = {
    "ecommerce": "E-commerce", "shopify": "E-commerce",
    "FulfillmentByAmazon": "E-commerce", "AmazonSeller": "E-commerce",
    "FPandA": "Finance", "accounting": "Finance", "CFO": "Finance",
    "financialmodelling": "Finance", "startups": "Tech/SaaS",
    "SaaS": "Tech/SaaS", "EntrepreneurRideAlong": "Tech/SaaS",
    "marketing": "Marketing", "PPC": "Marketing", "analytics": "Marketing",
    "projectmanagement": "PMO", "humanresources": "HR/People",
    "peopleanalytics": "HR/People", "realestateinvesting": "Real Estate",
    "CommercialRealEstate": "Real Estate", "healthIT": "Healthcare",
    "Construction": "Construction", "nocode": "Automation",
    "zapier": "Automation", "n8n": "Automation", "Automate": "Automation",
    "powerbi": "General", "BusinessIntelligence": "General",
    "datascience": "General", "excel": "General", "googlesheets": "General",
    "learnpython": "General", "dashboards": "General",
}

MIN_POST_SCORE = 1
HIGH_PRIORITY_MAX_COMMENTS = 5
HIGH_PRIORITY_MIN_SCORE = 3
MEDIUM_PRIORITY_MAX_COMMENTS = 15
SEARCH_LIMIT_PER_QUERY = 25
RATE_LIMIT_DELAY = 1.5


# ── Filtering and scoring ────────────────────────────────────────────────────

def has_negative(text):
    t = text.lower()
    return any(k.lower() in t for k in NEGATIVE_KEYWORDS)


def has_org_signal(text):
    t = text.lower()
    return any(p.lower() in t for p in ORG_SIGNAL_PHRASES)


def get_priority(org, score, comments, domain):
    if org:
        return "H"
    specific = domain != "General"
    if comments < HIGH_PRIORITY_MAX_COMMENTS and score > HIGH_PRIORITY_MIN_SCORE and specific:
        return "H"
    if specific and comments < MEDIUM_PRIORITY_MAX_COMMENTS:
        return "M"
    if comments < HIGH_PRIORITY_MAX_COMMENTS and score >= MIN_POST_SCORE:
        return "M"
    return "L"


# ── Notion ───────────────────────────────────────────────────────────────────

def url_already_in_notion(notion, db_id, url):
    res = notion.databases.query(
        database_id=db_id,
        filter={"property": "URL", "url": {"equals": url}},
        page_size=1,
    )
    return len(res["results"]) > 0


def insert_lead(notion, db_id, lead):
    notion.pages.create(
        parent={"database_id": db_id},
        properties={
            "Title": {"title": [{"text": {"content": lead["title"][:80]}}]},
            "URL": {"url": lead["url"]},
            "Subreddit": {"select": {"name": f"r/{lead['subreddit']}"}},
            "Query Match": {"select": {"name": lead["query_match"]}},
            "Track": {"select": {"name": lead["track"]}},
            "Domain": {"select": {"name": lead["domain"]}},
            "Priority": {"select": {"name": lead["priority"]}},
            "Post Body": {"rich_text": [{"text": {"content": lead["post_body"]}}]},
            "Status": {"status": {"name": "New"}},
            "Date Found": {"date": {"start": lead["date_found"]}},
            "Post Score": {"number": lead["post_score"]},
            "Comment Count": {"number": lead["comment_count"]},
            "Org Signal": {"checkbox": lead["org_signal"]},
        },
    )


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=os.environ.get("REDDIT_USER_AGENT", "betterbi-reddit-leads:v1"),
    )
    notion = Notion(auth=os.environ["NOTION_TOKEN"])
    db_id = os.environ["NOTION_DATABASE_ID"]

    written = skipped_dup = filtered = errors = 0
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting")

    for query, track, domain_hint in QUERIES:
        print(f"  {query!r}", end=" ", flush=True)
        new_here = 0
        try:
            results = reddit.subreddit("all").search(
                query, sort="new", time_filter="day", limit=SEARCH_LIMIT_PER_QUERY,
            )
            for s in results:
                if s.score < MIN_POST_SCORE:
                    filtered += 1
                    continue
                if has_negative(f"{s.title} {s.selftext}"):
                    filtered += 1
                    continue
                url = f"https://www.reddit.com{s.permalink}"
                if url_already_in_notion(notion, db_id, url):
                    skipped_dup += 1
                    continue

                sname = s.subreddit.display_name
                org = has_org_signal(s.selftext)
                domain = SUBREDDIT_DOMAIN_MAP.get(sname, domain_hint)
                lead = {
                    "title": s.title,
                    "url": url,
                    "subreddit": sname,
                    "query_match": query,
                    "track": track,
                    "domain": domain,
                    "priority": get_priority(org, s.score, s.num_comments, domain),
                    "post_body": s.selftext[:500],
                    "post_score": s.score,
                    "comment_count": s.num_comments,
                    "org_signal": org,
                    "date_found": today,
                }
                try:
                    insert_lead(notion, db_id, lead)
                    written += 1
                    new_here += 1
                except Exception as e:
                    errors += 1
                    print(f"\n    ! Notion write failed for {url}: {e}")
        except Exception as e:
            errors += 1
            print(f"\n    ! Search failed: {e}", end="")
        print(f"-> +{new_here}")
        time.sleep(RATE_LIMIT_DELAY)

    print(
        f"\nDone. wrote={written}  dup_skipped={skipped_dup}  "
        f"filtered={filtered}  errors={errors}"
    )
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
