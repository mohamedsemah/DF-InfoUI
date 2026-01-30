import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Download, ArrowLeft, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { getJobStatus, downloadFixedZip, downloadReportPdf } from '../services/api'
import { JobStatus } from '../types'
import { IssueViewer } from '../components/IssueViewer'

export function JobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<'perceivable' | 'operable' | 'understandable' | 'robust'>('perceivable')

  const { data: jobStatus, isLoading, error } = useQuery({
    queryKey: ['jobStatus', jobId],
    queryFn: () => getJobStatus(jobId!),
    refetchInterval: (data) => {
      if (data?.status === 'complete' || data?.status === 'error') {
        return false
      }
      return 2000 // Poll every 2 seconds
    },
    enabled: !!jobId
  })

  if (isLoading) {
    return (
      <div className="container">
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>⏳</div>
          <h2>Loading job status...</h2>
        </div>
      </div>
    )
  }

  if (error || !jobStatus) {
    return (
      <div className="container">
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>❌</div>
          <h2>Error loading job</h2>
          <p>Please try again or go back to upload a new file.</p>
          <button onClick={() => navigate('/')} style={{ marginTop: '1rem' }}>
            <ArrowLeft size={16} style={{ marginRight: '0.5rem' }} />
            Back to Upload
          </button>
        </div>
      </div>
    )
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'complete':
        return <CheckCircle size={20} style={{ color: '#2e7d32' }} />
      case 'error':
        return <XCircle size={20} style={{ color: '#d32f2f' }} />
      default:
        return <AlertCircle size={20} style={{ color: '#f57c00' }} />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'complete':
        return '#2e7d32'
      case 'error':
        return '#d32f2f'
      default:
        return '#f57c00'
    }
  }

  return (
    <div className="container">
      <div style={{ marginBottom: '2rem' }}>
        <button onClick={() => navigate('/')} style={{ marginBottom: '1rem' }}>
          <ArrowLeft size={16} style={{ marginRight: '0.5rem' }} />
          Back to Upload
        </button>
        
        <h1>Job Details</h1>
        <p style={{ color: '#666' }}>Job ID: {jobId}</p>
      </div>

      {/* Status Section */}
      <div style={{
        backgroundColor: 'white',
        border: '1px solid #ddd',
        borderRadius: '8px',
        padding: '1.5rem',
        marginBottom: '2rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
          {getStatusIcon(jobStatus.status)}
          <div>
            <h3 style={{ margin: 0, color: getStatusColor(jobStatus.status) }}>
              {jobStatus.status.charAt(0).toUpperCase() + jobStatus.status.slice(1)}
            </h3>
            <p style={{ margin: 0, color: '#666' }}>{jobStatus.message}</p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${jobStatus.progress}%` }}
          />
        </div>
        <p style={{ textAlign: 'center', marginTop: '0.5rem' }}>
          {jobStatus.progress}% Complete
        </p>

        {/* Summary */}
        {jobStatus.summary && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '1rem',
            marginTop: '1rem',
            padding: '1rem',
            backgroundColor: '#f5f5f5',
            borderRadius: '4px'
          }}>
            {jobStatus.summary.total_issues && (
              <div>
                <strong>Total Issues:</strong> {jobStatus.summary.total_issues}
              </div>
            )}
            {(jobStatus.summary.total_fixes !== undefined || jobStatus.summary.issues_fixed !== undefined) && (
              <div>
                <strong>Issues Fixed:</strong> {jobStatus.summary.total_fixes ?? jobStatus.summary.issues_fixed}
              </div>
            )}
            {jobStatus.summary.validation_passed !== undefined && (
              <div>
                <strong>Validation:</strong> {jobStatus.summary.validation_passed ? 'Passed' : 'Failed'}
              </div>
            )}
            {jobStatus.summary.remaining_issues !== undefined && (
              <div>
                <strong>Remaining Issues:</strong> {jobStatus.summary.remaining_issues}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Download Buttons */}
      {jobStatus.status === 'complete' && (
        <div className="download-buttons">
          <a
            href={downloadFixedZip(jobId!)}
            download={`fixed_${jobId}.zip`}
            className="download-button"
          >
            <Download size={16} style={{ marginRight: '0.5rem' }} />
            Download Fixed ZIP
          </a>
          <a
            href={downloadReportPdf(jobId!)}
            download={`report_${jobId}.pdf`}
            className="download-button"
          >
            <Download size={16} style={{ marginRight: '0.5rem' }} />
            Download PDF Report
          </a>
        </div>
      )}

      {/* Issues Viewer */}
      {jobStatus.status === 'complete' && (
        <IssueViewer jobId={jobId!} activeTab={activeTab} onTabChange={setActiveTab} />
      )}
    </div>
  )
}
