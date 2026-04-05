import os
from dotenv import load_dotenv

load_dotenv()


def _get_secret(key: str, default: str = "") -> str:
    """Read from env vars (local .env) first, then fall back to st.secrets (Streamlit Cloud)."""
    value = os.getenv(key, "")
    if value:
        return value
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except (ImportError, FileNotFoundError, AttributeError):
        return default


OPENAI_API_KEY = _get_secret("OPENAI_KEY")
PINECONE_API_KEY = _get_secret("PINECONE_API_KEY")

# LangSmith Observability
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = _get_secret("LANGSMITH_API_KEY")
os.environ["LANGSMITH_PROJECT"] = _get_secret("LANGSMITH_PROJECT") or "finbuddy"

SUPERVISOR_MODEL = "gpt-5.2"
AGENT_MODEL = "gpt-5.2"

DEFAULT_RISK_TOLERANCE = "moderate"
MAX_CONVERSATION_MESSAGES = 20

# RAG Settings
RAG_CHUNK_SIZE = 500
RAG_CHUNK_OVERLAP = 50
RAG_TOP_K = 4

# Guardrails
BLOCKED_TOPICS = [
    "insider trading",
    "money laundering",
    "tax evasion",
    "market manipulation",
    "pump and dump",
    "ponzi scheme",
]

COMPLIANCE_DISCLAIMER = (
    "\n\n---\n"
    "*Disclaimer: This information is for educational purposes only and does not constitute "
    "personalized financial advice. Past performance does not guarantee future results. "
    "Please consult a certified financial advisor (CFA/CFP) before making investment decisions. "
    "All investments carry risk, including the potential loss of principal.*"
)

# Pinecone Settings
PINECONE_INDEX_NAME = "financial-advisor-kb"
PINECONE_DIMENSION = 1024
PINECONE_METRIC = "cosine"
PINECONE_NAMESPACE_QA = "finance_qa"
PINECONE_NAMESPACE_KB = "pinecone_kb"

# News Settings
NEWS_RSS_FEEDS = {
    "Reuters Business": "https://feeds.reuters.com/reuters/businessNews",
    "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
    "MarketWatch": "https://feeds.marketwatch.com/marketwatch/topstories/",
}
NEWS_MAX_ARTICLES = 10
