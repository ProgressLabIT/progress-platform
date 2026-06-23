import streamlit as st

st.set_page_config(
    page_title="Progress Platform Reports",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Hide Streamlit's default chrome (footer, hamburger menu, header background image)
# so the embedded iframe view stays focused on report content. The header element
# itself is preserved so the sidebar collapse/expand control stays reachable.
st.markdown(
    """
    <style type="text/css">
        footer { visibility: hidden }
        #MainMenu { visibility: hidden }
        header > div { background-image: none !important }
        [data-testid="collapsedControl"] { z-index: 9999 }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📊 Progress Platform Reports")
st.markdown("---")

st.markdown("""
## Welcome to Progress Platform Reports

This is your central hub for viewing reports and analytics for the Progress Platform.

### Available Reports

Select a report from the sidebar to get started — *Sparkplug* shows live UNS topology, online/offline state, and per-metric history charts.

### Getting Started

1. Use the sidebar navigation to browse available reports
2. Each report provides specific insights into different aspects of your operations
3. Reports are automatically updated with the latest data

---

*Progress Platform - Manufacturing Intelligence & Analytics*
""")

# Sidebar
with st.sidebar:
    st.markdown("## Navigation")
    st.markdown("Select a report above. *Sparkplug* is the first live report.")

