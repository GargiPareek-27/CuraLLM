# Runbook (Phase 1a)

Every command here is **UNVERIFIED until you run it** and record the result in `docs/IMPLEMENTATION_STATUS.md`. Only Phase 1a is covered. Later phases extend this file.

## Prerequisites

- Git
- Docker Desktop (Windows/macOS) or Docker Engine with the Compose v2 plugin (Linux)
- No GPU and no paid API key are needed. Inference runs in deterministic mock mode.

## Ports and services

| Service | Container port | Host address | Notes |
|---|---|---|---|
| `postgres` (pgvector image) | 5432 | `127.0.0.1:5433` | `POSTGRES_HOST_PORT` |
| `inference` | 8001 | `127.0.0.1:8001` | `INFERENCE_HOST_PORT`; keep private |
| `api` | 8000 | `127.0.0.1:8000` | `API_HOST_PORT`; docs at `/docs` |

All published ports are bound to 127.0.0.1 only.

## Variables (`.env`)

| Variable | Required | Meaning |
|---|---|---|
| `POSTGRES_PASSWORD` | yes | 12+ chars, letters/digits/`_`/`-` only. `CHANGE_ME` is rejected by the dev scripts. |
| `POSTGRES_USER`, `POSTGRES_DB` | no | default `curallm` |
| `POSTGRES_HOST_PORT`, `API_HOST_PORT`, `INFERENCE_HOST_PORT` | no | host ports |
| `INFERENCE_PROVIDER` | no | `mock` is the only provider implemented in Phase 1 |
| `CORS_ORIGINS` | no | explicit origins; `*` is rejected |

## 1. Setup

Windows PowerShell (if scripts are blocked, prefix with `powershell -ExecutionPolicy Bypass -File`):

```powershell
.\scripts\setup.ps1
```

Linux/macOS:

```bash
chmod +x scripts/*.sh
./scripts/setup.sh
```

Then edit `.env` and set `POSTGRES_PASSWORD`.

## 2. Start

```powershell
.\scripts\dev.ps1
```
```bash
./scripts/dev.sh
```

## 3. Migrate

```powershell
.\scripts\migrate.ps1
```
```bash
./scripts/migrate.sh
```

## 4. Check the services

One command that checks health, readiness, pgvector, the demo chat answer and input validation, and prints PASS/FAIL for each:

```powershell
.\scripts\verify.ps1
```
```bash
./scripts/verify.sh
```

Individual commands, if you want to look yourself:

```powershell
docker compose ps
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/ready
Invoke-RestMethod http://127.0.0.1:8001/health
docker compose exec postgres psql -U curallm -d curallm -c "SELECT extname FROM pg_extension;"
docker compose run --rm --no-deps api alembic current
docker compose exec api python -m app.cli healthcheck
```
```bash
docker compose ps
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/ready
curl -s http://127.0.0.1:8001/health
docker compose exec postgres psql -U curallm -d curallm -c "SELECT extname FROM pg_extension;"
docker compose run --rm --no-deps api alembic current
docker compose exec api python -m app.cli healthcheck
```

Expected after migration: the extension list contains `vector`, and `/ready` reports `"pgvector": "installed"`.

## 5. Send a demo chat request

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/chat -ContentType "application/json" -Body '{"message":"Hello"}'
```
```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/chat -H "Content-Type: application/json" -d '{"message":"Hello"}'
```

The answer must start with `[DEMO MODE ...]` and `is_demo` must be `true`. `citations` is empty in Phase 1 by design.

## 6. Run the tests

```powershell
.\scripts\test.ps1
```
```bash
./scripts/test.sh
```

## 7. Stop

```powershell
.\scripts\stop.ps1
```
```bash
./scripts/stop.sh
```

This keeps the database volume.

## Reset (deletes local data)

```powershell
.\scripts\reset.ps1                          # only explains
.\scripts\reset.ps1 -ConfirmDeleteLocalData  # deletes the local database volume
```
```bash
./scripts/reset.sh                           # only explains
./scripts/reset.sh --confirm-delete-local-data
```

## 8. Web app (Next.js)

Start the backend first (steps 1 to 3). Then, from `apps/web`:

```powershell
cd apps\web
npm install
npm run dev
```
```bash
cd apps/web
npm install
npm run dev
```

Open http://localhost:3000. Use `localhost`, not `127.0.0.1`, because the API only allows the origin `http://localhost:3000` (`CORS_ORIGINS`). Ask a question: the answer must carry a "Demo response" badge, and Sources must say that no evidence is retrieved yet.

