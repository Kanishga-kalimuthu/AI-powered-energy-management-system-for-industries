import streamlit as st
from utils.db import Database
from utils.auth import init_session_state

st.set_page_config(
    page_title="Energy Management System - Login",
    page_icon="⚡",
    layout="centered"
)

init_session_state()

st.title("⚡ Energy Management System")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Dashboard Login")
    
    user_type = st.radio(
        "Select Login Type:",
        ["Industry User", "Admin"],
        key="user_type"
    )

with col2:
    st.info("""
    **Demo Credentials:**
    
    **Industry:**
    - Email: industry@example.com
    - Pass: password123
    
    **Admin:**
    - Email: admin@example.com
    - Pass: admin123
    """)

st.markdown("---")

email = st.text_input("📧 Email", placeholder="Enter your email")
password = st.text_input("🔐 Password", type="password", placeholder="Enter your password")

if st.button("🔓 Login", use_container_width=True):
    if not email or not password:
        st.error("Please enter both email and password")
    else:
        if user_type == "Industry User":
            user = Database.industry_login(email, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.session_state.user['name'] = user['industry_name']
                st.success("✅ Login successful!")
                st.switch_page("pages/02_industry_dashboard.py")
            else:
                st.error("❌ Invalid email or password")
        else:
            user = Database.admin_login(email, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.success("✅ Login successful!")
                st.switch_page("pages/02_industry_dashboard.py")
            else:
                st.error("❌ Invalid email or password")

st.markdown("---")
st.caption("🔒 Secure Energy Monitoring & Optimization Platform")