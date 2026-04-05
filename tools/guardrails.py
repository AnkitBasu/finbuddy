import re
from config.settings import BLOCKED_TOPICS, COMPLIANCE_DISCLAIMER


def check_input_guardrails(user_message: str) -> tuple[bool, str]:
    """Check user input for prohibited topics and compliance violations.
    Returns (is_safe, reason_if_blocked)."""
    message_lower = user_message.lower()

    # Check for blocked topics
    for topic in BLOCKED_TOPICS:
        if topic in message_lower:
            return False, (
                f"I cannot provide guidance on '{topic}'. This topic involves potentially "
                f"illegal or unethical financial activities. Please consult a legal professional "
                f"for questions in this area."
            )

    # Check for requests for guaranteed returns
    guarantee_patterns = [
        r"guarantee.*return",
        r"guaranteed.*profit",
        r"risk.?free.*return",
        r"100%.*safe.*invest",
        r"can'?t lose",
        r"sure.*win",
    ]
    for pattern in guarantee_patterns:
        if re.search(pattern, message_lower):
            return True, ""  # Allow but flag for disclaimer emphasis

    return True, ""


def check_output_guardrails(response: str) -> str:
    """Post-process agent responses to enforce compliance and filter hallucinations."""
    # Flag patterns that suggest hallucination or overconfidence
    problematic_patterns = {
        r"(?i)I guarantee": "Based on historical data and analysis, ",
        r"(?i)you will definitely": "there is a possibility that you may ",
        r"(?i)guaranteed to": "historically shown potential to ",
        r"(?i)risk.?free investment": "lower-risk investment option ",
        r"(?i)can'?t go wrong": "has shown positive historical performance ",
        r"(?i)100% safe": "relatively lower-risk ",
        r"(?i)you should buy": "you may want to consider ",
        r"(?i)you must invest": "you might consider investing ",
        r"(?i)definitely buy": "consider researching ",
        r"(?i)this stock will": "this stock may ",
    }

    cleaned = response
    for pattern, replacement in problematic_patterns.items():
        cleaned = re.sub(pattern, replacement, cleaned)

    # Ensure the response doesn't claim to be a licensed advisor
    licensed_claims = [
        r"(?i)as a licensed",
        r"(?i)as a certified financial",
        r"(?i)as your financial advisor",
        r"(?i)I am a registered",
    ]
    for pattern in licensed_claims:
        cleaned = re.sub(
            pattern,
            "as an AI financial analysis tool",
            cleaned,
        )

    # Add compliance disclaimer if discussing investments
    investment_keywords = [
        "invest", "stock", "bond", "etf", "portfolio", "return",
        "buy", "sell", "allocation", "retirement", "sip", "mutual fund",
    ]
    if any(kw in cleaned.lower() for kw in investment_keywords):
        if "Disclaimer" not in cleaned:
            cleaned += COMPLIANCE_DISCLAIMER

    return cleaned


def validate_factual_grounding(response: str, tool_outputs: list[str]) -> str:
    """Add source attribution markers to ground the response in tool data.
    Appends a 'Sources' section listing which data tools were consulted."""
    if not tool_outputs:
        return response

    source_section = "\n\n**Data Sources Consulted:**\n"
    sources_added = set()

    source_mapping = {
        "Ticker:": "Live market data (Yahoo Finance)",
        "Sector Performance": "Sector ETF analysis (Yahoo Finance)",
        "Market Summary": "Major market indices (Yahoo Finance)",
        "Portfolio Analysis": "Portfolio analytics engine",
        "Budget Analysis": "Budget calculation engine",
        "SIP": "SIP/investment calculator",
        "Compound Interest": "Financial calculator",
        "Retirement": "Retirement planning calculator",
        "Sentiment Analysis": "Quantitative sentiment analysis",
        "Latest News": "Financial news feeds",
        "Allocation": "Asset allocation model",
        "Pinecone Vector DB": "Pinecone vector database (semantic search)",
        "QA | Topic": "Financial Q&A knowledge base (Pinecone)",
        "KB | Topic": "Financial knowledge base (Pinecone)",
        "Local Knowledge Base": "Local financial knowledge base (text files)",
    }

    for output in tool_outputs:
        for keyword, source in source_mapping.items():
            if keyword in output and source not in sources_added:
                sources_added.add(source)

    if sources_added:
        for src in sorted(sources_added):
            source_section += f"- {src}\n"
        return response + source_section

    return response
