import { useState, useRef, useEffect } from 'react'
import { askQuestion, compareModels } from '../../api/api'

const SUGGESTIONS = [
  'Compare sales by department',
  'Summarize monthly trends',
  'Which are the top regions?',
  'What was the highest sales month?',
  'Show sales distribution by category',
  'Compare department performance',
]

export default function QuestionSection() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [comparison, setComparison] = useState(null)
  const [comparing, setComparing] = useState(false)
  const [chatHistory, setChatHistory] = useState([])
  const chatEndRef = useRef(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatHistory])

  const handleAsk = async (q) => {
    const query = q || question
    if (!query.trim()) return
    try {
      setLoading(true); setError('')
      const res = await askQuestion(query)
      setAnswer(res.answer)
      setChatHistory((prev) => [...prev, { question: query, answer: res.answer }])
    } catch (err) {
      setError(err.response?.data?.error || 'Request failed')
    } finally { setLoading(false) }
  }

  const handleCompare = async () => {
    const query = question.trim()
    if (!query) return
    try {
      setComparing(true); setError('')
      const res = await compareModels(query)
      setComparison(res.comparisons)
    } catch (err) {
      setError(err.response?.data?.error || 'Comparison failed')
    } finally { setComparing(false) }
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">Ask a Question</h2>
      <div className="flex gap-3">
        <input type="text" value={question} onChange={(e) => setQuestion(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && !comparing && handleAsk()}
          placeholder="e.g., Which region has the highest sales?"
          disabled={comparing}
          className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100" />
        <button onClick={() => handleAsk()} disabled={loading || comparing || !question.trim()}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium">
          {loading ? 'Searching relevant data...' : 'Ask'}
        </button>
        <button onClick={handleCompare} disabled={comparing || loading || !question.trim()}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-sm whitespace-nowrap inline-flex items-center gap-2">
          {comparing && <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>}
          {comparing ? 'Comparing...' : 'Compare Models'}
        </button>
      </div>
      <div className="flex flex-wrap gap-2 mt-3">
        {SUGGESTIONS.map((s) => (
          <button key={s} onClick={() => { setQuestion(s); handleAsk(s) }}
            className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-xs hover:bg-blue-50 hover:text-blue-600 transition-colors border border-gray-200">
            {s}
          </button>
        ))}
      </div>
      {error && <div className="mt-3 bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded-lg text-sm">{error}</div>}
      {chatHistory.length > 0 && (
        <div className="mt-4 max-h-80 overflow-y-auto space-y-3 pr-1">
          {chatHistory.map((entry, i) => (
            <div key={i}>
              <div className="flex justify-end">
                <div className="bg-blue-100 text-blue-900 rounded-lg px-4 py-2 max-w-[80%] text-sm whitespace-pre-wrap leading-relaxed">
                  {entry.question}
                </div>
              </div>
              <div className="flex justify-start mt-2">
                <div className="bg-gray-100 text-gray-800 rounded-lg px-4 py-2 max-w-[80%] text-sm whitespace-pre-wrap leading-relaxed">
                  {entry.answer}
                </div>
              </div>
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>
      )}
      {answer && (
        <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-sm font-medium text-gray-500 mb-2">AI Answer:</p>
          <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{answer}</p>
        </div>
      )}
      {comparison && (
        <div className="mt-4">
          {(() => {
            const fastest = comparison.reduce((a, b) => a.response_time < b.response_time ? a : b)
            return (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {comparison.map((c) => (
                  <div key={c.model} className={`p-4 rounded-lg border ${c.model === fastest.model ? 'bg-green-50 border-green-300' : 'bg-gray-50 border-gray-200'}`}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-semibold text-gray-700">{c.model}</p>
                        {c.model === fastest.model && <span className="text-xs bg-green-200 text-green-800 px-2 py-0.5 rounded-full font-medium">Fastest</span>}
                      </div>
                      <span className="text-xs font-medium text-gray-500">{c.response_time}s</span>
                    </div>
                    <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">{c.response}</p>
                  </div>
                ))}
              </div>
            )
          })()}
        </div>
      )}
    </div>
  )
}
