'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Bot, Send, StopCircle, Loader2, ShoppingCart, AlertCircle, CheckCircle } from 'lucide-react'

interface Message {
  type: 'user' | 'agent' | 'system'
  content: string
  timestamp: Date
}

interface AgentState {
  status: string
  iteration: number
  url: string
  screenshot: string
}

export default function Home() {
  const [url, setUrl] = useState('')
  const [goal, setGoal] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [agentState, setAgentState] = useState<AgentState | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isRunning, setIsRunning] = useState(false)
  const [ws, setWs] = useState<WebSocket | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const addMessage = (type: Message['type'], content: string) => {
    setMessages(prev => [...prev, { type, content, timestamp: new Date() }])
  }

  const connectWebSocket = (sessionId: string) => {
    const websocket = new WebSocket(`ws://localhost:8000/ws/agent/${sessionId}`)

    websocket.onopen = () => {
      console.log('WebSocket connected')
      setIsConnected(true)
      addMessage('system', '🔗 Connected to agent')
    }

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      console.log('Received:', data)

      switch (data.type) {
        case 'started':
          addMessage('system', `🚀 Mission started: ${data.goal}`)
          setIsRunning(true)
          break

        case 'navigation':
          addMessage('agent', `📍 Navigated to: ${data.url}`)
          if (data.title) {
            addMessage('agent', `📄 Page: ${data.title}`)
          }
          break

        case 'state_update':
          // Update agent state
          setAgentState({
            status: data.status || 'unknown',
            iteration: data.iteration || 0,
            url: data.url || '',
            screenshot: data.screenshot || ''
          })

          // Add messages
          if (data.messages && Array.isArray(data.messages)) {
            data.messages.forEach((msg: string) => {
              if (msg && msg.trim()) {
                addMessage('agent', msg)
              }
            })
          }
          break

        case 'complete':
          addMessage('system', '✅ Mission complete!')
          setIsRunning(false)
          break

        case 'cancelled':
          addMessage('system', '🛑 Mission cancelled')
          setIsRunning(false)
          break

        case 'error':
          addMessage('system', `❌ Error: ${data.message}`)
          setIsRunning(false)
          break
      }
    }

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
      addMessage('system', '❌ Connection error')
      setIsConnected(false)
    }

    websocket.onclose = () => {
      console.log('WebSocket closed')
      setIsConnected(false)
      setIsRunning(false)
      addMessage('system', '🔌 Disconnected from agent')
    }

    setWs(websocket)
    return websocket
  }

  const startMission = () => {
    if (!url || !goal) {
      addMessage('system', '⚠️ Please provide both URL and goal')
      return
    }

    const sessionId = `session_${Date.now()}`
    const websocket = connectWebSocket(sessionId)

    // Wait for connection then send start message
    websocket.addEventListener('open', () => {
      websocket.send(JSON.stringify({
        type: 'start_mission',
        url: url,
        goal: goal
      }))
      addMessage('user', `Goal: ${goal}`)
      addMessage('user', `Starting URL: ${url}`)
    })
  }

  const stopMission = () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'cancel' }))
      ws.close()
    }
    setIsRunning(false)
    setWs(null)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white">
      {/* Header */}
      <header className="border-b border-gray-700 bg-gray-900/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <ShoppingCart className="w-8 h-8 text-blue-400" />
              <div>
                <h1 className="text-2xl font-bold">SmartCart AI</h1>
                <p className="text-sm text-gray-400">Agentic Shopping Assistant</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
                isConnected ? 'bg-green-500/20 text-green-400' : 'bg-gray-700 text-gray-400'
              }`}>
                <div className={`w-2 h-2 rounded-full ${
                  isConnected ? 'bg-green-400 animate-pulse' : 'bg-gray-500'
                }`} />
                {isConnected ? 'Connected' : 'Disconnected'}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-140px)]">
          {/* Left Panel - Chat */}
          <div className="flex flex-col bg-gray-800/50 rounded-lg border border-gray-700 overflow-hidden">
            {/* Input Area */}
            {!isRunning && (
              <div className="p-4 border-b border-gray-700 bg-gray-800/70">
                <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <Bot className="w-5 h-5 text-blue-400" />
                  Start New Mission
                </h2>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Website URL</label>
                    <input
                      type="url"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      placeholder="https://amazon.com"
                      className="w-full px-3 py-2 bg-gray-900 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500 text-white"
                      disabled={isRunning}
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Goal</label>
                    <input
                      type="text"
                      value={goal}
                      onChange={(e) => setGoal(e.target.value)}
                      placeholder="Find wireless headphones under $100"
                      className="w-full px-3 py-2 bg-gray-900 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500 text-white"
                      disabled={isRunning}
                      onKeyPress={(e) => e.key === 'Enter' && startMission()}
                    />
                  </div>
                  <button
                    onClick={startMission}
                    disabled={isRunning || !url || !goal}
                    className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                  >
                    <Send className="w-4 h-4" />
                    Start Mission
                  </button>
                </div>
              </div>
            )}

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              <AnimatePresence>
                {messages.map((msg, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className={`flex gap-3 ${
                      msg.type === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    {msg.type !== 'user' && (
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                        msg.type === 'agent' ? 'bg-blue-600' : 'bg-gray-700'
                      }`}>
                        {msg.type === 'agent' ? (
                          <Bot className="w-4 h-4" />
                        ) : (
                          <AlertCircle className="w-4 h-4" />
                        )}
                      </div>
                    )}
                    <div className={`max-w-[80%] px-4 py-2 rounded-lg whitespace-pre-wrap ${
                      msg.type === 'user'
                        ? 'bg-blue-600 text-white'
                        : msg.type === 'agent'
                        ? 'bg-gray-700 text-gray-100'
                        : 'bg-gray-800 text-gray-300 border border-gray-600'
                    }`}>
                      {msg.content}
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
              <div ref={messagesEndRef} />
            </div>

            {/* Status Bar */}
            {isRunning && (
              <div className="p-4 border-t border-gray-700 bg-gray-800/70">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                    <span className="text-sm">
                      {agentState?.status || 'Running'}
                      {agentState && agentState.iteration > 0 && ` (Step ${agentState.iteration})`}
                    </span>
                  </div>
                  <button
                    onClick={stopMission}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                  >
                    <StopCircle className="w-4 h-4" />
                    Stop
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Right Panel - Visualizer */}
          <div className="bg-gray-800/50 rounded-lg border border-gray-700 overflow-hidden flex flex-col">
            <div className="p-4 border-b border-gray-700 bg-gray-800/70">
              <h2 className="text-lg font-semibold">Live View</h2>
              {agentState?.url && (
                <p className="text-sm text-gray-400 truncate mt-1">{agentState.url}</p>
              )}
            </div>
            <div className="flex-1 overflow-hidden flex items-center justify-center bg-gray-900">
              {agentState?.screenshot ? (
                <img
                  src={`data:image/png;base64,${agentState.screenshot}`}
                  alt="Current page"
                  className="max-w-full max-h-full object-contain"
                />
              ) : (
                <div className="text-center text-gray-500">
                  <Bot className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p>Agent view will appear here</p>
                  <p className="text-sm mt-2">Start a mission to see live screenshots</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

