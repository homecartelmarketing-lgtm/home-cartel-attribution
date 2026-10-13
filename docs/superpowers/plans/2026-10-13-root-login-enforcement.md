# Root Login Enforcement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Visiting the bare site URL forces anonymous users to the login page.

**Architecture:** Reuse the existing `_require_login(user, request)` gate in `app/server.py` on the `/` route; anonymous browsers get a 307 redirect to `/login`, health checks and webhooks stay public.

**Tech Stack:** FastAPI (existing), `CurrentUser` cookie-JWT dependency, pytest + TestClient.

**Spec:** Conversation — "when I direct to my website it require to login right?" plus credential lookup ("where i can find the username and password"). Contract: `/` anonymous → 307 `/login`; `/` authed → existing JSON; `/health` anonymous → 200 always; webhooks unaffected.

## Global Constraints

- Python 3.12, FastAPI 0.141.1, PyJWT 2.10.1 — no new dependencies.
- Never log or return passwords, hashes, or `AUTH_SECRET_KEY`.
- Anonymous pages redirect (307 to `/login`); anonymous `/api/*` return 401; `/health` and `/webhook/*` stay public.
- New behavior covered in `tests/test_auth.py`; full suite green except pre-existing deselect.

---

### Task 1: Document credential locations

**Files:**
- Modify: `docs/railway_deployment.md`

**Interfaces:**
- Consumes: `app/config.py:91-96` (auth env vars), `scripts/make_password_hash.py`, Railway Variables tab.
- Produces: credential lookup + rotation runbook.

- [ ] **Step 1: Append runbook section to deployment doc**

```markdown
## Login credentials — where they live

- Username: Railway app Variables `ADMIN_USERNAME` (default `admin`). Readable anytime.
- Password: stored NOWHERE retrievable. Typed once into
  `scripts/make_password_hash.py`, which printed a one-way PBKDF2 hash into
  `ADMIN_PASSWORD_HASH`. Hashes cannot be reversed.
- Forgot password: rerun the script locally, paste the new
  `ADMIN_PASSWORD_HASH=pbkdf2_sha256$...` into Railway Variables.
- Login fails checklist: `AUTH_ENABLED=true`, `AUTH_SECRET_KEY` is 64-hex,
  `ADMIN_PASSWORD_HASH` starts with `pbkdf2_sha256$` (plain text = every login 401s).
```

- [ ] **Step 2: Verify doc renders**

Run: `python -c "from pathlib import Path; print('credentials' in Path('docs/railway_deployment.md').read_text().lower())"`
Expected: `True`

- [ ] **Step 3: Commit**

```bash
git add docs/railway_deployment.md
git commit -m "docs(deploy): document login credential locations and rotation"
```


---

### Task 2: Redirect anonymous `/` to `/login`

**Files:**
- Modify: `app/server.py` (`health_check` route stacked decorators)
- Test: `tests/test_auth.py`

**Interfaces:**
- Consumes: `CurrentUser`, `_require_login(user, request)` (307 `/login` for pages).
- Produces: `/` anonymous → 307 `/login`; `/` authed → JSON; `/health` anonymous → 200.

- [ ] **Step 1: Write the failing tests**

```python
def test_root_redirects_to_login_when_anonymous(auth_env):
    with TestClient(app) as client:
        resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"] == "/login"


def test_root_returns_json_when_authenticated(auth_env):
    with TestClient(app) as client:
        client.post("/login", data={"username": "admin", "password": "correct-horse"})
        resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "online"


def test_health_stays_public(auth_env):
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "online"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_auth.py -k "root or health_stays" -v`
Expected: FAIL — `/` returns 200 JSON anonymously today.

- [ ] **Step 3: Split the stacked route and gate `/`**

```python
@app.get("/")
def root_redirect(request: Request, user: CurrentUser):
    _require_login(user, request)
    return health_check()


@app.get("/health")
def health_check():
    with get_connection() as conn:
        ...
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_auth.py -v`
Expected: all PASS (8 existing + 3 new).

- [ ] **Step 5: Run full suite**

Run: `pytest tests/ -q --deselect tests/test_audit_and_alerts.py::test_database_campaign_spend_evaluation`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add app/server.py tests/test_auth.py
git commit -m "feat(auth): require login on site root, keep /health public"
```

---

### Task 3: Deploy and verify on Railway

**Files:** none (ops only).

- [ ] **Step 1: Push to main**

```bash
git push origin cline/1b544:main
```

- [ ] **Step 2: Redeploy from the fixed folder**

```bash
cd "C:\Users\User\Desktop\Ad-to-Sale Attribution System"
git pull origin main
railway up
```

- [ ] **Step 3: Verify live**

  - Anonymous `GET /` → 307 to `/login`.
  - `GET /login` → 200 sign-in page.
  - `GET /health` → 200 JSON.
  - Sign in → `/` returns JSON, `/dashboard` renders.

- [ ] **Step 4: Report**

Post the four check results; if `/login` 404s, paste the active deployment commit hash.
