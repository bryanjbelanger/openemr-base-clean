---
name: docker-dev-verify
description: Start (or restart) the already-created OpenEMR development-easy Docker stack and verify it's actually reachable before testing a change — checks container health, curls the login page and health endpoint, and reports URLs/credentials or tails logs on failure. Use when the user wants to "deploy locally to test", "spin the app back up to test this", "check if OpenEMR is up", "restart the dev container", or run a quick smoke check after code changes.
---

# Verify the OpenEMR Dev Docker Stack

Get the `docker/development-easy` stack running and prove it's actually serving before the user starts testing a change against it. This is the fast, repeatable loop — it assumes the stack was already created once (via the `docker-dev-build` skill or a prior session) and its volumes still exist.

## When to use
- The user wants to test a local change against a running OpenEMR instance.
- The stack may be stopped, partially up, or already running — this skill gets it to a known-good, verified state either way.
- Not for a from-scratch rebuild after `down -v` — that's the `docker-dev-build` skill.

## Workflow
1. Run `scripts/verify.sh` (no arguments; it resolves the repo root itself, so it works from anywhere in the checkout). It starts stopped containers if needed (leaves an already-running stack alone), waits for `mysql`/`openemr` to report healthy, then curls the health endpoint and the login page directly rather than trusting Docker's healthcheck alone.
2. Relay its output as-is — on success that's the login URL and credentials; nothing further to do.
3. If it exits `2`, no containers exist at all: tell the user to run the `docker-dev-build` skill instead of retrying this one.
4. If it exits `1`, it has already printed the relevant `docker compose logs` tail to stderr. Read that before deciding next steps — if the logs point to a from-scratch problem rather than something transient, suggest `docker-dev-build` as the fallback instead of re-running this script in a loop.

## Gotchas
- A container reporting `healthy` in `docker compose ps` is necessary but not sufficient — the internal healthcheck hits `https://localhost/meta/health/readyz` *inside* the container; `check_reachable`'s external curl (in `scripts/lib.sh`) is what actually proves the host-side port mapping and TLS termination work too. That's why the script does both rather than stopping at the health status.
- Ports are `8300`/`9300` by default (http/https) — if a worktree stack overrode them via `WT_HTTP_PORT`/`WT_HTTPS_PORT`, those env vars need to be set before running the script, or it will check the wrong port.
- `scripts/verify.sh` already prefers `docker compose start` over `up` when containers exist but are stopped, and never runs `down` — don't second-guess this by running `docker compose down && up` by hand, which is unnecessary and destroys volumes if `-v` slips in.

## Resources
- `scripts/verify.sh` — run this; it does the actual work. Don't read its source before running it, only if a failure needs deeper diagnosis than its stderr output gives.
- `../docker-dev-build/scripts/lib.sh` — shared health-check/reachability helpers `verify.sh` sources. Not run directly.
- `../docker-dev-build/references/environment.md` — full port map and default credentials, shared with the build skill.
