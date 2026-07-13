import { useState, useRef } from 'react'
import { uploadCSV, getInsights } from '../../api/api'

export default function UploadSection({ onUploadSuccess }) {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [uploaded, setUploaded] = useState(false)
  const pipelineStarted = useRef(false)

  const handleUpload = async () => {
    if (!file) { setError('Select a CSV file'); return }
    try {
      setLoading(true); setError('')
      await uploadCSV(file)
      setUploaded(true)
      if (onUploadSuccess) onUploadSuccess(file.name)

      if (!pipelineStarted.current) {
        pipelineStarted.current = true
        getInsights().catch(() => {})
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Upload failed')
    } finally { setLoading(false) }
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">Upload CSV</h2>
      <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
        <input type="file" accept=".csv" onChange={(e) => { setFile(e.target.files[0]); setError(''); setUploaded(false) }}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer" />
        <button onClick={handleUpload} disabled={loading || !file}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium whitespace-nowrap">
          {loading ? 'Uploading...' : 'Upload'}
        </button>
      </div>
      {error && <div className="mt-3 bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded-lg text-sm">{error}</div>}
      {uploaded && <div className="mt-3 bg-green-50 border border-green-200 text-green-700 px-4 py-2 rounded-lg text-sm">Uploaded: <strong>{file.name}</strong></div>}
    </div>
  )
}
