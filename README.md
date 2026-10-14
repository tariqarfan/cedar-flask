# Cedar Flask app

Login and registration with Flask, MySQL, hashed passwords, CSRF-protected forms, sessions, and a protected account page. The blue design lives in `static/style.css`; Flask pages live in `templates/`. `dist/` contains the earlier static version and is not served by Flask.

## Run locally (macOS / Linux)

Start your MySQL server at `127.0.0.1:8889`. The existing `tariq` database must be accessible to the configured user, with permission to create and read/write the `cedar_users` table. Initialization preserves existing tables.

The local `.env` is configured with the supplied connection details and a generated session secret; it is excluded from Git. For another checkout, copy `.env.example` to `.env` and fill in the settings.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m flask --app app init-db
python -m flask --app app run --port 5000
```

Open http://127.0.0.1:5000 and register an account, then sign in. Stop with Ctrl+C. For later runs, activate `.venv` and run the last command; initialization is only required once.

The database itself must already exist. If it does not, create it using a MySQL administrator: `CREATE DATABASE tariq CHARACTER SET utf8mb4;`, then grant the intended user access.

Password reset is not implemented. The Flask development server is for local use. Deployment requires a Python hosting environment that can reach MySQL; the earlier static Sites deployment does not run this backend. For HTTPS deployment set `COOKIE_SECURE=true` and retain a private, stable `SECRET_KEY`.
