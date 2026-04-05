from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END

from agents.state import AdvisorState
from agents.investment_agent import investment_agent
from agents.budgeting_agent import budgeting_agent
from agents.market_agent import market_agent
from agents.planning_agent import planning_agent
from tools.guardrails import (
    check_input_guardrails,
    check_output_guardrails,
    validate_factual_grounding,
)
from tools.rag import retrieve_financial_knowledge
from config.settings import SUPERVISOR_MODEL, OPENAI_API_KEY

MEMBERS = ["investment", "budgeting", "market", "planning"]

SUPERVISOR_PROMPT = """You are a senior financial advisor coordinating a team of specialists. Based on the user's message and profile, route to the most appropriate specialist:

- **investment**: Stock analysis, portfolio review, asset allocation, ETF/mutual fund recommendations, buy/sell decisions, stock news, sentiment
- **budgeting**: Expense tracking, budget creation, savings strategies, debt management, emergency funds, spending analysis
- **market**: Market conditions, sector performance, market summaries, economic trends, stock research, financial news, market sentiment
- **planning**: Retirement planning, goal-based planning (education, home, etc.), SIP calculations, long-term projections, insurance

If the user's query spans multiple areas, pick the MOST relevant specialist for the primary question.
If it's a general greeting or unclear question, route to **planning** as the default.

Respond with ONLY the specialist name: investment, budgeting, market, or planning."""

supervisor_llm = ChatOpenAI(
    model=SUPERVISOR_MODEL,
    api_key=OPENAI_API_KEY,
    max_tokens=50,
)


# ──────────────────────────────────────────────
# Node: Input Guardrails
# ──────────────────────────────────────────────
def input_guardrails_node(state: AdvisorState) -> dict:
    """Check user input for prohibited topics and compliance violations."""
    user_msg = state["messages"][-1].content
    is_safe, block_reason = check_input_guardrails(user_msg)

    if not is_safe:
        return {
            "guardrail_blocked": True,
            "guardrail_message": block_reason,
        }

    return {
        "guardrail_blocked": False,
        "guardrail_message": "",
    }


# ──────────────────────────────────────────────
# Node: RAG Retrieval
# ──────────────────────────────────────────────
def rag_retrieval_node(state: AdvisorState) -> dict:
    """Retrieve relevant financial knowledge to provide context for the specialist."""
    user_msg = state["messages"][-1].content
    rag_result = retrieve_financial_knowledge.invoke({"query": user_msg})
    return {"rag_context": rag_result}


# ──────────────────────────────────────────────
# Node: Supervisor (Router)
# ──────────────────────────────────────────────
def supervisor_node(state: AdvisorState) -> dict:
    messages = state["messages"]
    profile = state.get("user_profile", "No profile provided")

    routing_messages = [
        SystemMessage(content=SUPERVISOR_PROMPT),
        HumanMessage(
            content=f"User Profile:\n{profile}\n\nUser Message: {messages[-1].content}"
        ),
    ]

    response = supervisor_llm.invoke(routing_messages)
    route = response.content.strip().lower()

    for member in MEMBERS:
        if member in route:
            return {"current_agent": member}

    return {"current_agent": "planning"}


# ──────────────────────────────────────────────
# Specialist Runner (with RAG context injection)
# ──────────────────────────────────────────────
def _run_specialist(agent, state: AdvisorState) -> dict:
    """Run a specialist agent with RAG context and collect tool outputs."""
    profile = state.get("user_profile", "No profile provided")
    user_msg = state["messages"][-1].content
    rag_context = state.get("rag_context", "")

    # Build enriched message with RAG context
    enriched_msg = f"[User Profile]\n{profile}\n\n"

    if rag_context and "No directly relevant" not in rag_context:
        enriched_msg += (
            f"[Retrieved Knowledge Base Context — use this to ground your response]\n"
            f"{rag_context}\n\n"
        )

    enriched_msg += f"[User Question]\n{user_msg}"

    input_messages = [HumanMessage(content=enriched_msg)]
    result = agent.invoke({"messages": input_messages})

    # Collect tool outputs for factual grounding validation
    tool_outputs = []
    for msg in result["messages"]:
        if hasattr(msg, "type") and msg.type == "tool":
            tool_outputs.append(msg.content)

    final_message = result["messages"][-1]
    return {
        "messages": [AIMessage(content=final_message.content)],
        "tool_outputs": tool_outputs,
    }


