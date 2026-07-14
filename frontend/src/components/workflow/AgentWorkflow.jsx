import { useState, useRef, useEffect } from 'react'
import { getPipelineStatus } from '../../api/api'

const INITIAL_AGENTS = [
  { role: 'Upload Agent', input: 'CSV file', output: 'Raw data ingested', status: 'idle', icon: '📁' },
  { role: 'Profiling Agent', input: 'Raw dataset', output: 'Column types, stats, quality score', status: 'idle', icon: '📋' },
  { role: 'Analysis Agent', input: 'Profiled data', output: 'KPIs, trends, correlations', status: 'idle', icon: '🔍' },
  { role: 'Insight Agent', input: 'Analysis results', output: 'Natural language insights', status: 'idle', icon: '🧠' },
  { role: 'Q&A Agent', input: 'User question + context', output: 'Contextual answers', status: 'idle', icon: '💬' },
  { role: 'Recommendation Agent', input: 'Insights + KPIs', output: 'Business recommendations', status: 'idle', icon: '🎯' },
]

const STATUS_MAP = {
  idle: { label: 'Waiting', class: 'bg-gray-100 text-gray-500' },
  running: { label: 'Running...', class: 'bg-blue-100 text-blue-700 animate-pulse' },
  done: { label: 'Completed', class: 'bg-green-100 text-green-700' },
  error: { label: 'Failed', class: 'bg-red-100 text-red-700' },
}

export default function AgentWorkflow() {
  const [agents, setAgents] = useState(INITIAL_AGENTS)
  const pollingRef = useRef(null)

  const STEP_MAP = [
    { key: 'upload', index: 0 },
    { key: 'profiling', index: 1 },
    { key: 'charts', index: 2 },
    { key: 'insights', index: 3 },
    { key: 'recommendations', index: 5 },
  ]

  const mapStatus = (s) => {
    switch (s) {
      case 'pending': return 'idle'
      case 'running': return 'running'
      case 'completed': return 'done'
      case 'failed': return 'error'
      default: return 'idle'
    }
  }

  const startPolling = () => {
    let pollCount = 0
    pollingRef.current = setInterval(async () => {
      pollCount++
      if (pollCount > 120) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
        return
      }
      try {
        const status = await getPipelineStatus()
        setAgents(prev => {
          const next = prev.map(a => ({ ...a }))
          STEP_MAP.forEach(({ key, index }) => {
            if (status[key]) next[index] = { ...next[index], status: mapStatus(status[key]) }
          })
          if (status.completed || status.error) {
            clearInterval(pollingRef.current)
            pollingRef.current = null
          }
          return next
        })
      } catch {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
    }, 500)
  }

  useEffect(() => {
    (async () => {
      try {
        const status = await getPipelineStatus()
        if (status.completed) {
          setAgents(prev => {
            const next = prev.map(a => ({ ...a }))
            STEP_MAP.forEach(({ key, index }) => {
              if (status[key]) next[index] = { ...next[index], status: mapStatus(status[key]) }
            })
            return next
          })
          return
        }
        if (Object.values(status).some(v => v === 'running') || status.upload === 'pending') {
          startPolling()
        }
      } catch {}
    })()
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
    }
  }, [])

  const reset = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
    setAgents(INITIAL_AGENTS)
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-800">Agent Workflow</h2>
        <div className="flex gap-2">
          <button onClick={reset}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 font-medium text-sm">
            Reset
          </button>
        </div>
      </div>
      <div className="relative">
        {agents.map((agent, i) => {
          const st = STATUS_MAP[agent.status]
          return (
            <div key={agent.role} className="flex items-stretch gap-4 mb-3 last:mb-0">
              <div className="flex flex-col items-center w-8 shrink-0">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                  agent.status === 'done' ? 'bg-green-500 text-white' :
                  agent.status === 'running' ? 'bg-blue-500 text-white' :
                  'bg-gray-200 text-gray-500'
                }`}>
                  {agent.status === 'running' ? (
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                  ) : i + 1}
                </div>
                {i < agents.length - 1 && <div className="w-0.5 flex-1 bg-gray-300 my-1" />}
              </div>
              <div className="flex-1 bg-gray-50 rounded-lg border border-gray-200 p-4 hover:shadow-sm transition-shadow">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{agent.icon}</span>
                    <h3 className="font-semibold text-gray-800 text-sm">{agent.role}</h3>
                  </div>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${st.class}`}>{st.label}</span>
                </div>
                <div className="grid grid-cols-2 gap-4 text-xs text-gray-600">
                  <div>
                    <span className="text-gray-400 block mb-0.5">Input</span>
                    <span className="font-medium">{agent.input}</span>
                  </div>
                  <div>
                    <span className="text-gray-400 block mb-0.5">Output</span>
                    <span className="font-medium">{agent.output}</span>
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
