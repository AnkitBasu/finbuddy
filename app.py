import streamlit as st

st.set_page_config(
    page_title="FinBuddy",
    page_icon="💹",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "user_profile" not in st.session_state:
    st.session_state["user_profile"] = None
if "user_consent" not in st.session_state:
    st.session_state["user_consent"] = False

from ui.sidebar import render_sidebar
from ui.chat import render_chat
from ui.dashboards import render_portfolio_dashboard, render_goals_tracker, render_budget_overview

# Header
st.title("💹 FinBuddy : Your Personalized Financial Advisor")

st.markdown(
    "<div style='text-align: center; color: #888;'>"
    "Powered by AI"
    "</div>",
    unsafe_allow_html=True,
)


# Sidebar
render_sidebar()

# Main content area
tab_chat, tab_dashboard = st.tabs(["💬 Chat", "📊 Dashboard"])

with tab_chat:
    if not st.session_state.get("user_consent"):
        st.info("👈 Please accept the terms and conditions in the sidebar to proceed.")
    elif not st.session_state.get("user_profile"):
        st.info("👈 Please fill in your financial profile in the sidebar to get personalized advice.")

    render_chat()

with tab_dashboard:
    profile = st.session_state.get("user_profile")
    if profile:
        render_budget_overview(profile)
        col1, col2 = st.columns(2)
        with col1:
            render_portfolio_dashboard(profile)
        with col2:
            render_goals_tracker(profile)
    else:
        st.info("👈 Save your profile in the sidebar to see your financial dashboard.")

# Compliance Disclaimer Banner


# System features info
with st.expander("ℹ️ System Architecture & Safety Features"):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            "**RAG-Enhanced Responses**\n"
            "- Financial knowledge base retrieval\n"
            "- Responses grounded in verified data\n"
            "- Source attribution on all answers\n"
            "- Live market data integration"
        )
    with col2:
        st.markdown(
            "**Guardrails & Compliance**\n"
            "- Input filtering for prohibited topics\n"
            "- Output compliance checking\n"
            "- Hallucination detection & correction\n"
            "- Mandatory disclaimers on advice"
        )
    with col3:
        st.markdown(
            "**Multi-Agent System**\n"
            "- Investment Analyst (stocks, ETFs)\n"
            "- Budget Advisor (spending, saving)\n"
            "- Market Analyst (trends, news)\n"
            "- Financial Planner (goals, retirement)"
        )

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #888;'>"
    "Developed by Ankit Basu"
    "</div>",
    unsafe_allow_html=True,
)
