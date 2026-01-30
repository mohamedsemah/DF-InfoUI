import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Download, ArrowLeft, CheckCircle, XCircle, AlertCircle, FileDown } from 'lucide-react'
import { getJobStatus, getJobReport, downloadFixedZip, downloadReportPdf } from '../services/api'
import { IssueViewer } from '../components/IssueViewer'
import { Layout } from '../components/Layout'

const POUR_COLORS = {
  perceivable: { bg: 'linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%)', text: 'var(--pour-red)', label: 'Visual accessibility issues' },
  operable: { bg: 'linear-gradient(135deg, #9a3412 0%, #c2410c 100%)', text: 'var(--pour-orange)', label: 'Interaction and navigation issues' },
  understandable: { bg: 'linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 100%)', text: 'var(--pour-blue)', label: 'Content clarity issues' },
  robust: { bg: 'linear-gradient(135deg, #14532d 0%, #166534 100%)', text: 'var(--pour-green)', label: 'Technical compliance issues' }
} as const

export function JobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<'perceivable' | 'operable' | 'understandable' | 'robust'>('perceivable')

  const { data: jobStatus, isLoading, error } = useQuery({
    queryKey: ['jobStatus', jobId],
    queryFn: () => getJobStatus(jobId!),
    refetchInterval: (query) => {
      const data = query.state.data as { status?: string } | undefined
      if (data?.status === 'complete' || data?.status === 'error') return false
      return 2000
    },
    enabled: !!jobId
  })

  if (isLoading) {
    return (
      <Layout showBack backLabel="Back to Upload" backTo="/upload">
        <div className="container" style={{ textAlign: 'center', padding: '3rem' }}>
          <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>⏳</div>
          <h2 style={{ color: 'white' }}>Loading job status...</h2>
          <p style={{ color: 'var(--text-muted)' }}>Analysis in progress</p>
        </div>
      </Layout>
    )
  }

  if (error || !jobStatus) {
    return (
      <Layout showBack backLabel="Back to Upload" backTo="/upload">
        <div className="container" style={{ textAlign: 'center', padding: '3rem' }}>
          <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>❌</div>
          <h2 style={{ color: 'white' }}>Error loading job</h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>Please try again or go back to upload a new file.</p>
          <button onClick={() => navigate('/upload')} className="btn-secondary">
            <ArrowLeft size={16} /> Back to Upload
          </button>
        </div>
      </Layout>
    )
  }

  const summary = jobStatus.summary || {}
  const totalIssues = summary.total_issues ?? 0
  const fixedCount = summary.total_fixes ?? summary.issues_fixed ?? 0
  const { data: report } = useQuery({
    queryKey: ['jobReport', jobId],
    queryFn: () => getJobReport(jobId!),
    enabled: !!jobId && jobStatus.status === 'complete'
  })
  const reportSummary = report?.summary || {}
  const pourCounts = {
    perceivable: reportSummary.issues_by_category?.perceivable ?? 0,
    operable: reportSummary.issues_by_category?.operable ?? 0,
    understandable: reportSummary.issues_by_category?.understandable ?? 0,
    robust: reportSummary.issues_by_category?.robust ?? 0
  }
  const totalFromReport = (report?.issues?.length) ?? totalIssues
  const displayTotal = totalFromReport || totalIssues

  return (
    <Layout showBack backLabel="Back to Upload" backTo="/upload">
      <div className="container" style={{ paddingTop: '1.5rem' }}>
        {jobStatus.status === 'complete' ? (
          <>
            <h1 className="gradient-text" style={{ fontSize: 'clamp(1.5rem, 3vw, 2rem)', marginBottom: '0.25rem', textAlign: 'center' }}>
              Analysis Results
            </h1>
            <h2 style={{ color: 'white', fontSize: '1.35rem', marginBottom: '2rem', textAlign: 'center', fontWeight: 600 }}>
              Accessibility Assessment Complete
            </h2>

            {/* POUR summary cards */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '1rem',
              marginBottom: '2rem'
            }}>
              {(['perceivable', 'operable', 'understandable', 'robust'] as const).map(cat => {
                const count = pourCounts[cat] ?? 0
                const style = POUR_COLORS[cat]
                return (
                  <div
                    key={cat}
                    style={{
                      background: style.bg,
                      borderRadius: 12,
                      padding: '1.25rem',
                      color: 'white',
                      position: 'relative'
                    }}
                  >
                    <div style={{ fontSize: '0.85rem', marginBottom: '0.5rem', opacity: 0.9 }}>{cat.charAt(0).toUpperCase() + cat.slice(1)}</div>
                    <div style={{ fontSize: '0.8rem', marginBottom: '0.75rem', opacity: 0.9 }}>{style.label}</div>
                    <div style={{ fontSize: '2rem', fontWeight: 700, color: style.text }}>{count}</div>
                    <div style={{ fontSize: '0.85rem', color: style.text }}>Issues Found</div>
                  </div>
                )
              })}
            </div>

            {/* Action buttons */}
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap', marginBottom: '2rem' }}>
              <Link to={`/job/${jobId}/report`} className="btn-white">
                <CheckCircle size={18} /> View Detailed Report
              </Link>
              <a href={downloadFixedZip(jobId!)} download={`fixed_${jobId}.zip`} className="btn-secondary">
                <Download size={18} /> Download Results
              </a>
              <a href={downloadReportPdf(jobId!)} download={`report_${jobId}.pdf`} className="btn-secondary">
                <FileDown size={18} /> Export Fixes
              </a>
            </div>

            {/* Analysis complete summary */}
            <div style={{
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--border)',
              borderRadius: 12,
              padding: '2rem',
              textAlign: 'center',
              marginBottom: '2rem'
            }}>
              <CheckCircle size={48} color="var(--pour-green)" style={{ marginBottom: '1rem' }} />
              <h3 style={{ color: 'white', marginBottom: '0.5rem', fontSize: '1.25rem' }}>Analysis Complete</h3>
              <p style={{ color: 'var(--text-muted)', lineHeight: 1.6 }}>
                Brain Agent has completed the accessibility analysis.                 Found{' '}
                <strong style={{ color: 'var(--pour-red)' }}>{displayTotal} total issues</strong>{' '}
                across all POUR categories. Review the detailed report for specific recommendations and automated fixes.
              </p>
            </div>

            {/* Neuron Fixes section */}
            <IssueViewer jobId={jobId!} activeTab={activeTab} onTabChange={setActiveTab} />
          </>
        ) : (
          <>
            <div style={{ marginBottom: '2rem' }}>
              <h1 style={{ color: 'white', marginBottom: '0.5rem' }}>Job Details</h1>
              <p style={{ color: 'var(--text-muted)' }}>Job ID: {jobId}</p>
            </div>

            <div className="summary-card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
                {jobStatus.status === 'error' ? <XCircle size={24} color="var(--pour-red)" /> : <AlertCircle size={24} color="var(--pour-orange)" />}
                <div>
                  <h3 style={{ margin: 0, color: 'white', textTransform: 'capitalize' }}>{jobStatus.status}</h3>
                  <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.9rem' }}>{jobStatus.message}</p>
                </div>
              </div>
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${jobStatus.progress}%` }} />
              </div>
              <p style={{ textAlign: 'center', marginTop: '0.5rem', color: 'var(--text-muted)' }}>
                {jobStatus.progress}% Complete
              </p>
              {jobStatus.summary && (
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                  gap: '1rem',
                  marginTop: '1rem',
                  padding: '1rem',
                  backgroundColor: 'var(--bg-elevated)',
                  borderRadius: 8
                }}>
                  {jobStatus.summary.total_issues != null && (
                    <div><strong style={{ color: 'var(--text-muted)' }}>Total Issues:</strong> {jobStatus.summary.total_issues}</div>
                  )}
                  {(jobStatus.summary.total_fixes != null || jobStatus.summary.issues_fixed != null) && (
                    <div><strong style={{ color: 'var(--text-muted)' }}>Fixed:</strong> {jobStatus.summary.total_fixes ?? jobStatus.summary.issues_fixed}</div>
                  )}
                  {jobStatus.summary.remaining_issues != null && (
                    <div><strong style={{ color: 'var(--text-muted)' }}>Remaining:</strong> {jobStatus.summary.remaining_issues}</div>
                  )}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </Layout>
  )
}
