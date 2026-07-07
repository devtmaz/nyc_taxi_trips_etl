# GitHub Actions Workflows

## Continuous Integration Workflow (`ci.yml`)

Runs on every pull request targeting `main`. All three jobs execute in parallel.

| Job | Tool | Purpose |
|-----|------|---------|
| **Databricks Bundle Validate** | Databricks CLI | Parses and resolves `databricks.yml` and all `resources/jobs/*.yml` files to catch schema errors and invalid variable references before anything is deployed. Requires `DATABRICKS_CLIENT_ID` and `DATABRICKS_CLIENT_SECRET` secrets configured on the `dev` environment. |
| **Code Style** | pre-commit | Runs all hooks defined in `.pre-commit-config.yaml`: YAML validation, trailing whitespace, `black`/`black-jupyter` formatting, and `ruff` linting. |
| **Unit Tests** | pytest + uv | Installs the `dev` dependency group via `uv sync` and runs the test suite under `tests/`. The `src/` layout is resolved automatically via `pythonpath` in `pyproject.toml`. |
