#!/bin/sh
set -e

cd /flows

# Deploy flows (creates work pool if needed, registers deployments)
echo "Ensuring system work pool exists and deploying system flows..."
python sys_loader.py

# Start worker
echo "Starting system worker..."
exec prefect worker start -p system
