# Cedar PHP + MySQL

A PHP 8.3 application for regular Hostinger hosting, with the cedar-green login/registration pages, a protected dashboard, live local date/time, and logout. No Python, Node.js, Composer, or compilation is required on the server.

## Hosting

Only upload the **contents of `public/`** to the folder mapped to https://kabir.marmareen.com (`public_html/kabir`). Keep the source repository, tests, scripts, and old `dist/` prototype out of the public web root.

The private `public/includes/config.php` contains database settings and is Git-ignored. `includes/.htaccess` denies web requests to that directory. Hostinger must have PHP 8.3+ with PDO MySQL enabled. The database user must be able to create/read/write tables. The app creates `cedar_users` and `cedar_login_limits` without dropping existing tables. Password hashes from the earlier Flask/TypeScript PBKDF2 app remain compatible and are upgraded after successful login when possible. Sessions use PHP's server-side session storage, secure cookies, CSRF tokens, and session ID rotation. Authentication is limited to 30 attempts per IP in 15 minutes.

## GitHub Actions deployment

`.github/workflows/php.yml` checks syntax and password compatibility. After checks pass on `main`, the production job generates configuration from GitHub secrets, uploads `public/` using FTPS, and checks the live login page. Pull requests never deploy. Credentials are not committed or included in artifacts.

Repository secrets required:

| Secret | Purpose |
| --- | --- |
| `FTP_SERVER` | Exact FTP hostname from hPanel |
| `FTP_PORT` | Usually `21` |
| `FTP_TLS_HOSTNAME` | Certificate hostname when connecting by IP; this server presents `hstgr.io` |
| `FTP_USERNAME` | FTP login |
| `FTP_PASSWORD` | FTP password |
| `FTP_DIRECTORY` | Existing destination relative to FTP account login directory; use `.` if the account already opens in `public_html/kabir` |
| `DB_HOST` | Usually `localhost` on Hostinger |
| `DB_PORT` | Usually `3306` |
| `DB_NAME` | Hostinger database name |
| `DB_USER` | Hostinger database user |
| `DB_PASSWORD` | Database password |
| `SMTP_USERNAME` | Gmail sender address |
| `SMTP_PASSWORD` | Gmail app password (without spaces) |

Manage secrets at Settings → Secrets and variables → Actions, or with `gh secret set NAME` (enter the value at the prompt). FTPS requires a valid server certificate; use the actual FTP hostname rather than a proxied domain. Deployment does not delete unrelated remote files. If an earlier `index.html` exists, `DirectoryIndex index.php` selects the PHP entry point.

## Local development

Copy `public/includes/config.example.php` to `public/includes/config.php`, enter local MySQL credentials, set `cookie_secure` to `false` for local HTTP, and run:

```sh
php -S 127.0.0.1:8080 -t public
```

Open http://127.0.0.1:8080. On this Mac, PHP is available as `/Applications/MAMP/bin/php/php8.3.30/bin/php` if it is not in PATH.

```sh
php tests/password.php
find public -name '*.php' -exec php -l {} \;
```

Password recovery sends a cedar-green HTML email with a plain-text alternative via Gmail SMTP, using PHPMailer. Configure `SMTP_USERNAME` and `SMTP_PASSWORD` as repository secrets. Links expire in 30 minutes, are single-use, and invalidate prior sign-ins after a successful reset. The app also creates `cedar_password_resets`. New passwords accept 8–72 bytes to match PHP's default bcrypt limit. The live clock uses the visitor's browser timezone. The old static `dist/` and Sites manifest are historical files and are not deployed by this workflow.
