# 🏗️ SmartCart AI - Architecture Documentation

## System Overview

SmartCart AI is a multi-tier agentic system that combines web automation, computer vision, and AI reasoning to autonomously browse e-commerce websites.

---

## 📊 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER BROWSER                          │
│                     (localhost:3000)                         │
└────────────────────────────┬────────────────────────────────┘
                             │ WebSocket
                             │ (Real-time bidirectional)
┌────────────────────────────▼────────────────────────────────┐
│                     FASTAPI BACKEND                          │
│                     (localhost:8000)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           WebSocket Connection Manager                │  │
│  └───────────────────┬──────────────────────────────────┘  │
│                      │                                       │
│  ┌───────────────────▼──────────────────────────────────┐  │
│  │              Agent Executor                           │  │
│  │  ┌─────────────────────────────────────────────────┐ │  │
│  │  │         LangGraph State Machine              │ │  │
│  │  │                                                  │ │  │
│  │  │  ┌──────────┐   ┌──────────┐   ┌──────────┐  │ │  │
│  │  │  │ Observer │──▶│ Reasoning│──▶│  Action  │  │ │  │
│  │  │  └──────────┘   └──────────┘   └──────────┘  │ │  │
│  │  │       │              │              │         │ │  │
│  │  │       ▼              ▼              ▼         │ │  │
│  │  │  [Browser]      [Gemini]      [Browser]      │ │  │
│  │  └─────────────────────────────────────────────┘ │  │
│  └─────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
                      │              │
                      │              │
        ┌─────────────▼──────────┐   │
        │   Playwright Browser    │   │
        │    (Chromium)          │   │
        │  - Navigation          │   │
        │  - Screenshots         │   │
        │  - Click/Type/Scroll   │   │
        └────────────────────────┘   │
                                     │
                    ┌────────────────▼──────────────┐
                    │   Google Gemini 2.0 Flash     │
                    │   - Vision Analysis           │
                    │   - Decision Making           │
                    │   - JSON Output               │
                    └───────────────────────────────┘
```

---

## 🔄 Data Flow

### 1. Mission Start
```
User (Frontend)
  │
  ├─ Enters URL + Goal
  │
  ▼
WebSocket Message
  │
  ├─ type: "start_mission"
  ├─ url: "https://amazon.com"
  ├─ goal: "Find headphones"
  │
  ▼
Agent Executor
  │
  ├─ Create session
  ├─ Initialize browser
  ├─ Create initial state
  │
  ▼
LangGraph Workflow
```

### 2. Agentic Loop
```
┌──────────────────────────────────────────┐
│         OBSERVER NODE                     │
│  1. Take screenshot                       │
│  2. Inject numbered markers               │
│  3. Update state                          │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│         REASONING NODE                    │
│  1. Send screenshot to Gemini             │
│  2. Include markers + goal + history      │
│  3. Get decision (JSON)                   │
│  4. Validate action                       │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│         ACTION NODE                       │
│  1. Safety check (if click)              │
│  2. Execute action                        │
│     - Click element                       │
│     - Type text                           │
│     - Scroll page                         │
│  3. Update history                        │
│  4. Increment iteration                   │
└──────────────┬───────────────────────────┘
               │
               ▼
       ┌───────────────┐
       │  Complete?    │
       │  Error?       │
       │  Max iters?   │
       └───┬───────┬───┘
           │       │
      Yes  │       │ No
           ▼       │
         END       │
                   │
                   └──▶ Back to OBSERVER
```

### 3. State Updates
```
Each Node Completion
  │
  ├─ Update AgentState
  │  - status
  │  - screenshot
  │  - last_action
  │  - messages
  │  - iteration
  │
  ▼
Stream to Frontend
  │
  ├─ WebSocket message
  │  - type: "state_update"
  │  - node: "observer"
  │  - screenshot: base64
  │  - messages: [...]
  │
  ▼
Frontend Updates UI
  │
  ├─ Add messages to chat
  ├─ Update screenshot
  ├─ Show iteration count
  └─ Update status
