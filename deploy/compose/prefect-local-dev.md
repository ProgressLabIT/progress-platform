# Running Prefect Server Locally with Ephemeral Database

This guide explains how to run a Prefect server locally with an ephemeral database and connect your Docker-based `progress-api` service to it.

## Prerequisites

- Python 3.11+ installed locally
- Prefect 2.x installed (`pip install prefect==2.*`)
- Docker running (for progress-api service)

## Step 1: Start Prefect Server Locally with Ephemeral Database

Run Prefect server with an ephemeral SQLite database (data is lost when server stops):

```bash
prefect server start --host 0.0.0.0 --port 4200
```

This will:
- Start the Prefect server on `http://localhost:4200`
- Use an ephemeral SQLite database (no persistence)
- Make the server accessible from Docker containers via `host.docker.internal`

**Note:** The `--host 0.0.0.0` flag is important to allow connections from Docker containers.

## Step 2: Configure progress-api Docker Container

You need to configure the `progress-api` service to connect to your local Prefect server. The URL depends on your Docker setup:

### Option A: Using Docker Desktop (macOS/Windows)

Docker Desktop provides `host.docker.internal` to access the host machine:

```yaml
# In your docker-compose file or environment
environment:
  - PREFECT_API_URL=http://host.docker.internal:4200/api
```

### Option B: Using Linux Docker

On Linux, you may need to use the host's IP address or add `extra_hosts`:

```yaml
services:
  api:
    extra_hosts:
      - "host.docker.internal:host-gateway"
    environment:
      - PREFECT_API_URL=http://host.docker.internal:4200/api
```

### Option C: Using Docker Network

If your containers are on a custom network, you can also bind the Prefect server to the Docker network's gateway IP.

## Step 3: Verify Connection

1. Check that Prefect server is running:
   ```bash
   curl http://localhost:4200/api/health
   ```

2. From inside the Docker container, test connectivity:
   ```bash
   docker exec -it <progress-api-container> curl http://host.docker.internal:4200/api/health
   ```

## Step 4: Create Work Pool

Before deploying workflows, you need to create a work pool named 'system':

```bash
# Create a process work pool (runs flows in local processes)
prefect work-pool create system --type process

# Or create it via the Prefect UI at http://localhost:4200
```

**Note:** If you're using Prefect 2.x with work pools (instead of work queues), you'll need to create the work pool first. The deployment script expects a work pool named 'system'.

## Step 5: Deploy Your Workflows

Before the progress-api can trigger workflows, you need to deploy them to your local Prefect server:

```bash
# Navigate to your workflow directory
cd backend/workflow/flows

# Deploy the workflows (this will register them with your local Prefect server)
python sys_loader.py
```

**Note:** Make sure your `PREFECT_API_URL` environment variable is set to point to your local server:
```bash
export PREFECT_API_URL=http://localhost:4200/api
```

## Alternative: Using Prefect Cloud

If you prefer to use Prefect Cloud instead of a local server:

1. Sign up at https://app.prefect.cloud
2. Create an API key
3. Set the environment variable:
   ```bash
   export PREFECT_API_URL=https://api.prefect.cloud/api/accounts/<your-account-id>/workspaces/<your-workspace-id>
   export PREFECT_API_KEY=<your-api-key>
   ```

## Troubleshooting

### Connection Refused

- Ensure Prefect server is running: `prefect server start --host 0.0.0.0 --port 4200`
- Check firewall settings
- Verify Docker can reach host: `docker exec -it <container> ping host.docker.internal`

### Workflow Not Found

- Ensure workflows are deployed to your local Prefect server
- Check deployment name matches: `Apply Inventory Counts/main`
- View deployments: `prefect deployment ls`

### Work Pool Not Found

If you get an error about work pool not being found:
```bash
# List existing work pools
prefect work-pool ls

# Create the 'system' work pool if it doesn't exist
prefect work-pool create system --type process
```

### Port Already in Use

If port 4200 is already in use:
```bash
prefect server start --host 0.0.0.0 --port 4201
```
Then update `PREFECT_API_URL` to use port 4201.
