import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'
import UploadSection from '../components/upload/UploadSection'
import KPICards from '../components/analysis/KPICards'
import ChartDisplay from '../components/charts/ChartDisplay'
import QuestionSection from '../components/analysis/QuestionSection'
import PromptPlayground from '../components/prompt/PromptPlayground'
import AgentWorkflow from '../components/workflow/AgentWorkflow'
import {
  getInsights, getDataQuality, getDataProfile,
  getRecommendations, getModelInfo, setModel,
  getPipelineStatus
} from '../api/api'

const NAV_ITEMS = [
  { key: 'upload', label: 'Upload', icon: '📁' },
  { key: 'profiling', label: 'Profiling', icon: '📋' },
  { key: 'kpis', label: 'KPIs', icon: '📊' },
  { key: 'insights', label: 'AI Insights', icon: '🧠' },
  { key: 'qa', label: 'AI Q&A', icon: '💬' },
  { key: 'quality', label: 'Data Quality', icon: '✅' },
  { key: 'recommend', label: 'Recommendations', icon: '🎯' },
  { key: 'playground', label: 'Prompt Playground', icon: '🎮' },
  { key: 'workflow', label: 'Agent Workflow', icon: '🔄' },
  { key: 'architecture', label: 'Architecture', icon: '🏗️' },
]

