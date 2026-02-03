## Overview

The Progress Platform uses **Traefik** as a reverse proxy and supports both HTTP and HTTPS deployments:

- **HTTP (default)** — For private networks, development, or when TLS termination happens externally (VPN, reverse proxy)
- **HTTPS with TLS** — For public-facing deployments, enabled by including the `tls.yaml` compose file

When HTTPS is enabled, two certificate strategies are supported:

1. **Let's Encrypt (HTTP challenge)** — Default for deployments with public internet access. No DNS or API credentials required.
2. **Custom certificates** — For private networks or customers who provide their own certificates. Certificates are placed manually via SSH in a designated folder.

Custom certificates take precedence when present. This avoids requiring DNS credentials from privacy-minded customers on private networks.

## Architecture

### Core Components

1. **Traefik Proxy** (`traefik:v2.3`)
   - Main entry point for HTTPS traffic
   - SSL/TLS termination
   - File provider for custom certs; ACME resolver for Let's Encrypt
   - Routes traffic to backend services via Docker labels

2. **Let's Encrypt (HTTP challenge)**
   - Domain validation via HTTP (port 80 must be reachable from the internet)
   - Certificates stored in `/letsencrypt/acme.json`
   - Automatic renewal by Traefik

3. **File provider (custom certificates)**
   - Watches `/letsencrypt/custom/` for dynamic TLS config
   - Loads certificates from `tls.yml` + `cert.pem` / `key.pem`
   - Hot reload on file change

## Configuration Files

