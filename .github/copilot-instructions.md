# demo03_am Copilot Instructions

- Always read `doc/tips/copilot/01-mandatory-rules.md` before making changes.
- Follow `doc/tips/copilot/02-reference-order.md` to determine which project documents to read for the current task.
- Treat `doc/spec/it-asset-management-demo.md`, `doc/spec-auth/prompt.md`, and `doc/dev-plan/README.md` as project source-of-truth documents.
- Keep all runnable project resources under `sys\` and keep documentation under `doc\`.
- Keep environment files and dependency manifests such as `sys\.env`, `sys\.env.example`, and `sys\requirements.txt` under `sys\`.
- Use Python + Django for application work.
- Use PostgreSQL for persistence.
- Do not introduce a standalone login flow for this project.
- Do not read or handle `portal_token` in frontend JavaScript.
- Keep authentication aligned with the `demo01_crm` handover model described in `doc/spec-auth/prompt.md`.
- Keep authentication decisions, reservation validation, duplicate booking prevention, and authorization enforcement on the backend.
- Do not add production-environment or production-configuration details to `README.md` or docs unless explicitly requested.
- Do not make unrelated changes or broad refactors outside the requested scope.
- Update related docs when behavior, interfaces, or implementation assumptions change.
