"""
LangGraph workflow definition for the shopping agent.
Builds and compiles the state graph that orchestrates agent behavior.
"""
from typing import Literal
from langgraph.graph import StateGraph, END
import structlog

from agent_state import AgentState, should_stop, is_complete
from agent_nodes import observer_node, reasoning_node, action_node

logger = structlog.get_logger()


def create_agent_graph() -> StateGraph:
    """
    Build the agent workflow graph
    
    The graph follows this flow:
    1. START -> observer (capture page state)
    2. observer -> reasoning (analyze and decide)
    3. reasoning -> action (execute decision)
    4. action -> observer (loop) OR END (complete/error)
    
    Returns:
        Compiled StateGraph ready for execution
    """
    logger.info("Building agent graph")
    
    # Initialize graph with AgentState
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("observer", observer_node)
    workflow.add_node("reasoning", reasoning_node)
    workflow.add_node("action", action_node)
    
    # Set entry point
    workflow.set_entry_point("observer")
    
    # Add edges
    workflow.add_edge("observer", "reasoning")
    workflow.add_edge("reasoning", "action")
    
    # Add conditional edge from action
    workflow.add_conditional_edges(
        "action",
        route_after_action,
        {
            "continue": "observer",  # Loop back for next iteration
            "end": END               # Stop execution
        }
    )
    
    # Compile graph
    graph = workflow.compile()
    
    logger.info("Agent graph compiled successfully")
    
    return graph


def route_after_action(state: AgentState) -> Literal["continue", "end"]:
    """
    Determine whether to continue or end after an action
    
    Args:
        state: Current agent state
    
    Returns:
        "continue" to loop back to observer, "end" to stop
    """
    # Check if should stop
    if should_stop(state):
        reason = "unknown"
        
        if is_complete(state):
            reason = "mission complete"
        elif state["status"] == "error":
            reason = f"error: {state.get('error')}"
        elif state["iterations"] >= state["max_iterations"]:
            reason = "max iterations reached"
        elif state["approval_required"]:
            reason = "waiting for approval"
        
        logger.info("Ending agent execution", reason=reason)
        return "end"
    
    # Continue to next iteration
    logger.debug("Continuing to next iteration", 
                iteration=state["iterations"])
    return "continue"


def visualize_graph(graph: StateGraph) -> str:
    """
    Generate a visual representation of the graph (for debugging)
    
    Args:
        graph: Compiled state graph
    
    Returns:
        ASCII representation of graph structure
    """
    return """
    Agent Workflow Graph:
    
    START
      ↓
    [observer] ← ─ ─ ─ ─ ─ ─ ┐
      ↓                      │
    [reasoning]              │
      ↓                      │
    [action] ─ ─ ─ ─ ─ ─ ─ ─ ┘
      ↓
    END (when complete/error/max iterations)
    
    Nodes:
    - observer: Captures page state, injects markers, takes screenshot
    - reasoning: Analyzes screenshot with Gemini, decides next action
    - action: Executes the decided action (click/type/scroll)
    
    Flow:
    - Loops continuously until mission complete or stopping condition
    - Each iteration: observe → reason → act
    """

