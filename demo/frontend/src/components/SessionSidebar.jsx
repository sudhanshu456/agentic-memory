import React from 'react'
import { Plus, MessageSquare, Trash2, X } from 'lucide-react'

export default function SessionSidebar({ sessions, activeSession, onSelect, onNewSession, onDeleteSession, onDeleteAllSessions }) {
  return (
    <aside className="w-56 shrink-0 border-r border-ops-border bg-ops-panel/30 flex flex-col">
      <div className="p-3 border-b border-ops-border space-y-2">
        <button
          onClick={onNewSession}
          className="w-full flex items-center justify-center gap-1.5 px-3 py-2 text-sm font-medium bg-ops-accent/10 text-ops-accent border border-ops-accent/30 rounded-lg hover:bg-ops-accent/20 transition-colors"
        >
          <Plus className="w-4 h-4" /> New Session
        </button>
        {sessions.length > 0 && (
          <button
            onClick={() => {
              if (confirm('Delete ALL sessions? This cannot be undone.')) onDeleteAllSessions()
            }}
            className="w-full flex items-center justify-center gap-1.5 px-2 py-1.5 text-[11px] text-gray-500 border border-ops-border rounded-lg hover:text-ops-red hover:border-ops-red/40 transition-colors"
          >
            <Trash2 className="w-3 h-3" /> Clear All Sessions
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {sessions.length === 0 && (
          <p className="text-xs text-gray-500 text-center mt-4">No sessions yet</p>
        )}
        {[...sessions].reverse().map((s) => {
          const isActive = s.session_id === activeSession
          const title = s.title || s.session_id.slice(0, 8) + '…'
          return (
            <div
              key={s.session_id}
              className={`group relative w-full text-left px-3 py-2 rounded-lg text-sm transition-colors flex items-center gap-2 cursor-pointer ${
                isActive
                  ? 'bg-ops-accent/15 text-ops-accent border border-ops-accent/30'
                  : 'text-gray-400 hover:bg-white/5 hover:text-gray-200 border border-transparent'
              }`}
              onClick={() => onSelect(s.session_id)}
            >
              <MessageSquare className="w-3.5 h-3.5 shrink-0" />
              <div className="min-w-0 flex-1">
                <div className="truncate text-xs">{title}</div>
                <div className="text-[10px] text-gray-500">
                  {s.message_count || 0} msg{s.message_count !== 1 ? 's' : ''}
                  {s.summary && ' · summarized'}
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onDeleteSession(s.session_id)
                }}
                className="opacity-0 group-hover:opacity-100 p-0.5 text-gray-500 hover:text-ops-red transition-all"
                title="Delete session"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          )
        })}
      </div>

      <div className="p-3 border-t border-ops-border">
        <div className="text-[10px] text-gray-500 text-center">
          Cross-session persistence demo
        </div>
      </div>
    </aside>
  )
}
