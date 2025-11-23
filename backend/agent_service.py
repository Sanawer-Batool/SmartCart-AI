"""
Agent Execution Service.
Manages agent lifecycle, session state, and execution control.
"""
import asyncio
import sys
import uuid
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime, timedelta
import structlog

# CRITICAL FIX: Set event loop policy for Windows before ANY async operations
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from config import Config
from browser_controller import BrowserController
from agent_state import AgentState, create_initial_state, format_state_summary
from agent_graph import create_agent_graph
from agent_nodes import set_browser

logger = structlog.get_logger()


class AgentSession:
    """Represents an active agent session"""
    
    def __init__(self, session_id: str, user_goal: str, initial_url: str):
        self.session_id = session_id
        self.user_goal = user_goal
        self.initial_url = initial_url
        self.created_at = datetime.now()
        self.browser: Optional[BrowserController] = None
        self.state: Optional[AgentState] = None
        self.is_running = False
        self.is_cancelled = False
    
    def __repr__(self) -> str:
        return f"AgentSession(id={self.session_id}, goal={self.user_goal[:30]}...)"


class AgentExecutor:
    """
    Executes agent missions and manages sessions
    """
    
    def __init__(self):
        self.sessions: Dict[str, AgentSession] = {}
        self.graph = create_agent_graph()
        logger.info("AgentExecutor initialized")
    
    def create_session(
        self,
        user_goal: str,
        initial_url: str,
        session_id: Optional[str] = None
    ) -> AgentSession:
        """
        Create a new agent session
        
        Args:
            user_goal: User's stated goal
            initial_url: Starting URL
            session_id: Optional custom session ID
        
        Returns:
            Created AgentSession
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        session = AgentSession(session_id, user_goal, initial_url)
        self.sessions[session_id] = session
        
        logger.info("Session created", 
                   session_id=session_id,
                   goal=user_goal)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[AgentSession]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def cancel_session(self, session_id: str) -> bool:
        """
        Cancel a running session
        
        Args:
            session_id: Session to cancel
        
        Returns:
            True if cancelled, False if not found or not running
        """
        session = self.get_session(session_id)
        if not session:
            logger.warning("Session not found for cancellation", session_id=session_id)
            return False
        
        if not session.is_running:
            logger.warning("Session not running", session_id=session_id)
            return False
        
        session.is_cancelled = True
        logger.info("Session cancelled", session_id=session_id)
        
        return True
    
    async def execute_mission(
        self,
        session_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute agent mission and stream updates
        
        Args:
            session_id: Session ID to execute
        
        Yields:
            State updates as dictionaries
        """
        session = self.get_session(session_id)
        if not session:
            yield {
                "type": "error",
                "message": f"Session not found: {session_id}"
            }
            return
        
        try:
            session.is_running = True
            
            # Send start event
            yield {
                "type": "started",
                "session_id": session_id,
                "goal": session.user_goal,
                "url": session.initial_url
            }
            
            # Initialize browser
            logger.info("Initializing browser", session_id=session_id)
            session.browser = BrowserController(headless=Config.HEADLESS)
            await session.browser.initialize()
            
            # Set global browser for nodes
            set_browser(session.browser)
            
            # Navigate to initial URL
            if session.initial_url:
                logger.info("Navigating to initial URL", url=session.initial_url)
                nav_result = await session.browser.navigate(session.initial_url)
                
                if nav_result["status"] == "error":
                    yield {
                        "type": "error",
                        "message": f"Navigation failed: {nav_result.get('error')}"
                    }
                    return
                
                yield {
                    "type": "navigation",
                    "url": nav_result["url"],
                    "title": nav_result["title"]
                }
            
            # Create initial state
            session.state = create_initial_state(
                user_goal=session.user_goal,
                session_id=session_id,
                initial_url=session.initial_url,
                max_iterations=Config.MAX_ITERATIONS
            )
            
            # Execute graph
            logger.info("Starting agent execution", session_id=session_id)
            
            async for update in self._run_graph(session):
                # Check if cancelled
                if session.is_cancelled:
                    yield {
                        "type": "cancelled",
                        "message": "Mission cancelled by user"
                    }
                    break
                
                yield update
            
            # Send completion event
            if not session.is_cancelled:
                yield {
                    "type": "complete",
                    "message": "Mission complete",
                    "state_summary": format_state_summary(session.state) if session.state else ""
                }
            
        except Exception as e:
            logger.error("Mission execution failed", 
                        session_id=session_id,
                        error=str(e))
            
            yield {
                "type": "error",
                "message": f"Execution failed: {str(e)}"
            }
        
        finally:
            # Cleanup
            session.is_running = False
            
            if session.browser:
                await session.browser.close()
                session.browser = None
            
            logger.info("Mission execution ended", session_id=session_id)
    
    async def _run_graph(self, session: AgentSession) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Run the agent graph and stream state updates
        
        Args:
            session: Agent session
        
        Yields:
            State update dictionaries
        """
        try:
            # Execute graph step by step
            state = session.state
            
            # Run graph with streaming
            async for event in self.graph.astream(state):
                # Extract state from event
                # LangGraph returns dict with node name as key
                if isinstance(event, dict):
                    # Get the latest state from any node
                    for node_name, node_state in event.items():
                        if isinstance(node_state, dict):
                            # Update session state
                            session.state.update(node_state)
                            
                            # Yield update
                            yield {
                                "type": "state_update",
                                "node": node_name,
                                "status": node_state.get("status"),
                                "iteration": node_state.get("iterations"),
                                "last_action": node_state.get("last_action"),
                                "screenshot": node_state.get("screenshot_base64", ""),
                                "url": node_state.get("current_url", ""),
                                "messages": [
                                    msg.content for msg in node_state.get("messages", [])[-3:]
                                ]
                            }
                            
                            # Small delay to avoid overwhelming clients
                            await asyncio.sleep(0.1)
                
                # Check for cancellation
                if session.is_cancelled:
                    break
        
        except Exception as e:
            logger.error("Graph execution error", 
                        session_id=session.session_id,
                        error=str(e))
            
            yield {
                "type": "error",
                "message": f"Graph execution failed: {str(e)}"
            }
    
    async def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """
        Remove old inactive sessions
        
        Args:
            max_age_hours: Maximum age in hours
        
        Returns:
            Number of sessions cleaned up
        """
        now = datetime.now()
        cutoff = now - timedelta(hours=max_age_hours)
        
        to_remove = []
        for session_id, session in self.sessions.items():
            if not session.is_running and session.created_at < cutoff:
                to_remove.append(session_id)
        
        for session_id in to_remove:
            del self.sessions[session_id]
        
        if to_remove:
            logger.info("Cleaned up old sessions", count=len(to_remove))
        
        return len(to_remove)
    
    def get_active_sessions_count(self) -> int:
        """Get count of currently running sessions"""
        return sum(1 for s in self.sessions.values() if s.is_running)
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a session"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        return {
            "session_id": session.session_id,
            "user_goal": session.user_goal,
            "initial_url": session.initial_url,
            "is_running": session.is_running,
            "is_cancelled": session.is_cancelled,
            "created_at": session.created_at.isoformat(),
            "state_summary": format_state_summary(session.state) if session.state else None
        }


# Global executor instance
_executor: Optional[AgentExecutor] = None


def get_agent_executor() -> AgentExecutor:
    """Get or create the global agent executor"""
    global _executor
    
    if _executor is None:
        _executor = AgentExecutor()
    
    return _executor

