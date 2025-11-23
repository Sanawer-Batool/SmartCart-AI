# 🤖 SmartCart AI - Agentic E-Commerce Shopping Assistant

An AI agent that can autonomously browse e-commerce sites, search for products, compare prices, and complete purchases using natural language commands.

## 🚀 Features

- **Autonomous Navigation**: AI agent browses websites like a human
- **Visual Understanding**: Uses Google Gemini 2.0 Flash for multimodal vision analysis
- **Smart Interaction**: Detects and interacts with clickable elements using Set-of-Marks
- **Safety First**: Human-in-the-loop approval for checkout/purchases
- **Real-time Updates**: WebSocket streaming of agent progress
- **Multi-site Support**: Works with Amazon, eBay, Shopify, and more

## 🛠️ Tech Stack

- **Backend**: Python FastAPI + Playwright + LangGraph
- **AI**: Google Gemini 2.0 Flash (multimodal, fast, cost-effective)
- **Browser Automation**: Playwright (headless Chrome)
- **Agent Framework**: LangGraph for agentic workflows

## 📋 Prerequisites

- Python 3.10 or higher
- Node.js 18+ (for frontend)
- Google Gemini API Key ([Get one here](https://aistudio.google.com/app/apikey))

## 🔧 Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd ecommerce-agent/backend
```

### 2. Create virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright browsers

```bash
playwright install chromium
```

### 5. Configure environment variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your Gemini API key
# GOOGLE_API_KEY=your_key_here
```

## 🚀 Running the Backend

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=. --cov-report=html
```

## 🔑 Getting Your Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Get API Key" → "Create API key"
3. Copy your key (format: `AIza...`)
4. Add to `.env` file: `GOOGLE_API_KEY=your_key_here`

### Free Tier Limits (Generous for Development)

- **Gemini 2.0 Flash**: 15 requests/minute, 1M requests/day
- **Gemini 1.5 Pro**: 2 requests/minute, 50 requests/day
- Both have 1M token context windows

## 📖 Usage Examples

### Start a shopping mission

```bash
curl -X POST http://localhost:8000/api/agent/start \
  -H "Content-Type: application/json" \
  -d '{"url": "https://amazon.com", "goal": "Find wireless headphones under $100"}'
```

## 🏗️ Project Structure

```
backend/
├── app.py                  # FastAPI application entry point
├── config.py              # Configuration management
├── browser_controller.py  # Playwright browser automation
├── vision_utils.py        # Set-of-Marks marker injection
├── ai_vision.py          # Gemini vision analysis
├── gemini_helper.py      # Gemini API utilities
├── agent_state.py        # LangGraph state definition
├── agent_nodes.py        # LangGraph node functions
├── agent_graph.py        # LangGraph workflow
├── agent_service.py      # Agent execution service
├── form_handler.py       # Form detection and filling
├── checkout_guard.py     # Purchase safety checks
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🛡️ Safety Features

- **Checkout Detection**: Automatically detects checkout pages
- **Human Approval**: Requires user confirmation before purchases
- **Action History**: Tracks all agent actions
- **Error Recovery**: Graceful handling of failures
- **Rate Limiting**: Respects API limits

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.

## 📄 License

MIT License - See LICENSE file for details

## 🆘 Troubleshooting

### "ResourceExhausted" error
- You hit the rate limit (15 req/min for Flash). Add delays between calls.

### Image not recognized
- Ensure image is RGB, max 20MB, formats: PNG/JPEG/WEBP

### API key invalid
- Regenerate key at aistudio.google.com
- Check `.env` file is loaded correctly

### Playwright browser won't start
- Run `playwright install chromium` again
- Check system dependencies: `playwright install-deps`

## 📞 Support

- [Gemini API Docs](https://ai.google.dev/docs)
- [Playwright Docs](https://playwright.dev/python/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)

---

Built with ❤️ using Google Gemini 2.0 Flash

