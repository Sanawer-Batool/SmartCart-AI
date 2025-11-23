# 🤖 SmartCart AI - Agentic E-Commerce Shopping Assistant

An autonomous AI agent that can browse e-commerce websites, search for products, compare prices, and complete purchases using natural language commands. Built with Google Gemini 2.0 Flash for multimodal vision analysis.

![SmartCart AI](https://img.shields.io/badge/AI-Gemini%202.0%20Flash-blue)
![Python](https://img.shields.io/badge/Python-3.10+-green)
![Next.js](https://img.shields.io/badge/Next.js-14-black)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

- 🎯 **Autonomous Navigation**: AI agent browses websites like a human
- 👁️ **Visual Understanding**: Uses Gemini 2.0 Flash for multimodal vision analysis
- 🔴 **Set-of-Marks**: Injects numbered markers on interactive elements for precise control
- 🛡️ **Safety First**: Human-in-the-loop approval for checkout/purchases
- 🔄 **Real-time Updates**: WebSocket streaming of agent progress
- 🌐 **Multi-site Support**: Works with Amazon, eBay, Shopify, and more
- 🧠 **LangGraph Workflow**: Structured agentic loop with observe-reason-act pattern

## 🏗️ Architecture

### Tech Stack

**Backend:**
- Python FastAPI (REST API & WebSocket)
- Playwright (Browser automation)
- LangGraph (Agent workflow orchestration)
- Google Gemini 2.0 Flash (Vision AI)
- Structured logging with structlog

**Frontend:**
- Next.js 14 with App Router
- TypeScript
- Tailwind CSS
- Framer Motion (animations)
- WebSocket client

### How It Works

1. **Observe**: Agent captures screenshot and injects numbered markers on interactive elements
2. **Reason**: Gemini 2.0 Flash analyzes the screenshot and decides the next action
3. **Act**: Agent executes the action (click, type, scroll)
4. **Loop**: Repeat until goal is achieved or max iterations reached

The agent uses a state machine powered by LangGraph, ensuring robust and maintainable workflow.

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- Google Gemini API Key ([Get one here](https://aistudio.google.com/app/apikey))

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Create .env file
echo "GOOGLE_API_KEY=your_gemini_key_here" > .env

# Run the server
python app.py
# OR
uvicorn app:app --reload
```

Backend will be available at `http://localhost:8000`

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at `http://localhost:3000`

## 🎮 Usage

1. **Open the frontend** at `http://localhost:3000`

2. **Enter details:**
   - Website URL: `https://amazon.com`
   - Goal: `Find wireless headphones under $100`

3. **Click "Start Mission"** and watch the agent work!

4. **Monitor progress** in real-time:
   - Left panel shows chat logs and agent reasoning
   - Right panel shows live screenshots with visual markers

5. **Stop anytime** by clicking the "Stop" button

### Example Goals

```
"Find the top-rated laptop under $1000"
"Search for Nike running shoes size 10"
"Compare prices for iPhone 15 Pro"
"Find organic dog food with free shipping"
"Look for wireless earbuds with noise cancellation"
```

## 📖 API Documentation

Once the backend is running, visit:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

**REST API:**
- `GET /` - Health check
- `POST /api/agent/start` - Start agent on URL
- `POST /api/agent/analyze` - Analyze page with vision AI
- `GET /api/config` - Get configuration

**WebSocket:**
- `WS /ws/agent/{session_id}` - Real-time agent communication

## 🔑 Getting Your Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Get API Key" → "Create API key"
3. Copy your key (format: `AIza...`)
4. Add to `backend/.env` file:

```bash
GOOGLE_API_KEY=your_key_here
```

### Free Tier Limits

- **Gemini 2.0 Flash**: 15 requests/minute, 1M requests/day
- **Context Window**: 1M tokens
- **Perfect for development and demos!**

## 🛡️ Safety Features

### Checkout Detection

The agent automatically detects checkout pages using vision AI and requires human approval before completing purchases:

```python
# Agent detects:
- "Place Order" buttons
- Payment information fields
- Order summary with total price
- Checkout page indicators

# Then pauses and requests approval
```

### Human-in-the-Loop

When a potentially risky action is detected:
1. Agent pauses execution
2. Displays order summary to user
3. Waits for explicit approval
4. Only proceeds after confirmation

## 📁 Project Structure

```
SmartCart AI/
├── backend/
│   ├── app.py                    # FastAPI application
│   ├── config.py                 # Configuration management
│   ├── browser_controller.py    # Playwright automation
│   ├── vision_utils.py           # Set-of-Marks injection
│   ├── ai_vision.py              # Gemini vision analysis
│   ├── gemini_helper.py          # Gemini API utilities
│   ├── agent_state.py            # State definition
│   ├── agent_nodes.py            # LangGraph nodes
│   ├── agent_graph.py            # Workflow graph
│   ├── agent_service.py          # Execution service
│   ├── checkout_guard.py         # Safety checks
│   ├── form_handler.py           # Form detection
│   ├── requirements.txt          # Python dependencies
│   ├── setup.py                  # Setup script
│   ├── run.sh / run.bat         # Run scripts
│   └── README.md
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx           # Root layout
│   │   ├── page.tsx             # Main interface
│   │   └── globals.css          # Global styles
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── README.md
│
└── README.md                     # This file
```

## 🧪 Testing

### Manual Testing

1. Start backend: `python backend/app.py`
2. Test health endpoint: `curl http://localhost:8000/health`
3. Test navigation:
```bash
curl -X POST http://localhost:8000/api/agent/start \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Browser Testing

1. Open frontend at `http://localhost:3000`
2. Try different websites and goals
3. Test stop/cancel functionality
4. Verify screenshot updates in real-time

## 🐛 Troubleshooting

### "ResourceExhausted" error
- You hit the Gemini rate limit (15 req/min for Flash)
- Add delays or implement rate limiting
- Use caching for repeated operations

### Image not recognized
- Ensure image is RGB format
- Check image size (< 20MB)
- Verify formats: PNG/JPEG/WEBP

### API key invalid
- Regenerate key at aistudio.google.com
- Check `.env` file exists and is loaded
- Verify no extra spaces in key

### Playwright browser won't start
- Run `playwright install chromium` again
- Install system dependencies: `playwright install-deps` (Linux)
- Check Python version (3.10+)

### WebSocket connection fails
- Ensure backend is running on port 8000
- Check firewall settings
- Verify CORS configuration in backend

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- [ ] Add more site-specific adapters (Amazon, eBay, etc.)
- [ ] Implement price comparison feature
- [ ] Add persistent browser contexts (saved logins)
- [ ] Improve error recovery strategies
- [ ] Add unit and integration tests
- [ ] Implement caching for vision API calls
- [ ] Add dark mode toggle in frontend
- [ ] Support for multiple concurrent sessions

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- **Google Gemini 2.0 Flash** - Powerful multimodal AI
- **Playwright** - Reliable browser automation
- **LangGraph** - Agent workflow framework
- **Next.js** - Excellent React framework

## 📞 Support

- [Gemini API Docs](https://ai.google.dev/docs)
- [Playwright Docs](https://playwright.dev/python/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [Next.js Docs](https://nextjs.org/docs)

---

**Built with ❤️ using Google Gemini 2.0 Flash**

🌟 If you find this project useful, please give it a star!