```

---

## 🧩 Component Details

### Backend Components

#### 1. **FastAPI Application** (`app.py`)
- REST endpoints for health checks and testing
- WebSocket endpoint for real-time agent communication
- CORS middleware for frontend access
- Connection manager for multiple clients
- Structured logging

**Key Endpoints:**
```python
GET  /                    # Health check
GET  /health             # Detailed status
POST /api/agent/start    # Start agent (test)
POST /api/agent/analyze  # Analyze page (test)
GET  /api/config         # Get config
WS   /ws/agent/{id}      # WebSocket stream
```

#### 2. **Browser Controller** (`browser_controller.py`)
- Playwright wrapper for browser automation
- Async context manager pattern
- Screenshot capture
- Navigation and interaction methods
- Error handling and retries

**Methods:**
```python
async def initialize()                    # Launch browser
async def navigate(url)                   # Go to URL
async def take_screenshot()               # Capture image
async def click(selector)                 # Click element
async def fill(selector, text)           # Fill input
async def type_text(selector, text)      # Human typing
async def scroll(direction, amount)      # Scroll page
async def close()                         # Cleanup
```

#### 3. **Vision Utilities** (`vision_utils.py`)
- Set-of-Marks marker injection
- JavaScript execution for DOM manipulation
- Element information extraction
- Marker removal
- Helper functions

**Key Functions:**
```python
async def inject_markers(page)            # Add numbered labels
async def remove_markers(page)            # Clean up
async def get_element_by_marker(...)      # Get selector
async def highlight_element(...)          # Visual feedback
def format_markers_for_prompt(...)        # Format for LLM
```

#### 4. **AI Vision Analyzer** (`ai_vision.py`)
- Gemini 2.0 Flash integration
- Image optimization (resize to 1024x1024)
- Structured JSON parsing
- Retry logic with exponential backoff
- Checkout detection
- Product information extraction

**Key Methods:**
```python
async def analyze_page(...)               # Main analysis
async def detect_checkout_page(...)       # Safety check
async def extract_product_info(...)       # Product details
```

#### 5. **Gemini Helper** (`gemini_helper.py`)
- API configuration
- Prompt engineering
- JSON parsing utilities
- Action validation
- Safety settings

**Functions:**
```python
def setup_gemini()                        # Configure API
def create_vision_prompt(...)             # Build prompt
def parse_gemini_json(...)                # Parse response
def validate_action(...)                  # Check validity
```

#### 6. **Agent State** (`agent_state.py`)
- TypedDict state definition
- State manipulation helpers
- Completion checking
- Status management

**State Structure:**
```python
AgentState = {
    'messages': List[BaseMessage],
    'current_url': str,
    'screenshot_base64': str,
    'markers_map': Dict[int, Dict],
    'last_action': Dict,
    'action_history': List[Dict],
    'user_goal': str,
    'session_id': str,
    'status': Literal[...],
    'iterations': int,
    'max_iterations': int,
    'error': Optional[str],
    'approval_required': bool,
    'approval_granted': bool
}
```

#### 7. **Agent Nodes** (`agent_nodes.py`)
- Observer: Page capture
- Reasoning: AI decision
- Action: Execution
- Element interaction
- Error handling

#### 8. **Agent Graph** (`agent_graph.py`)
- LangGraph workflow definition
- State transitions
- Conditional routing
- Loop control

#### 9. **Agent Service** (`agent_service.py`)
- Session management
- Execution orchestration
- Streaming updates
- Cleanup

#### 10. **Checkout Guard** (`checkout_guard.py`)
- Page classification
- Risk assessment
- Safety checks
- Approval flow

#### 11. **Form Handler** (`form_handler.py`)
- Field detection
- Form filling
- Search box finding
- Submit button location

---

### Frontend Components

#### 1. **Main Page** (`app/page.tsx`)
- WebSocket client
- Message state management
- Agent state tracking
- UI rendering
- Event handlers

**State Management:**
```typescript
const [url, setUrl] = useState('')
const [goal, setGoal] = useState('')
const [messages, setMessages] = useState<Message[]>([])
const [agentState, setAgentState] = useState<AgentState | null>(null)
const [isConnected, setIsConnected] = useState(false)
const [isRunning, setIsRunning] = useState(false)
const [ws, setWs] = useState<WebSocket | null>(null)
```

#### 2. **Layout** (`app/layout.tsx`)
- Root HTML structure
- Metadata
- Font loading
- Global providers

#### 3. **Styles** (`app/globals.css`)
- Tailwind directives
- Custom animations
- Scrollbar styling
- Color variables

---

## 🔐 Security Architecture

### 1. **API Key Management**
```
.env file (backend)
  ↓
config.py loads
  ↓
gemini_helper.py uses
  ↓
Never exposed to frontend
```

### 2. **Checkout Protection**
```
Click Action Requested
  ↓
Extract element text
  ↓
Check keywords ("Place Order", "Buy Now", etc.)
  ↓
Analyze screenshot with Gemini
  ↓
Detect checkout indicators
  ↓
Calculate confidence score
  ↓
If risky (>0.7 confidence)
  ↓
Pause execution
  ↓
Request human approval
  ↓
