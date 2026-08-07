# Minutes Guide

Setup and field rules for **Generate Minutes**.

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
- `public/seeds/minutes_default_chairmen.json` — chairman per company + meeting type, extracted from official templates

On server start, Minutes also **auto-seeds** empty director tables from JSON.

## How Meeting Chairman is auto-filled

Chairman is **per company + meeting type** (Board vs Audit Committee), not one person for the whole BU.

| Company | Meeting type | Chairman (from templates) |
|---------|--------------|---------------------------|
| Adani Green Energy Limited | Board Meeting | Gautam S. Adani |
| Adani Green Energy Limited | Audit Committee | Raminder Singh Gujral |
| Adani Green Energy (UP) Limited | Board / AC | Raj Kumar Jain |
| Adani Green Energy Twenty Five B Limited | Board Meeting | Pragnesh Darji |

**Lookup order (dynamic, not hardcoded):**
1. Previous generated minutes for same company + type  
2. Matching official template DOCX (`Name - Chairman` / `occupied the Chair`)  
3. Seed JSON extracted from templates  
4. If still unknown → user selects  

**UI rule:** auto-filled and read-only while that person is Present. Dropdown appears **only if** the default chairman is on Leave of Absence (or unknown).

## Template fields that must be dynamic

Official templates are filled sample minutes (almost no `[brackets]`). Generation replaces sample text. These must stay dynamic:

| # | Field | Source |
|---|--------|--------|
| 1 | **Company name** | Selected company |
| 2 | **Meeting number** | Auto from previous (90th → 91st) |
| 3 | **Meeting type** | Board / Audit Committee / etc. |
| 4 | **Day, date, time** | Schedule form |
| 5 | **Venue / address** | Meeting place — if user picks non-default address, template must use that address |
| 6 | **Present physically** | Attendance = Present |
| 7 | **Present virtually / VC** | If marked virtual |
| 8 | **Leave of absence / absent** | Attendance = Leave of Absence (or “all present” wording) |
| 9 | **Meeting Chairman** | Auto from previous minutes/template for company + type |
| 10 | **“X occupied the Chair…”** | Same chairman name |
| 11 | **In attendance / invitees** | CS, CFO, guests |
| 12 | **Previous meeting number + date** | Prior meeting for company + type |
| 13 | **FY / quarter ended** | Derived from meeting date |
| 14 | **Date of entry / signing + place** | Signing step |
| 15 | **Resolutions / agenda body** | Form resolutions (or carefully kept from template) |

**Usually keep as-is:** boilerplate Companies Act / SEBI wording, unless the form supplies custom resolution text.

## On a new machine

```bash
cd Backend/aegis_backend
python scripts/seed_minutes_directors.py
python fastapi_server.py
```

Then open Generate Minutes → company → Attendance: directors auto-fill; chairman auto-fills from previous minutes/template for that meeting type.