export default function Dashboard() {
  const { user, logout } = useAuth()
  const [page, setPage] = useState('upload')
  const [uploaded, setUploaded] = useState(false)
  const [fileName, setFileName] = useState('')
  const [kpis, setKpis] = useState(null)
  const [insights, setInsights] = useState('')
  const [charts, setCharts] = useState(null)
  const [profile, setProfile] = useState(null)
  const [quality, setQuality] = useState(null)
  const [recommendation, setRecommendation] = useState(null)
  const [performance, setPerformance] = useState(null)
  const [model, setModelState] = useState('tinyllama')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [exporting, setExporting] = useState(false)
  const chartRef = useRef(null)
  const archRef = useRef(null)

  const pageIdx = NAV_ITEMS.findIndex(i => i.key === page)
  const prevPage = pageIdx > 0 ? NAV_ITEMS[pageIdx - 1].key : null
  const nextPage = pageIdx < NAV_ITEMS.length - 1 ? NAV_ITEMS[pageIdx + 1].key : null

  const handleGenerate = async () => {
    try {
      setLoading(true); setError('')
      const data = await getInsights()
      setKpis(data.kpis); setInsights(data.insights); setCharts(data.charts)
      setPerformance(data.performance)
      setProfile(data.profile)
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to generate insights')
    } finally { setLoading(false) }
  }

  const handleQuality = async () => {
    try {
      setLoading(true); setError('')
      const data = await getDataQuality()
      setQuality(data)
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to check quality')
    } finally { setLoading(false) }
  }

  const handleRecommend = async () => {
    try {
      setLoading(true); setError('')
      const data = await getRecommendations()
      setRecommendation(data)
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to get recommendations')
    } finally { setLoading(false) }
  }

  const handleModelChange = async (m) => {
    setModelState(m)
    try {
      await setModel(m)
    } catch { /* ignore */ }
  }

  const handleExportPDF = async () => {
    try {
      setExporting(true)
      const doc = new jsPDF()
      const pw = doc.internal.pageSize.getWidth()
      const m = 20
      let y = m

      doc.setFontSize(22)
      doc.setFont(undefined, 'bold')
      doc.text('AI Data Analyst - Report', m, y)
      y += 12

      doc.setFontSize(10)
      doc.setFont(undefined, 'normal')
      doc.text(`Generated: ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })}`, m, y)
      y += 7

      if (fileName) {
        doc.text(`Dataset: ${fileName}`, m, y)
        y += 7
      }

      y += 3
      doc.setDrawColor(200, 200, 200)
      doc.line(m, y, pw - m, y)
      y += 12

      const sectionBreak = 10
      const lineHeight = 6
      const pageBottom = 275
      const checkPage = () => { if (y > pageBottom) { doc.addPage(); y = m } }
      const maxContentLines = 300

      if (kpis) {
        checkPage()
        doc.setFontSize(16)
        doc.setFont(undefined, 'bold')
        doc.text('Key Performance Indicators', m, y)
        y += 10
        doc.setFontSize(11)
        doc.setFont(undefined, 'normal')
        Object.entries(kpis).forEach(([key, value]) => {
          checkPage()
          doc.text(`\u2022 ${key}: ${value}`, m, y)
          y += lineHeight
        })
        y += sectionBreak
      }

      if (insights) {
        checkPage()
        doc.setFontSize(16)
        doc.setFont(undefined, 'bold')
        doc.text('AI Insights', m, y)
        y += 10
        doc.setFontSize(11)
        doc.setFont(undefined, 'normal')
        const insightLines = doc.splitTextToSize(insights, pw - m * 2 - 5)
        const truncated = insightLines.length > maxContentLines
        const toRender = truncated ? insightLines.slice(0, maxContentLines) : insightLines
        toRender.forEach(line => {
          checkPage()
          doc.text(line, m, y)
          y += lineHeight
        })
        if (truncated) {
          checkPage()
          doc.text('... [insights truncated]', m, y)
          y += lineHeight
        }
        y += sectionBreak
      }

      if (recommendation?.text) {
        checkPage()
        doc.setFontSize(16)
        doc.setFont(undefined, 'bold')
        doc.text('AI Recommendations', m, y)
        y += 10
        doc.setFontSize(11)
        doc.setFont(undefined, 'normal')
        const recLines = doc.splitTextToSize(recommendation.text, pw - m * 2 - 5)
        const truncated = recLines.length > maxContentLines
        const toRender = truncated ? recLines.slice(0, maxContentLines) : recLines
        toRender.forEach(line => {
          checkPage()
          doc.text(line, m, y)
          y += lineHeight
        })
        if (truncated) {
          checkPage()
          doc.text('... [recommendations truncated]', m, y)
          y += lineHeight
        }
        y += sectionBreak
      }

      const chartEntries = charts ? Object.entries(charts).filter(([, url]) => url) : []
      if (chartEntries.length > 0 && chartRef.current) {
        const chartImgs = chartRef.current.querySelectorAll('img')
        if (chartImgs.length > 0) {
          await Promise.all(Array.from(chartImgs).map(img =>
            img.complete && img.naturalWidth > 0
              ? Promise.resolve()
              : new Promise(resolve => { img.onload = resolve; img.onerror = resolve })
          ))

          checkPage()
          doc.setFontSize(16)
          doc.setFont(undefined, 'bold')
          doc.text('Charts', m, y)
          y += 10

          for (const img of chartImgs) {
            try {
              const canvas = await html2canvas(img, { useCORS: true, scale: 2, logging: false })
              const imgData = canvas.toDataURL('image/png')
              const maxW = pw - m * 2
              const maxH = 160
              const ratio = canvas.width / canvas.height
              let w = maxW
              let h = w / ratio
              if (h > maxH) { h = maxH; w = h * ratio }

              if (y + h + 15 > 275) { doc.addPage(); y = m + sectionBreak }
              doc.addImage(imgData, 'PNG', m + (maxW - w) / 2, y, w, h)
              y += h + 10
            } catch { /* skip failed chart */ }
          }
        }
      }

      if (archRef.current) {
        try {
          const archCanvas = await html2canvas(archRef.current, { useCORS: true, scale: 2, logging: false })
          const archImgData = archCanvas.toDataURL('image/png')
          const archMaxW = pw - m * 2
          const archRatio = archCanvas.width / archCanvas.height
          let archW = archMaxW
          let archH = archW / archRatio
          if (archH > 220) { archH = 220; archW = archH * archRatio }

          if (y + archH + 15 > 275) { doc.addPage(); y = m + sectionBreak }
          checkPage()
          doc.setFontSize(16)
          doc.setFont(undefined, 'bold')
          doc.text('AI Architecture', m, y)
          y += 10
          doc.addImage(archImgData, 'PNG', m + (archMaxW - archW) / 2, y, archW, archH)
          y += archH + 10
        } catch { /* skip architecture capture */ }
      }

      doc.save('ai-data-analyst-report.pdf')
    } catch (err) {
      setError('Failed to export PDF: ' + (err.message || 'Unknown error'))
    } finally {
      setExporting(false)
    }
  }

  useEffect(() => {
    (async () => {
      try {
        const data = await getModelInfo()
        setModelState(data.model)
      } catch { /* ignore */ }
    })()
  }, [])

  const renderPage = () => {
    switch (page) {
      case 'upload':
        return (
          <UploadSection onUploadSuccess={(name) => { setUploaded(true); setFileName(name); setError(''); setPage('profiling') }} />
        )
      case 'profiling':
        return (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Data Profiling</h2>
            {!profile ? (
              <div className="text-center py-8">
                <p className="text-gray-500 mb-4">Generate insights first to see data profiling</p>
                <button onClick={handleGenerate} disabled={loading}
                  className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium">
                  {loading ? 'Generating...' : 'Generate AI Insights'}
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <div className="bg-gray-50 p-4 rounded-lg"><span className="text-sm text-gray-500">Rows</span><p className="text-xl font-bold">{profile.rows}</p></div>
                  <div className="bg-gray-50 p-4 rounded-lg"><span className="text-sm text-gray-500">Columns</span><p className="text-xl font-bold">{profile.columns}</p></div>
                  <div className="bg-gray-50 p-4 rounded-lg"><span className="text-sm text-gray-500">Duplicates</span><p className="text-xl font-bold">{profile.duplicate_rows}</p></div>
                  <div className="bg-gray-50 p-4 rounded-lg"><span className="text-sm text-gray-500">Quality Score</span><p className="text-xl font-bold">{profile.quality_score ?? 'N/A'}%</p></div>
                </div>
                {profile.column_types && (
                  <div>
                    <h3 className="font-semibold text-gray-700 mb-2">Column Types</h3>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                      {Object.entries(profile.column_types).map(([col, t]) => (
                        <div key={col} className="bg-gray-50 px-3 py-2 rounded text-sm"><span className="font-medium">{col}:</span> <span className="text-gray-500">{t}</span></div>
                      ))}
                    </div>
                  </div>
                )}
                {profile.missing_pct && Object.keys(profile.missing_pct).length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-700 mb-2">Missing Values</h3>
                    {Object.entries(profile.missing_pct).map(([col, pct]) => (
                      <div key={col} className="flex items-center gap-2 mb-1">
                        <span className="text-sm w-40 truncate">{col}</span>
                        <div className="flex-1 bg-gray-200 rounded-full h-2"><div className="bg-red-400 h-2 rounded-full" style={{ width: `${Math.min(pct, 100)}%` }} /></div>
                        <span className="text-sm text-gray-500 w-12 text-right">{pct}%</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )
      case 'kpis':
        return <KPICards kpis={kpis} loading={loading} />
      case 'insights':
        return (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">AI Insights</h2>
            {loading && !insights ? (
              <div className="space-y-4">
                <div className="h-40 bg-gray-200 rounded-lg animate-pulse" />
                <ChartDisplay charts={charts} loading={loading} />
              </div>
            ) : !insights ? (
              <div className="text-center py-8">
                <p className="text-gray-500 mb-4">Generate insights first</p>
                <button onClick={handleGenerate} disabled={loading}
                  className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium">
                  {loading ? 'Generating...' : 'Generate AI Insights'}
                </button>
              </div>
            ) : (
              <>
                <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{insights}</p>
                </div>
                <ChartDisplay charts={charts} loading={loading} />
              </>
            )}
          </div>
        )
      case 'qa':
        return <QuestionSection />
      case 'quality':
        return (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Data Quality Dashboard</h2>
            {!quality ? (
              <div className="text-center py-8">
                <p className="text-gray-500 mb-4">Run quality check on your data</p>
                <button onClick={handleQuality} disabled={loading}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium">
                  {loading ? 'Checking...' : 'Run Quality Check'}
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center gap-4 mb-4">
                  <div className="text-4xl font-bold" style={{ color: quality.quality_score >= 80 ? '#22c55e' : quality.quality_score >= 50 ? '#eab308' : '#ef4444' }}>{quality.quality_score}%</div>
                  <div><p className="text-sm font-medium text-gray-500">Data Quality Score</p><p className="text-sm text-gray-400">{quality.total_rows} rows × {quality.total_columns} columns</p></div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="bg-gray-50 p-4 rounded-lg border">
                    <p className="text-sm text-gray-500">Duplicate Rows</p>
                    <p className="text-xl font-bold">{quality.duplicate_rows}</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg border">
                    <p className="text-sm text-gray-500">Columns with Missing</p>
                    <p className="text-xl font-bold">{Object.keys(quality.missing_values || {}).length}</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg border">
                    <p className="text-sm text-gray-500">Columns with Outliers</p>
                    <p className="text-xl font-bold">{Object.keys(quality.outliers || {}).length}</p>
                  </div>
                </div>
                {quality.missing_pct && Object.keys(quality.missing_pct).length > 0 && (
                  <div><h3 className="font-semibold text-gray-700 mb-2">Missing Values</h3>
                    {Object.entries(quality.missing_pct).map(([col, pct]) => (
                      <div key={col} className="flex items-center gap-2 mb-1">
                        <span className="text-sm w-40 truncate">{col}</span>
                        <div className="flex-1 bg-gray-200 rounded-full h-2"><div className="bg-yellow-400 h-2 rounded-full" style={{ width: `${Math.min(pct, 100)}%` }} /></div>
                        <span className="text-sm text-gray-500 w-12 text-right">{pct}%</span>
                      </div>
                    ))}
                  </div>
                )}
                {quality.outliers && Object.keys(quality.outliers).length > 0 && (
                  <div><h3 className="font-semibold text-gray-700 mb-2">Outliers Detected</h3>
                    {Object.entries(quality.outliers).map(([col, count]) => (
                      <div key={col} className="flex items-center gap-2 mb-1">
                        <span className="text-sm w-40 truncate">{col}</span>
                        <span className="text-sm text-orange-600 font-medium">{count} outlier(s)</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )
      case 'recommend':
        return (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">AI Recommendations</h2>
            {!recommendation ? (
              <div className="text-center py-8">
                <p className="text-gray-500 mb-4">Get AI-powered business recommendations</p>
                <button onClick={handleRecommend} disabled={loading}
                  className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 font-medium">
                  {loading ? 'Thinking...' : 'Get Recommendations'}
                </button>
              </div>
            ) : (
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{recommendation.text}</p>
              </div>
            )}
          </div>
        )
      case 'playground':
        return <PromptPlayground />
      case 'workflow':
        return <AgentWorkflow />
      case 'architecture':
        return (
          <div ref={archRef} className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">AI Architecture</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { title: 'Local LLM Processing', desc: 'Uses Ollama with tinyllama/phi3 for lightweight on-device inference. No external API calls needed.', icon: '⚡' },
                { title: 'SLM vs LLM', desc: 'Small Language Models (TinyLlama 1.1B, Phi-3 3.8B) for fast inference vs Large Language Models for complex reasoning. Balance speed vs depth.', icon: '⚖️' },
                { title: 'Prompt Orchestration', desc: 'System prompts are dynamically constructed per agent role. Modes control tone, verbosity, and factual strictness.', icon: '🎛️' },
                { title: 'Modular AI Agents', desc: 'Profiling, Insight, QA, Recommendation, and Chart agents operate independently with clear inputs/outputs.', icon: '🧩' },
                { title: 'Lightweight Retrieval', desc: 'Keyword-based row retrieval from uploaded CSV data. No vector DB required.', icon: '🔍' },
                { title: 'JWT Security', desc: 'All API endpoints protected with JWT Bearer token authentication. Token expiry and refresh supported.', icon: '🔒' },
                { title: 'Scalability', desc: 'Stateless API design. Add more Ollama instances or upgrade to larger models. Horizontally scalable.', icon: '📈' },
                { title: 'Docker Support', desc: 'Frontend + Backend containerized. Single docker-compose up to run. Multi-stage builds.', icon: '🐳' },
              ].map((item) => (
                <div key={item.title} className="bg-gray-50 rounded-lg p-4 border border-gray-200 hover:shadow-md transition-shadow">
                  <div className="text-2xl mb-2">{item.icon}</div>
                  <h3 className="font-semibold text-gray-800 mb-1">{item.title}</h3>
                  <p className="text-sm text-gray-600">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>
        )
      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 flex">
      {/* Sidebar */}
      <aside className="w-56 bg-white border-r border-gray-200 flex flex-col shrink-0">
        <div className="p-4 border-b border-gray-200">
          <h1 className="text-lg font-bold text-gray-800">AI Data Analyst</h1>
          <p className="text-xs text-gray-400 mt-1">v2.0</p>
        </div>
        <nav className="flex-1 overflow-y-auto p-2 space-y-1">
          {NAV_ITEMS.map((item) => (
            <button key={item.key} onClick={() => setPage(item.key)}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-colors ${page === item.key ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'}`}>
              <span className="mr-2">{item.icon}</span>{item.label}
            </button>
          ))}
        </nav>
        {/* Model Selector */}
        <div className="p-3 border-t border-gray-200">
          <label className="text-xs text-gray-400 block mb-1">Model</label>
          <select value={model} onChange={(e) => handleModelChange(e.target.value)}
            className="w-full text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500">
            <option value="tinyllama">tinyllama ⚡ Fast</option>
            <option value="phi3:mini">phi3 🎯 Quality</option>
            <option value="qwen2.5-coder:3b">Qwen2.5-Coder 3B 🧠</option>
          </select>
        </div>
        {/* Performance Metrics */}
        {performance && (
          <div className="p-3 border-t border-gray-200 bg-gray-50">
            <p className="text-xs text-gray-400 mb-1">Performance</p>
            <p className="text-xs text-gray-600">Response: {performance.total_duration}s</p>
            <p className="text-xs text-gray-600">Rows: {performance.rows_processed}</p>
            <p className="text-xs text-gray-600">Mode: {performance.lightweight ? '⚡ Lightweight' : '🎯 Full'}</p>
          </div>
        )}
        {/* User */}
        <div className="p-3 border-t border-gray-200 flex items-center justify-between">
          <span className="text-xs text-gray-600 truncate">{user?.name}</span>
          <button onClick={logout} className="text-xs text-red-500 hover:text-red-700">Logout</button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        {/* Top Bar */}
        <header className="bg-white shadow-sm border-b border-gray-200 px-6 py-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-800">{NAV_ITEMS.find(i => i.key === page)?.label}</h2>
          <div className="flex items-center gap-3">
            {uploaded && page !== 'upload' && <span className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded">CSV loaded</span>}
            {model && <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded">{model}</span>}
            {uploaded && (kpis || insights || recommendation) && (
              <button onClick={handleExportPDF} disabled={exporting}
                className="text-xs bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 disabled:opacity-50">
                {exporting ? 'Exporting...' : 'Export PDF'}
              </button>
            )}
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {page !== 'upload' && !uploaded && (
            <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-lg mb-6 text-sm">
              No CSV uploaded. Go to <button onClick={() => setPage('upload')} className="underline font-medium">Upload</button> first.
            </div>
          )}
          {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">{error}</div>}
          {renderPage()}
          {/* Navigation */}
          <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200">
            <button disabled={!prevPage} onClick={() => setPage(prevPage)}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-30 disabled:cursor-not-allowed text-sm font-medium">
              ← {prevPage ? NAV_ITEMS.find(i => i.key === prevPage)?.label : ''}
            </button>
            <span className="text-xs text-gray-400">{pageIdx + 1} / {NAV_ITEMS.length}</span>
            <button disabled={!nextPage} onClick={() => setPage(nextPage)}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-30 disabled:cursor-not-allowed text-sm font-medium">
              {nextPage ? NAV_ITEMS.find(i => i.key === nextPage)?.label : ''} →
            </button>
          </div>
        </div>
        {charts && (
          <div ref={chartRef} style={{ position: 'absolute', left: '-9999px', top: 0, zIndex: -1 }}>
            {Object.entries(charts).filter(([, url]) => url).map(([key, url]) => (
              <img key={key} src={`http://localhost:5000${url}`} crossOrigin="anonymous" alt="" />
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
