### Crm Pipeline

Middleware between CRM Lead and CRM Deal.

This app overrides the Frappe CRM frontend by copying the base `crm` app's `frontend/src` and overlaying files from `frontend/src_override/` on top. This means any Vue component placed in `src_override/` will replace the corresponding file in the base CRM app at build time.

> **Important:** Never edit files in `frontend/src/` directly — they are overwritten on every build by `custom-build.js`. Always edit in `frontend/src_override/`.

---

### Installation

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/lijsamuael/crm_pipeline.git
bench --site [site-name] install-app crm_pipeline
```

---

### Build & Deploy (Frontend Changes)

When you modify any Vue file in `frontend/src_override/`, you must rebuild and redeploy. Run these steps from the `frappe-bench` root directory.

#### Step 1: Build the frontend (inside the app)

```bash
cd apps/crm_pipeline/frontend
yarn build
```

This does three things (defined in `package.json`):
1. **prebuild** — Runs `custom-build.js` which copies `crm/frontend/src` → `crm_pipeline/frontend/src`, then overlays `src_override/` on top
2. **vite build** — Compiles the Vue app into `crm_pipeline/public/frontend/`
3. **copy-html-entry** — Copies the built `index.html` to `crm_pipeline/www/crm.html`

#### Step 2: Collect assets (from bench root)

```bash
cd ../../../   # back to frappe-bench root
bench build --app crm_pipeline
```

This copies the compiled assets from `crm_pipeline/public/` into `sites/assets/crm_pipeline/` where Frappe's web server serves them.

#### Step 3: Clear cache and restart

```bash
bench --site [site-name] clear-cache
bench restart
```

#### Quick reference (all commands from frappe-bench root)

```bash
# Full rebuild sequence:
cd apps/crm_pipeline/frontend && yarn build && cd ../../.. && bench build --app crm_pipeline && bench --site [site-name] clear-cache && bench restart
```

---

### Deploy (Python-Only Changes)

If you only changed Python files (hooks, backend logic in other apps like `fr8labs_custom_crm`), no frontend build is needed:

```bash
bench restart
```

If there are doctype schema changes or fixtures:

```bash
bench --site [site-name] migrate
bench restart
```

---

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/crm_pipeline
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit
