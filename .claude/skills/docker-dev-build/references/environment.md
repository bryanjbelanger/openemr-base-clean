# OpenEMR Dev Docker: Ports & Credentials (`docker/development-easy`)

| Service | URL / Port | Notes |
|---|---|---|
| OpenEMR (HTTP) | http://localhost:8300 | override: `WT_HTTP_PORT` |
| OpenEMR (HTTPS) | https://localhost:9300 | override: `WT_HTTPS_PORT`; self-signed cert |
| OpenEMR login | `admin` / `pass` | |
| Swagger (API docs/testing) | https://localhost:9300/swagger | |
| phpMyAdmin | http://localhost:8310 | override: `WT_PMA_PORT` |
| MySQL/MariaDB direct | localhost:8320 | override: `WT_MYSQL_PORT`; user `openemr` / pass `openemr`; root pass `root` |
| CouchDB | http://localhost:5984/_utils/ (or https://localhost:6984/_utils/) | override: `WT_COUCHDB_PORT` / `WT_COUCHDB_SSL_PORT`; `admin` / `password` |
| Mailpit (SMTP capture UI) | http://localhost:8025 | override: `WT_MAILPIT_UI_PORT`; no auth |
| Selenium (e2e, VNC viewer) | http://localhost:7900 | override: `WT_VNC_PORT`; VNC password `openemr123` |
| Health endpoint (internal) | https://localhost/meta/health/readyz | reachable from the mapped host HTTPS port with `curl --insecure` |

All host ports are overridable by exporting the matching `WT_*` env var before `docker compose up` — useful when running more than one stack (e.g. multiple git worktrees) at once. `docker/development-easy/docker-compose.yml` is the authoritative source if this drifts.
