# NYC Taxi Trips ETL

Code repository for the NYC Taxi Trips ETL project. It extracts, transforms, and loads New York City taxi trip data using Databricks. The pipeline follows the **medallion architecture** and is deployed via [Databricks Asset Bundles (DAB)](https://docs.databricks.com/dev-tools/bundles/index.html), which provides a consistent, repeatable deployment model across DEV and PROD environments.

## Table of Contents

- [Project Structure](#project-structure)
- [Source Code Documentation](#source-code-documentation)
  - [ETL](#etl)
  - [Unity Catalog Permission Model — PROD](#uc-permission-model---prod)
- [Contribute](#contribute)
  - [Prerequisites](#prerequisites)
  - [Setup Local Environment](#setup-local-environment)
  - [Run Unit Tests](#run-unit-tests)
  - [Deploy a Development Copy](#deploy-a-development-copy)
- [CI/CD Setup](#cicd-setup)

---

## Project Structure

```
nyc_taxi_trips_etl/
├── .github/
│   └── workflows/                          # GitHub Actions CI/CD workflows
├── fixtures/                               # Lookup dataset used in ETL and fixtures used in unit tests
├── notebooks/                              # Setup and connection testing notebooks
├── resources/
│   └── jobs/                               # Databricks job definitions (DAB)
├── src/
│   └── nyc_taxi_trips_etl/
│       ├── etl/                            # ETL notebooks per medallion layer
│       └── utils/                          # Shared Python utilities
├── tests/                                  # Unit tests for shared Python code
├── databricks.yml                          # Databricks Asset Bundle configuration
├── pyproject.toml                          # Python project & dependency configuration
└── ruff.toml                               # Linter configuration
```

---

## Source Code Documentation

### ETL

The ETL logic follows the **medallion architecture** with four data processing layers:

| Layer | Description |
|-------|-------------|
| **Landing** | Raw files downloaded from the NYC Taxi Web API and stored in a Unity Catalog volume. |
| **Bronze** | Delta tables loaded from Landing as-is, enriched with job execution metadata (`run_id`, `data_collection_started_at`). |
| **Silver** | Cleaned and refined Delta tables derived from Bronze. Processing includes deduplication, removal of invalid rows, and casting columns to appropriate types. |
| **Gold** | Business-ready Delta tables with aggregated metrics prepared for analysis and reporting. |

### UC Permission Model — PROD

For the Production workspace, a group named `nyctaxi_contributors` must be created with the following entitlements:

- Consumer access
- Databricks SQL access
- Workspace access

This group should be granted the **Data Reader** preset on the `nyctaxi_prod` catalog. Only members of `nyctaxi_contributors` can modify data in the production catalog.
As per [UC best practices](https://docs.databricks.com/aws/en/data-governance/unity-catalog/best-practices), ownership of catalogs and schemas should be assigned to this group.

> [!NOTE]
> Because of the Databricks Free Edition limitation, `default storage` was selected as the storage location for the catalog.
> This means the production catalog will be accessible only within the Prod workspace.

---

## Contribute

### Prerequisites

Install the following tools before setting up the local environment.

#### UV (Python Package Manager)

UV is used for virtual environment and dependency management.

1. Follow the [UV installation guide](https://docs.astral.sh/uv/getting-started/installation/) for your OS.
2. Verify the installation:
    ```pwsh
    uv --version
    ```
    Expected output:
    ```
    uv 0.11.21 (5aa65dd7a 2026-06-11 x86_64-pc-windows-msvc)
    ```

#### Python 3.12

1. Download **Python 3.12** from the [Python Downloads page](https://www.python.org/downloads/release/python-31213/). During installation, ensure the *Add Python to PATH* option is selected.
2. Verify the installation:
    ```pwsh
    python --version
    ```
    Expected output:
    ```
    Python 3.12.3
    ```

#### Databricks CLI

1. Install the Databricks CLI following the [official installation guide](https://docs.databricks.com/aws/en/dev-tools/cli/install).
2. Verify the installation:
    ```pwsh
    databricks --version
    ```
    Expected output:
    ```
    Databricks CLI v1.2.1
    ```

### Setup Local Environment

1. Clone this repository:
    ```pwsh
    git clone https://github.com/devtmaz/nyc_taxi_trips_etl.git
    cd nyc_taxi_trips_etl
    ```

2. Install all dependencies including dev tools:
    ```pwsh
    uv sync --dev
    ```

3. Install pre-commit hooks (enforces code quality checks on every commit):
    ```pwsh
    uv run pre-commit install
    ```

4. Authenticate with the DEV Databricks workspace:
    - Open the [Databricks DEV Workspace](https://dbc-cdd467ab-cdba.cloud.databricks.com/).
    - Navigate to **Settings > Developer > Access tokens** and click **Generate new token**. Copy the token.
    - Run the following command and paste the token when prompted:
        ```pwsh
        databricks configure --host https://dbc-cdd467ab-cdba.cloud.databricks.com/ --profile dev --target dev
        ```

5. Validate the bundle to confirm authentication is working:
    ```pwsh
    databricks bundle validate -p dev -t dev
    ```
    No errors means the setup is complete.

### Run Unit Tests

To run unit tests locally run command:
```pwsh
uv run pytest
```

### Deploy a Development Copy

Deploys the bundle to the DEV workspace. Resources will be prefixed with your username (e.g., `[dev john.doe] NYC Taxi Trips ETL`) and all job schedules are paused by default.

```pwsh
databricks bundle deploy -p dev -t dev
```

To trigger a deployed job manually:

```pwsh
databricks bundle run nyc_taxi_trips_etl -p dev -t dev
```

---

## CI/CD Setup

This project uses GitHub Actions workflows to automatically validate and deploy code to DEV and PROD environments.
For a detailed description of each workflow, see [.github/workflows](.github/workflows/README.md).

### GitHub Secrets

The following secrets must be configured in GitHub repository settings under the `dev` and `prod` environments respectively:

| Secret | Description |
|--------|-------------|
| `DATABRICKS_CLIENT_ID` | Service principal client ID for the target workspace |
| `DATABRICKS_CLIENT_SECRET` | Service principal client secret for the target workspace |

### Triggering a Production Deployment

Production deployments are triggered by pushing a **version tag** that matches the `version` field in `pyproject.toml` (e.g., `0.0.2`). The workflow will fail if the tag and the package version do not match, preventing accidental mismatched deployments.

```pwsh
git tag 0.0.2
git push origin 0.0.2
```
