"""
Agent State definition for LangGraph.
Defines the state structure that flows through the agent workflow.
"""
from typing import List, Dict, Any, Literal, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import structlog

logger = structlog.get_logger()


class AgentState(TypedDict):
    """
    State structure for the shopping agent workflow
    
    This state flows through all nodes in the LangGraph workflow.
    """
    # Message history
    messages: List[BaseMessage]
    
    # Browser state
    current_url: str
    screenshot_base64: str
    markers_map: Dict[int, Dict[str, Any]]
    
    # Action tracking
    last_action: Optional[Dict[str, Any]]
    action_history: List[Dict[str, Any]]
    
    # Mission context
    user_goal: str
    session_id: str
    
    # Execution status
    status: Literal["planning", "observing", "reasoning", "executing", "waiting", "complete", "error"]
    iterations: int
    max_iterations: int
    
    # Error handling
    error: Optional[str]
    
    # Safety
    approval_required: bool
    approval_granted: bool


def create_initial_state(
    user_goal: str,
    session_id: str,
    initial_url: str = "",
    max_iterations: int = 20
) -> AgentState:
    """
    Create initial agent state
    
    Args:
        user_goal: User's stated goal/objective
        session_id: Unique session identifier
        initial_url: Starting URL (optional)
        max_iterations: Maximum iterations before stopping
    
    Returns:
        Initial AgentState dictionary
    """
    return AgentState(
        messages=[
            HumanMessage(content=f"Goal: {user_goal}")
        ],
        current_url=initial_url,
        screenshot_base64="",
        markers_map={},
        last_action=None,
        action_history=[],
        user_goal=user_goal,
        session_id=session_id,
        status="planning",
        iterations=0,
        max_iterations=max_iterations,
        error=None,
        approval_required=False,
        approval_granted=False
    )


def add_message(state: AgentState, message: BaseMessage) -> AgentState:
    """
    Add a message to the state
    
    Args:
        state: Current agent state
        message: Message to add
    
    Returns:
        Updated state
    """
    state["messages"].append(message)
    return state


def add_action(state: AgentState, action: Dict[str, Any]) -> AgentState:
    """
    Add an action to the history
    
    Args:
        state: Current agent state
        action: Action dictionary to add
    
    Returns:
        Updated state
    """
    state["last_action"] = action
    state["action_history"].append(action)
    return state


def is_complete(state: AgentState) -> bool:
    """
    Check if the mission is complete
    
    Args:
        state: Current agent state
    
    Returns:
        True if complete, False otherwise
    """
    # Mission is complete if:
    # 1. Status is explicitly set to complete
    if state["status"] == "complete":
        return True
    
    # 2. Last action was "done"
    if state["last_action"] and state["last_action"].get("action") == "done":
        return True
    
    return False


def should_stop(state: AgentState) -> bool:
    """
    Check if agent should stop execution
    
    Args:
        state: Current agent state
    
    Returns:
        True if should stop, False otherwise
    """
    # Stop if complete
    if is_complete(state):
        return True
    
    # Stop if max iterations reached
    if state["iterations"] >= state["max_iterations"]:
        logger.warning("Max iterations reached", 
                      iterations=state["iterations"],
                      max_iterations=state["max_iterations"])
        return True
    
    # Stop if error occurred
    if state["status"] == "error":
        logger.error("Error status detected", error=state.get("error"))
        return True
    
    # Stop if waiting for approval
    if state["approval_required"] and not state["approval_granted"]:
        logger.info("Waiting for user approval")
        return True
    
    return False


def increment_iteration(state: AgentState) -> AgentState:
    """
    Increment iteration counter
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state
    """
    state["iterations"] += 1
    logger.debug("Iteration incremented", 
                iteration=state["iterations"],
                max_iterations=state["max_iterations"])
    return state


def set_status(state: AgentState, status: str) -> AgentState:
    """
    Update agent status
    
    Args:
        state: Current agent state
        status: New status
    
    Returns:
        Updated state
    """
    old_status = state["status"]
    state["status"] = status
    
    logger.info("Status changed", 
               from_status=old_status,
               to_status=status,
               iteration=state["iterations"])
    
    return state


def set_error(state: AgentState, error: str) -> AgentState:
    """
    Set error state
    
    Args:
        state: Current agent state
        error: Error message
    
    Returns:
        Updated state
    """
    state["error"] = error
    state["status"] = "error"
    
    logger.error("Error set in state", error=error)
    
    return state


def get_recent_actions(state: AgentState, count: int = 3) -> List[Dict[str, Any]]:
    """
    Get the most recent actions
    
    Args:
        state: Current agent state
        count: Number of recent actions to return
    
    Returns:
        List of recent action dictionaries
    """
    return state["action_history"][-count:] if state["action_history"] else []


def format_state_summary(state: AgentState) -> str:
    """
    Format a human-readable summary of the current state
    
    Args:
        state: Current agent state
    
    Returns:
        Formatted summary string
    """
    summary_lines = [
        f"Session: {state['session_id']}",
        f"Goal: {state['user_goal']}",
        f"Status: {state['status']}",
        f"Iteration: {state['iterations']}/{state['max_iterations']}",
        f"Current URL: {state['current_url']}",
        f"Actions taken: {len(state['action_history'])}",
    ]
    
    if state["last_action"]:
        action = state["last_action"]
        summary_lines.append(
            f"Last action: {action.get('action')} on [{action.get('target')}]"
        )
    
    if state["error"]:
        summary_lines.append(f"Error: {state['error']}")
    
    return "\n".join(summary_lines)

