import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

function extractErrorMessage(error) {
  if (error.response && error.response.data) {
    const detail = error.response.data.detail
    if (typeof detail === 'string') {
      return detail
    }
    if (Array.isArray(detail) && detail.length > 0) {
      return detail.map((item) => item.msg).join(' ')
    }
  }
  if (error.message) {
    return error.message
  }
  return 'An unexpected error occurred. Please try again.'
}

export async function ingestNote(title, content) {
  try {
    const response = await apiClient.post('/ingest', {
      source_type: 'note',
      title,
      content,
    })
    return response.data
  } catch (error) {
    throw new Error(extractErrorMessage(error))
  }
}

export async function ingestUrl(url) {
  try {
    const response = await apiClient.post('/ingest', {
      source_type: 'url',
      url,
    })
    return response.data
  } catch (error) {
    throw new Error(extractErrorMessage(error))
  }
}

export async function fetchItems() {
  try {
    const response = await apiClient.get('/items')
    return response.data
  } catch (error) {
    throw new Error(extractErrorMessage(error))
  }
}

export async function askQuestion(question, topK = 3) {
  try {
    const response = await apiClient.post('/query', {
      question,
      top_k: topK,
    })
    return response.data
  } catch (error) {
    throw new Error(extractErrorMessage(error))
  }
}
