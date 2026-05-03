# demo03_am Copilot Instructions

- Always read `doc/tips/copilot/01-mandatory-rules.md` before making changes.
- Follow `doc/tips/copilot/02-reference-order.md` to determine which project documents to read for the current task.
- Treat `doc/spec/ferms-spec.md`, `doc/spec-auth/README.md`, and `doc/dev-plan/README.md` as project source-of-truth documents.
- Follow `doc/policy.md` for architecture and implementation direction.
- Use Nuxt + Vue 3 + TypeScript for frontend work.
- Use NestJS + TypeScript for backend work.
- Use PostgreSQL for persistence.
- Do not introduce a standalone login flow for this project.
- Do not read or handle `portal_token` in frontend JavaScript.
- Keep authentication aligned with the `demo01_crm` handover model described in `doc/spec-auth/README.md`.
- Keep authentication decisions, reservation validation, duplicate booking prevention, and authorization enforcement on the backend.
- Do not add production-environment or production-configuration details to `README.md` or docs unless explicitly requested.
- Do not make unrelated changes or broad refactors outside the requested scope.
- Update related docs when behavior, interfaces, or implementation assumptions change.
