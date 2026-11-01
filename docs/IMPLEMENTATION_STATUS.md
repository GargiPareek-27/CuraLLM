# Implementation status

Last updated: 2026-10-17 (Phase 1a written and self-reviewed once; nothing below has been run by the author yet).

Legend: **WRITTEN** = files exist but have not been executed. **VERIFIED** = a command was run and its real output checked. **PLANNED** = not started.

## Phase 1a: runnable backend foundation

| Item | State | How to verify |
|---|---|---|
| Docker Compose: PostgreSQL (pgvector image), API, inference | WRITTEN | `scripts/dev` then `docker compose ps` |
| FastAPI: `/health`, `/ready`, `POST /api/v1/chat` | WRITTEN | `docs/RUNBOOK.md`, step 5 |
| Inference service with deterministic mock provider | WRITTEN | `POST http://127.0.0.1:8001/v1/generate` |
| Provider interface; `ollama` and `openai_compatible` | Interface WRITTEN, those two providers PLANNED (Phase 2) | n/a |
| Alembic setup and migration `0001` (enable pgvector) | WRITTEN | `scripts/migrate` |
| Setup, dev, stop, migrate, test, verify, reset scripts (bash and PowerShell); reset needs an explicit confirm flag | WRITTEN | `docs/RUNBOOK.md` |
| Unit tests (API, inference client with simulated transport, inference service) | WRITTEN, not yet run | `scripts/test` |
| `.gitignore` anchored to repo root so `ml/data/` is tracked | WRITTEN | `git status` |

## Not yet done in Phase 1

- Next.js web app (Phase 1b). It will be generated with `create-next-app` so versions come from the current release, then extended.
- Dependency lockfile. `requirements.txt` files use version ranges, which is not reproducible. A lockfile must be generated on a machine with network access and committed.
- GitHub Actions workflow: WRITTEN (`.github/workflows/ci.yml`: lint, unit tests, and a full-stack smoke test that runs migrate and verify), not yet run on GitHub.
- Any test run result. No claim of passing tests is made.

## Review fixes after the first self-review (v2)

- Inference client retry loop simplified (no unreachable branch); behaviour is covered by new tests with a simulated transport.
- Response models with `model_id` / `model_revision` fields now disable Pydantic's protected `model_` namespace, avoiding warnings on older Pydantic 2.x.
- `dev.sh` tolerates Windows line endings in `.env`.
- The chat route no longer depends on middleware having set the request id.
- Added `scripts/verify` (PASS/FAIL checks of a running stack) and `scripts/reset` (needs an explicit confirm flag).

## Known limitations of what exists

- The chat endpoint sends the raw message to the mock provider. There is no retrieval, no citations, no safety check, and no versioned prompt yet (`safety_status` is `not_evaluated`).
- Mock responses are labelled demos and are not medical advice.
- No authentication, no persistence of conversations, no uploads.
- The PowerShell scripts have not been tested on Windows by the author.
- No request body size limit and no rate limiting yet (Phase 6). The API has no authentication yet (Phase 4).
- Containers run as a non-root user but are not otherwise hardened (no read-only filesystem, no dropped capabilities) yet.
- The retry loop holds a concurrency slot while it backs off.

## Phase checklist

- [ ] Phase 1: foundation (1a written, 1b web pending, verification pending)
- [ ] Phase 2: ingestion, hybrid retrieval, reranking, grounded generation, citation validation, abstention, real providers
- [ ] Phase 3: evaluation harness and reports
- [ ] Phase 4: authentication, authorization, persistence, consent, doctor workflow
- [ ] Phase 5: dashboards and observability
- [ ] Phase 6: security and end-to-end tests, deployment docs
- [ ] Phase 7: optional QLoRA fine-tuning

## Next concrete task

Run `scripts/setup`, set `POSTGRES_PASSWORD` in `.env`, run `scripts/dev`, `scripts/migrate`, `scripts/test`, and record the actual output here.