Wait for confirmation
```

### 3. **Session Isolation**
- Each mission gets unique session ID
- Browser context per session
- State isolation
- Clean session cleanup

---

## 📡 Communication Protocols

### WebSocket Message Format

**Client → Server:**
```json
{
  "type": "start_mission",
  "url": "https://example.com",
  "goal": "Find something"
}
```

**Server → Client:**
```json
{
  "type": "state_update",
  "node": "reasoning",
  "status": "reasoning",
  "iteration": 3,
  "last_action": {
    "action": "click",
    "target": 5,
    "reasoning": "..."
  },
  "screenshot": "base64...",
  "url": "https://...",
  "messages": ["msg1", "msg2"]
}
```

### Message Types

**Outgoing (Server → Client):**
- `started` - Mission began
- `navigation` - Page changed
- `state_update` - State changed
- `complete` - Mission finished
- `cancelled` - Mission stopped
- `error` - Error occurred

**Incoming (Client → Server):**
- `start_mission` - Begin mission
- `cancel` - Stop mission
- `ping` - Keep-alive

---

## 🎯 Design Patterns

### 1. **State Machine Pattern**
LangGraph manages agent as a state machine:
- Explicit states
- Defined transitions
- Conditional routing
- Error recovery

### 2. **Observer Pattern**
WebSocket for real-time updates:
- Server publishes events
- Client subscribes
- Asynchronous updates
- Bidirectional communication

### 3. **Strategy Pattern**
Different actions (click, type, scroll):
- Common interface
- Interchangeable strategies
- Runtime selection
- Easy extensibility

### 4. **Context Manager Pattern**
Browser lifecycle:
```python
async with BrowserController() as browser:
    # Use browser
    # Automatically closes on exit
```

### 5. **Singleton Pattern**
Global executors:
```python
_executor: Optional[AgentExecutor] = None

def get_agent_executor() -> AgentExecutor:
    global _executor
    if _executor is None:
        _executor = AgentExecutor()
    return _executor
```

---

## 🔄 Error Handling Strategy

```
Error Occurs
  │
  ├─ Catch in try/except
  │
  ▼
Log with structlog
  │
  ├─ Include context
  ├─ Stack trace
  ├─ Session ID
  │
  ▼
Update state
  │
  ├─ Set status: "error"
  ├─ Set error message
  │
  ▼
Stream to frontend
  │
  ├─ type: "error"
  ├─ message: "..."
  │
  ▼
Show to user
  │
  ├─ Red error message
  ├─ Stop mission
  │
  ▼
Cleanup
  │
  ├─ Close browser
  ├─ Clear session
  └─ Reset state
```

---

## 📈 Performance Considerations

### 1. **Image Optimization**
- Resize screenshots to 1024x1024
- Convert to RGB
- Compress before sending to Gemini
- Reduces token usage and latency

### 2. **Caching**
- Checkout detection results cached (5s TTL)
- Avoids duplicate API calls
- Significant cost savings

### 3. **Async/Await**
- Non-blocking I/O
- Concurrent operations
- Better resource utilization
- Scalable architecture

### 4. **Rate Limiting**
- Respects Gemini's 15 req/min limit
- Exponential backoff on errors
- Retry logic with delays

---

## 🧪 Testing Strategy

### Unit Tests (Future)
- Test individual functions
- Mock external dependencies
- Fast execution
- High coverage

### Integration Tests (Future)
- Test component interactions
- Mock Gemini API
- Verify workflows
- End-to-end scenarios

### Manual Testing (Current)
- Real browser automation
- Live Gemini API
- Various websites
- Different goals

---

## 📊 Monitoring & Logging

### Structured Logging
```python
logger.info("Action executed",
    action_type="click",
    target=5,
    session_id="abc123",
    iteration=3,
    success=True
)
```

### Log Levels
- **DEBUG**: Detailed information
- **INFO**: General information
- **WARNING**: Unexpected behavior
- **ERROR**: Errors that need attention

### What Gets Logged
- All agent actions
- API calls to Gemini
- Browser interactions
- State transitions
- Errors and exceptions
- Performance metrics

---

## 🚀 Deployment Considerations

### Current Setup (Development)
- Local backend on :8000
- Local frontend on :3000
- No authentication
- Debug mode enabled

### Production Recommendations
1. **Backend:**
   - Use production ASGI server (Gunicorn + Uvicorn)
   - Enable HTTPS
   - Add authentication
   - Rate limiting
   - Request validation
   - CORS restrictions

2. **Frontend:**
   - Build for production (`npm run build`)
   - Use CDN for static assets
   - Enable caching
   - Minify resources
   - Monitor performance

3. **Infrastructure:**
   - Container (Docker)
   - Orchestration (Kubernetes)
   - Load balancing
   - Auto-scaling
   - Health checks
   - Monitoring (Prometheus/Grafana)

4. **Security:**
   - Secret management (Vault)
   - API key rotation
   - Network isolation
   - WAF protection
   - Audit logging

---

## 🎓 Key Technologies Explained

### LangGraph
- Graph-based workflow orchestration
- State management framework
- Built on LangChain
- Designed for agents

### Playwright
- Modern browser automation
- Cross-browser support
- Reliable & fast
- Python async API

### Gemini 2.0 Flash
- Latest Google multimodal model
- Vision + text understanding
- Fast inference
- Structured outputs

### Next.js 14
- React framework
- App Router (latest)
- Server & client components
- Optimized performance

---

This architecture provides a solid foundation for an agentic shopping assistant while maintaining modularity, testability, and extensibility.

