import os
import hashlib
from pathlib import Path
from langchain_core.tools import tool
from config.settings import PINECONE_API_KEY, RAG_TOP_K

# Directory for financial knowledge base documents
KNOWLEDGE_DIR = Path(__file__).parent.parent / "data" / "knowledge_base"

# ──────────────────────────────────────────────
# Local txt-based document store (unchanged)
# ──────────────────────────────────────────────
_documents: list[dict] = []


def _load_knowledge_base():
    """Load all text documents from the knowledge base directory."""
    global _documents
    if _documents:
        return

    if not KNOWLEDGE_DIR.exists():
        KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
        _create_default_knowledge_base()

    for filepath in KNOWLEDGE_DIR.glob("*.txt"):
        content = filepath.read_text(encoding="utf-8")
        sections = [s.strip() for s in content.split("\n\n") if s.strip()]
        for i, section in enumerate(sections):
            _documents.append({
                "id": hashlib.md5(f"{filepath.name}:{i}".encode()).hexdigest()[:8],
                "source": filepath.name,
                "content": section,
                "keywords": _extract_keywords(section),
            })


def _extract_keywords(text: str) -> set[str]:
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "can", "shall", "to", "of", "in", "for",
        "on", "with", "at", "by", "from", "as", "into", "about", "between",
        "through", "during", "before", "after", "and", "but", "or", "not",
        "this", "that", "these", "those", "it", "its", "they", "their",
        "which", "what", "who", "when", "where", "how", "all", "each",
        "every", "both", "few", "more", "most", "other", "some", "such",
        "than", "too", "very", "just", "also", "over", "if", "your", "you",
    }
    words = set()
    for word in text.lower().split():
        cleaned = "".join(c for c in word if c.isalnum())
        if cleaned and len(cleaned) > 2 and cleaned not in stop_words:
            words.add(cleaned)
    return words


def _keyword_search(query: str, top_k: int = RAG_TOP_K) -> list[dict]:
    _load_knowledge_base()
    query_keywords = _extract_keywords(query)
    if not query_keywords:
        return []

    scored = []
    for doc in _documents:
        overlap = query_keywords & doc["keywords"]
        if overlap:
            score = len(overlap) / len(query_keywords)
            scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in scored[:top_k]]


# ──────────────────────────────────────────────
# Pinecone semantic search
# ──────────────────────────────────────────────
def _pinecone_search(query: str, top_k: int = RAG_TOP_K) -> list[dict]:
    """Query Pinecone vector DB for semantically relevant documents."""
    if not PINECONE_API_KEY:
        return []

    try:
        from tools.vector_store import query_pinecone
        results = query_pinecone(query, top_k=top_k)
        return results
    except Exception as e:
        print(f"Pinecone search failed (falling back to local): {e}")
        return []


# ──────────────────────────────────────────────
# Unified RAG tool
# ──────────────────────────────────────────────
@tool
def retrieve_financial_knowledge(query: str) -> str:
    """Retrieve relevant financial knowledge, regulations, and investment principles
    from the knowledge base (local text files + Pinecone vector DB).
    Use this to ground your responses in verified financial information."""

    output_sections = []

    # 1. Pinecone vector search (semantic)
    pinecone_results = _pinecone_search(query, top_k=RAG_TOP_K)
    if pinecone_results:
        output_sections.append("=== Pinecone Vector DB Results (Semantic Search) ===\n")
        for r in pinecone_results:
            meta = r["metadata"]
            text = meta.get("text", "")
            source = meta.get("source_file", "unknown")
            topic = meta.get("topic", "")
            score = r["score"]
            namespace = r["namespace"]

            # Format differently based on namespace
            if namespace == "finance_qa":
                question = meta.get("question", "")
                answer = meta.get("answer", "")
                output_sections.append(
                    f"[QA | Topic: {topic} | Score: {score:.3f}]\n"
                    f"  Q: {question}\n"
                    f"  A: {answer}\n"
                )
            else:
                region = meta.get("region", "")
                risk = meta.get("risk_level", "")
                source_name = meta.get("source", "")
                output_sections.append(
                    f"[KB | Topic: {topic} | Source: {source_name} | Region: {region} | "
                    f"Risk: {risk} | Score: {score:.3f}]\n"
                    f"  {text}\n"
                )

    # 2. Local keyword search (txt files)
    local_results = _keyword_search(query, top_k=RAG_TOP_K)
    if local_results:
        output_sections.append("=== Local Knowledge Base Results (Keyword Search) ===\n")
        for doc in local_results:
            output_sections.append(f"[Source: {doc['source']}]\n{doc['content']}\n")

    if not output_sections:
        return "No directly relevant knowledge base entries found for this query."

    output_sections.append(
        "\nIMPORTANT: Use the above verified information to ground your response. "
        "Do not contradict or embellish these facts."
    )
    return "\n".join(output_sections)


