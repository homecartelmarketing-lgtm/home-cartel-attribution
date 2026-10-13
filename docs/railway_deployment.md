# Railway deployment guide — Ad-to-Sale Attribution System
# Deploy via GitHub (recommended, auto-deploys on push to main).

## 1. Push to GitHub (done)
# Branch `main` already has the login commit (1f7358e).
# Repo: https://github.com/homecartelmarketing-lgtm/home-cartel-attribution

## 2. Create the Railway project
# 1. Go to https://railway.app/new — sign in with GitHub.
# 2. "Deploy from GitHub repo" → select
#    homecartelmarketing-lgtm/home-cartel-attribution.
# 3. Railway auto-detects Python: installs requirements.txt,
#    starts with `Procfile` → `uvicorn app.server:app --host 0.0.0.0 --port $PORT`.
# 4. Add a PostgreSQL plugin: "+ New" → Database → PostgreSQL.
#    Railway injects DATABASE_URL automatically; the app switches to
#    Postgres when DATABASE_URL starts with postgres:// or postgresql://.

## 3. Set Variables (service → Variables tab)
# Copy from .env.example — paste REAL values, never commit them.
# Minimum to boot with login:
AUTH_ENABLED=true
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=<output of: python scripts/make_password_hash.py>
AUTH_SECRET_KEY=<64-char random string, e.g. output of: python -c "import secrets; print(secrets.token_hex(32))">
TOKEN_EXPIRE_MINUTES=720
# After Railway assigns your domain (e.g. xxx.up.railway.app), add it:
CORS_ORIGINS=https://home-cartel.myshopify.com,https://dear-dining.myshopify.com,https://home22shop.myshopify.com,https://homecartel.net,https://<your-app>.up.railway.app
# Then your live integrations:
ZD_SUBDOMAIN=homecartelhelp
ZD_EMAIL=<real email>
ZD_TOKEN=<real token>
META_DATASET_ID=<id>
META_ACCESS_TOKEN=<token>
ZOHO_CLIENT_ID=<id>
ZOHO_CLIENT_SECRET=<secret>
ZOHO_REFRESH_TOKEN=<token>
# Optional but recommended for email audits:
SMTP_HOST, SMTP_PORT=587, SMTP_USER, SMTP_PASSWORD, ALERT_RECIPIENTS

## 4. Generate a domain
# Service → Settings → Networking → "Generate Domain".
# Open https://<your-app>.up.railway.app/health → expect {"status":"online",...}.
# Open https://<your-app>.up.railway.app/login → sign in with ADMIN_USERNAME
# + the password you hashed. You land on /dashboard.

## 5. Notes
# - Railway provides PORT automatically; app/config.py already reads $PORT.
# - SQLite fallback only applies locally; on Railway always add Postgres so
#   attribution.db data survives restarts (ephemeral filesystem otherwise).
# - Scheduler runs in-process (start_poller_daemon, 300s). For exactly-once
#   cron semantics at scale, move to Railway Cron later — current setup is
#   fine for one replica.
# - Cookies: app/auth.py sets Secure automatically on Railway (non-localhost),
#   HttpOnly + SameSite=lax. Always use the https:// URL.
# - Redeploys: every push to main redeploys automatically.

## Login credentials — where they live

- Username: Railway app Variables `ADMIN_USERNAME` (default `admin`). Readable anytime.
- Password: stored NOWHERE retrievable. Typed once into
  `scripts/make_password_hash.py`, which printed a one-way PBKDF2 hash into
  `ADMIN_PASSWORD_HASH`. Hashes cannot be reversed.
- Forgot password: rerun the script locally, paste the new
  `ADMIN_PASSWORD_HASH=pbkdf2_sha256$...` into Railway Variables.
- Login fails checklist: `AUTH_ENABLED=true`, `AUTH_SECRET_KEY` is 64-hex,
  `ADMIN_PASSWORD_HASH` starts with `pbkdf2_sha256$` (plain text = every login 401s).
