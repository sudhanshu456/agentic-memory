import React, { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { Send, Terminal, User } from 'lucide-react'

const SUGGESTIONS = [
  "I'm an SRE at Acme Corp. We run K8s on AWS with Datadog for monitoring and Terraform for IaC.",
  "We're getting P1 alerts — payment-service is throwing OOM errors in production.",
  "How do I rollback the last Helm release for checkout-service?",
  "Help me set up SLOs for our API gateway. We need 99.9% availability.",
  "What's the capacity planning formula for our order-service before Black Friday?",
]

export default function ChatPanel({ messages, loading, onSend }) {
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  function handleSubmit(e) {
    e.preventDefault()
    if (!input.trim() || loading) return
    onSend(input.trim())
    setInput('')
  }

  function handleSuggestion(text) {
    onSend(text)
  }

  return (
    <div className="flex-1 flex flex-col min-w-0">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Terminal className="w-12 h-12 text-ops-accent/40 mb-4" />
            <h2 className="text-lg font-semibold text-gray-300 mb-1">OpsAgent</h2>
            <p className="text-sm text-gray-500 mb-6 max-w-md">
              Your AI SRE assistant with persistent memory. Try one of these to get started:
            </p>
            <div className="space-y-2 max-w-lg w-full">
              {SUGGESTIONS.map((s, i) => (
                <button
                  key={i}
                  onClick={() => handleSuggestion(s)}
                  className="w-full text-left px-4 py-2.5 text-sm text-gray-300 bg-ops-panel/50 border border-ops-border rounded-lg hover:border-ops-accent/40 hover:text-gray-100 transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
            {msg.role === 'assistant' && (
              <div className="shrink-0 w-7 h-7 rounded-lg bg-ops-accent/15 flex items-center justify-center mt-0.5">
                <Terminal className="w-4 h-4 text-ops-accent" />
              </div>
            )}
            <div
              className={`max-w-[75%] rounded-xl px-4 py-2.5 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-ops-accent/15 text-gray-100 border border-ops-accent/20'
                  : 'bg-ops-panel border border-ops-border text-gray-200'
              }`}
            >
              {msg.role === 'assistant' ? (
                <div className="prose-ops">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              ) : (
                msg.content
              )}
            </div>
            {msg.role === 'user' && (
              <div className="shrink-0 w-7 h-7 rounded-lg bg-ops-purple/15 flex items-center justify-center mt-0.5">
                <User className="w-4 h-4 text-ops-purple" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-3">
            <div className="shrink-0 w-7 h-7 rounded-lg bg-ops-accent/15 flex items-center justify-center">
              <Terminal className="w-4 h-4 text-ops-accent" />
            </div>
            <div className="bg-ops-panel border border-ops-border rounded-xl px-4 py-3 flex items-center gap-1.5">
              <div className="typing-dot w-2 h-2 bg-ops-accent rounded-full" />
              <div className="typing-dot w-2 h-2 bg-ops-accent rounded-full" />
              <div className="typing-dot w-2 h-2 bg-ops-accent rounded-full" />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <form onSubmit={handleSubmit} className="shrink-0 p-4 border-t border-ops-border">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Describe your incident, ask about infra, or request a runbook..."
            className="flex-1 bg-ops-panel border border-ops-border rounded-xl px-4 py-2.5 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-ops-accent/50 transition-colors"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-4 py-2.5 bg-ops-accent text-ops-dark font-medium rounded-xl hover:bg-ops-accent/90 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  )
}
