"""
FastAPI application entry point for SmartCart AI E-Commerce Agent.
Provides REST API and WebSocket endpoints for agent control.
"""
import asyncio
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
import structlog

from config import Config
from browser_controller import BrowserController
from vision_utils import inject_markers, remove_markers, format_markers_for_prompt
from ai_vision import get_vision_analyzer
from agent_service import get_agent_executor

# Fix for Python 3.13 on Windows - Playwright subprocess issue
if sys.platform == 'win32':
    # Set event loop policy to WindowsProactorEventLoopPolicy for subprocess support
    if sys.version_info >= (3, 13):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    # For older versions, explicitly set the policy if needed
    elif not isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()


# Request/Response Models
class StartAgentRequest(BaseModel):
    """Request to start the agent on a URL"""
    url: str
    goal: Optional[str] = None


class AnalyzePageRequest(BaseModel):
    """Request to analyze a page"""
    url: str
    goal: str


class AgentResponse(BaseModel):
    """Standard agent response"""
    status: str
    message: str
    data: Dict[str, Any] = {}


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic"""
    # Startup
    logger.info("Starting SmartCart AI Agent API")
    try:
        Config.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error("Configuration validation failed", error=str(e))
    
    yield
    
    # Shutdown
    logger.info("Shutting down SmartCart AI Agent API")


# Initialize FastAPI app
app = FastAPI(
    title="SmartCart AI - E-Commerce Agent API",
    description="AI agent for autonomous e-commerce browsing and shopping",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "service": "SmartCart AI Agent",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        Config.validate()
        return {
            "status": "healthy",
            "gemini_configured": bool(Config.GOOGLE_API_KEY),
            "debug_mode": Config.DEBUG
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.post("/api/agent/start", response_model=AgentResponse)
async def start_agent(request: StartAgentRequest):
    """
    Start the agent and navigate to a URL
    
    Args:
        request: Contains URL and optional goal
    
    Returns:
        Response with screenshot and status
    """
    logger.info("Starting agent", url=request.url, goal=request.goal)
    
    try:
        # Initialize browser
        browser = BrowserController(headless=Config.HEADLESS)
        
        try:
            await browser.initialize()
            
            # Navigate to URL
            nav_result = await browser.navigate(request.url)
            
            if nav_result["status"] == "error":
                raise HTTPException(
                    status_code=400,
                    detail=f"Navigation failed: {nav_result.get('error')}"
                )
            
            # Take screenshot
            screenshot = await browser.take_screenshot()
            
            logger.info("Agent started successfully", 
                       url=nav_result["url"],
                       title=nav_result["title"])
            
            return AgentResponse(
                status="success",
                message="Agent started and navigated to URL",
                data={
                    "url": nav_result["url"],
                    "title": nav_result["title"],
                    "screenshot": screenshot,
                    "goal": request.goal
                }
            )
            
        finally:
            await browser.close()
            
    except Exception as e:
        logger.error("Failed to start agent", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start agent: {str(e)}"
        )


@app.post("/api/agent/navigate")
async def navigate_page(request: StartAgentRequest):
    """
    Navigate to a URL and return page info
    
    Args:
        request: Contains URL
    
    Returns:
        Page information and screenshot
    """
    logger.info("Navigating to page", url=request.url)
    
    try:
        async with BrowserController(headless=Config.HEADLESS) as browser:
            # Navigate
            nav_result = await browser.navigate(request.url)
            
            if nav_result["status"] == "error":
                raise HTTPException(
                    status_code=400,
                    detail=f"Navigation failed: {nav_result.get('error')}"
                )
            
            # Take screenshot
            screenshot = await browser.take_screenshot()
            
            return {
                "status": "success",
                "url": nav_result["url"],
                "title": nav_result["title"],
                "screenshot": screenshot
            }
            
    except Exception as e:
        logger.error("Navigation failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Navigation failed: {str(e)}"
        )


@app.post("/api/agent/analyze")
async def analyze_page(request: AnalyzePageRequest):
    """
    Analyze a page with vision AI to determine next action
    
    Args:
        request: Contains URL and goal
    
    Returns:
        Analysis result with suggested action, screenshot, and markers
    """
    logger.info("Analyzing page", url=request.url, goal=request.goal)
    
    try:
        async with BrowserController(headless=Config.HEADLESS) as browser:
            # Navigate to URL
            nav_result = await browser.navigate(request.url)
            
            if nav_result["status"] == "error":
                raise HTTPException(
                    status_code=400,
                    detail=f"Navigation failed: {nav_result.get('error')}"
                )
            
            # Inject markers
            markers_map = await inject_markers(browser.page)
            
            # Take screenshot with markers
            screenshot = await browser.take_screenshot()
            
            # Analyze with Gemini
            vision_analyzer = get_vision_analyzer()
            action = await vision_analyzer.analyze_page(
                screenshot_base64=screenshot,
                markers_map=markers_map,
                user_goal=request.goal,
                action_history=[]
            )
            
            # Remove markers
            await remove_markers(browser.page)
            
            logger.info("Page analysis complete",
                       action=action.get('action'),
                       target=action.get('target'))
            
            return {
                "status": "success",
                "url": nav_result["url"],
                "title": nav_result["title"],
                "action": action,
                "screenshot": screenshot,
                "markers": markers_map,
                "markers_formatted": format_markers_for_prompt(markers_map)
            }
            
    except Exception as e:
        logger.error("Page analysis failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@app.get("/api/config")
async def get_config():
    """Get public configuration information"""
    return {
        "headless": Config.HEADLESS,
        "debug": Config.DEBUG,
        "max_iterations": Config.MAX_ITERATIONS,
        "gemini_configured": bool(Config.GOOGLE_API_KEY)
    }


# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time agent updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, session_id: str, websocket: WebSocket):
        """Accept and store WebSocket connection"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info("WebSocket connected", session_id=session_id)
    
    def disconnect(self, session_id: str):
        """Remove WebSocket connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info("WebSocket disconnected", session_id=session_id)
    
    async def send_message(self, session_id: str, message: dict):
        """Send message to specific session"""
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(message)
            except Exception as e:
                logger.error("Failed to send message", 
                           session_id=session_id, 
                           error=str(e))
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for session_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error("Failed to broadcast", 
                           session_id=session_id, 
                           error=str(e))


manager = ConnectionManager()


@app.websocket("/ws/agent/{session_id}")
async def websocket_agent(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time agent communication
    
    Args:
        websocket: WebSocket connection
        session_id: Unique session identifier
    """
    # CRITICAL FIX: Ensure Windows event loop policy is set for this async context
    if sys.platform == 'win32':
        try:
            loop = asyncio.get_event_loop()
            if not isinstance(loop, asyncio.ProactorEventLoop):
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except Exception:
            pass
    
    await manager.connect(session_id, websocket)
    
    try:
        # Wait for start_mission message
        data = await websocket.receive_json()
        
        logger.info("Received WebSocket message", 
                   session_id=session_id,
                   type=data.get("type"))
        
        if data.get("type") == "start_mission":
            user_goal = data.get("goal", "")
            initial_url = data.get("url", "")
            
            if not user_goal or not initial_url:
                await manager.send_message(session_id, {
                    "type": "error",
                    "message": "Missing required fields: goal and url"
                })
                return
            
            # Get agent executor
            executor = get_agent_executor()
            
            # Create session
            executor.create_session(
                user_goal=user_goal,
                initial_url=initial_url,
                session_id=session_id
            )
            
            # Execute mission and stream updates
            async for update in executor.execute_mission(session_id):
                try:
                    await manager.send_message(session_id, update)
                except Exception as e:
                    logger.error("Failed to send update", 
                               session_id=session_id,
                               error=str(e))
                    break
        
        elif data.get("type") == "cancel":
            executor = get_agent_executor()
            executor.cancel_session(session_id)
            await manager.send_message(session_id, {
                "type": "cancelled",
                "message": "Mission cancelled"
            })
        
        elif data.get("type") == "ping":
            await manager.send_message(session_id, {
                "type": "pong",
                "timestamp": data.get("timestamp")
            })
        
        else:
            logger.warning("Unknown message type", 
                         type=data.get("type"),
                         session_id=session_id)
                
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info("Client disconnected", session_id=session_id)
    except Exception as e:
        logger.error("WebSocket error", 
                    session_id=session_id,
                    error=str(e))
        manager.disconnect(session_id)


if __name__ == "__main__":
    import uvicorn
    
    # CRITICAL: Set event loop policy BEFORE uvicorn creates its loop
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # CRITICAL: Disable reload on Windows - the reloader creates subprocesses that don't inherit event loop policy
    # This causes Playwright subprocess creation to fail with NotImplementedError
    use_reload = Config.DEBUG and sys.platform != 'win32'
    
    print(f"[STARTUP] Auto-reload: {'enabled' if use_reload else 'DISABLED (Windows + Playwright compatibility)'}")
    
    uvicorn.run(
        "app:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=use_reload,
        loop="asyncio"  # Use asyncio loop (which will use our policy)
    )

