# melo-iac-cli

A lightweight Python CLI built with `argparse` for interacting with the **melo-iac** GitOps engine.

---

## Features

* Inspect status and latest plan diffs of managed `TerraformApp` deployments.
* Trigger manual reconciliation syncs on demand.
* List monitored infrastructure workspaces directly from your terminal.

---

## Installation

### From Source

```bash
git clone https://github.com/EdmilsonRodrigues/melo-iac-cli.git
cd melo-iac-cli
pip install -e .
```

---

## Configuration

The CLI communicates with the `melo-iac` Go REST server. Configure the server URL using the `MELO_API_URL` environment variable:

```bash
export MELO_API_URL="http://localhost:8080" # or your cluster REST API ingress URL
```

---

## Usage Guide

### 1. Authenticate

``` bash
melo-iac auth login --username username --password password
```

For this endpoint you can also pass them as ENV variables MELO_IAC_USERNAME and MELO_IAC_PASSWORD

You can also not pass the password, and a prompt will be shown to write it.

### 2. Logout

``` bash
melo-iac auth logout
```

### 3. List All Apps
```bash
melo-iac app list
```

### 4. Check App Status & Plan Summary
```bash
melo-iac app status --name my-vpc-app
```

### 5. Trigger a Manual Sync
Sends a patch request to update the CRD reconciliation annotation, forcing an immediate `terraform plan/apply` run.

```bash
melo-iac app sync --name my-vpc-app
```

### 6. Fetch Raw DAG Topology
Outputs the node and edge topology parsed from the current Terraform state:

```bash
melo-iac app graph --name my-vpc-app --json
```

### 6. Fetch Raw DAG Topology
Outputs the node and edge topology parsed from the future Terraform state (if out of sync):

```bash
melo-iac app graph --name my-vpc-app --future --json
```

---

## Development

Run tests locally using `pytest`:

```bash
pip install pytest
pytest tests/
```
