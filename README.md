# IICS CI/CD Pipeline

This repository contains a CI/CD pipeline for Informatica Intelligent Cloud Services (IICS) using GitHub Actions. It automates the promotion of assets from a Development environment to a UAT environment.

## Overview

The pipeline implements the following workflow:
1.  **Development Review**: Checks out code, logs into the IICS Development organization, and runs tests on the committed mapping tasks.
2.  **UAT Promotion**: Merges changes into a `dev` branch (simulated via cherry-pick in the script), logs into the UAT organization, pulls the changes using the commit hash, and tests the deployed assets.

## Prerequisites

### 1. IICS Environments
You need access to two IICS organizations (or environments within one):
- **Development** (Source)
- **UAT** (Target)

### 2. GitHub Secrets
Configure the following secrets in your GitHub repository:

| Secret Name | Description |
|Data Type| String |
|Parameters| |
|---|---|
| `IICS_USERNAME` | Username for the Development Org |
| `IICS_PASSWORD` | Password for the Development Org |
| `UAT_IICS_USERNAME` | Username for the UAT Org |
| `UAT_IICS_PASSWORD` | Password for the UAT Org |
| `GH_TOKEN` | Personal Access Token for git operations (fetching/pushing) |

### 3. Environment Variables
The workflow uses the following environment variables (defined in `.github/workflows/IICS_DEPLOYMENT.yml`):
- `IICS_LOGIN_URL`: The login URL for IICS (e.g., `https://dm-em.informaticacloud.com`)
- `IICS_POD_URL`: The POD URL for your org (e.g., `https://emw1.dm-em.informaticacloud.com/saas`)

## Scripts Structure

The `scripts/` directory contains the Python logic for interacting with the IICS API.

- **`iics_client.py`**: The core class handling authentication, API, and job execution.
- **`infa_login.py`**: Handles login to both environments and sets session IDs for the workflow.
- **`infa_get_updates.py`**: Retrieves changed objects from a commit and triggers jobs/tests in Dev.
- **`infa_update_and_test.py`**: Pulls changes to UAT and triggers jobs/tests.
- **`helper_functions.py`**: (Deprecated) Legacy helper functions.
- **`testing_functions.py`**: (Deprecated) Legacy testing functions.

## Implementation Details

The pipeline uses the IICS REST API v3 for source control operations and v2 for job execution.

### Important Note on Object Filtering
Currently, the scripts filter for objects with type `ZZZ`. This is a placeholder. You should verify the correct type for your assets (e.g., `MTT` for Mapping Task, `DSS` for Synchronization Task) and update the scripts or the workflow inputs accordingly.

## Setup

1.  Clone this repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Set up the Secrets in GitHub.
4.  Trigger the workflow manually (`workflow_dispatch`) with:
    - **Commit Hash**: The hash you want to promote.
    - **Repository Name**: The `owner/repo` where the assets reside (defaults to `nrislani/iics`).
