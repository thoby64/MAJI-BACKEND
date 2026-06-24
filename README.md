# Majiscope Backend

Majiscope Backend is the FastAPI service for the live Majiscope platform.

## Live hierarchy

The active operational model is:

`Admin -> Utility -> DMA -> Team -> Engineer`

Branch compatibility has been removed from the live backend surface. The startup
migration now upgrades older SQLite/Postgres schemas by removing legacy
`branch_id` columns from `team`, `engineer`, and `report`, then dropping the
legacy `branch` table.

## Main capabilities

- authentication for admin, utility manager, DMA manager, engineer, and team leader
- report intake and assignment
- team and engineer management
- DMA map/location support
- scoped notifications
- Expo push-token registration and delivery for mobile users

## Local setup

```bash
cd WEB-BASED/Backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Important environment variables

```env
ENVIRONMENT=development
DATABASE_URL=sqlite:///./majiscope.db
FRONTEND_URL=http://localhost:3000
SECRET_KEY=change-me
HOST=0.0.0.0
PORT=8000
```

## Startup behavior

On startup the backend now:

1. runs runtime schema migrations
2. removes old branch-linked columns if they still exist
3. adds notification metadata columns if needed
4. creates current tables such as `push_device_token`

For SQLite, the migration creates a timestamped backup before rewriting the old
schema.

## Key API groups

- `/api/auth`
- `/api/users`
- `/api/utilities`
- `/api/dmas`
- `/api/teams`
- `/api/engineers`
- `/api/reports`
- `/api/notifications`
- `/api/push-tokens`
- `/api/logs`
- `/api/uploads`

## Push notifications

The backend stores Expo device tokens in `push_device_token` and can deliver push
messages whenever notification records are created for mobile users.

Key flow:

- mobile app registers token at `/api/push-tokens/register`
- backend creates scoped `notification` records during assignment/review actions
- backend delivers Expo push payloads to active tokens

## Production notes

- set `DATABASE_URL`, `FRONTEND_URL`, and `SECRET_KEY` explicitly
- do not rely on localhost fallbacks outside development
- use a real ASGI process manager for production
- if you deploy on Postgres, let the startup migrator run once on the updated code before traffic

## Historical DUWASA import on deploy

The backend includes a deployment-safe importer for the committed backend-local
CSV file `Leakage_Reporting_Excel_Up_to_January_2026_DUWASA.csv`.

You can run it manually:

```bash
python import_legacy_duwasa_reports.py --database-url "$DATABASE_URL"
python import_legacy_duwasa_reports.py --database-url "$DATABASE_URL" --execute
```

Or let Render run it automatically on app startup:

```env
LEGACY_DUWASA_IMPORT_ON_STARTUP=true
# Optional override. Leave blank to use the CSV inside WEB-BASED/Backend.
LEGACY_DUWASA_IMPORT_CSV_PATH=
LEGACY_DUWASA_IMPORT_STRICT=false
```

Recommended deploy flow:

1. Commit and push the backend changes together with the CSV file in `WEB-BASED/Backend`.
2. In Render, set `LEGACY_DUWASA_IMPORT_ON_STARTUP=true`.
3. Redeploy the backend service once.
4. Check logs for the importer summary.
5. Set `LEGACY_DUWASA_IMPORT_ON_STARTUP=false` after the import is complete.

The importer is idempotent for the imported tracking IDs, so if startup runs it
again later it will skip rows that already exist instead of duplicating them.

## Verification

- Swagger: `/docs`
- ReDoc: `/redoc`
- OpenAPI schema: `/openapi.json`