# ──────────────────────────────────────────────
# Default knowledge base creation (txt files only)
# ──────────────────────────────────────────────
def _create_default_knowledge_base():
    """Create default financial knowledge base documents."""

    docs = {
        "investment_principles.txt": """Asset Allocation Fundamentals
Asset allocation is the process of dividing investments among different asset categories such as stocks, bonds, real estate, and cash. The right allocation depends on your time horizon, risk tolerance, and financial goals. A common rule of thumb is to subtract your age from 110 to determine your stock allocation percentage.

Diversification Strategy
Diversification reduces risk by spreading investments across various financial instruments, industries, and categories. A well-diversified portfolio typically includes domestic stocks, international stocks, bonds, real estate (REITs), and commodities. No single investment should represent more than 5-10% of a portfolio for individual stocks.

Dollar-Cost Averaging (DCA)
Dollar-cost averaging involves investing a fixed amount at regular intervals regardless of market conditions. This strategy reduces the impact of volatility on the overall purchase price. DCA is particularly effective for long-term investors in volatile markets and helps avoid the pitfall of trying to time the market.

Risk-Return Tradeoff
Higher potential returns generally come with higher risk. Conservative investors should emphasize bonds and stable value funds. Moderate investors typically hold a 60/40 stock-to-bond ratio. Aggressive investors may allocate 80-90% to equities. Risk tolerance should decrease as you approach your financial goal's target date.

Index Fund Investing
Index funds provide broad market exposure at low cost. The S&P 500 index has historically returned approximately 10% annually before inflation (about 7% after inflation). Total market index funds offer even broader diversification. Low expense ratios (under 0.10%) significantly impact long-term returns due to compounding.

Rebalancing
Portfolio rebalancing involves periodically adjusting your asset mix back to your target allocation. This typically means selling assets that have performed well and buying those that have underperformed. Most financial advisors recommend rebalancing at least annually or when allocations drift more than 5% from targets.

Compound Interest
Compound interest is the addition of interest to the principal sum, meaning interest earns interest over time. The Rule of 72 states that dividing 72 by your annual return rate gives you the approximate years to double your investment. Starting early is crucial — a 25-year-old investing $500/month at 10% return will accumulate approximately $3.2 million by age 65.

Value vs Growth Investing
Value investing focuses on stocks that appear underpriced relative to their fundamentals (low P/E ratio, high dividend yield). Growth investing targets companies with above-average revenue and earnings growth potential. Historically, value stocks have outperformed growth stocks over long periods, though growth stocks have dominated in recent decades.""",

        "retirement_planning.txt": """Retirement Savings Guidelines
Financial experts recommend saving 15-20% of pre-tax income for retirement. The 4% withdrawal rule suggests you can safely withdraw 4% of your retirement portfolio annually (adjusted for inflation) with minimal risk of running out of money over a 30-year retirement period.

401(k) and IRA Strategies
Maximize employer 401(k) matching contributions first — this is essentially free money with an immediate 100% return. The 2024 401(k) contribution limit is $23,000 ($30,500 for those 50+). Traditional IRA contributions may be tax-deductible. Roth IRA contributions are made with after-tax dollars but grow tax-free.

Social Security Optimization
Full Social Security retirement age ranges from 66 to 67 depending on birth year. Claiming at 62 permanently reduces benefits by up to 30%. Delaying until age 70 increases benefits by 8% per year beyond full retirement age. Spousal benefits can be up to 50% of the higher-earning spouse's benefit.

Required Minimum Distributions (RMDs)
Traditional IRA and 401(k) accounts require minimum distributions starting at age 73 (as of SECURE 2.0 Act). Roth IRAs have no RMDs during the owner's lifetime. Failing to take RMDs results in a 25% excise tax on the amount not distributed.

Retirement Corpus Calculation
To estimate your retirement corpus: (1) Calculate your expected annual expenses at retirement, adjusted for inflation. (2) Multiply by 25 (based on the 4% rule). (3) Subtract expected Social Security and pension income (capitalized). For example, if you expect $60,000 annual expenses and $24,000 from Social Security, you need ($60,000 - $24,000) × 25 = $900,000.

Healthcare in Retirement
Medicare eligibility begins at age 65. Before Medicare, COBRA or marketplace insurance is needed. Average healthcare costs in retirement are estimated at $315,000 per couple (Fidelity 2023 estimate). Health Savings Accounts (HSAs) are triple-tax-advantaged and can be used as retirement healthcare funds.""",

        "budgeting_principles.txt": """The 50/30/20 Budget Rule
Allocate 50% of after-tax income to needs (housing, groceries, insurance, minimum debt payments), 30% to wants (dining out, entertainment, subscriptions), and 20% to savings and extra debt payments. This framework provides a flexible starting point that can be adjusted based on individual circumstances.

Emergency Fund Guidelines
Maintain 3-6 months of essential expenses in a high-yield savings account. If you have variable income or are the sole earner, aim for 6-12 months. Emergency funds should be liquid and easily accessible, not invested in stocks or locked in CDs. High-yield savings accounts currently offer 4-5% APY.

Debt Management Strategies
The debt avalanche method pays off highest-interest debt first, minimizing total interest paid. The debt snowball method pays off smallest balances first for psychological momentum. For credit card debt averaging 20%+ APR, debt payoff should generally be prioritized over investing (except for employer 401k match).

Zero-Based Budgeting
In zero-based budgeting, every dollar of income is assigned a purpose. Income minus all allocations (expenses + savings + investments) equals zero. This method provides maximum control and visibility over spending. It requires more effort but is highly effective for people who want to optimize their finances.

Savings Rate Impact
A 10% savings rate with average market returns leads to retirement in approximately 50 years. A 25% savings rate reduces this to about 32 years. A 50% savings rate reduces this to about 17 years. The savings rate is often more impactful than investment returns in the early years of wealth building.

Lifestyle Inflation
Lifestyle inflation (or lifestyle creep) occurs when spending increases as income rises. To combat this, commit to saving at least 50% of every raise or bonus. Automate savings increases with income increases. The hedonic treadmill suggests that increased spending provides only temporary happiness increases.""",

        "market_fundamentals.txt": """Stock Market Basics
Stocks represent ownership shares in a company. Stock prices are driven by supply and demand, which reflect investor expectations about future earnings. The price-to-earnings (P/E) ratio is a key valuation metric — the S&P 500 historical average P/E is approximately 15-16. Current market P/E ratios above 20 suggest higher valuations relative to historical norms.

Bond Market Fundamentals
Bonds are debt instruments where the investor lends money to an entity. Bond prices move inversely to interest rates. When interest rates rise, existing bond prices fall. US Treasury bonds are considered risk-free. Corporate bonds carry credit risk but offer higher yields. Duration measures a bond's sensitivity to interest rate changes.

Market Cycles and Bear Markets
Bear markets (20%+ decline from recent highs) have occurred approximately every 3-5 years historically. The average bear market lasts about 9-14 months. Bull markets average 4-5 years in duration. Historically, markets have always recovered from bear markets, though recovery times vary from months to years.

Inflation and Its Impact
Inflation erodes purchasing power over time. The Federal Reserve targets 2% annual inflation. Investments must earn above the inflation rate to grow in real terms. Treasury Inflation-Protected Securities (TIPS) provide direct inflation protection. Stocks have historically outpaced inflation over long periods. Real estate and commodities can also serve as inflation hedges.

Market Indicators
Key indicators include: GDP growth rate (healthy economy: 2-3% annually), unemployment rate (healthy: under 5%), Consumer Price Index (CPI) for inflation, Federal Funds Rate (influences all borrowing costs), yield curve (inverted yield curve has preceded every recession since 1970), VIX index (market fear gauge, above 30 indicates high volatility).

Sector Rotation
Different sectors outperform at different stages of the economic cycle. Early recovery favors cyclicals (consumer discretionary, financials). Mid-cycle favors technology and industrials. Late cycle favors energy and materials. Recession favors defensive sectors (utilities, healthcare, consumer staples).""",

        "financial_regulations.txt": """SEC Investor Protection Rules
The Securities and Exchange Commission (SEC) enforces federal securities laws. Key regulations include: mandatory disclosure of material information by public companies, prohibition of insider trading, regulation of securities exchanges and broker-dealers, and investor protection through the Securities Investor Protection Corporation (SIPC) which covers up to $500,000 per account.

Fiduciary Duty
Registered Investment Advisors (RIAs) owe a fiduciary duty to clients, meaning they must act in the client's best interest. Broker-dealers operate under a suitability standard, which is less strict. The SEC's Regulation Best Interest (Reg BI) enhanced the standard for broker-dealers in 2020. Always verify whether your advisor is a fiduciary.

FINRA Regulations
The Financial Industry Regulatory Authority (FINRA) oversees broker-dealers. FINRA rules include suitability requirements, margin requirements, and advertising regulations. Investors can check broker backgrounds at FINRA BrokerCheck. FINRA arbitration handles disputes between investors and brokers.

Know Your Customer (KYC) and Anti-Money Laundering (AML)
Financial institutions must verify customer identity and monitor for suspicious activity. The Bank Secrecy Act requires reporting of transactions over $10,000. Structuring transactions to avoid reporting requirements is illegal. These regulations protect against fraud, money laundering, and terrorist financing.

Tax Implications of Investing
Long-term capital gains (assets held over 1 year) are taxed at 0%, 15%, or 20% depending on income. Short-term capital gains are taxed as ordinary income. Tax-loss harvesting can offset gains with losses (up to $3,000 of net losses can offset ordinary income annually). Wash sale rules prohibit repurchasing substantially identical securities within 30 days of a loss sale.

Suitability and Risk Disclosure
Investment recommendations must be suitable for the client's financial situation, objectives, and risk tolerance. All material risks must be disclosed. Past performance disclaimers are legally required. No investment can be marketed as guaranteed or risk-free. Projected returns must be accompanied by appropriate disclaimers.""",
    }

    for filename, content in docs.items():
        filepath = KNOWLEDGE_DIR / filename
        filepath.write_text(content, encoding="utf-8")


# Initialize local knowledge base on import
_load_knowledge_base()
