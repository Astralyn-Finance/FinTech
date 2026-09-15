# Fintech Platform — Backend

Phase 1 deliverable: project foundation + database layer, matching the
finalized 10-table schema (users, assets, portfolios, portfolio_snapshots,
portfolio_positions, asset_daily_prices, news_articles, sentiment_analysis,
backtest_results, agent_execution_logs).

Agents, auth, and API endpoints are **not** in this phase by design — this
phase is DB + FastAPI skeleton only, validated against a real Postgres
instance.

## Setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env if your local Postgres user/password/db differ

# create the database (adjust to your local Postgres setup)
createdb fintech_db

alembic upgrade head
```

## Verify

```bash
# ORM-level smoke test: inserts, append-only price revision, two-phase
# sentiment lifecycle, position-weight sum — asserts on all of it.
python -m scripts.smoke_test

# API-level check
uvicorn app.main:app --reload
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/health/database
# interactive docs at http://127.0.0.1:8000/docs
```

## What's here

```
app/
  config.py       # Settings, read from .env — nothing hard-coded
  database.py      # shared declarative Base AND engine, SessionLocal, get_db() FastAPI dependency
  models/                # one file per domain, mirrors the ERD exactly
  main.py               # FastAPI app + /health, /health/database
alembic/                 # migrations; env.py pulls target_metadata from app.models
scripts/smoke_test.py    # end-to-end ORM sanity check (see "Verify" above)
```

## Design notes carried over from the data layer

- **Surrogate keys**: `assets.asset_id` is the PK everywhere, never `ticker`.
- **Append-only prices**: `asset_daily_prices` has no unique constraint on
  `(asset_id, ts)` — revisions are new rows with a later `ingested_at`,
  never UPDATEs. Point-in-time queries filter on `ingested_at`.
- **Two-phase sentiment**: a `sentiment_analysis` row is created at
  link-time with null score fields; the sentiment agent fills them in later.
  `UNIQUE(article_id, asset_id)` prevents duplicate links.

## Next phase (not yet started)

Auth (JWT + password hashing) is the natural next step — everything else
(assets, portfolios, prices endpoints) sits behind it. Confirm before I
start.
