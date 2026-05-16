# Implementation Instructions

- When the user prompt specifies a development plan file such as `doc\dev-plan\<phase>\dev-plan.md` and a target step, read that development plan first and limit the implementation scope to the specified step unless the user explicitly asks for a wider scope.
- Treat `doc\spec\it-asset-management-demo.md` as the implementation source of truth, and use `doc\spec-auth\prompt.md` for auth-related work.
- Keep all runnable project resources such as app code, infrastructure, and future e2e assets under `sys\`.
- Keep environment files and dependency manifests under `sys\` as well.
- Keep project documentation under `doc\`.

- After implementing a requested step, always create or update a working result document under the sibling `result` directory of the target development plan.
- If the target plan is `doc\dev-plan\01\dev-plan.md` and the user asks for `step1`, write the result document to `doc\dev-plan\01\result\step1-result.md`.
- Use the same naming pattern for other steps: `step2-result.md`, `step3-result.md`, and so on.
- The result document must include:
  - what was implemented
  - files changed
  - docker commands used for verification
  - actual verification result
  - remaining issues or follow-up items, if any

- Verification must be performed using Docker containers whenever the requested implementation can be validated through the project container setup.
- Do not treat the task as complete without actually running the relevant verification through Docker.
- Prefer project containers over host execution for app startup, migrations, tests, and runtime checks.
- If Docker-based verification cannot be executed because the required compose file, container, image, or service is missing or broken, clearly report the task as blocked and record that fact in the result document.

- Keep changes scoped to the requested step.
- Update related docs when implementation changes behavior or assumptions.
