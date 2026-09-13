---
name: docker-dev-build
description: Create and start the OpenEMR local development Docker stack (docker/development-easy) from a fresh or reset checkout — pulls the pinned images, brings up MySQL/OpenEMR/supporting services, and waits through the first-boot install until OpenEMR is ready. Use when the user wants to "build the docker container", "create the dev container", "set up the OpenEMR docker environment", "spin up OpenEMR locally", or after running `down -v` / `openemr-cmd down` to rebuild from scratch.
---

# Build the OpenEMR Dev Docker Stack

Bring the `docker/development-easy` compose stack up from nothing — first checkout, or after a volume reset — and confirm OpenEMR has finished installing and is serving.

## When to use
- First time setting up this checkout for local Docker development.
- After `docker compose down -v` (or `openemr-cmd down`) wiped the named volumes and the next `up` needs to reinstall from scratch.
- The stack exists but won't come up cleanly and a rebuild is the fastest fix.

For starting an already-built stack and verifying it before a test pass, use the `docker-dev-verify` skill instead — this one is for the slower from-scratch path.

## Workflow
1. Run `scripts/build.sh` (no arguments; it `cd`s itself via `git rev-parse --show-toplevel`, so it works from anywhere in the checkout). It detects `openemr-cmd`, brings the stack up, waits out the first-boot install, checks container health, and prints the ready URLs — all in one call.
2. Relay the script's output to the user as-is; its final block already has the URLs and credentials, plus a pointer to `docker-dev-verify` for next time.
3. If it exits non-zero, it has already printed the relevant `docker compose logs` tail to stderr — read that before deciding whether to retry, and don't just re-run it blind if the error looks structural (e.g. a real syntax error in the compose file) rather than transient.
4. First boot can legitimately take several minutes (composer/npm install inside the container against empty volumes); the script's default timeout is generous (`MAX_INSTALL_SECONDS=600`). Only raise it (`MAX_INSTALL_SECONDS=1200 scripts/build.sh`) if the user's machine is unusually slow — don't mask a real hang by cranking it up reflexively.

## Gotchas
- **`scripts/build.sh` handles the `cd` into `docker/development-easy` itself** — don't run raw `docker compose` commands from the repo root when diagnosing a failure by hand; `docker-compose.yml` only resolves relative to that directory.
- **`down -v` vs `down`**: `-v` deletes the named volumes (database, `vendor/`, `node_modules/`, composer cache) — the next `up` reinstalls everything from scratch (slow, this skill's scenario). Plain `down` keeps them — the next `up` is fast, which is `docker-dev-verify`'s scenario instead.
- **Port collisions**: if `8300`/`9300`/`8310`/`8320` etc. are already bound (e.g. another OpenEMR worktree stack is up), override via the `WT_HTTP_PORT`/`WT_HTTPS_PORT`/`WT_MYSQL_PORT`/`WT_PMA_PORT` env vars before `up` rather than editing the compose file. Full port table in `references/environment.md`.
- **Don't hand-edit `docker-compose.yml`** to inject secrets or tokens — this file is committed to git. Anything like `GITHUB_COMPOSER_TOKEN` belongs in the shell environment or an untracked `.env`, never in the tracked compose file.
- If the user is working across multiple git worktrees, point them at `openemr-cmd worktree add`/`up` instead of this skill directly — it manages per-worktree env files and port offsets automatically.

## Resources
- `scripts/build.sh` — run this; it does the actual work. Don't read its source before running it, only if a failure needs deeper diagnosis than its stderr output gives.
- `scripts/lib.sh` — shared health-check/reachability helpers sourced by `build.sh` and by `docker-dev-verify`'s script. Not run directly.
- `references/environment.md` — full port map, default credentials, and the `WT_*` env var overrides. Also used by `docker-dev-verify`.
