# Contributing to Obscura

## Before contributing

- Read `AGENTS.md`, `docs/PROJECT_WORKFLOW.md` and `docs/TESTING.md`.
- Search existing issues before opening a new one.
- Do not include screenshots containing private data, credentials, API keys or access tokens.

## Contribution flow

1. Open or reference an issue describing the problem or proposal.
2. Create a short-lived branch from `main`, such as `feature/<topic>` or `fix/<topic>`.
3. Make focused commits using Conventional Commits.
4. Run the validation commands in `docs/TESTING.md`.
5. Open a pull request that explains the change and references the issue.
6. After merge, delete the local and remote branch.

## Pull request expectations

- Keep changes focused and reversible.
- Include tests for changed critical behavior.
- Update user-facing documentation, configuration examples and roadmap entries when applicable.
- Preserve Obscura’s offline processing model: image content and OCR data must not be sent to network services.

## Code of conduct

Be respectful. Harassment, discrimination, deliberate malice and disclosure of private information are not accepted.

## License

By submitting a contribution, you agree that it may be distributed under the MIT License.