def investment_node(state: AdvisorState) -> dict:
    return _run_specialist(investment_agent, state)


def budgeting_node(state: AdvisorState) -> dict:
    return _run_specialist(budgeting_agent, state)


def market_node(state: AdvisorState) -> dict:
    return _run_specialist(market_agent, state)


def planning_node(state: AdvisorState) -> dict:
    return _run_specialist(planning_agent, state)


# ──────────────────────────────────────────────
# Node: Output Guardrails
# ──────────────────────────────────────────────
def output_guardrails_node(state: AdvisorState) -> dict:
    """Apply output guardrails: compliance checks, hallucination filtering, source attribution."""
    messages = state["messages"]
    last_msg = messages[-1]

    if not hasattr(last_msg, "content") or not last_msg.content:
        return {}

    response = last_msg.content
    tool_outputs = state.get("tool_outputs", [])

    # Step 1: Compliance and hallucination filtering
    cleaned = check_output_guardrails(response)

    # Step 2: Add factual grounding / source attribution
    grounded = validate_factual_grounding(cleaned, tool_outputs)

    return {"messages": [AIMessage(content=grounded)]}


# ──────────────────────────────────────────────
# Routing Functions
# ──────────────────────────────────────────────
def check_guardrail_block(state: AdvisorState) -> Literal["blocked", "proceed"]:
    if state.get("guardrail_blocked", False):
        return "blocked"
    return "proceed"


def blocked_response_node(state: AdvisorState) -> dict:
    """Return the guardrail block message."""
    return {
        "messages": [AIMessage(content=state["guardrail_message"])],
    }


def route_decision(state: AdvisorState) -> Literal["investment", "budgeting", "market", "planning"]:
    return state["current_agent"]


# ──────────────────────────────────────────────
# Build the LangGraph
# ──────────────────────────────────────────────
graph = StateGraph(AdvisorState)

# Add all nodes
graph.add_node("input_guardrails", input_guardrails_node)
graph.add_node("blocked_response", blocked_response_node)
graph.add_node("rag_retrieval", rag_retrieval_node)
graph.add_node("supervisor", supervisor_node)
graph.add_node("investment", investment_node)
graph.add_node("budgeting", budgeting_node)
graph.add_node("market", market_node)
graph.add_node("planning", planning_node)
graph.add_node("output_guardrails", output_guardrails_node)

# Entry: Start -> Input Guardrails
graph.add_edge(START, "input_guardrails")

# After input guardrails: check if blocked
graph.add_conditional_edges(
    "input_guardrails",
    check_guardrail_block,
    {
        "blocked": "blocked_response",
        "proceed": "rag_retrieval",
    },
)

# Blocked -> END
graph.add_edge("blocked_response", END)

# RAG retrieval -> Supervisor
graph.add_edge("rag_retrieval", "supervisor")

# Supervisor -> Specialist routing
graph.add_conditional_edges(
    "supervisor",
    route_decision,
    {
        "investment": "investment",
        "budgeting": "budgeting",
        "market": "market",
        "planning": "planning",
    },
)

# All specialists -> Output Guardrails -> END
graph.add_edge("investment", "output_guardrails")
graph.add_edge("budgeting", "output_guardrails")
graph.add_edge("market", "output_guardrails")
graph.add_edge("planning", "output_guardrails")
graph.add_edge("output_guardrails", END)

from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
compiled_graph = graph.compile(checkpointer=memory)
