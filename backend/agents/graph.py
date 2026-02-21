import logging
import asyncio
from langgraph.graph import StateGraph, END
from agents.base_agents import (
    AgentState,
    router_agent,
    finance_agent,
    housing_agent,
    visa_agent,
    rag_agent,
    risk_agent
)

logger = logging.getLogger(__name__)


def build_graph():
    """
    Build the LangGraph workflow for document analysis.
    
    Flow:
    Router → (Finance/Housing/Visa based on domain) → RAG → Risk → Output
    """
    graph = StateGraph(AgentState)
    
    # Convert async agents to sync wrappers for LangGraph
    def sync_router(state):
        return asyncio.run(router_agent(state))
    
    def sync_finance(state):
        return asyncio.run(finance_agent(state))
    
    def sync_housing(state):
        return asyncio.run(housing_agent(state))
    
    def sync_visa(state):
        return asyncio.run(visa_agent(state))
    
    def sync_rag(state):
        return asyncio.run(rag_agent(state))
    
    def sync_risk(state):
        return asyncio.run(risk_agent(state))
    
    # Add nodes
    graph.add_node("router", sync_router)
    graph.add_node("finance", sync_finance)
    graph.add_node("housing", sync_housing)
    graph.add_node("visa", sync_visa)
    graph.add_node("rag", sync_rag)
    graph.add_node("risk", sync_risk)
    
    # Router determines which specialized agent to call
    def route_to_domain(state):
        domain = state.get("domain", "general")
        if domain == "finance":
            return "finance"
        elif domain == "housing":
            return "housing"
        elif domain == "visa":
            return "visa"
        else:
            return "rag"  # Default to RAG if no specific domain
    
    # Define edges
    graph.add_edge("START", "router")
    graph.add_conditional_edges("router", route_to_domain)
    graph.add_edge("finance", "rag")
    graph.add_edge("housing", "rag")
    graph.add_edge("visa", "rag")
    graph.add_edge("rag", "risk")
    graph.add_edge("risk", END)
    
    return graph.compile()


async def run_analysis_workflow(session_id: str, raw_text: str):
    """
    Execute the full analysis workflow.
    
    Returns the final state with all agent outputs.
    """
    try:
        graph = build_graph()
        
        # Initialize state
        initial_state = AgentState(
            session_id=session_id,
            raw_text=raw_text,
            domain="",
            language="en",
            clauses=[],
            obligations=[],
            financial_details=None,
            housing_details=None,
            visa_details=None,
            risk_assessment=None,
            red_flags=[],
            resources=[],
            translation=None,
            scenario=None,
            error=None
        )
        
        # Run the workflow
        final_state = await asyncio.to_thread(graph.invoke, initial_state)
        
        logger.info(f"Analysis complete for session {session_id}")
        return final_state
        
    except Exception as e:
        logger.error(f"Workflow execution error: {e}")
        return {
            "error": str(e),
            "session_id": session_id
        }
