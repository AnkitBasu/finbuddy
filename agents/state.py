from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages


class AdvisorState(TypedDict):
    messages: Annotated[list, add_messages]
    user_profile: str
    current_agent: str
    rag_context: str
    tool_outputs: list[str]
    guardrail_blocked: bool
    guardrail_message: str
