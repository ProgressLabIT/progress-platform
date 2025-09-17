#!/bin/bash

# Install requirements if they exist
if [ -f "/app/requirements.txt" ]; then
    echo "Installing Python requirements..."
    pip install -r /app/requirements.txt
fi

# Install streamlit if not already installed
pip install streamlit

echo "Starting Streamlit application..."
exec streamlit run /app/main.py \
  --server.port=8501 \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --server.trust_xheaders=True \
  --server.enableCORS=False \
  --server.enableXsrfProtection=False \
  --browser.serverAddress=reporting.$SUBDOMAIN.$DOMAIN
