# Implementation status

Last updated: 2026-11-06.

Legend: **VERIFIED (CI)** = ran and passed on GitHub's Linux runner. **WRITTEN** = files exist but have not been executed by the author. **PLANNED** = not started.

## Phase 1: runnable foundation

| Item | State | Notes |
|---|---|---|
| Docker Compose stack: PostgreSQL (pgvector image), API, inference service | VERIFIED (CI) | CI builds it, starts it, waits for health, runs the migration and `scripts/verify.sh` |
| FastAPI: `/health`, `/ready`, `POST /api/v1/chat` | VERIFIED (CI) | via the smoke test |
| Inference service with deterministic mock provider | VERIFIED (CI) | `ollama` and `openai_compatible` providers are PLANNED (Phase 2) |
| Alembic migration `0001` (enable pgvector) | VERIFIED (CI) | |
| Unit tests (API, inference client, inference service) | VERIFIED (CI) | test counts are not recorded here |
| Lint (ruff, syntax and pyflakes rules only) | VERIFIED (CI) | stricter rules not enabled yet |
| Dependabot: grouped Actions, base image held, npm for the web app, pip paused | Configured | pip returns once a lockfile exists |
| PowerShell scripts on Windows (setup, dev, migrate, verify, test) | VERIFIED (local) | run on Windows with Docker Desktop: stack healthy, migration applied, 7 of 7 verify checks passed, 29 API and 16 inference tests passed |
| Next.js chat page (`apps/web`) | VERIFIED (local) | `npm run lint` and `npm run build` pass; browser test against the Dockerized API passed, including the red error alert and recovery after restarting the API. The `web` CI job result is not recorded here yet |

## Phase 2b: MedlinePlus ingestion and keyword search

| Item | State | Notes |
|---|---|---|
| Source registry and validator | VERIFIED (local) | validator passes on Windows; a CI job runs it |
| HTML-to-text, chunker, MedlinePlus XML parser | WRITTEN | 25 unit tests passed in the author's sandbox using a stand-in for pytest; a real pytest run is pending |
| Migration 0002 (documents, chunks, ingestion runs), store, search SQL, CLI, `/api/v1/search` | WRITTEN | not yet executed; the `Ingestion smoke test` CI job runs migrate, ingest, re-ingest and search |
| Ingesting the real MedlinePlus file | NOT YET RUN | no real counts are recorded yet |

## M0 (roadmap step 0): closing Phase 2

| Item | State | Notes |
|---|---|---|
| Hashed Python lockfiles (`requirements.in` to `requirements.txt`) | WRITTEN | tooling in `scripts/lock`; lockfiles not generated yet |
| Type-check baseline (`mypy`, reports only) | WRITTEN | `.github/workflows/types.yml`; first result not recorded |
| Run manifest for experiments (`ml/common/manifest.py`) | VERIFIED (sandbox) | 5 stdlib unit tests passed; a CI job runs them |
| `corpus-stats` command | WRITTEN | SQL not executed yet; the ingestion CI job asserts it on the fixture |
| Real MedlinePlus ingestion | NOT YET RUN | counts to be recorded here |

## Known limitations

- Search is keyword-only (PostgreSQL full text). There are no embeddings, no reranking and no hybrid retrieval yet, and the chat endpoint does not use retrieval yet.
- Chunk token counts are a heuristic (about 1.3 tokens per word) until an embedding model is chosen.
- Only the latest version of each topic is kept; the ingestion run log records what each run did.
- MedlinePlus content is US-centric.
- The chat endpoint sends the raw message to the mock provider. There is no retrieval, no citations, no safety check and no versioned prompt yet (`safety_status` is `not_evaluated`).
- Mock responses are labelled demos and are not medical advice.
- No authentication, no persistence of conversations, no uploads.
- No request body size limit and no rate limiting yet (Phase 6).
- Python dependencies use version ranges, not a lockfile, so Python builds are not fully reproducible. The web app has a committed `package-lock.json`.
- Containers run as a non-root user but are not otherwise hardened (read-only filesystem, dropped capabilities).
- The retry loop holds a concurrency slot while it backs off.
- Test runs print a deprecation warning: Starlette's `TestClient` is moving from `httpx` to `httpx2`. It does not affect the running app; the test dependency will be updated.

## Phase checklist

- [ ] Phase 1: foundation (backend verified in CI; web app written, verification pending)
- [ ] Phase 2: ingestion, hybrid retrieval, reranking, grounded generation, citation validation, abstention, real providers
- [ ] Phase 3: evaluation harness and reports
- [ ] Phase 4: authentication, authorization, persistence, consent, doctor workflow
- [ ] Phase 5: dashboards and observability
- [ ] Phase 6: security and end-to-end tests, deployment docs
- [ ] Phase 7: optional QLoRA fine-tuning

## Next concrete task

Run the fixture ingestion locally, then ingest the real MedlinePlus file, record the counts here, and add embeddings and hybrid retrieval.
