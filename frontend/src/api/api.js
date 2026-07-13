import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || ''

const client = axios.create({
  baseURL: `${BASE}/api`,
})


// =====================================================
// Request Interceptor
// =====================================================

client.interceptors.request.use((config) => {

  const token = localStorage.getItem('token')

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})


// =====================================================
// Response Interceptor
// =====================================================

client.interceptors.response.use(

  (res) => (
    'success' in res.data
      ? (res.data.data ?? res.data)
      : res.data
  ),

  (err) => {

    if (err.response?.status === 401) {

      localStorage.removeItem('token')

      window.location.href = '/login'
    }

    return Promise.reject(err)
  }
)


// =====================================================
// Auth APIs
// =====================================================

export const signupUser = (name, email, password) =>
  client.post('/auth/signup', {
    name,
    email,
    password,
  })

export const loginUser = (email, password) =>
  client.post('/auth/login', {
    email,
    password,
  })

export const getProfile = async (token) => {

  const res = await axios.get(
    `${BASE}/api/auth/me`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  )

  return res.data.data ?? res.data
}


// =====================================================
// Upload API
// =====================================================

export const uploadCSV = (file) => {

  const fd = new FormData()

  fd.append('file', file)

  return client.post('/uploads', fd, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}


// =====================================================
// Analysis APIs
// =====================================================

export const getAnalysis = (
  filepath,
  mode = 'executive_summary'
) =>
  client.post(
    '/analysis/analyze',
    {
      filepath,
      mode,
    },
    {
      headers: {
        'Content-Type': 'application/json',
      },
    }
  )


export const getInsights = (
  filepath,
  mode = 'executive_summary'
) =>
  client.post(
    '/analysis/insights',
    {
      filepath,
      mode,
    },
    {
      headers: {
        'Content-Type': 'application/json',
      },
    }
  )


export const askQuestion = (
  question,
  filepath,
  mode = 'executive_summary'
) =>
  client.post(
    '/analysis/ask',
    {
      question,
      filepath,
      mode,
    },
    {
      headers: {
        'Content-Type': 'application/json',
      },
    }
  )


// =====================================================
// History APIs
// =====================================================

export const getAnalysisHistory = () =>
  client.get('/history/analysis')

export const getUploadHistory = () =>
  client.get('/history/uploads')


// =====================================================
// Data Quality APIs
// =====================================================

export const getDataQuality = (filepath) =>
  client.post(
    '/analysis/quality',
    {
      filepath,
    },
    {
      headers: {
        'Content-Type': 'application/json',
      },
    }
  )


export const getDataProfile = (filepath) =>
  client.post(
    '/analysis/profile',
    {
      filepath,
    },
    {
      headers: {
        'Content-Type': 'application/json',
      },
    }
  )


export const getRecommendations = (
  filepath,
  mode = 'executive_summary'
) =>
  client.post(
    '/analysis/recommend',
    {
      filepath,
      mode,
    },
    {
      headers: {
        'Content-Type': 'application/json',
      },
    }
  )


// =====================================================
// Model APIs
// =====================================================

export const getModelInfo = () =>
  client.get('/analysis/model')

export const setModel = (model) =>
  client.post(
    '/analysis/model',
    { model },
    {
      headers: {
        'Content-Type': 'application/json',
      },
    }
  )


export const getPipelineStatus = () =>
  client.get('/analysis/status')

export const compareModels = (question) =>
  client.post(
    '/analysis/compare-models',
    { question },
    {
      headers: {
        'Content-Type': 'application/json',
      },
    }
  )