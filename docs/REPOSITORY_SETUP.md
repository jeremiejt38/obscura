# GitHub repository setup

Apply the shared checklist in `/home/jerem/workspace/.devin/templates/project-standards/REPOSITORY_SETUP_CHECKLIST.md`.

For Obscura:

- Protect `main` with required CI checks and up-to-date branches before merge.
- Disable force pushes to `main`.
- Enable automatic deletion of merged head branches.
- Allow GitHub Actions to create pull requests so Release Please can open release pull requests.
- Enable private vulnerability reporting before inviting public security reports.
- Keep repository secrets in GitHub Actions secrets only.
