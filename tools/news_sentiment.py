import yfinance as yf
import feedparser
from datetime import datetime
from langchain_core.tools import tool
from config.settings import NEWS_RSS_FEEDS, NEWS_MAX_ARTICLES


@tool
def get_stock_news(ticker: str) -> str:
    """Get the latest news articles for a specific stock ticker using Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker.upper())
        news = stock.news
        if not news:
            return f"No recent news found for {ticker.upper()}."

        results = [f"=== Latest News for {ticker.upper()} ===\n"]
        for article in news[:NEWS_MAX_ARTICLES]:
            content = article.get("content", {})
            title = content.get("title", "No title")
            provider = content.get("provider", {}).get("displayName", "Unknown")
            pub_date = content.get("pubDate", "Unknown date")
            summary = content.get("summary", "No summary available.")

            results.append(
                f"• [{provider}] {title}\n"
                f"  Date: {pub_date}\n"
                f"  Summary: {summary[:200]}...\n"
            )

        return "\n".join(results)
    except Exception as e:
        return f"Error fetching news for {ticker}: {str(e)}"


@tool
def get_market_news() -> str:
    """Get the latest financial market news from major RSS feeds (Reuters, MarketWatch)."""
    all_articles = []

    for source_name, feed_url in NEWS_RSS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                pub_date = ""
                if hasattr(entry, "published"):
                    pub_date = entry.published
                elif hasattr(entry, "updated"):
                    pub_date = entry.updated

                summary = ""
                if hasattr(entry, "summary"):
                    summary = entry.summary[:200]

                all_articles.append({
                    "source": source_name,
                    "title": entry.get("title", "No title"),
                    "date": pub_date,
                    "summary": summary,
                    "link": entry.get("link", ""),
                })
        except Exception:
            continue

    if not all_articles:
        return "Unable to fetch market news at this time. News feeds may be temporarily unavailable."

    results = [f"=== Latest Market News ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ===\n"]
    for a in all_articles[:NEWS_MAX_ARTICLES]:
        results.append(
            f"• [{a['source']}] {a['title']}\n"
            f"  {a['date']}\n"
            f"  {a['summary']}\n"
        )

    return "\n".join(results)


@tool
def analyze_stock_sentiment(ticker: str) -> str:
    """Analyze sentiment signals for a stock based on recent price action, volume, and news volume.
    Provides a data-driven sentiment assessment without speculation."""
    try:
        stock = yf.Ticker(ticker.upper())

        # Price momentum signals
        hist_5d = stock.history(period="5d")
        hist_1mo = stock.history(period="1mo")
        hist_3mo = stock.history(period="3mo")

        if hist_5d.empty or hist_1mo.empty:
            return f"Insufficient data to analyze sentiment for {ticker.upper()}."

        current = hist_5d["Close"].iloc[-1]

        # Short-term momentum (5-day)
        pct_5d = ((hist_5d["Close"].iloc[-1] - hist_5d["Close"].iloc[0]) / hist_5d["Close"].iloc[0]) * 100

        # Medium-term momentum (1-month)
        pct_1mo = ((hist_1mo["Close"].iloc[-1] - hist_1mo["Close"].iloc[0]) / hist_1mo["Close"].iloc[0]) * 100

        # Longer-term momentum (3-month)
        pct_3mo = 0
        if not hist_3mo.empty and len(hist_3mo) > 1:
            pct_3mo = ((hist_3mo["Close"].iloc[-1] - hist_3mo["Close"].iloc[0]) / hist_3mo["Close"].iloc[0]) * 100

        # Volume analysis
        avg_vol_1mo = hist_1mo["Volume"].mean()
        recent_vol = hist_5d["Volume"].mean()
        vol_ratio = recent_vol / avg_vol_1mo if avg_vol_1mo > 0 else 1

        # Volatility (standard deviation of daily returns)
        if len(hist_1mo) > 2:
            daily_returns = hist_1mo["Close"].pct_change().dropna()
            volatility = daily_returns.std() * (252 ** 0.5) * 100  # Annualized
        else:
            volatility = 0

        # Simple sentiment score (-100 to +100)
        score = 0
        score += min(30, max(-30, pct_5d * 5))    # Short-term weight
        score += min(40, max(-40, pct_1mo * 2))    # Medium-term weight
        score += min(30, max(-30, pct_3mo * 1))    # Longer-term weight

        if score > 30:
            sentiment = "BULLISH"
        elif score > 10:
            sentiment = "SLIGHTLY BULLISH"
        elif score > -10:
            sentiment = "NEUTRAL"
        elif score > -30:
            sentiment = "SLIGHTLY BEARISH"
        else:
            sentiment = "BEARISH"

        # News count
        news_count = 0
        try:
            news = stock.news
            news_count = len(news) if news else 0
        except Exception:
            pass

        return (
            f"=== Sentiment Analysis: {ticker.upper()} ===\n\n"
            f"Current Price: ${current:.2f}\n"
            f"Overall Sentiment: {sentiment} (Score: {score:.0f}/100)\n\n"
            f"Price Momentum:\n"
            f"  5-Day Change: {pct_5d:+.2f}%\n"
            f"  1-Month Change: {pct_1mo:+.2f}%\n"
            f"  3-Month Change: {pct_3mo:+.2f}%\n\n"
            f"Volume Analysis:\n"
            f"  Recent Avg Volume: {recent_vol:,.0f}\n"
            f"  1-Month Avg Volume: {avg_vol_1mo:,.0f}\n"
            f"  Volume Ratio: {vol_ratio:.2f}x {'(Above Average)' if vol_ratio > 1.2 else '(Below Average)' if vol_ratio < 0.8 else '(Normal)'}\n\n"
            f"Volatility: {volatility:.1f}% annualized {'(High)' if volatility > 40 else '(Moderate)' if volatility > 20 else '(Low)'}\n"
            f"Recent News Articles: {news_count}\n\n"
            f"Note: This analysis is based on quantitative price/volume signals only. "
            f"It does not account for fundamental factors, earnings, or macroeconomic events."
        )
    except Exception as e:
        return f"Error analyzing sentiment for {ticker}: {str(e)}"
