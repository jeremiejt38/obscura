# Obscura Development Guidelines

- Keep Obscura an offline, cross-platform screenshot redactor. Do not introduce network processing of image content.
- Preserve the `obscura` CLI and cross-platform clipboard support.
- Keep packaging in `pyproject.toml`, use pytest for tests, and maintain CI across Linux, Windows, and macOS.
- Follow `docs/PROJECT_WORKFLOW.md` for branch lifecycle, Conventional Commits, validation, releases, tags and cleanup.
- Keep `main` stable. Develop on short-lived `feature/*`, `fix/*`, `docs/*`, `chore/*`, `refactor/*` or `test/*` branches; rebase then fast-forward validated work into `main`, and delete merged branches.
- Keep commits atomic and use Conventional Commits. Release Please creates a reviewed Release PR from these commits.
- Run the commands documented in `docs/TESTING.md` before merge and add regression coverage for practical bug fixes.
- Release stable versions only through annotated `vX.Y.Z` tags. Default to patch releases; use minor releases for coherent feature milestones.
  - Progression attendue : `1.0.0 → 1.0.1 (patch) → 1.0.2 (patch) → 1.1.0 (mineure) → 1.1.1 (patch) → …`.
- Do not approve or create a major release, including `1.0.0`, without explicit user approval.
- Keep `pyproject.toml` as the authoritative project version. Keep detailed release history in `CHANGELOG.md` and GitHub Releases.
- Keep `README.md` aligned with `docs/README_TEMPLATE.md` whenever behavior, setup, support or roadmap changes.
- Preserve `CONTRIBUTING.md` and `SECURITY.md` for public collaboration and vulnerability reporting. Never commit private screenshots, secrets or generated local outputs.
- Talos delegation is enabled (re-enabled by the maintainer on 2026-08-05). Submit only isolated, well-scoped sandboxed jobs with a clear objective and a `validate_cmd` (pytest/lint) when possible. Talos never modifies the repository directly; review every diff before integration, and never merge a Talos result without human validation.
