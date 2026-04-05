import streamlit as st
from models.user_profile import UserProfile, FinancialGoal, RiskTolerance


def render_sidebar():
    st.sidebar.title("👤 Your Financial Profile")

    # ── User Consent Section ──
    st.sidebar.markdown("### Terms & Consent")
    consent = st.sidebar.checkbox(
        "I understand that this AI provides general financial information only, "
        "not personalized financial advice. I consent to the processing of my "
        "profile data for generating insights. All information is "
        "retrieved from public market data and a curated financial knowledge base. All investments carry risk, "
        "including potential loss of principal. I will consult a certified "
        "financial advisor before making investment decisions.",
        value=st.session_state.get("user_consent", False),
        key="consent_checkbox",
    )
    st.session_state["user_consent"] = consent

    if not consent:
        st.sidebar.warning("Please accept the terms to use the advisor.")
        return

    st.sidebar.markdown("---")

    with st.sidebar.form("profile_form"):
        name = st.text_input("Name", value="User")
        age = st.number_input("Age", min_value=18, max_value=100, value=30)
        annual_income = st.number_input(
            "Annual Fixed Income (₹)", min_value=0, value=1200000, step=50000
        )
        monthly_expenses = st.number_input(
            "Monthly Expenses (₹)", min_value=0, value=40000, step=5000
        )
        risk_tolerance = st.selectbox(
            "Risk Tolerance",
            options=["conservative", "moderate", "aggressive"],
            index=1,
        )
        investment_horizon = st.slider(
            "Investment Horizon (years)", min_value=1, max_value=40, value=10
        )
        existing_investments = st.text_area(
            "Existing Investments",
            placeholder="e.g., RELIANCE:50, INFY:100, PPF: ₹5,00,000, NPS: ₹3,00,000",
        )

        st.markdown("---")
        st.markdown("**Financial Goals**")

        goal1_name = st.text_input("Goal 1 Name", value="Retirement")
        goal1_amount = st.number_input("Goal 1 Target (₹)", min_value=0, value=50000000, step=500000)
        goal1_years = st.number_input("Goal 1 Timeline (years)", min_value=1, value=25)

        goal2_name = st.text_input("Goal 2 Name", value="", placeholder="e.g., House Down Payment")
        goal2_amount = st.number_input("Goal 2 Target (₹)", min_value=0, value=0, step=100000)
        goal2_years = st.number_input("Goal 2 Timeline (years)", min_value=1, value=5)

        submitted = st.form_submit_button("💾 Save Profile", use_container_width=True)

        if submitted:
            goals = []
            if goal1_name and goal1_amount > 0:
                goals.append(
                    FinancialGoal(
                        name=goal1_name,
                        target_amount=goal1_amount,
                        target_years=goal1_years,
                        priority="high",
                    )
                )
            if goal2_name and goal2_amount > 0:
                goals.append(
                    FinancialGoal(
                        name=goal2_name,
                        target_amount=goal2_amount,
                        target_years=goal2_years,
                        priority="medium",
                    )
                )

            profile = UserProfile(
                name=name,
                age=age,
                annual_income=annual_income,
                monthly_expenses=monthly_expenses,
                risk_tolerance=RiskTolerance(risk_tolerance),
                investment_horizon_years=investment_horizon,
                existing_investments=existing_investments,
                financial_goals=goals,
            )
            st.session_state["user_profile"] = profile
            st.sidebar.success("Profile saved!")

    # Display current profile summary
    if st.session_state.get("user_profile"):
        profile = st.session_state["user_profile"]
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 Current Profile")
        monthly_savings = max(0, (profile.annual_income / 12) - profile.monthly_expenses)
        st.sidebar.metric("Monthly Savings", f"₹{monthly_savings:,.0f}")
        st.sidebar.metric("Risk Profile", profile.risk_tolerance.value.title())
        st.sidebar.metric("Horizon", f"{profile.investment_horizon_years} years")
