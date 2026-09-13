# File-based secrets convention in the OpenEMR entrypoint

`docker/production/docker-compose.yml` hardcodes `MYSQL_ROOT_PASSWORD`, `OE_USER`, and `OE_PASS` in plaintext. The entrypoint behind `openemr/openemr:latest` (`docker/release/openemr.sh`) only reads these as plain environment variables — no Docker/Compose secrets support. The final deployment target (self-hosted Docker, AWS, or elsewhere) isn't decided yet.

**Decision**: patch `openemr.sh` (and its Dockerfile) to read credentials from `*_FILE`-suffixed environment variables when present (e.g. `OE_PASS_FILE`), falling back to the existing plain env var otherwise. Wire the production compose to Docker Compose's native `secrets:` feature using this convention now.

**Why**: Docker Compose secrets need no external service and unblock this immediately. The `*_FILE` convention is also how most cloud secret stores integrate with containers that don't natively speak their APIs (mounted-file injection), so this is a low-regret stepping stone rather than a rewrite once the deployment target is chosen. The alternative — a compose-only wrapper entrypoint — would create a second, divergent entrypoint to maintain long-term.

## Considered options

- **Wrapper entrypoint** used only by the production compose, translating secret files to env vars before calling the real entrypoint. Rejected: leaves the shared image/script untouched but creates a parallel script to keep in sync.
- **Jump straight to a cloud secrets manager** (e.g. AWS Secrets Manager). Rejected for now: the deployment target isn't chosen yet, and this would block progress on a decision that isn't ready to make.
