#!/bin/bash

if [ -f "/app/requirements.txt" ]; then
    echo "Installing Python requirements..."
    pip install -r /app/requirements.txt
fi

# Fallback in case requirements.txt is empty or missing streamlit
pip install streamlit

# Server flags below are deploy-shape specific (port binding, Traefik path prefix,
# host advertised to the browser). Behavioural flags (CORS, XSRF, runOnSave,
# toolbar) live in /app/.streamlit/config.toml so they are visible to anyone
# running streamlit standalone outside this container.
echo "Starting Streamlit application..."
exec streamlit run /app/main.py \
  --server.port=8501 \
  --server.address=0.0.0.0 \
  --server.baseUrlPath=/reports \
  --browser.serverAddress=$HOST
