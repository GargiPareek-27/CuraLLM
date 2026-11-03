# Implementation status

Last updated: 2026-11-02.

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
| PowerShell scripts on Windows | WRITTEN | not yet run by the author |
| Next.js chat page (`apps/web`) | WRITTEN | lint and build not yet verified; `.github/workflows/web.yml` will run them |

## Known limitations

- The chat endpoint sends the raw message to the mock provider. There is no retrieval, no citations, no safety check and no versioned prompt yet (`safety_status` is `not_evaluated`).
- Mock responses are labelled demos and are not medical advice.
- No authentication, no persistence of conversations, no uploads.
- No request body size limit and no rate limiting yet (Phase 6).
- Python dependencies use version ranges, not a lockfile, so Python builds are not fully reproducible. The web app has a committed `package-lock.json`.
- Containers run as a non-root user but are not otherwise hardened (read-only filesystem, dropped capabilities).
- The retry loop holds a concurrency slot while it backs off.

## Phase checklist

- [ ] Phase 1: foundation (backend verified in CI; web app written, verification pending)
- [ ] Phase 2: ingestion, hybrid retrieval, reranking, grounded generation, citation validation, abstention, real providers
- [ ] Phase 3: evaluation harness and reports
- [ ] Phase 4: authentication, authorization, persistence, consent, doctor workflow
- [ ] Phase 5: dashboards and observability
- [ ] Phase 6: security and end-to-end tests, deployment docs
- [ ] Phase 7: optional QLoRA fine-tuning

## Next concrete task

Run `npm run lint` and `npm run build` in `apps/web`, then try the chat page against the running backend and record the result here.
