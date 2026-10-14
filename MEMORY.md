# Cedar app — project memory

Last updated: 2026-10-14 (Asia/Karachi).

## Standing publication preference

The user has authorized automatic publication after code changes: run the relevant checks, commit and push to GitHub `main`, monitor GitHub Actions deployment to Hostinger, and verify the affected live behavior. No repeated confirmation is needed for routine task changes. Respect any later local-only instruction. `AGENTS.md` records this workflow for future sessions. Never publish credentials or unrelated changes, and report deployment blockers clearly.

## Current application

- Live URL: https://kabir.marmareen.com
- Public GitHub repository: https://github.com/tariqarfan/cedar-flask
- Deployment branch: `main`.
- Active runtime: **PHP 8.3+ with PDO MySQL**, on regular Hostinger hosting.
- The project began as static HTML, then Flask, then TypeScript/Express. PHP replaced those backends because the target is a regular website folder. The repository name is historical.
- `app.py` was deleted; an IDE tab showing it is stale. Do not use Flask or Node.js run/build commands for the active app.

## Features and design

- Blue login and registration pages, password visibility toggles, browser and server form validation.
- MySQL-backed accounts, hashed passwords, CSRF-protected forms, server-side PHP sessions, session ID rotation, remember-me, and POST-only logout.
- Dashboard displays the user's name/email, a welcome message, header/footer, and a clock updated each second in the visitor's browser timezone.
- Authentication attempts are limited to 30 per IP per 15 minutes through MySQL.
- Legacy PBKDF2-SHA256 password hashes from Flask/TypeScript remain supported. Eligible hashes are upgraded after login. New passwords use PHP `PASSWORD_DEFAULT`, with an 8–72 byte limit.
- Password recovery is not implemented; its button explains that it is unavailable.

## Active source files

| Path | Purpose |
| --- | --- |
| `public/index.php` | Redirects to login |
| `public/login.php`, `public/register.php` | Authentication page templates |
| `public/dashboard.php`, `public/logout.php` | Protected dashboard and logout |
| `public/includes/bootstrap.php` | Configuration, sessions, CSRF, database, rate limits, route handlers |
| `public/includes/password.php` | PHP/legacy password verification |
| `public/includes/config.example.php` | Credential-free configuration example |
| `public/includes/config.php` | Private, Git-ignored database configuration |
| `public/assets/` | Active CSS, form JavaScript, dashboard clock |
| `public/.htaccess`, `public/includes/.htaccess` | Directory protection and PHP entry point |
| `scripts/deploy.py` | Verified FTPS deployment using environment variables |
| `.github/workflows/php.yml` | PHP/MySQL checks and production deployment |
| `tests/password.php`, `tests/integration.py` | Password compatibility and authentication tests |

`dist/`, `static/`, and `.openai/hosting.json` are retained historical assets/configuration. They do not control the PHP deployment. Edit `public/assets/` for the live design. Old local `.env`, `.venv`, `node_modules`, or `build` files are not the active runtime or production configuration.

## Hostinger deployment

- Site document folder: `public_html/kabir`.
- FTP server IP: `31.220.110.7`; explicit FTPS port: `21`.
- FTP username: `u488328344.kabir`.
- FTP account is scoped to the destination directory: its login directory is `/`, and the deployment-relative `FTP_DIRECTORY` is **`.`**, not `public_html/kabir`.
- TLS certificate hostname: `hstgr.io`. The deployment connects to the IP and verifies the certificate using this name. Do not disable TLS verification.
- Earlier attempts using `marmareen.com` timed out; username `kabir` alone was rejected. Use the confirmed settings above.
- Upload only the contents of `public/`, including hidden `.htaccess` files. Do not upload the repository root.
- Deployment uploads access protections first, writes each file through a temporary upload name, and renames it. It does not delete unrelated remote files.

Production database: host `localhost`, port `3306`, name/user `u488328344_kabir`. Tables `cedar_users` and `cedar_login_limits` are created if missing; existing users are preserved. Database create/read/write/delete permissions are required.

**Do not put passwords, tokens, session identifiers, or private configuration contents in this file or Git.** Passwords are configured as GitHub Actions secrets and in the ignored local PHP configuration. Base64 in generated PHP configuration is serialization, not encryption; access protection remains essential.

## GitHub configuration

- GitHub CLI is installed at `/opt/homebrew/bin/gh` and was authenticated as `tariqarfan` at last verification. Check current authentication before relying on it.
- `origin` points to the repository above; Git HTTPS authentication was configured with `gh auth setup-git`.
- Configured repository secrets: `FTP_SERVER`, `FTP_PORT`, `FTP_TLS_HOSTNAME`, `FTP_USERNAME`, `FTP_PASSWORD`, `FTP_DIRECTORY`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.
- Workflow checks run on pull requests, pushes to `main`, and manual dispatch. Deployment runs only for `main`, after checks pass, using the `production` environment.
- CI runs PHP syntax checks, password compatibility checks, and real HTTP authentication tests against a disposable MySQL 8.4 service.
- Pushes to `main` deploy to the live production domain. A memory/documentation commit also triggers the current workflow.

Useful commands:

```sh
/opt/homebrew/bin/gh auth status
/opt/homebrew/bin/gh secret list --repo tariqarfan/cedar-flask
/opt/homebrew/bin/gh workflow run php.yml --repo tariqarfan/cedar-flask
/opt/homebrew/bin/gh run list --repo tariqarfan/cedar-flask
```

## Local development and checks

PHP on this Mac: `/Applications/MAMP/bin/php/php8.3.30/bin/php`.

The local ignored PHP config currently targets production database settings. Before local authentication testing, configure a local/test database and set `cookie_secure=false` for HTTP. Do not inadvertently run destructive tests against production.

```sh
php -S 127.0.0.1:8080 -t public
php tests/password.php
find public -name '*.php' -exec php -l {} \;
```

The integration test reads `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` from the environment, plus optional `PHP_BIN`. It temporarily replaces/restores local PHP configuration, starts a local PHP server, creates a unique test user, exercises registration/login/CSRF/dashboard/logout, and removes that user. Use a test database. The historical local MySQL connection was `127.0.0.1:8889`, database/user `tariq`; its password is not recorded here.

## Last verified state

- Commit `6370b16` contains the FTP IP/certificate configuration; commit `21f3225` introduced the PHP app and workflow.
- Successful deployment run: https://github.com/tariqarfan/cedar-flask/actions/runs/38571697639
- All CI checks and the deployment job passed.
- Live login/registration returned HTTP 200; private `/includes/config.php` returned HTTP 403.
- Live server-side registration validation successfully exercised MySQL without creating an account.
- Unauthenticated dashboard access redirected to login.
- These are historical observations; verify current deployment status when making further changes.
