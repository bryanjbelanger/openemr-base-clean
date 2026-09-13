# Local-only authentication, no external SSO/LDAP

Production-hardening authentication for a single-organization OpenEMR deployment (`docker/production/docker-compose.yml`) under a hard HIPAA/PHI requirement. OpenEMR already supports LDAP bind auth and could add SAML/OIDC SSO for staff login, but either means trusting and depending on an external identity provider.

**Decision**: authentication stays local to OpenEMR's built-in user table, hardened with mandatory MFA (TOTP/U2F), account lockout, and idle-session timeout. LDAP stays disabled; no SAML/OIDC SSO login path is added for staff.

**Why**: for a single organization, every external identity integration is another system that can leak credentials, misconfigure trust, or go unavailable and lock out clinical staff. OpenEMR's native controls close the practical gap SSO would otherwise cover without that dependency.

## Consequences

If this organization later joins a larger health system with existing centralized identity, this decision needs revisiting. OpenEMR's OAuth2 layer (`src/RestControllers/AuthorizationController.php` and friends) already exists for API/FHIR client auth and is the natural extension point for staff OIDC login if that day comes.