- **`deploy/compose/stack.yaml`**: Base production stack (HTTP-only by default)
- **`deploy/compose/tls.yaml`**: TLS/HTTPS configuration (optional, include for HTTPS support)
- **`deploy/compose/workflow.yaml`**: Prefect workflow server (optional)
- **`deploy/compose/reporting.yaml`**: Streamlit reporting service (optional)
- **`deploy/compose/warehouse.yaml`**: Warehouse mobile app (optional)
- **`deploy/config/progress.env.yaml`**: Domain and TLS_EMAIL (for Let's Encrypt)
- **`deploy/config/env_template.j2`**: Generates `progress.env`
- **`deploy/config/tls.yml`**: Template for custom certificate dynamic config (Traefik file provider)

## Deployment

### Using Ansible (Recommended)

The `single_node_setup.yaml` Ansible playbook automatically handles TLS configuration based on the `ENABLE_TLS` environment variable:

```bash
# Edit progress.env.yaml and set ENABLE_TLS: true or false
ansible-playbook -i inventory.yml deploy/single_node_setup.yaml
```

The playbook will automatically include or exclude `tls.yaml` based on your configuration.

### Manual Deployment

#### Production with HTTPS (Public Internet)

For deployments with public internet access, include `tls.yaml` to enable HTTPS with Let's Encrypt:

```bash
cd /opt/progress/config
export $(cat progress.env | xargs)
docker stack deploy \
  -c ../deploy/compose/base.yaml \
  -c ../deploy/compose/stack.yaml \
  -c ../deploy/compose/tls.yaml \
  --project-directory .. \
  --project-name progress_prod
```

#### Production with HTTP (Private Network)

For deployments on private networks without TLS, omit `tls.yaml`:

```bash
cd /opt/progress/config
export $(cat progress.env | xargs)
docker stack deploy \
  -c ../deploy/compose/base.yaml \
  -c ../deploy/compose/stack.yaml \
  --project-directory .. \
  --project-name progress_prod
```

All services will be accessible via HTTP on port 80.

### Adding Optional Services

Include additional compose files as needed:

```bash
docker stack deploy \
  -c ../deploy/compose/base.yaml \
  -c ../deploy/compose/stack.yaml \
  -c ../deploy/compose/tls.yaml \
  -c ../deploy/compose/workflow.yaml \
  -c ../deploy/compose/reporting.yaml \
  -c ../deploy/compose/warehouse.yaml \
  --project-directory .. \
  --project-name progress_prod
```

## Environment Variables

### Required (progress.env)

File: `/opt/progress/config/progress.env` (generated from template)

```bash
VERSION=0.10.1
DOMAIN=domain.com
SUBDOMAIN=mysub
TLS_EMAIL=admin@domain.com   # Let's Encrypt account/notifications
ENABLE_TLS=true              # Set to 'true' for HTTPS, 'false' for HTTP-only
```

- **ENABLE_TLS** (optional): Controls whether HTTPS/TLS is enabled
  - `true`: Ansible deployment includes `tls.yaml`, enables HTTPS with Let's Encrypt or custom certificates
  - `false` or omitted: HTTP-only deployment on port 80 (suitable for private networks)
  - Default: `false` if not specified in `progress.env.yaml`

No DNS provider or API credentials are required for HTTP challenge.

## Persistent Storage

### letsencrypt volume

- **Bind mount**: `/opt/progress/letsencrypt` → container `/letsencrypt`
- **Contents**:
  - `acme.json` — Let's Encrypt certificates and account data (when using HTTP challenge)
  - `custom/` — Directory for customer-provided certificates (created by Ansible)

### Custom certificate directory

- **Path on host**: `/opt/progress/letsencrypt/custom`
- **Path in container**: `/letsencrypt/custom`
- **Mode**: `0700` (created by Ansible)
- Required files when using custom certs:
  - `tls.yml` — Traefik dynamic TLS config (see below)
  - `cert.pem` — Certificate (or full chain)
  - `key.pem` — Private key

## Custom Certificate Installation

For private networks or when HTTP challenge is not possible, customers install certificates via SSH.

1. **Copy the TLS config template** (from repo `deploy/config/tls.yml`) to the server:
   ```bash
   sudo cp tls.yml /opt/progress/letsencrypt/custom/tls.yml
   ```

2. **Copy certificate and key** (names must match `tls.yml`):
   ```bash
   sudo cp your-cert.pem /opt/progress/letsencrypt/custom/cert.pem
   sudo cp your-key.pem /opt/progress/letsencrypt/custom/key.pem
   ```

3. **Set permissions**:
   ```bash
   sudo chmod 600 /opt/progress/letsencrypt/custom/*.pem
   ```

4. Traefik picks up the new files automatically (file provider with watch). No router restart required for certificate changes.

### tls.yml format

The file in `deploy/config/tls.yml` is the reference. It must live in `/opt/progress/letsencrypt/custom/tls.yml`:

```yaml
tls:
  certificates:
    - certFile: /letsencrypt/custom/cert.pem
      keyFile: /letsencrypt/custom/key.pem
```

Use container paths (`/letsencrypt/custom/...`), not host paths.

## Certificate Renewal

- **Let's Encrypt**: Traefik renews automatically (e.g. 30 days before expiry). No action needed.
- **Custom certificates**: Customer is responsible for renewal. Replace `cert.pem` and optionally `key.pem` in `/opt/progress/letsencrypt/custom/`, then Traefik reloads via file provider.

## Troubleshooting

### Certificate / HTTPS issues

1. **Check router logs**
   ```bash
   docker service logs progress_router
   ```

2. **Let's Encrypt HTTP challenge**
   - Port 80 must be reachable from the internet for the domain.
   - Ensure `DOMAIN`, `SUBDOMAIN`, and `TLS_EMAIL` are set in `progress.env` and exported before `docker stack deploy`.
   - Rate limits: use Let's Encrypt staging for testing if needed.

3. **Custom certificates**
   - Confirm files exist: `tls.yml`, `cert.pem`, `key.pem` in `/opt/progress/letsencrypt/custom/`.
   - Check PEM permissions (e.g. 600 for key).
   - Ensure `tls.yml` uses container paths (`/letsencrypt/custom/...`).
   - Restart router only if file provider does not reload: `docker service update progress_router`.

### Routing / dashboard

- **Traefik dashboard**: `http://router-host:8080` (insecure; dev/debug only)
- Verify service labels and router rules if endpoints are unreachable.

## Security Considerations

- Back up the `letsencrypt` volume (and `custom/` if used) before major upgrades.
- Restrict access to `/opt/progress/letsencrypt/custom/`; private keys must not be world-readable.
- Traefik dashboard (`--api.insecure`) must not be exposed in production.

## Updates and Maintenance

1. **Change domain or email**
   - Edit `/opt/progress/config/progress.env` (e.g. `DOMAIN`, `SUBDOMAIN`, `TLS_EMAIL`).
   - Export vars and redeploy: `cd /opt/progress/config && export $(cat progress.env | xargs) && docker stack deploy ...`
   - Optionally update only the router: `docker service update progress_router`.

2. **Enable HTTPS on existing HTTP deployment**
   - Ensure the `letsencrypt` Docker volume exists: `docker volume create letsencrypt`
   - Add `-c ../deploy/compose/tls.yaml` to your `docker stack deploy` command and redeploy

3. **Disable HTTPS (switch to HTTP-only)**
   - Remove `-c ../deploy/compose/tls.yaml` from your `docker stack deploy` command and redeploy
   - Services will be accessible via HTTP on port 80

4. **Switch to custom certificates**
   - Add `tls.yml`, `cert.pem`, and `key.pem` under `/opt/progress/letsencrypt/custom/` as above. Traefik will use them in addition to or instead of ACME-issued certs depending on configuration.

5. **Switch back to Let's Encrypt only**
   - Remove or rename the dynamic config (e.g. `tls.yml`) and cert files from `custom/` so Traefik relies only on the Let's Encrypt resolver.
