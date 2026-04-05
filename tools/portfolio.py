import yfinance as yf
from langchain_core.tools import tool


@tool
def suggest_allocation(risk_tolerance: str, horizon_years: int) -> str:
    """Suggest a portfolio asset allocation based on risk tolerance and investment horizon.
    risk_tolerance: conservative, moderate, or aggressive."""
    allocations = {
        "conservative": {
            "Equities (Large Cap)": 20,
            "Equities (Mid/Small Cap)": 5,
            "Bonds / Fixed Income": 45,
            "Gold / Commodities": 15,
            "Cash / Money Market": 15,
        },
        "moderate": {
            "Equities (Large Cap)": 35,
            "Equities (Mid/Small Cap)": 15,
            "Bonds / Fixed Income": 30,
            "Gold / Commodities": 10,
            "Cash / Money Market": 10,
        },
        "aggressive": {
            "Equities (Large Cap)": 40,
            "Equities (Mid/Small Cap)": 30,
            "Bonds / Fixed Income": 15,
            "Gold / Commodities": 10,
            "Cash / Money Market": 5,
        },
    }

    risk = risk_tolerance.lower()
    if risk not in allocations:
        risk = "moderate"

    alloc = allocations[risk]

    # Adjust for horizon
    if horizon_years > 15:
        alloc["Equities (Large Cap)"] = min(60, alloc["Equities (Large Cap)"] + 10)
        alloc["Bonds / Fixed Income"] = max(5, alloc["Bonds / Fixed Income"] - 10)
    elif horizon_years < 3:
        alloc["Cash / Money Market"] = min(40, alloc["Cash / Money Market"] + 15)
        alloc["Equities (Mid/Small Cap)"] = max(0, alloc["Equities (Mid/Small Cap)"] - 15)

    result = [
        f"=== Suggested Asset Allocation ===",
        f"Risk Profile: {risk.title()} | Horizon: {horizon_years} years\n",
    ]
    sample_etfs = {
        "Equities (Large Cap)": "VOO, SPY, IVV",
        "Equities (Mid/Small Cap)": "VB, IJR, VXF",
        "Bonds / Fixed Income": "BND, AGG, TLT",
        "Gold / Commodities": "GLD, IAU, GSG",
        "Cash / Money Market": "SHV, BIL, SGOV",
    }
    for asset, pct in alloc.items():
        result.append(f"  {asset}: {pct}% (e.g., {sample_etfs.get(asset, '')})")

    return "\n".join(result)


@tool
def analyze_portfolio(holdings: str) -> str:
    """Analyze a portfolio of stock holdings. Provide holdings as comma-separated 'TICKER:SHARES' pairs.
    Example: 'AAPL:10,MSFT:5,GOOGL:3'"""
    try:
        pairs = [h.strip().split(":") for h in holdings.split(",")]
        portfolio = []
        total_value = 0

        for ticker, shares in pairs:
            ticker = ticker.strip().upper()
            shares = float(shares.strip())
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")
            if hist.empty:
                portfolio.append({"ticker": ticker, "shares": shares, "price": 0, "value": 0, "error": True})
                continue
            price = hist["Close"].iloc[-1]
            value = price * shares
            total_value += value

            hist_6m = stock.history(period="6mo")
            pct_6m = 0
            if len(hist_6m) > 1:
                pct_6m = ((hist_6m["Close"].iloc[-1] - hist_6m["Close"].iloc[0]) / hist_6m["Close"].iloc[0]) * 100

            portfolio.append({
                "ticker": ticker,
                "shares": shares,
                "price": price,
                "value": value,
                "pct_6m": pct_6m,
            })

        result = [f"=== Portfolio Analysis ===\n", f"Total Portfolio Value: ${total_value:,.2f}\n"]
        for h in portfolio:
            if h.get("error"):
                result.append(f"  {h['ticker']}: Data unavailable")
            else:
                weight = (h["value"] / total_value * 100) if total_value > 0 else 0
                result.append(
                    f"  {h['ticker']}: {h['shares']:.0f} shares @ ${h['price']:.2f} = "
                    f"${h['value']:,.2f} ({weight:.1f}% of portfolio, {h['pct_6m']:+.1f}% 6mo)"
                )

        return "\n".join(result)
    except Exception as e:
        return f"Error analyzing portfolio. Please use format 'TICKER:SHARES,TICKER:SHARES'. Error: {str(e)}"
