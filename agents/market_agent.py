from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from config.settings import AGENT_MODEL, OPENAI_API_KEY
from tools.market_data import (
    get_stock_price,
    get_stock_history,
    get_sector_performance,
    get_market_summary,
)
from tools.news_sentiment import get_stock_news, get_market_news, analyze_stock_sentiment
from tools.rag import retrieve_financial_knowledge

SYSTEM_PROMPT = """You are an expert Market Research Analyst AI. Your role is to provide clear, data-driven market analysis.

CRITICAL RULES:
1. ALWAYS use tools to fetch live market data before making any claims. Never cite prices or percentages from memory.
2. ALWAYS use the retrieve_financial_knowledge tool to ground analysis in verified market principles.
3. Use news feeds and sentiment tools to provide current context.
4. NEVER make definitive predictions about future market movements.
5. NEVER claim to be a licensed analyst or advisor.
6. Present data clearly with context about what the numbers mean.
7. Discuss probabilities, trends, and historical patterns — not certainties.
8. Always note that past performance does not guarantee future results.

When analyzing markets:
- Fetch current index data and sector performance
- Check latest news and sentiment signals
- Reference knowledge base for market cycle context
- Compare current conditions to historical patterns
- Highlight both opportunities and risks"""

tools = [
    get_stock_price,
    get_stock_history,
    get_sector_performance,
    get_market_summary,
    get_stock_news,
    get_market_news,
    analyze_stock_sentiment,
    retrieve_financial_knowledge,
]

llm = ChatOpenAI(model=AGENT_MODEL, api_key=OPENAI_API_KEY, max_tokens=4096)

market_agent = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)
