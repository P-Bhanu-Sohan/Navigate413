import logging
from typing import Awaitable, Callable
from langgraph.graph import StateGraph, END
from pipelines.intent_router import classify_document_domain
from agents.base_agents import (
    AgentState,
    finance_agent,
    housing_agent,
    visa_agent,
    rag_agent
)
from agents.specialized_agents import translation_agent, scenario_agent

logger = logging.getLogger(__name__)


async def intent_router_node(state: AgentState) -> AgentState:
    """Classify document domain and route to appropriate agent."""
    try:
        text = state.get("raw_text", "")
        domain = await classify_document_domain(text)
        state["domain"] = domain
        logger.info(f"Classified document as: {domain}")
        return state
    except Exception as e:
        logger.error(f"Intent router error: {e}")
        state["domain"] = "unknown"
        state["error"] = str(e)
        return state


def build_graph():
    """Build the LangGraph workflow."""
    graph = StateGraph(AgentState)
    
    # Wrapper functions to handle async nodes in LangGraph
    def sync_intent_router(state):
        import asyncio
        return asyncio.run(intent_router_node(state))
    
    def sync_finance_agent(state):
        import asyncio
        return asyncio.run(finance_agent(state))
    
    def sync_housing_agent(state):
        import asyncio
        return asyncio.run(housing_agent(state))
    
    def sync_visa_agent(state):
        import asyncio
        return asyncio.run(visa_agent(state))
    
    def sync_rag_agent(state):
        import asyncio
        return asyncio.run(rag_agent(state))
    
    def sync_translation_agent(state):
        import asyncio
        return asyncio.run(translation_agent(state))
    
    def sync_scenario_agent(state):
        import asyncio
        return asyncio.run(scenario_agent(state))
    
    # Add nodes
    graph.add_node("intent_router", sync_intent_router)
    graph.add_node("finance_agent", sync_finance_agent)
    graph.add_node("housing_agent", sync_housing_agent)
    graph.add_node("visa_agent", sync_visa_agent)
    graph.add_node("rag_agent", sync_rag_agent)
    graph.add_node("translation_agent", sync_translation_agent)
    graph.add_node("scenario_agent", sync_scenario_agent)
    
    # Define routing logic
    def route_by_domain(state):
        domain = state.get("domain", "unknown")
        if domain == "finance":
            return "finance_agent"
        elif domain == "housing":
            return "housing_agent"
        elif domain == "visa":
            return "visa_agent"
        else:
            # For unknown, still process but mark as such
            return "rag_agent"
    
    # Set entry point
    graph.set_entry_point("intent_router")
    
    # Add edges
    graph.add_conditional_edges(
        "intent_router",
        route_by_domain,
        {
            "finance_agent": "finance_agent",
            "housing_agent": "housing_agent",
            "visa_agent": "visa_agent",
            "rag_agent": "rag_agent"
        }
    )
    
    # All domain agents lead to RAG agent
    graph.add_edge("finance_agent", "rag_agent")
    graph.add_edge("housing_agent", "rag_agent")
    graph.add_edge("visa_agent", "rag_agent")
    
    # RAG agent leads to conditional translation/scenario
    def needs_translation(state):
        language = state.get("language", "en")
        return language != "en"
    
    def needs_scenario(state):
        return state.get("scenario") is not None
    
    # After RAG, check if translation needed
    def route_after_rag(state):
        if needs_translation(state):
            return "translation_agent"
        elif needs_scenario(state):
            return "scenario_agent"
        else:
            return END
    
    graph.add_conditional_edges(
        "rag_agent",
        route_after_rag,
        {
            "translation_agent": "translation_agent",
            "scenario_agent": "scenario_agent",
            END: END
        }
    )
    
    # Translation can lead to scenario
    def route_after_translation(state):
        if needs_scenario(state):
            return "scenario_agent"
        else:
            return END
    
    graph.add_conditional_edges(
        "translation_agent",
        route_after_translation,
        {
            "scenario_agent": "scenario_agent",
            END: END
        }
    )
    
    # Scenario leads to end
    graph.add_edge("scenario_agent", END)
    
    return graph.compile()


# Build the compiled graph
workflow = build_graph()