The API address defaults to `http://127.0.0.1:8000`. Override it with `NEXT_PUBLIC_API_URL` (PowerShell: `$env:NEXT_PUBLIC_API_URL="http://127.0.0.1:8000"` before `npm run dev`).

Checks that also run in CI:

```
npm run lint
npm run build
```

## 9. Ingest MedlinePlus and search (Phase 2b)

Needs the stack running and migrated (steps 1 to 3). First try the small **synthetic** fixture. It needs no internet, and its topics are invented test text, not medical information:

```powershell
docker compose exec api python -m app.cli ingest-medlineplus --xml-file tests/fixtures/mplus_sample.xml --corpus-version 2026-01-01
docker compose exec api python -m app.cli search "zebra fever"
```

Run the first command a second time. It must report `"unchanged": 3` and `"inserted": 0`.

Then the real data. This downloads the official health topic file for a publication date (files are published Tuesday to Saturday) from medlineplus.gov at run time. Nothing is committed to the repository:

```powershell
docker compose exec api python -m app.cli ingest-medlineplus --date 2026-11-03
docker compose exec api python -m app.cli search "high blood pressure"
```

A full real run deactivates the fixture topics, so they stop appearing in search. Searching over HTTP:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/search -ContentType "application/json" -Body '{"query":"high blood pressure","limit":3}'
```
```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/search -H "Content-Type: application/json" -d '{"query":"high blood pressure","limit":3}'
```

Every result carries its source URL, licence text, attribution and corpus version. Scores are keyword scores, not probabilities of being correct.

## 10. Corpus statistics

```powershell
docker compose exec api python -m app.cli corpus-stats
```

Prints active and total documents, chunk counts, approximate chunk token sizes (min, median, 95th percentile, max), documents split into several chunks, documents per corpus version, and the last five ingestion runs. Record these numbers in `docs/IMPLEMENTATION_STATUS.md` after each real ingestion.

## 11. Lock the Python dependencies

`services/*/requirements.in` hold the version ranges. `requirements.txt` and `requirements-dev.txt` are generated lockfiles with exact versions and hashes. Regenerate them with Docker running:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\lock.ps1
```
```bash
./scripts/lock.sh
```

Then run `scripts/test` and `scripts/dev` to confirm everything still works, and commit the changed `.txt` files. The lock is built inside a Linux Python 3.12 container, the same platform as the images and CI. pip enforces the hashes automatically once they are present.

## Troubleshooting

- **Web page says it could not reach the API:** start the backend (`scripts/dev`), open the page at `http://localhost:3000`, and check `NEXT_PUBLIC_API_URL`.
- **`search` or `ingest-medlineplus` says the database is not ready:** run `scripts/migrate` (migration 0002 creates the tables).
- **Port already in use:** change the matching `*_HOST_PORT` in `.env`, then run the dev script again.
- **`POSTGRES_PASSWORD` rejected:** use 12+ characters from letters, digits, `_`, `-`.
- **API never becomes ready:** `docker compose logs api inference postgres`.
- **`/ready` returns 503:** the response body says whether the database or inference failed.
- **Changed the password after the first start:** the Postgres volume keeps the old one. Use the reset command above, which **deletes all local database data**.
