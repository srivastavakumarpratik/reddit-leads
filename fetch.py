"""
Reddit Lead Gen — Fetcher
Searches Reddit via PRAW, filters, scores, deduplicates, outputs JSON.
"""

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import praw

from config import (
    QUERIES,
    NEGATIVE_KEYWORDS,
    ORG_SIGNAL_PHRASES,
    SUBREDDIT_DOMAIN_MAP,
    KARMA_SUBREDDITS,
    DIAGNOSTIC_SUBREDDITS,
    AUTOMATION_SUBREDDITS,
    MIN_POST_SCORE,
    HIGH_PRIORITY_MAX_COMMENTS,
    HIGH_PRIORITY_MIN_SCORE,
    MEDIUM_PRIORITY_MAX_COMMENTS,
    SEARCH_SORT,
    SEARCH_TIME_FILTER,
    SEARCH_LIMIT_PER_QUERY,
    RATE_LIMIT_DELAY_SECONDS,
)

# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
SEEN_URLS_PATH = SCRIPT_DIR / "seen_urls.json"
OUTPUT_PATH = SCRIPT_DIR / "today_leads.json"


# ─────────────────────────────────────────────
# Dedup Registry
# ─────────────────────────────────────────────

def load_seen_urls() -> set:
    if SEEN_URLS_PATH.exists():
        with open(SEEN_URLS_PATH, "r") as f:
            return set(json.load(f))
    return set()


def save_seen_urls(seen: set) -> None:
    with open(SEEN_URLS_PATH, "w") as f:
        json.dump(sorted(seen), f, indent=2)


# ─────────────────────────────────────────────
# Filtering
# ─────────────────────────────────────────────

def has_negative_keyword(text: str) -> bool:
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in NEGATIVE_KEYWORDS)


def has_org_signal(text: str) -> bool:
    text_lower = text.lower()
    return any(phrase.lower() in text_lower for phrase in ORG_SIGNAL_PHRASES)


# ─────────────────────────────────────────────
# Domain Tagging
# ─────────────────────────────────────────────

def get_domain(subreddit_name: str, query_domain_hint: str) -> str:
    return SUBREDDIT_DOMAIN_MAP.get(subreddit_name, query_domain_hint)


# ─────────────────────────────────────────────
# Persona Selection
# ─────────────────────────────────────────────

AUTOMATION_KEYWORDS = [
    "power automate", "n8n", "make.com", "zapier",
    "automate", "automation", "scheduled report",
    "email report automatically", "pdf report",
]


def get_persona(subreddit_name: str, track: str, text: str) -> str:
    text_lower = text.lower()

    # Check automation keywords in text first (overrides subreddit)
    if any(kw in text_lower for kw in AUTOMATION_KEYWORDS):
        return "Automation Advisor"

    if subreddit_name in AUTOMATION_SUBREDDITS:
        return "Automation Advisor"

    if track == "karma" or subreddit_name in KARMA_SUBREDDITS:
        return "Quick Fix"

    if subreddit_name in DIAGNOSTIC_SUBREDDITS:
        return "Diagnostic Expert"

    # Default for Track 2 non-technical subreddits
    return "Business Translator"


# ─────────────────────────────────────────────
# Scoring
# ─────────────────────────────────────────────

def get_priority(
    org_signal: bool,
    post_score: int,
    comment_count: int,
    domain: str,
) -> str:
    if org_signal:
        return "H"

    is_specific_domain = domain not in ("General",)

    if (
        comment_count < HIGH_PRIORITY_MAX_COMMENTS
        and post_score > HIGH_PRIORITY_MIN_SCORE
        and is_specific_domain
    ):
        return "H"

    if is_specific_domain and comment_count < MEDIUM_PRIORITY_MAX_COMMENTS:
        return "M"

    # Technical authority posts in General domain still get M
    # if they have low comment count (good for first-reply advantage)
    if comment_count < HIGH_PRIORITY_MAX_COMMENTS and post_score >= MIN_POST_SCORE:
        return "M"

    return "L"


# ─────────────────────────────────────────────
# Main Fetch
# ─────────────────────────────────────────────

def create_reddit_client() -> praw.Reddit:
    return praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=os.environ.get("REDDIT_USER_AGENT", "betterbi-reddit-leads:v1.0"),
    )


def fetch_leads() -> list[dict]:
    reddit = create_reddit_client()
    seen = load_seen_urls()
    leads = []
    new_urls = set()

    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting fetch run")
    print(f"Loaded {len(seen)} previously seen URLs")

    for query_str, track, domain_hint in QUERIES:
        print(f"  Searching: {query_str!r}")

        try:
            results = reddit.subreddit("all").search(
                query_str,
                sort=SEARCH_SORT,
                time_filter=SEARCH_TIME_FILTER,
                limit=SEARCH_LIMIT_PER_QUERY,
            )

            count = 0
            for submission in results:
                url = f"https://www.reddit.com{submission.permalink}"

                # Dedup
                if url in seen or url in new_urls:
                    continue

                # Score floor
                if submission.score < MIN_POST_SCORE:
                    continue

                # Negative keyword filter
                combined_text = f"{submission.title} {submission.selftext}"
                if has_negative_keyword(combined_text):
                    continue

                # Extract fields
                subreddit_name = submission.subreddit.display_name
                org_signal = has_org_signal(submission.selftext)
                domain = get_domain(subreddit_name, domain_hint)
                persona = get_persona(subreddit_name, track, combined_text)
                priority = get_priority(
                    org_signal=org_signal,
                    post_score=submission.score,
                    comment_count=submission.num_comments,
                    domain=domain,
                )

                lead = {
                    "title": submission.title[:200],
                    "url": url,
                    "subreddit": subreddit_name,
                    "query_match": query_str,
                    "track": track,
                    "domain": domain,
                    "priority": priority,
                    "persona": persona,
                    "post_body": submission.selftext[:500],
                    "post_score": submission.score,
                    "comment_count": submission.num_comments,
                    "org_signal": org_signal,
                    "date_found": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "author": str(submission.author) if submission.author else "[deleted]",
                }

                leads.append(lead)
                new_urls.add(url)
                count += 1

            print(f"    → {count} new leads")

        except Exception as e:
            print(f"    ✗ Error on query {query_str!r}: {e}")

        time.sleep(RATE_LIMIT_DELAY_SECONDS)

    # Update dedup registry
    seen.update(new_urls)
    save_seen_urls(seen)

    # Write output
    with open(OUTPUT_PATH, "w") as f:
        json.dump(leads, f, indent=2)

    # Summary
    h_count = sum(1 for l in leads if l["priority"] == "H")
    m_count = sum(1 for l in leads if l["priority"] == "M")
    l_count = sum(1 for l in leads if l["priority"] == "L")

    print(f"\nRun complete: {len(leads)} total leads")
    print(f"  H: {h_count} | M: {m_count} | L: {l_count}")
    print(f"  Dedup registry now has {len(seen)} URLs")
    print(f"  Output written to {OUTPUT_PATH}")

    return leads


if __name__ == "__main__":
    fetch_leads()
