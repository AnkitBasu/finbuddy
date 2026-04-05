import yfinance as yf
from langchain_core.tools import tool


@tool
def get_stock_price(ticker: str) -> str:
    """Get current stock price and key metrics for a given ticker symbol (e.g., AAPL, MSFT, GOOGL)."""
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info
        if not info or "currentPrice" not in info:
            hist = stock.history(period="1d")
            if hist.empty:
                return f"Could not fetch data for ticker '{ticker}'. Please verify the symbol."
            price = hist["Close"].iloc[-1]
            return (
                f"Ticker: {ticker.upper()}\n"
                f"Latest Price: ${price:.2f}\n"
                f"(Limited data available for this ticker)"
            )

        return (
            f"Ticker: {ticker.upper()}\n"
            f"Company: {info.get('shortName', 'N/A')}\n"
            f"Current Price: ${info.get('currentPrice', 'N/A')}\n"
            f"Day Range: ${info.get('dayLow', 'N/A')} - ${info.get('dayHigh', 'N/A')}\n"
            f"52-Week Range: ${info.get('fiftyTwoWeekLow', 'N/A')} - ${info.get('fiftyTwoWeekHigh', 'N/A')}\n"
            f"Market Cap: ${info.get('marketCap', 'N/A'):,}\n"
            f"P/E Ratio: {info.get('trailingPE', 'N/A')}\n"
            f"Dividend Yield: {info.get('dividendYield', 'N/A')}\n"
            f"Sector: {info.get('sector', 'N/A')}\n"
            f"Industry: {info.get('industry', 'N/A')}"
        )
    except Exception as e:
        return f"Error fetching data for {ticker}: {str(e)}"


@tool
def get_stock_history(ticker: str, period: str = "6mo") -> str:
    """Get historical stock price data. Period options: 1mo, 3mo, 6mo, 1y, 2y, 5y."""
    try:
        stock = yf.Ticker(ticker.upper())
        hist = stock.history(period=period)
        if hist.empty:
            return f"No historical data found for '{ticker}'."

        start_price = hist["Close"].iloc[0]
        end_price = hist["Close"].iloc[-1]
        high = hist["High"].max()
        low = hist["Low"].min()
        pct_change = ((end_price - start_price) / start_price) * 100
        avg_volume = hist["Volume"].mean()

        return (
            f"Ticker: {ticker.upper()} | Period: {period}\n"
            f"Start Price: ${start_price:.2f}\n"
            f"End Price: ${end_price:.2f}\n"
            f"Period Change: {pct_change:+.2f}%\n"
            f"Period High: ${high:.2f}\n"
            f"Period Low: ${low:.2f}\n"
            f"Average Daily Volume: {avg_volume:,.0f}\n"
            f"Data Points: {len(hist)} trading days"
        )
    except Exception as e:
        return f"Error fetching history for {ticker}: {str(e)}"


@tool
def get_sector_performance() -> str:
    """Get current performance of major market sectors using sector ETFs."""
    sectors = {
        "Technology": "XLK",
        "Financial": "XLF",
        "Healthcare": "XLV",
        "Energy": "XLE",
        "Consumer Discretionary": "XLY",
        "Consumer Staples": "XLP",
        "Industrial": "XLI",
        "Real Estate": "XLRE",
        "Utilities": "XLU",
        "Materials": "XLB",
    }
    results = ["=== Sector Performance (6-Month) ===\n"]
    for name, etf in sectors.items():
        try:
            hist = yf.Ticker(etf).history(period="6mo")
            if not hist.empty:
                pct = ((hist["Close"].iloc[-1] - hist["Close"].iloc[0]) / hist["Close"].iloc[0]) * 100
                results.append(f"{name} ({etf}): {pct:+.2f}%")
        except Exception:
            results.append(f"{name} ({etf}): Data unavailable")
    return "\n".join(results)


@tool
def get_market_summary() -> str:
    """Get a summary of major market indices (S&P 500, Nasdaq, Dow Jones)."""
    indices = {
        "S&P 500": "^GSPC",
        "Nasdaq Composite": "^IXIC",
        "Dow Jones": "^DJI",
        "Russell 2000": "^RUT",
    }
    results = ["=== Market Summary ===\n"]
    for name, symbol in indices.items():
        try:
            hist = yf.Ticker(symbol).history(period="5d")
            if len(hist) >= 2:
                current = hist["Close"].iloc[-1]
                prev = hist["Close"].iloc[-2]
                change = ((current - prev) / prev) * 100
                results.append(f"{name}: {current:,.2f} ({change:+.2f}% daily)")
        except Exception:
            results.append(f"{name}: Data unavailable")
    return "\n".join(results)
