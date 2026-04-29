import streamlit as st
from utils.auth import init_session_state, check_login

st.set_page_config(
    page_title="Advanced Energy Management System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

init_session_state()

if not check_login():
    st.switch_page("pages/01_login.py")
else:
    st.switch_page("pages/02_industry_dashboard.py")