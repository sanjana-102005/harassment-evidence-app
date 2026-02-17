import os
import hmac
import streamlit as st


def _get_password_from_env():
    # For local run: you can set environment variable
    # set APP_PASSWORD=yourpass
    return os.environ.get("APP_PASSWORD", "")


def _get_password_from_secrets():
    # For Streamlit Cloud: put in secrets
    # APP_PASSWORD = "yourpass"
    try:
        return st.secrets.get("APP_PASSWORD", "")
    except Exception:
        return ""


def get_app_password():
    p = _get_password_from_secrets()
    if p:
        return p
    return _get_password_from_env()


def verify_password(entered: str, actual: str) -> bool:
    if not entered or not actual:
        return False
    return hmac.compare_digest(entered.strip(), actual.strip())


def require_login():
    """
    Call this at the TOP of streamlit_app.py.
    If not logged in, shows login UI and stops execution.
    """
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        return True

    st.title("🔒 Secure Access Required")
    st.write("This application is protected to prevent misuse and protect privacy.")

    pw = st.text_input("Enter Password", type="password")

    if st.button("Login"):
        actual = get_app_password()
        if verify_password(pw, actual):
            st.session_state.logged_in = True
            st.success("Login successful.")
            st.rerun()
        else:
            st.error("Incorrect password.")

    st.stop()
