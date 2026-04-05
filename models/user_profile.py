from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class RiskTolerance(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class FinancialGoal(BaseModel):
    name: str
    target_amount: float
    target_years: int = Field(ge=1, description="Years to achieve the goal")
    priority: str = "medium"


class UserProfile(BaseModel):
    name: str = "User"
    age: int = Field(default=30, ge=18, le=100)
    annual_income: float = Field(default=0, ge=0)
    monthly_expenses: float = Field(default=0, ge=0)
    risk_tolerance: RiskTolerance = RiskTolerance.MODERATE
    investment_horizon_years: int = Field(default=10, ge=1)
    existing_investments: str = ""
    financial_goals: list[FinancialGoal] = []

    def summary(self) -> str:
        goals_text = ""
        if self.financial_goals:
            goals_text = "\n  Financial Goals:\n"
            for g in self.financial_goals:
                goals_text += f"    - {g.name}: ₹{g.target_amount:,.0f} in {g.target_years} years (priority: {g.priority})\n"

        monthly_savings = max(0, (self.annual_income / 12) - self.monthly_expenses)

        return (
            f"Name: {self.name}\n"
            f"Age: {self.age}\n"
            f"Annual Income: ₹{self.annual_income:,.0f}\n"
            f"Monthly Expenses: ₹{self.monthly_expenses:,.0f}\n"
            f"Monthly Savings Capacity: ₹{monthly_savings:,.0f}\n"
            f"Risk Tolerance: {self.risk_tolerance.value}\n"
            f"Investment Horizon: {self.investment_horizon_years} years\n"
            f"Existing Investments: {self.existing_investments or 'None specified'}\n"
            f"Currency: INR (Indian Rupees)"
            f"{goals_text}"
        )
