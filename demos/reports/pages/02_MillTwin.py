"""Phase 5: Aerospace Mill Live Twin — Streamlit reports page.

Embeds the demo_twin HMI panel (served at /twin on the Progress host) via
st.iframe. No session handling, no Progress API calls — the page only wraps
the panel in the reports sidebar so the full demo loop is visible inside
the Progress UI.

The twin_url is built from the HOST and PROTOCOL environment variables injected
into the reporting container by reporting.yaml. Defaults to http://localhost/twin/
for local dev outside compose.

The trailing slash is REQUIRED: the panel's index.html references its assets with
relative paths (charts.js, styles.css, vendor/echarts.min.js). Without the slash the
document URL is /twin (looks like a file), so the browser resolves assets against /
→ GET /charts.js, which misses Traefik's PathPrefix(`/twin`) router and falls through
to the SPA catch-all (priority 1) → index.html returned as text/html → module MIME
errors + unstyled page. With /twin/ the assets resolve to /twin/charts.js and route
correctly.

Canonical demo beat:
  Drag Tool Wear past the threshold → spindle torque crosses 45 N·m → 5 s dwell
  → "Spindle torque overload" Issue fires → switch to Progress Issues view to
  confirm the linked Issue is attached to WING-DEMO-001 / WO-DEMO-001 / OP-DEMO-001.
"""
import os

import streamlit as st

# ---------------------------------------------------------------------------
# Page config — must be the first Streamlit call (RESEARCH Pitfall 5).
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Mill Live Twin",
    page_icon="⚙",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Build iframe URL from environment (never hardcoded).
# HOST and PROTOCOL are injected by reporting.yaml; fall back to safe defaults.
# ---------------------------------------------------------------------------
host = os.environ.get("HOST", "localhost")
protocol = os.environ.get("PROTOCOL", "http")
twin_url = f"{protocol}://{host}/twin/"

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
st.title("Aerospace Mill Live Twin — Control Panel")
st.caption(
    "Drag the **Tool Wear** slider past the threshold "
    "→ torque crosses 45 N·m "
    "→ Issue fires. "
    "Switch to the Progress **Issues view** to confirm the linked Issue."
)

# ---------------------------------------------------------------------------
# Panel embed — cross-origin iframe at fixed height.
# height="content" falls back to 400 px for cross-origin frames; use explicit
# height=900 to cover the full-canvas HMI (meta width=1440).
# Use st.iframe (Streamlit >= 1.56). Do NOT use st.components.v1 — deprecated.
# ---------------------------------------------------------------------------
st.iframe(twin_url, height=900)
