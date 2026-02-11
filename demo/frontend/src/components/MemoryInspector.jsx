import React, { useState } from 'react'
import {
  Database, User, Clock, Zap, BookOpen, ChevronDown, ChevronRight,
  ArrowDownUp, Shrink, Brain, Layers, Search, FileText
} from 'lucide-react'

function Section({ icon: Icon, title, color, badge, defaultOpen = false, children }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="border border-ops-border rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium hover:bg-white/5 transition-colors"
      >
        {open ? <ChevronDown className="w-3 h-3 text-gray-500" /> : <ChevronRight className="w-3 h-3 text-gray-500" />}
        <Icon className={`w-3.5 h-3.5 ${color}`} />
        <span className="text-gray-200">{title}</span>
        {badge !== undefined && (
          <span className={`ml-auto px-1.5 py-0.5 rounded text-[10px] font-mono ${color} bg-white/5`}>
            {badge}
          </span>
        )}
      </button>
      {open && <div className="px-3 pb-3 pt-1">{children}</div>}
    </div>
  )
}

function Tag({ children, color = 'text-gray-400 bg-white/5' }) {
  return (
    <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-mono ${color}`}>
      {children}
    </span>
  )
}

export default function MemoryInspector({ debug, memoryStats }) {
  // Use debug profile if available (current turn), otherwise fall back to persisted profile from memoryStats
  const profile = debug?.profile || memoryStats?.profile || null
  return (
    <aside className="w-80 shrink-0 border-l border-ops-border bg-ops-panel/30 flex flex-col overflow-hidden">
      <div className="px-3 py-2.5 border-b border-ops-border flex items-center gap-2">
        <Brain className="w-4 h-4 text-ops-accent" />
        <span className="text-sm font-semibold text-gray-200">Memory Inspector</span>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
        {/* Agent Loop Steps */}
        {debug?.steps && (
          <Section icon={Zap} title="Agent Loop Steps" color="text-ops-yellow" badge={debug.steps.length} defaultOpen={true}>
            <ol className="space-y-1">
              {debug.steps.map((step, i) => (
                <li key={i} className="flex items-start gap-2 text-[11px]">
                  <span className="text-gray-500 font-mono shrink-0 w-4 text-right">{i + 1}.</span>
                  <span className="text-gray-300 font-mono">{step}</span>
                </li>
              ))}
            </ol>
          </Section>
        )}

        {/* Retrieved Memories (Step 1: Vector Store) */}
        <Section
          icon={Search}
          title="Retrieved Memories"
          color="text-ops-accent"
          badge={debug?.retrieved_memories?.length ?? 0}
          defaultOpen={true}
        >
          {(!debug?.retrieved_memories || debug.retrieved_memories.length === 0) ? (
            <p className="text-[11px] text-gray-500 italic">No memories retrieved this turn</p>
          ) : (
            <div className="space-y-2">
              {debug.retrieved_memories.map((mem, i) => (
                <div key={i} className="bg-ops-dark/50 rounded p-2 border border-ops-border/50">
                  <div className="flex items-center gap-1.5 mb-1">
                    <Tag color="text-ops-accent bg-ops-accent/10">{mem.metadata?.memory_type}</Tag>
                    <Tag>sim: {mem.similarity}</Tag>
                    <Tag>rec: {mem.recency_score}</Tag>
                  </div>
                  <p className="text-[11px] text-gray-300 leading-relaxed">{mem.text}</p>
                  <div className="mt-1 flex items-center gap-1">
                    <Tag color="text-ops-green bg-ops-green/10">combined: {mem.combined_score}</Tag>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Section>

        {/* New Memories Stored (Write-back) */}
        <Section
          icon={Database}
          title="New Memories Stored"
          color="text-ops-green"
          badge={debug?.new_memories?.length ?? 0}
        >
          {(!debug?.new_memories || debug.new_memories.length === 0) ? (
            <p className="text-[11px] text-gray-500 italic">No new memories extracted this turn</p>
          ) : (
            <div className="space-y-2">
              {debug.new_memories.map((mem, i) => (
                <div key={i} className="bg-ops-dark/50 rounded p-2 border border-ops-border/50">
                  <div className="flex items-center gap-1.5 mb-1">
                    <Tag color="text-ops-green bg-ops-green/10">{mem.metadata?.memory_type}</Tag>
                    <span className="text-[10px] font-mono text-gray-500">{mem.id}</span>
                  </div>
                  <p className="text-[11px] text-gray-300">{mem.text}</p>
                </div>
              ))}
            </div>
          )}
        </Section>

        {/* Compression Stats (Step 2) */}
        <Section icon={Shrink} title="Compression & Pruning" color="text-ops-purple">
          {debug?.compression_stats ? (
            <div className="space-y-1.5 text-[11px]">
              <div className="flex justify-between text-gray-400">
                <span>Messages</span>
                <span className="text-gray-300 font-mono">
                  {debug.compression_stats.original_messages}
                  {debug.compression_stats.pruned && (
                    <span className="text-ops-red"> → {debug.compression_stats.final_messages}</span>
                  )}
                </span>
              </div>
              <div className="flex justify-between text-gray-400">
                <span>Tokens</span>
                <span className="text-gray-300 font-mono">
                  {debug.compression_stats.original_tokens} / {debug.compression_stats.budget}
                </span>
              </div>
              <div className="flex justify-between text-gray-400">
                <span>Strategy</span>
                <Tag>{debug.compression_stats.strategy}</Tag>
              </div>
              {debug.compression_stats.pruned && (
                <div className="flex justify-between text-gray-400">
                  <span>Dropped</span>
                  <Tag color="text-ops-red bg-ops-red/10">{debug.compression_stats.dropped_messages} msgs</Tag>
                </div>
              )}
              {debug.summary && (
                <div className="mt-2 bg-ops-dark/50 rounded p-2 border border-ops-purple/20">
                  <div className="text-[10px] text-ops-purple font-medium mb-1">Rolling Summary</div>
                  <p className="text-[11px] text-gray-300 leading-relaxed">{debug.summary}</p>
                </div>
              )}
            </div>
          ) : (
            <p className="text-[11px] text-gray-500 italic">No compression data yet</p>
          )}
        </Section>

        {/* User Profile (Step 3) */}
        <Section icon={User} title="User Profile" color="text-ops-yellow" defaultOpen={!!profile?.name || (profile?.facts?.length > 0)}>
          {profile ? (
            <div className="space-y-1.5 text-[11px]">
              {profile.name && (
                <div className="flex justify-between text-gray-400">
                  <span>Name</span>
                  <span className="text-gray-200">{profile.name}</span>
                </div>
              )}
              {Object.keys(profile.preferences || {}).length > 0 && (
                <div>
                  <div className="text-gray-400 mb-1">Preferences:</div>
                  {Object.entries(profile.preferences).map(([k, v]) => (
                    <div key={k} className="flex justify-between pl-2">
                      <span className="text-gray-500">{k}</span>
                      <span className="text-gray-300">{String(v)}</span>
                    </div>
                  ))}
                </div>
              )}
              {(profile.constraints || []).length > 0 && (
                <div>
                  <div className="text-gray-400 mb-1">Constraints:</div>
                  {profile.constraints.map((c, i) => (
                    <div key={i} className="pl-2 text-gray-300">• {c}</div>
                  ))}
                </div>
              )}
              {(profile.facts || []).length > 0 && (
                <div>
                  <div className="text-gray-400 mb-1">Facts:</div>
                  {profile.facts.map((f, i) => (
                    <div key={i} className="pl-2 text-gray-300">• {f}</div>
                  ))}
                </div>
              )}
              {debug?.profile_updates && Object.keys(debug.profile_updates).length > 0 && (
                <div className="mt-1.5 bg-ops-dark/50 rounded p-2 border border-ops-yellow/20">
                  <div className="text-[10px] text-ops-yellow font-medium mb-1">Updated this turn</div>
                  <pre className="text-[10px] text-gray-400 whitespace-pre-wrap">
                    {JSON.stringify(debug.profile_updates, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ) : (
            <p className="text-[11px] text-gray-500 italic">No profile loaded</p>
          )}
        </Section>

        {/* Episodic Context (Step 3) */}
        <Section icon={Clock} title="Episodic Context" color="text-blue-400">
          {debug?.episodic_context ? (
            <div className="bg-ops-dark/50 rounded p-2 border border-blue-400/20">
              <p className="text-[11px] text-gray-300 leading-relaxed whitespace-pre-wrap">
                {debug.episodic_context}
              </p>
            </div>
          ) : (
            <p className="text-[11px] text-gray-500 italic">
              No previous session context (start a 2nd session to see this)
            </p>
          )}
        </Section>

        {/* Skills / Progressive Disclosure (Bonus) */}
        <Section
          icon={BookOpen}
          title="Skills (Progressive Disclosure)"
          color="text-orange-400"
          badge={debug?.skills_loaded?.filter(s => s.loaded)?.length ?? 0}
        >
          {(!debug?.skills_loaded || debug.skills_loaded.length === 0) ? (
            <p className="text-[11px] text-gray-500 italic">No skills data</p>
          ) : (
            <div className="space-y-1.5">
              {debug.skills_loaded.map((skill) => (
                <div
                  key={skill.id}
                  className={`flex items-center gap-2 p-1.5 rounded border ${
                    skill.loaded
                      ? 'border-orange-400/30 bg-orange-400/5'
                      : 'border-ops-border/50 bg-ops-dark/30'
                  }`}
                >
                  <FileText className={`w-3 h-3 shrink-0 ${skill.loaded ? 'text-orange-400' : 'text-gray-600'}`} />
                  <div className="min-w-0">
                    <div className={`text-[11px] font-medium ${skill.loaded ? 'text-orange-300' : 'text-gray-500'}`}>
                      {skill.name}
                    </div>
                    <div className="text-[10px] text-gray-500 truncate">{skill.summary}</div>
                  </div>
                  <Tag color={skill.loaded ? 'text-orange-400 bg-orange-400/10' : 'text-gray-600 bg-white/5'}>
                    {skill.loaded ? 'LOADED' : 'idle'}
                  </Tag>
                </div>
              ))}
            </div>
          )}
        </Section>

        {/* Global Memory Stats */}
        {memoryStats && (
          <Section icon={Layers} title="Memory Store Stats" color="text-gray-400">
            <div className="space-y-1.5 text-[11px]">
              <div className="flex justify-between text-gray-400">
                <span>Total memories in vector DB</span>
                <span className="text-gray-200 font-mono">{memoryStats.total_memories}</span>
              </div>
              <div className="flex justify-between text-gray-400">
                <span>Sessions</span>
                <span className="text-gray-200 font-mono">{memoryStats.sessions?.length ?? 0}</span>
              </div>
              <div className="flex justify-between text-gray-400">
                <span>Skills registered</span>
                <span className="text-gray-200 font-mono">{memoryStats.skills_index?.length ?? 0}</span>
              </div>
            </div>
          </Section>
        )}
      </div>
    </aside>
  )
}
