# Project instructions

Read `MEMORY.md` before working on this app for the active PHP architecture, deployment configuration, and verification commands.

## Standing user authorization

The user explicitly requests that code changes be published to GitHub and deployed to Hostinger through GitHub Actions. After completing requested code changes:

1. Run checks appropriate to the change; resolve failures before publishing.
2. Review the diff and keep credentials, private configuration, and unrelated changes out of the commit.
3. Commit the task's changes and push to `main` in `tariqarfan/cedar-flask`.
4. Monitor `.github/workflows/php.yml` through GitHub CLI until the run finishes.
5. Verify the affected live behavior at `https://kabir.marmareen.com` and report deployment success or the precise failure.

Publishing and deployment are already authorized; do not request confirmation again for routine task changes. Respect a later request to keep work local or not deploy. Do not force-push or overwrite unrelated work. Use the existing GitHub secrets and verified FTPS deployment; never commit passwords. If publishing or deployment is blocked, finish unaffected work and explain the blocker without claiming the site was updated.

Keep `MEMORY.md` current when architecture, configuration, deployment behavior, or significant verification results change.
