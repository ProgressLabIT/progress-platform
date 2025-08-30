import streamlit as st

# Configure the page
st.set_page_config(
    page_title="Progress Platform Reports",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main page content
st.title("📊 Progress Platform Reports")
st.markdown("---")

st.markdown("""
## Welcome to Progress Platform Reports

This is your central hub for viewing reports and analytics for the Progress Platform.

### Available Reports

Select a report from the sidebar to get started.

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
    st.markdown("Select a report from the available options above.")

