# GitHub Actions Workflows

## Continuous Integration Workflow (`ci.yml`)

Runs on every pull request targeting `main`. All three jobs execute in parallel.

| Job | Tool | Purpose |
|-----|------|---------|
| **Databricks Bundle Validate** | Databricks CLI | Parses and resolves `databricks.yml` and all `resources/jobs/*.yml` files to catch schema errors and invalid variable references before anything is deployed. Requires `DATABRICKS_CLIENT_ID` and `DATABRICKS_CLIENT_SECRET` secrets configured on the `dev` environment. |
| **Code Style** | pre-commit | Runs all hooks defined in `.pre-commit-config.yaml`: YAML validation, trailing whitespace, `black`/`black-jupyter` formatting, and `ruff` linting. |
| **Unit Tests** | pytest + uv | Installs the `dev` dependency group via `uv sync` and runs the test suite under `tests/`. The `src/` layout is resolved automatically via `pythonpath` in `pyproject.toml`. |

## Continuous Deployment — Development (`cd-dev.yml`)

Runs on every push to `main`. Uses a `concurrency` group (`cd-dev`) so that a newer push cancels any in-progress deployment, preventing stale runs from overwriting a more recent one.

| Step | Tool | Purpose |
|------|------|---------|
| **Install dependencies** | uv | Installs runtime dependencies via `uv sync`. |
| **Build wheel** | uv | Builds the Python package artifact required by the bundle (`uv build --wheel`). |
| **Deploy bundle** | Databricks CLI | Runs `databricks bundle deploy` targeting the `dev` bundle target. Requires `DATABRICKS_CLIENT_ID` and `DATABRICKS_CLIENT_SECRET` secrets configured on the `dev` environment. |

## Continuous Deployment — Production (`cd-prod.yml`)

Runs when a version tag matching `*.*.*` (e.g. `1.2.3`) is pushed. Validation must pass before deployment proceeds.

| Step | Tool | Purpose |
|------|------|---------|
| **Install dependencies** | uv | Installs runtime dependencies via `uv sync`. |
| **Build wheel** | uv | Builds the Python package artifact required by the bundle (`uv build --wheel`). |
| **Validate bundle** | Databricks CLI | Runs `databricks bundle validate --target prod` to catch any configuration errors against the production target before making changes. |
| **Deploy bundle** | Databricks CLI | Runs `databricks bundle deploy --target prod`. Requires `DATABRICKS_CLIENT_ID` and `DATABRICKS_CLIENT_SECRET` secrets configured on the `prod` environment. |
