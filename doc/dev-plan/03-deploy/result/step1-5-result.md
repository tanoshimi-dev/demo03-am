# Step 1.5 Result — Portal JWT Authentication

## What Was Implemented

Replaced the header-based portal identity resolution (`X-Portal-*` headers) with JWT cookie verification for `AUTH_MODE=portal`. This resolves the production auth blocker where nothing on the VPS injected portal headers.

### Changes

| File | Change |
|---|---|
| `sys/requirements.txt` | Added `PyJWT[crypto]>=2.8,<3.0` |
| `sys/app/accounts/models.py` | Added `SOURCE_PORTAL_JWT = "portal-jwt"` constant and choices entry |
| `sys/app/accounts/migrations/0002_accountsession_source_portal_jwt.py` | Migration to update `source` field choices |
| `sys/app/accounts/services.py` | Refactored `resolve_portal_identity()` to dispatch on `AUTH_MODE`; added `_resolve_portal_identity_from_jwt()` with `PyJWKClient`; renamed existing path to `_resolve_portal_identity_from_header()` |
| `sys/app/accounts/tests/test_auth.py` | Added `PortalJWTAuthTests` class (6 tests); updated existing portal test name |

### Implementation Details

- **`portal` mode** (`AUTH_MODE=portal`): reads JWT from cookies listed in `PORTAL_COOKIE_NAMES` (`portal_token` by default), verifies RS256 signature via `PyJWKClient` against `PORTAL_JWKS_URL`, validates issuer (`PORTAL_ISSUER`) and expiry, extracts `sub/email/name/role/roles` claims.
- **`dev-header` mode**: unchanged — reads `X-Portal-*` headers as before.
- JWKS client is module-level cached (thread-safe singleton per URL) to avoid repeated JWKS fetches.
- Both `role` (string) and `roles` (array) claim formats are supported.
- Any JWT verification failure logs a warning and redirects to portal login — no error is surfaced to the user.

## Verification

```
docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml exec -T tdev-demo03-web python manage.py test accounts
```

Result:
```
Found 27 test(s).
...AUTH_MODE=portal but PORTAL_JWKS_URL is not configured
.portal JWT verification failed: expired
.portal JWT verification failed: invalid signature
...AUTH_MODE=portal but PORTAL_JWKS_URL is not configured
..................
----------------------------------------------------------------------
Ran 27 tests in 2.663s
OK
```

All 27 tests pass, including 6 new portal JWT tests.

## Remaining Issues / Follow-up

- `PORTAL_JWKS_URL` must be set in the VPS `.env` file: `https://api.tanoshimi.dev/v1/.well-known/jwks.json`
- `PORTAL_ISSUER` must match the Keycloak issuer: `https://auth.tanoshimi.dev/realms/tanoshimi` (confirm from portal team)
- `PORTAL_COOKIE_NAMES` must include the actual cookie name the portal sets (default `portal_token`)
- `AUTH_MODE=portal` must be set in the VPS `.env`
- Proceed to Step 2 (VPS env file and container startup)
