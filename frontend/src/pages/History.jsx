import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getAnalysisHistory, getUploadHistory } from '../api/api'

export default function History() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [uploads, setUploads] = useState([])
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetch = async () => {
      try {
        const [u, h] = await Promise.all([getUploadHistory(), getAnalysisHistory()])
        setUploads(u.uploads || [])
        setHistory(h.history || [])
      } catch { /* ignore */ }
      finally { setLoading(false) }
    }
    fetch()
  }, [])

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">History</h1>
            <p className="text-sm text-gray-500 mt-1">Your uploads and analysis activity</p>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600"><strong>{user?.name}</strong></span>
            <button onClick={() => navigate('/')}
              className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 text-sm font-medium">
              Dashboard
            </button>
            <button onClick={logout}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-sm font-medium">
              Logout
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-6 py-6">
        {loading ? <p className="text-gray-500">Loading...</p> : (
          <>
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">Upload History</h2>
              {uploads.length === 0 ? (
                <p className="text-gray-400 text-sm">No uploads yet</p>
              ) : (
                <div className="space-y-2">
                  {uploads.map((u) => (
                    <div key={u.id} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg border border-gray-200">
                      <span className="text-blue-600 font-medium text-sm">{u.filename}</span>
                      <span className="text-xs text-gray-400">{new Date(u.uploaded_at).toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">Analysis History</h2>
              {history.length === 0 ? (
                <p className="text-gray-400 text-sm">No analyses yet</p>
              ) : (
                <div className="space-y-4">
                  {history.map((item) => (
                    <div key={item.id} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                      <div className="flex justify-between mb-2">
                        <p className="text-sm font-medium text-gray-700">Q: {item.question}</p>
                        <span className="text-xs text-gray-400 ml-4 whitespace-nowrap">
                          {new Date(item.created_at).toLocaleString()}
                        </span>
                      </div>
                      {item.response && (
                        <p className="text-sm text-gray-600 mt-1 pl-4 border-l-2 border-blue-300">
                          A: {item.response.length > 200 ? item.response.substring(0, 200) + '...' : item.response}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
