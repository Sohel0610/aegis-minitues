# Minutes Guide

Setup notes for **Generate Minutes** so directors, chairman, and attendance auto-populate on every machine.

## Why another device shows empty directors

`local_fallback.db` is **gitignored** (`*.db`). Pulling code does **not** copy director data.

Attendance loads people dynamically from:

1. Director Disclosure DB (Postgres) — when configured  
2. Minutes DB `external_board_members`  
3. Minutes DB `company_directors`

If those tables are empty locally → Attendance step has nobody to auto-fill.

## Quick fix (local / SQLite)

From `Backend/aegis_backend`:

```bash
python scripts/seed_minutes_directors.py
```

Reload if needed:

```bash
python scripts/seed_minutes_directors.py --force
```

Then **restart** the FastAPI server:

```bash
python fastapi_server.py
```

Committed seed files (no hardcoded UI lists):

- `public/seeds/minutes_external_board_members.json`
- `public/seeds/minutes_company_directors.json`

On server start, Minutes also **auto-seeds** these into an empty DB.

## What auto-populates on Attendance (Step 3)

When `companyName` is set:

- Board directors for **that company** load from the API  
- All start as **Present**  
- **Meeting Chairman** defaults to:
  - director whose designation contains “Chair”, else  
  - API `default_chairman`, else  
  - first present director  

Names match with **Ltd. / Limited** normalization (no hardcoding).

## Optional: full Director Disclosure sync (Postgres)

Only if you use live Falcon / Disclosure Postgres (not SQLite-only):

1. Uncomment Postgres host/user/password in `.env`  
2. Set `USE_SQLITE_FALLBACK=false` when using Azure Postgres  
3. Ensure `POSTGRES_DATABASE_DIRECTOR=director_disclosure_system`  
4. Run (from `Backend/Director_Disclosure`):

```bash
python sync_director_registry.py
```

That refreshes the disclosure registry. Minutes then prefers that source when connected.

## Checklist on a new machine

1. `git pull` on `minutes` branch  
2. Copy / configure `.env` (at least `USE_SQLITE_FALLBACK=true` for local)  
3. `python scripts/seed_minutes_directors.py`  
4. Start backend + frontend  
5. Open a company → Continue to Generate Minutes → Step 3 should list that company’s directors  

## Where generated minutes are saved

- File: `Backend/aegis_backend/public/generated/`  
- Record: `generated_minutes` (status **draft** until Finalize)  
- UI: sidebar **Meeting Minutes** repository  

## Related scripts (Minutes only)

| Script | Purpose |
|--------|---------|
| `scripts/seed_minutes_directors.py` | Load director seed JSON into local minutes DB |
| (auto on API start) | Seeds empty `company_directors` / `external_board_members` |

Do **not** rely on copying `local_fallback.db` between machines unless you intend to; prefer the seed script so data stays in git via JSON.
