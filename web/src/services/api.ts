import axios from 'axios'
import { JobStatus } from '../types'

// Use VITE_API_URL in production (e.g. http://localhost:8000) so uploads/downloads work
const API_BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL.replace(/\/$/, '')}/api`
  : '/api'

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
})

export const uploadFile = async (file: File): Promise<{ job_id: string }> => {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  
  return response.data
}

export const getJobStatus = async (jobId: string): Promise<JobStatus> => {
  const response = await api.get(`/status/${jobId}`)
  return response.data
}

export const downloadFixedZip = (jobId: string): string => {
  return `${API_BASE_URL}/download/${jobId}/fixed.zip`
}

export const downloadReportPdf = (jobId: string): string => {
  return `${API_BASE_URL}/download/${jobId}/report.pdf`
}

export const getJobReport = async (jobId: string): Promise<any> => {
  const response = await api.get(`/report/${jobId}`)
  return response.data
}
