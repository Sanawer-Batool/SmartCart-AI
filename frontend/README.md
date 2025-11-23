# SmartCart AI - Frontend

Modern Next.js 14 frontend for the SmartCart AI shopping assistant.

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
npm install

# Run development server
npm run dev
```

Visit `http://localhost:3000`

### Build for Production

```bash
npm run build
npm start
```

## 🏗️ Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Framer Motion** - Animations
- **Lucide React** - Icons
- **WebSocket** - Real-time agent communication

## 📁 Project Structure

```
frontend/
├── app/
│   ├── layout.tsx      # Root layout
│   ├── page.tsx        # Main page with agent interface
│   └── globals.css     # Global styles
├── package.json
├── tsconfig.json
└── tailwind.config.js
```

## 🎨 Features

- **Real-time Agent View**: Live screenshots of what the agent sees
- **Chat Interface**: Message history showing agent actions and reasoning
- **Mission Control**: Start/stop agent missions
- **Connection Status**: Real-time WebSocket connection indicator
- **Responsive Design**: Works on desktop and mobile

## 🔌 Backend Connection

The frontend connects to the FastAPI backend via WebSocket:

- **REST API**: `http://localhost:8000`
- **WebSocket**: `ws://localhost:8000/ws/agent/{session_id}`

Make sure the backend is running before starting the frontend!

## 🎯 Usage

1. Enter a website URL (e.g., `https://amazon.com`)
2. Enter your goal (e.g., "Find wireless headphones under $100")
3. Click "Start Mission"
4. Watch the agent work in real-time!
5. Click "Stop" to cancel at any time

## 🛠️ Development

### Environment Variables

Create `.env.local` (optional):

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Adding New Features

The main UI is in `app/page.tsx`. Key state:

- `messages`: Chat message history
- `agentState`: Current agent status and screenshot
- `ws`: WebSocket connection
- `isRunning`: Whether agent is active

### WebSocket Message Types

**Incoming:**
- `started`: Mission began
- `navigation`: Agent navigated to new page
- `state_update`: Agent state changed (includes screenshot)
- `complete`: Mission finished
- `cancelled`: Mission cancelled
- `error`: Error occurred

**Outgoing:**
- `start_mission`: Begin new mission with goal and URL
- `cancel`: Stop current mission
- `ping`: Keep-alive check

## 📝 License

MIT License

