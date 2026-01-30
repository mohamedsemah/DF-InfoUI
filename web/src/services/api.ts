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

/** Upload one or more files (ZIP or supported UI/source files). Backend accepts key "files". */
export const uploadFiles = async (files: File | File[]): Promise<{ job_id: string }> => {
  const list = Array.isArray(files) ? files : [files]
  const formData = new FormData()
  list.forEach((file) => formData.append('files', file))
  const response = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

/** @deprecated Use uploadFiles; kept for compatibility. */
export const uploadFile = uploadFiles

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
