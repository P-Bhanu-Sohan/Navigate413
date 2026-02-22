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
    risk_agent,
    simulation_agent
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
        print("🔀 [GRAPH] Executing ROUTER agent")
        result = asyncio.run(router_agent(state))
        print(f"🔀 [GRAPH] Router classified domain: {result.get('domain', 'unknown')}")
        return result
    
    def sync_finance(state):
        print("💰 [GRAPH] Executing FINANCE agent")
        return asyncio.run(finance_agent(state))
    
    def sync_housing(state):
        print("🏠 [GRAPH] Executing HOUSING agent")
        return asyncio.run(housing_agent(state))
    
    def sync_visa(state):
        print("✈️ [GRAPH] Executing VISA agent")
        return asyncio.run(visa_agent(state))
    
    def sync_rag(state):
        print("🔍 [GRAPH] Executing RAG agent")
        result = asyncio.run(rag_agent(state))
        print(f"🔍 [GRAPH] RAG agent retrieved {len(result.get('rag_context', []))} clauses")
        return result
    
    def sync_risk(state):
        print("⚠️ [GRAPH] Executing RISK agent")
        return asyncio.run(risk_agent(state))
    
    def sync_simulation(state):
        print("🎲 [GRAPH] Executing SIMULATION agent")
        result = asyncio.run(simulation_agent(state))
        print(f"🎲 [GRAPH] Extracted {len(result.get('simulation_options', []))} simulations")
        return result
    
    # Add nodes
    graph.add_node("router", sync_router)
    graph.add_node("finance", sync_finance)
    graph.add_node("housing", sync_housing)
    graph.add_node("visa", sync_visa)
    graph.add_node("rag", sync_rag)
    graph.add_node("risk", sync_risk)
    graph.add_node("simulation", sync_simulation)
    
    # Router determines which specialized agent to call
    def route_to_domain(state):
        domain = state.get("domain", "general")
        print(f"🔀 [GRAPH] Routing to domain: {domain}")
        if domain == "finance":
            return "finance"
        elif domain == "housing":
            return "housing"
        elif domain == "visa":
            return "visa"
        else:
            return "rag"  # Default to RAG if no specific domain
    
    # Define edges
    graph.set_entry_point("router")  # Set router as entry point instead of START edge
    graph.add_conditional_edges("router", route_to_domain)
    graph.add_edge("finance", "rag")
    graph.add_edge("housing", "rag")
    graph.add_edge("visa", "rag")
    graph.add_edge("rag", "risk")
    graph.add_edge("risk", "simulation")
    graph.add_edge("simulation", END)
    
    return graph.compile()


async def run_analysis_workflow(session_id: str, raw_text: str):
    """
    Execute the full analysis workflow.
    
    Returns the final state with all agent outputs.
    """
    try:
        print(f"\n{'='*60}")
        print(f"🚀 [WORKFLOW] Starting analysis for session: {session_id}")
        print(f"{'='*60}\n")
        
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
            rag_context=[],  # Retrieved clauses from campus_embeddings collection
            translation=None,
            scenario=None,
            simulation_options=[],  # Dynamic simulations extracted from document
            error=None
        )
        
        # Run the workflow
        final_state = await asyncio.to_thread(graph.invoke, initial_state)
        
        print(f"\n{'='*60}")
        print(f"✅ [WORKFLOW] Analysis complete for session: {session_id}")
        print(f"{'='*60}\n")
        logger.info(f"Analysis complete for session {session_id}")
        return final_state
        
    except Exception as e:
        logger.error(f"Workflow execution error: {e}")
        return {
            "error": str(e),
            "session_id": session_id
        }
