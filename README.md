# Reddit Lead Gen — Setup Guide

## Repo Structure

```
reddit-leads/
├── CLAUDE.md          # Routine instructions (personas, schema, rules)
├── config.py          # Pain phrases, filters, scoring config
├── fetch.py           # PRAW fetcher script
├── seen_urls.json     # Dedup registry (auto-updated each run)
├── requirements.txt   # Python deps
└── README.md          # This file
```

## Prerequisites

1. **Reddit API app** — Go to https://www.reddit.com/prefs/apps
   - Click "create another app"
   - Type: **script**
   - Name: `betterbi-reddit-leads`
   - Redirect URI: `http://localhost:8080`
   - Note the `client_id` (under the app name) and `client_secret`

2. **Notion integration** — Go to https://www.notion.so/my-integrations
   - Create a new integration
   - Copy the token
   - Create a database in Notion with the schema from CLAUDE.md
   - Share the database with your integration

3. **Claude Code on web enabled** — Required for Routines

## Routine Setup

### 1. Push this repo to GitHub

```bash
cd reddit-leads
git init
git add .
git commit -m "initial setup"
gh repo create reddit-leads --private --push
```

### 2. Create the Routine

Go to https://claude.ai/code/routines → New Routine

**Prompt:** Point it at this repo's CLAUDE.md (it will read the instructions from there)

**Repo:** Select `reddit-leads`

**Connectors:** Enable Notion

**Schedule:** Daily (set to ~00:30 UTC = 6:00 AM IST)

**Environment variables** (set in routine config):
```
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
```

**Network access:** Enable (required for Reddit API + Notion API)

**Setup script** (runs before the routine):
```bash
pip install -r requirements.txt
```

### 3. Notion Database

Create a database with these properties matching the schema in CLAUDE.md:
- Title (title)
- URL (url)
- Subreddit (select)
- Query Match (select)
- Track (select): Karma, Authority
- Domain (select): Finance, E-commerce, Healthcare, Construction, PMO, Automotive, Education, Real Estate, Marketing, Tech/SaaS, Automation, HR/People, General
- Priority (select): H, M, L
- Post Body (rich text)
- Status (status): New, Drafted, Posted, Got Reply, Converted, Skip
- Claude Draft (rich text)
- Persona Used (select): Quick Fix, Diagnostic Expert, Business Translator, Automation Advisor
- Date Found (date)
- Post Score (number)
- Comment Count (number)
- Org Signal (checkbox)

Set the default view to Kanban grouped by Status.

## Morning Routine

1. Open Notion → Kanban view → "Drafted" column
2. Scan titles. Drag junk to "Skip"
3. Review drafts on H/M items. Tweak if needed.
4. Post to Reddit. Move card to "Posted"
5. If someone replies or DMs → "Got Reply"
6. If it converts to a Fiverr/Upwork order → "Converted"

## Tuning

- **Add pain phrases:** Edit `QUERIES` in `config.py`, commit, push
- **Add negative keywords:** Edit `NEGATIVE_KEYWORDS` in `config.py`
- **Adjust scoring:** Edit thresholds in `config.py`
- **Edit personas/voice:** Edit `CLAUDE.md` directly
- **Dedup reset:** Delete contents of `seen_urls.json` (replace with `[]`)
