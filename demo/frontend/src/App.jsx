import React, { useState, useEffect, useRef } from 'react'
import ChatPanel from './components/ChatPanel'
import MemoryInspector from './components/MemoryInspector'
import SessionSidebar from './components/SessionSidebar'
import { Brain, PanelRightOpen, PanelRightClose, RotateCcw } from 'lucide-react'

const API = ''  // proxied via vite
const DEFAULT_USER = 'sre-demo-user'

export default function App() {
  const [userId] = useState(DEFAULT_USER)
  const [sessionId, setSessionId] = useState(null)
  const [sessions, setSessions] = useState([])
  const [messages, setMessages] = useState([])
  const [debugLog, setDebugLog] = useState([])  // array of debug objects per turn
  const [memoryStats, setMemoryStats] = useState(null)
  const [loading, setLoading] = useState(false)
  const [inspectorOpen, setInspectorOpen] = useState(true)
  const [latestDebug, setLatestDebug] = useState(null)

  // On first load, just fetch existing sessions and memory stats (don't auto-create)
  useEffect(() => {
    fetchSessions()
    fetchMemoryStats()
  }, [])

  // Refresh memory stats when debug changes
  useEffect(() => {
    if (latestDebug) fetchMemoryStats()
  }, [latestDebug])

  async function createSession() {
    try {
      const res = await fetch(`${API}/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId }),
      })
      const data = await res.json()
      setSessionId(data.session_id)
      setMessages([])
      setDebugLog([])
      setLatestDebug(null)
      fetchSessions()
      fetchMemoryStats()
    } catch (err) {
      console.error('Failed to create session:', err)
    }
  }

  async function fetchSessions() {
    try {
      const res = await fetch(`${API}/sessions/${userId}`)
      const data = await res.json()
      setSessions(data)
    } catch (err) {
      console.error('Failed to fetch sessions:', err)
    }
  }

  async function fetchMemoryStats() {
    try {
      const res = await fetch(`${API}/memory/${userId}`)
      const data = await res.json()
      setMemoryStats(data)
    } catch (err) {
      console.error('Failed to fetch memory stats:', err)
    }
  }

  async function sendMessage(text) {
    if (!text.trim() || loading) return

    // Auto-create session if none active
    let activeSessionId = sessionId
    if (!activeSessionId) {
      try {
        const res = await fetch(`${API}/sessions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId }),
        })
        const data = await res.json()
        activeSessionId = data.session_id
        setSessionId(activeSessionId)
        fetchSessions()
      } catch (err) {
        console.error('Failed to auto-create session:', err)
        return
      }
    }

    const userMsg = { role: 'user', content: text }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      const res = await fetch(`${API}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          session_id: activeSessionId,
          message: text,
        }),
      })
      const data = await res.json()
      const assistantMsg = { role: 'assistant', content: data.response }
      setMessages(prev => [...prev, assistantMsg])
      setLatestDebug(data.debug)
      setDebugLog(prev => [...prev, data.debug])
      fetchSessions()  // refresh sidebar (title, message count)
    } catch (err) {
      console.error('Chat error:', err)
      setMessages(prev => [...prev, { role: 'assistant', content: '⚠️ Error contacting OpsAgent backend. Is it running on :8000?' }])
    } finally {
      setLoading(false)
    }
  }

  async function switchSession(sid) {
    setSessionId(sid)
    setDebugLog([])
    setLatestDebug(null)
    fetchMemoryStats()  // refresh profile + memory stats on session switch
    // Load existing messages for this session
    try {
      const res = await fetch(`${API}/sessions/${userId}/${sid}`)
      if (res.ok) {
        const session = await res.json()
        const loaded = (session.messages || []).map(m => ({
          role: m.role,
          content: m.content,
        }))
        setMessages(loaded)
      } else {
        setMessages([])
      }
    } catch (err) {
      console.error(err)
      setMessages([])
    }
  }

  async function deleteSession(sid) {
    try {
      await fetch(`${API}/sessions/${userId}/${sid}`, { method: 'DELETE' })
      if (sid === sessionId) {
        setSessionId(null)
        setMessages([])
        setDebugLog([])
        setLatestDebug(null)
      }
      fetchSessions()
    } catch (err) {
      console.error(err)
    }
  }

  async function deleteAllSessions() {
    try {
      await fetch(`${API}/sessions/${userId}`, { method: 'DELETE' })
      setSessionId(null)
      setMessages([])
      setDebugLog([])
      setLatestDebug(null)
      setSessions([])
    } catch (err) {
      console.error(err)
    }
  }

  async function resetMemory() {
    if (!confirm('This will delete ALL memories and profile data. Continue?')) return
    try {
      await fetch(`${API}/memory/${userId}`, { method: 'DELETE' })
      setMemoryStats(null)
      fetchMemoryStats()
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-2 border-b border-ops-border bg-ops-panel/50 shrink-0">
        <div className="flex items-center gap-2">
          <Brain className="w-6 h-6 text-ops-accent" />
          <h1 className="text-lg font-bold tracking-tight">
            OpsAgent <span className="text-ops-accent font-normal text-sm ml-1">Agentic Memory Demo</span>
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={resetMemory}
            className="flex items-center gap-1 px-2 py-1 text-xs text-gray-400 hover:text-ops-red border border-ops-border rounded hover:border-ops-red/50 transition-colors"
            title="Reset all memories"
          >
            <RotateCcw className="w-3 h-3" /> Reset
          </button>
          <button
            onClick={() => setInspectorOpen(!inspectorOpen)}
            className="p-1.5 text-gray-400 hover:text-ops-accent border border-ops-border rounded hover:border-ops-accent/50 transition-colors"
            title="Toggle memory inspector"
          >
            {inspectorOpen ? <PanelRightClose className="w-4 h-4" /> : <PanelRightOpen className="w-4 h-4" />}
          </button>
        </div>
      </header>

      {/* Main layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Session sidebar */}
        <SessionSidebar
          sessions={sessions}
          activeSession={sessionId}
          onSelect={switchSession}
          onNewSession={createSession}
          onDeleteSession={deleteSession}
          onDeleteAllSessions={deleteAllSessions}
        />

        {/* Chat panel */}
        <ChatPanel
          messages={messages}
          loading={loading}
          onSend={sendMessage}
        />

        {/* Memory inspector */}
        {inspectorOpen && (
          <MemoryInspector
            debug={latestDebug}
            memoryStats={memoryStats}
          />
        )}
      </div>
    </div>
  )
}
