import uuid
import streamlit as st
from langchain_core.messages import HumanMessage
from agents.supervisor import compiled_graph


def render_chat():
    # Consent check
    if not st.session_state.get("user_consent"):
        st.info(
            "Please accept the terms in the sidebar before using the advisor."
        )
        return

    # Initialize a unique thread ID per session for stateful memory
    if "thread_id" not in st.session_state:
        st.session_state["thread_id"] = str(uuid.uuid4())

    # Display existing messages
    for msg in st.session_state.get("messages", []):
        role = msg["role"]
        with st.chat_message(role):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask me about investments, budgeting, or financial planning..."):
        # Add user message
        st.session_state["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get user profile summary
        profile = st.session_state.get("user_profile")
        profile_summary = profile.summary() if profile else "No profile set. Using defaults."

        # Thread config for stateful memory — the checkpointer tracks
        # conversation history automatically using this thread ID
        thread_config = {"configurable": {"thread_id": st.session_state["thread_id"]}}

        # Run the agent graph
        with st.chat_message("assistant"):
            with st.spinner("Analyzing your request..."):
                try:
                    result = compiled_graph.invoke(
                        {
                            "messages": [HumanMessage(content=prompt)],
                            "user_profile": profile_summary,
                            "current_agent": "",
                            "rag_context": "",
                            "tool_outputs": [],
                            "guardrail_blocked": False,
                            "guardrail_message": "",
                        },
                        config=thread_config,
                    )

                    # Extract the final AI response
                    response = result["messages"][-1].content
                    agent_used = result.get("current_agent", "unknown")
                    was_blocked = result.get("guardrail_blocked", False)

                    # Display agent badge
                    if was_blocked:
                        st.caption("*Handled by: Compliance Filter*")
                    else:
                        agent_labels = {
                            "investment": "📈 Investment Analyst",
                            "budgeting": "💰 Budget Advisor",
                            "market": "📊 Market Analyst",
                            "planning": "🎯 Financial Planner",
                        }
                        label = agent_labels.get(agent_used, "🤖 Advisor")
                        st.caption(f"*Handled by: {label} | RAG-enhanced | Guardrails applied*")

                    st.markdown(response)

                except Exception as e:
                    response = f"I encountered an error processing your request: {str(e)}. Please check your API key and try again."
                    st.error(response)

        # Save assistant response
        st.session_state["messages"].append({"role": "assistant", "content": response})
