# e-brain

A personal memory capture and retrieval web app I built for my final year project at Westminster International University in Tashkent.

The idea is simple — I wanted one place to dump everything. A thought I had on the bus, a URL I found interesting, a screenshot of something, a business idea at 2am. And then months later, even if I don't remember the exact words or the date, I can just describe it vaguely and find it instantly.

## What it does

- Capture text notes, URLs, images and screenshots
- Every capture is automatically analyzed — generates a title, summary, hashtags and extracts people/companies/technologies mentioned
- Search using natural language. Not keyword search. You can say "that VC I saw in a video about space robots" and it will find it
- Hashtags are normalized so #VentureCapital and #venturecapital and #VC are all connected
- Tracks entities across memories — if you mention the same company in 10 different notes, they're all linked
- Analytics showing your capture habits, most used tags, active days
- Everything stored in Supabase, user auth included

## Stack

- Python + Flask
- Supabase (PostgreSQL + Auth)
- OpenAI GPT-4o for analysis and search
- Vanilla HTML/CSS/JS on the frontend

## Running it locally

```bash
git clone https://github.com/00014216/e-brain.git
cd e-brain
pip install -r requirements.txt
cp .env.example .env
# fill in your Supabase and OpenAI keys in .env
python app.py
```

Before running, go to your Supabase project → SQL Editor and run the full `schema.sql` file. That creates all the tables.

## Project structure

```
app.py              — starts the Flask server
database.py         — all database operations
ai_client.py        — OpenAI integration
capture.py          — handles text, URL and image capture
memories.py         — memory list, search, delete
ai_search.py        — natural language search logic
hashtags.py         — hashtag management and aliases
entities.py         — entity tracking
analytics.py        — usage stats
schema.sql          — full database schema, run this in Supabase
```

## Why I built this

I keep forgetting things I found useful. Articles, ideas, people's names, random insights — they all disappear. I wanted something that actually works the way memory works, not the way a file system works.

---

Sardor Ibrokhimjonov — BISP Final Year Project 2025/2026
