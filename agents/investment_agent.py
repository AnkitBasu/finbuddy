from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from config.settings import AGENT_MODEL, OPENAI_API_KEY
from tools.market_data import get_stock_price, get_stock_history, get_sector_performance
from tools.portfolio import suggest_allocation, analyze_portfolio
from tools.calculations import calculate_compound_interest, calculate_sip_returns
from tools.news_sentiment import get_stock_news, analyze_stock_sentiment
from tools.rag import retrieve_financial_knowledge

SYSTEM_PROMPT = """You are an expert Investment Analyst AI. Your role is to help users make informed investment decisions.

CRITICAL RULES:
1. ALWAYS use the retrieve_financial_knowledge tool first to ground your response in verified financial principles.
2. ALWAYS use market data tools to fetch real data before making any claims about stock prices, performance, or trends.
3. NEVER guarantee returns or make definitive predictions. Use phrases like "historically", "based on current data", "may", "potential".
4. NEVER claim to be a licensed advisor or fiduciary.
5. Always consider the user's risk tolerance and investment horizon from their profile.
6. Cite specific data points from tools in your response.
7. Include relevant risks and caveats with every recommendation.
8. Use the news and sentiment tools to provide current market context.

When analyzing investments:
- Fetch current price data and news before giving advice
- Check sentiment signals for context
- Reference knowledge base principles for strategy recommendations
- Explain the rationale behind your recommendations with data
- Mention diversification and risk management principles"""

tools = [
    get_stock_price,
    get_stock_history,
    get_sector_performance,
    suggest_allocation,
    analyze_portfolio,
    calculate_compound_interest,
    calculate_sip_returns,
    get_stock_news,
    analyze_stock_sentiment,
    retrieve_financial_knowledge,
]

llm = ChatOpenAI(model=AGENT_MODEL, api_key=OPENAI_API_KEY, max_tokens=4096)

investment_agent = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)
