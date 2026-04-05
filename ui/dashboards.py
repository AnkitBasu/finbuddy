import streamlit as st
import plotly.graph_objects as go


def render_portfolio_dashboard(profile):
    st.subheader("📈 Recommended Asset Allocation")

    risk = profile.risk_tolerance.value
    horizon = profile.investment_horizon_years

    allocations = {
        "conservative": {
            "Large Cap Equity": 20,
            "Mid/Small Cap Equity": 5,
            "Bonds": 45,
            "Gold": 15,
            "Cash": 15,
        },
        "moderate": {
            "Large Cap Equity": 35,
            "Mid/Small Cap Equity": 15,
            "Bonds": 30,
            "Gold": 10,
            "Cash": 10,
        },
        "aggressive": {
            "Large Cap Equity": 40,
            "Mid/Small Cap Equity": 30,
            "Bonds": 15,
            "Gold": 10,
            "Cash": 5,
        },
    }

    alloc = allocations.get(risk, allocations["moderate"])

    # Adjust for horizon
    if horizon > 15:
        alloc["Large Cap Equity"] = min(60, alloc["Large Cap Equity"] + 10)
        alloc["Bonds"] = max(5, alloc["Bonds"] - 10)

    colors = ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D", "#3B1F2B"]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=list(alloc.keys()),
                values=list(alloc.values()),
                hole=0.4,
                marker=dict(colors=colors),
                textinfo="label+percent",
                textfont_size=12,
            )
        ]
    )
    fig.update_layout(
        title=f"Allocation for {risk.title()} Profile ({horizon}yr horizon)",
        height=400,
        showlegend=True,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_goals_tracker(profile):
    if not profile.financial_goals:
        st.info("Add financial goals in the sidebar to see your progress tracker.")
        return

    st.subheader("🎯 Financial Goals")

    monthly_savings = max(0, (profile.annual_income / 12) - profile.monthly_expenses)

    for goal in profile.financial_goals:
        st.markdown(f"**{goal.name}** — Target: ₹{goal.target_amount:,.0f} in {goal.target_years} years")

        # Estimate progress with monthly savings at 10% return
        monthly_rate = 0.10 / 12
        months = goal.target_years * 12
        if monthly_rate > 0 and monthly_savings > 0:
            future_value = monthly_savings * (
                ((1 + monthly_rate) ** months - 1) / monthly_rate
            ) * (1 + monthly_rate)
            progress = min(1.0, future_value / goal.target_amount)
        else:
            progress = 0

        st.progress(progress, text=f"{progress * 100:.0f}% achievable with current savings")

        # Required monthly SIP
        if monthly_rate > 0:
            required_sip = goal.target_amount / (
                ((1 + monthly_rate) ** months - 1) / monthly_rate * (1 + monthly_rate)
            )
            col1, col2 = st.columns(2)
            col1.metric("Required Monthly SIP", f"₹{required_sip:,.0f}")
            col2.metric("Your Monthly Savings", f"₹{monthly_savings:,.0f}")

        st.markdown("---")


def render_budget_overview(profile):
    st.subheader("💰 Budget Overview")

    monthly_income = profile.annual_income / 12
    expenses = profile.monthly_expenses
    savings = monthly_income - expenses

    col1, col2, col3 = st.columns(3)
    col1.metric("Monthly Income", f"₹{monthly_income:,.0f}")
    col2.metric("Monthly Expenses", f"₹{expenses:,.0f}")
    col3.metric("Monthly Savings", f"₹{savings:,.0f}", delta=f"{(savings/monthly_income*100):.0f}%" if monthly_income > 0 else "0%")

    # 50/30/20 comparison
    ideal_needs = monthly_income * 0.50
    ideal_wants = monthly_income * 0.30
    ideal_savings = monthly_income * 0.20

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Actual",
            x=["Expenses", "Savings"],
            y=[expenses, savings],
            marker_color=["#F18F01", "#2E86AB"],
        )
    )
    fig.add_trace(
        go.Bar(
            name="Recommended (50/30/20)",
            x=["Expenses", "Savings"],
            y=[ideal_needs + ideal_wants, ideal_savings],
            marker_color=["#FFD166", "#90BE6D"],
        )
    )
    fig.update_layout(
        barmode="group",
        title="Actual vs Recommended Budget",
        height=350,
        yaxis_title="Amount (₹)",
    )
    st.plotly_chart(fig, use_container_width=True)
