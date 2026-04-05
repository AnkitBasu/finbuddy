import math
from langchain_core.tools import tool


@tool
def calculate_compound_interest(
    principal: float,
    annual_rate: float,
    years: int,
    compounds_per_year: int = 12,
) -> str:
    """Calculate compound interest. annual_rate should be in percentage (e.g., 8 for 8%). All amounts in INR."""
    rate = annual_rate / 100
    amount = principal * (1 + rate / compounds_per_year) ** (compounds_per_year * years)
    interest = amount - principal
    return (
        f"Principal: ₹{principal:,.2f}\n"
        f"Annual Rate: {annual_rate}%\n"
        f"Duration: {years} years\n"
        f"Compounding: {compounds_per_year}x/year\n"
        f"Final Amount: ₹{amount:,.2f}\n"
        f"Total Interest Earned: ₹{interest:,.2f}\n"
        f"Total Return: {((amount / principal) - 1) * 100:.1f}%"
    )


@tool
def calculate_sip_returns(
    monthly_amount: float,
    annual_rate: float,
    years: int,
) -> str:
    """Calculate Systematic Investment Plan (SIP) / monthly investment returns.
    annual_rate in percentage (e.g., 12 for 12%). All amounts in INR."""
    monthly_rate = annual_rate / 100 / 12
    months = years * 12
    if monthly_rate == 0:
        future_value = monthly_amount * months
    else:
        future_value = monthly_amount * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)
    total_invested = monthly_amount * months
    wealth_gained = future_value - total_invested

    return (
        f"Monthly Investment: ₹{monthly_amount:,.2f}\n"
        f"Annual Return Rate: {annual_rate}%\n"
        f"Duration: {years} years ({months} months)\n"
        f"Total Invested: ₹{total_invested:,.2f}\n"
        f"Future Value: ₹{future_value:,.2f}\n"
        f"Wealth Gained: ₹{wealth_gained:,.2f}\n"
        f"Effective Return: {((future_value / total_invested) - 1) * 100:.1f}%"
    )


@tool
def calculate_retirement_corpus(
    current_age: int,
    retirement_age: int,
    monthly_expense: float,
    inflation_rate: float = 6.0,
    post_retirement_return: float = 7.0,
    life_expectancy: int = 85,
) -> str:
    """Calculate the retirement corpus needed. Rates in percentage. All amounts in INR."""
    years_to_retire = retirement_age - current_age
    retirement_years = life_expectancy - retirement_age

    if years_to_retire <= 0:
        return "Retirement age must be greater than current age."

    future_monthly_expense = monthly_expense * ((1 + inflation_rate / 100) ** years_to_retire)
    future_annual_expense = future_monthly_expense * 12

    real_return = ((1 + post_retirement_return / 100) / (1 + inflation_rate / 100)) - 1
    if real_return <= 0:
        corpus_needed = future_annual_expense * retirement_years
    else:
        corpus_needed = future_annual_expense * ((1 - (1 + real_return) ** (-retirement_years)) / real_return)

    return (
        f"Current Age: {current_age} | Retirement Age: {retirement_age}\n"
        f"Years to Retirement: {years_to_retire}\n"
        f"Current Monthly Expenses: ₹{monthly_expense:,.2f}\n"
        f"Projected Monthly Expenses at Retirement: ₹{future_monthly_expense:,.2f}\n"
        f"Inflation Rate: {inflation_rate}%\n"
        f"Post-Retirement Return: {post_retirement_return}%\n"
        f"Retirement Duration: {retirement_years} years (until age {life_expectancy})\n"
        f"Estimated Corpus Needed: ₹{corpus_needed:,.2f}\n"
        f"Monthly SIP Required (at 12% return): ₹{corpus_needed / (((1 + 0.01) ** (years_to_retire * 12) - 1) / 0.01 * 1.01):,.2f}"
    )


@tool
def calculate_goal_sip(
    target_amount: float,
    years: int,
    expected_annual_return: float = 12.0,
) -> str:
    """Calculate how much monthly SIP is needed to reach a financial goal. All amounts in INR."""
    monthly_rate = expected_annual_return / 100 / 12
    months = years * 12
    if monthly_rate == 0:
        monthly_sip = target_amount / months
    else:
        monthly_sip = target_amount / ((((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate))

    total_invested = monthly_sip * months
    return (
        f"Target Amount: ₹{target_amount:,.2f}\n"
        f"Time Horizon: {years} years\n"
        f"Expected Annual Return: {expected_annual_return}%\n"
        f"Required Monthly SIP: ₹{monthly_sip:,.2f}\n"
        f"Total You'll Invest: ₹{total_invested:,.2f}\n"
        f"Wealth Gain from Returns: ₹{target_amount - total_invested:,.2f}"
    )


@tool
def budget_analysis(
    monthly_income: float,
    rent: float = 0,
    food: float = 0,
    transport: float = 0,
    utilities: float = 0,
    entertainment: float = 0,
    insurance: float = 0,
    emi: float = 0,
    other: float = 0,
) -> str:
    """Analyze a monthly budget using the 50/30/20 rule. All amounts in INR (Indian Rupees)."""
    total_expenses = rent + food + transport + utilities + entertainment + insurance + emi + other
    savings = monthly_income - total_expenses
    savings_rate = (savings / monthly_income * 100) if monthly_income > 0 else 0

    needs = rent + food + transport + utilities + insurance + emi
    wants = entertainment + other
    ideal_needs = monthly_income * 0.50
    ideal_wants = monthly_income * 0.30
    ideal_savings = monthly_income * 0.20

    return (
        f"=== Monthly Budget Analysis ===\n"
        f"Income: ₹{monthly_income:,.2f}\n\n"
        f"Expenses Breakdown:\n"
        f"  Rent/Housing: ₹{rent:,.2f}\n"
        f"  Food/Groceries: ₹{food:,.2f}\n"
        f"  Transport: ₹{transport:,.2f}\n"
        f"  Utilities: ₹{utilities:,.2f}\n"
        f"  Entertainment: ₹{entertainment:,.2f}\n"
        f"  Insurance: ₹{insurance:,.2f}\n"
        f"  EMI/Loans: ₹{emi:,.2f}\n"
        f"  Other: ₹{other:,.2f}\n"
        f"  Total Expenses: ₹{total_expenses:,.2f}\n\n"
        f"Savings: ₹{savings:,.2f} ({savings_rate:.1f}% of income)\n\n"
        f"50/30/20 Rule Comparison:\n"
        f"  Needs (50%): ₹{needs:,.2f} vs Ideal ₹{ideal_needs:,.2f} {'✓' if needs <= ideal_needs else '⚠ Over budget'}\n"
        f"  Wants (30%): ₹{wants:,.2f} vs Ideal ₹{ideal_wants:,.2f} {'✓' if wants <= ideal_wants else '⚠ Over budget'}\n"
        f"  Savings (20%): ₹{savings:,.2f} vs Ideal ₹{ideal_savings:,.2f} {'✓' if savings >= ideal_savings else '⚠ Below target'}"
    )
