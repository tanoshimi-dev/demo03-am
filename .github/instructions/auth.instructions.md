# Auth Instructions

- Before changing auth-related code or docs, read `doc/spec-auth/prompt.md` and the relevant `doc/dev-plan/*` file for the requested step.
- Preserve the portal handover authentication model used by `demo01_crm`.
- Keep portal authentication as the entry point and app-local session as the app protection mechanism.
- Do not add an app-specific login page.
- Do not move auth trust decisions to the frontend.
- Keep `returnTo` handling restricted and safe.
- Prefer environment-driven auth configuration; do not hardcode security-sensitive values.
