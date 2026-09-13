# Production Auth/Authz Hardening Plan

Decision log for making OpenEMR's authentication and authorization production-ready, targeting `docker/production/docker-compose.yml` for a single organization under a hard HIPAA/PHI requirement. Deeper rationale for the three most consequential decisions lives in `docs/adr/0001`–`0003`; this document is the full list.

## Decisions

| # | Decision | Rationale |
|---|---|---|
| D1 | Target artifact is `docker/production/docker-compose.yml` | The only compose file in the repo labeled production; it currently ships default credentials. |
| D2 | HIPAA/PHI protection is a hard requirement | This is EHR software; treat the bar as mandatory, not best-effort. |
| D3 | Local OpenEMR auth only — no LDAP, no OIDC/SAML staff SSO | See [ADR-0001](adr/0001-local-auth-only-no-external-sso.md). |
| D4 | Single organization | No multi-tenant partitioning needed in the authz model. |
| D5 | Prefer native OpenEMR fixes over third-party tooling | Minimizes integration surface and dependencies for a single-org deployment. |
| D6 | Lockout: 5 failed attempts → 15-minute auto-expiring lock, audit-logged, admin can unlock early | OpenEMR only has an optional per-request delay (off by default), no real lockout. These are common clinical-system defaults balancing brute-force protection against locking out staff during a shift. |
| D7 | MFA (TOTP/U2F) mandatory for all accounts | Already implemented but opt-in; nearly every account in a clinical EHR touches PHI, so an opt-out role becomes the weakest link. |
| D8 | 15-minute idle session timeout; concurrent sessions per user allowed | Satisfies HIPAA's automatic-logoff expectation; concurrent-session blocking was skipped since shared clinic workstations often need it and there's no specific incident driving the extra complexity. |
| D9 | Audit trail stays self-contained in OpenEMR's own database, no external log/SIEM export | The built-in audit trail (`EventAuditLogger`) already has a working search/review UI — `interface/logview/logview.php`, ACL-gated to admin/users — so no third-party log system is needed. |
| D10 | Self-signed TLS accepted for now | Deployment reachability (internal vs. internet-facing) isn't finalized; revisit if this becomes internet-facing. |
| D11 | Start with Docker Compose secrets | Native Docker feature, no external service, unblocks immediately. |
| D12 | Patch `openemr.sh` to support `*_FILE`-suffixed env vars | See [ADR-0002](adr/0002-file-based-secrets-convention.md). Chosen specifically so the same convention carries forward to a cloud secrets manager once the deployment target is chosen. |
| D13 | Audit log retention: 6 years | Common benchmark healthcare orgs apply from HIPAA's documentation-retention rule (45 CFR 164.316), extended by convention to audit trails. |
| D14 | Password policy: NIST 800-63B (12+ char minimum, no forced rotation, breach-list blocking) | See [ADR-0003](adr/0003-modern-password-policy.md). |
| D15 | Regenerate the session ID on successful login | `session_regenerate_id` is called nowhere in the codebase today — a session-fixation gap with a standard, no-downside fix. |

## Findings that drove these decisions

- **F1** — no hard account-lockout mechanism exists today, only an optional, off-by-default per-request delay.
- **F9** — `interface/logview/logview.php` is a working, ACL-gated audit log viewer backed by `EventAuditLogger` — confirmed before deciding D9.
- **F10** — `docker/release/openemr.sh` (the entrypoint behind `openemr/openemr:latest`) reads `MYSQL_ROOT_PASS`/`MYSQL_PASS`/`OE_PASS` as plain env vars with insecure inline defaults (`root`/`openemr`/`pass`) and has no secrets-file support.
- **F11** — `session_regenerate_id` is not called anywhere in the codebase (session-fixation gap).

## Explicitly out of scope

Adjacent HIPAA safeguards not addressed by this plan, called out so they aren't mistaken for oversights:

- Encryption at rest for the MySQL data volume
- Backup policy and encryption
- Network segmentation / firewall rules around the deployment
- Hardening the OAuth2/FHIR API client-auth layer (SMART-on-FHIR, patient portal apps) — this plan covers staff login, not API client authentication
- TLS certificate source beyond "self-signed is acceptable for now" (D10) — revisit once the deployment's public/internal reachability is finalized

## Separately flagged (not part of this plan)

A real-looking GitHub personal access token was found committed in git history across four dev docker-compose files (`development-easy`, `development-easy-light`, `development-easy-redis`, `development-insane`), first introduced at commit `e1e8afd`. Uncommitted working-tree changes already remove it from the files, but it remains in git history. Recommend rotating/revoking the token on GitHub and scrubbing history before this repo is ever pushed anywhere shared.
