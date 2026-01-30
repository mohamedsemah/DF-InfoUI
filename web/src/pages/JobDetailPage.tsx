import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Download, ArrowLeft, CheckCircle, XCircle, AlertCircle, FileDown } from 'lucide-react'
import { getJobStatus, getJobReport, downloadFixedZip, downloadReportPdf } from '../services/api'
import { IssueViewer } from '../components/IssueViewer'
import { Layout } from '../components/Layout'

const POUR_COLORS = {
  perceivable: { bg: 'linear-gradient(145deg, #7f1d1d 0%, #991b1b 100%)', text: 'var(--pour-red)', label: 'Visual accessibility issues' },
  operable: { bg: 'linear-gradient(145deg, #9a3412 0%, #c2410c 100%)', text: 'var(--pour-orange)', label: 'Interaction and navigation issues' },
  understandable: { bg: 'linear-gradient(145deg, #1e3a8a 0%, #1d4ed8 100%)', text: 'var(--pour-blue)', label: 'Content clarity issues' },
  robust: { bg: 'linear-gradient(145deg, #14532d 0%, #166534 100%)', text: 'var(--pour-green)', label: 'Technical compliance issues' },
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
    enabled: !!jobId,
  })

  const { data: report } = useQuery({
    queryKey: ['jobReport', jobId],
    queryFn: () => getJobReport(jobId!),
    enabled: !!jobId && jobStatus?.status === 'complete',
  })

  if (isLoading) {
    return (
      <Layout showBack backLabel="Back to Upload" backTo="/upload">
        <div className="container" style={{ textAlign: 'center', padding: '4rem' }}>
          <div style={{ fontSize: '2rem', marginBottom: '1.25rem' }}>⏳</div>
          <h2 style={{ color: 'var(--text-primary)', fontWeight: 600, marginBottom: '0.5rem' }}>Loading job status...</h2>
          <p style={{ color: 'var(--text-muted)' }}>Analysis in progress</p>
        </div>
      </Layout>
    )
  }

  if (error || !jobStatus) {
    return (
      <Layout showBack backLabel="Back to Upload" backTo="/upload">
        <div className="container" style={{ textAlign: 'center', padding: '4rem' }}>
          <div style={{ fontSize: '2rem', marginBottom: '1.25rem' }}>❌</div>
          <h2 style={{ color: 'var(--text-primary)', fontWeight: 600, marginBottom: '0.5rem' }}>Error loading job</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>Please try again or go back to upload a new file.</p>
          <button onClick={() => navigate('/upload')} className="btn-secondary">
            <ArrowLeft size={18} strokeWidth={2} /> Back to Upload
          </button>
        </div>
      </Layout>
    )
  }

  const summary = jobStatus.summary || {}
  const totalIssues = summary.total_issues ?? 0
  const reportSummary = report?.summary || {}
  const pourCounts = {
    perceivable: reportSummary.issues_by_category?.perceivable ?? 0,
    operable: reportSummary.issues_by_category?.operable ?? 0,
    understandable: reportSummary.issues_by_category?.understandable ?? 0,
    robust: reportSummary.issues_by_category?.robust ?? 0,
  }
  const totalFromReport = report?.issues?.length ?? totalIssues
  const displayTotal = totalFromReport || totalIssues

  return (
    <Layout showBack backLabel="Back to Upload" backTo="/upload">
      <div className="container" style={{ paddingTop: '2rem' }}>
        {jobStatus.status === 'complete' ? (
          <>
            <p style={{ fontSize: '0.8125rem', fontWeight: 600, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--accent-blue)', marginBottom: '0.5rem', textAlign: 'center' }}>
              Assessment Complete
            </p>
            <h1 className="gradient-text" style={{ fontSize: 'clamp(1.75rem, 3.5vw, 2.25rem)', marginBottom: '0.5rem', textAlign: 'center', fontWeight: 700 }}>
              Analysis Results
            </h1>
            <h2 style={{ color: 'var(--text-secondary)', fontSize: '1.25rem', marginBottom: '2.5rem', textAlign: 'center', fontWeight: 500 }}>
              Accessibility Assessment Complete
            </h2>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '1.25rem',
                marginBottom: '2.5rem',
              }}
            >
              {(['perceivable', 'operable', 'understandable', 'robust'] as const).map((cat) => {
                const count = pourCounts[cat]
                const style = POUR_COLORS[cat]
                return (
                  <div
                    key={cat}
                    className="pour-card"
                    style={{
                      background: style.bg,
                      padding: '1.5rem',
                      color: 'white',
                      position: 'relative',
                      border: '1px solid rgba(255,255,255,0.08)',
                    }}
                  >
                    <div style={{ fontSize: '0.8125rem', marginBottom: '0.5rem', opacity: 0.9, fontWeight: 600, letterSpacing: '0.02em' }}>
                      {cat.charAt(0).toUpperCase() + cat.slice(1)}
                    </div>
                    <div style={{ fontSize: '0.75rem', marginBottom: '0.75rem', opacity: 0.85 }}>{style.label}</div>
                    <div style={{ fontSize: '2.25rem', fontWeight: 700, color: style.text, letterSpacing: '-0.02em' }}>{count}</div>
                    <div style={{ fontSize: '0.8125rem', color: style.text, fontWeight: 500 }}>Issues Found</div>
                  </div>
                )
              })}
            </div>

            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap', marginBottom: '2.5rem' }}>
              <Link to={`/job/${jobId}/report`} className="btn-white">
                <CheckCircle size={18} strokeWidth={2} /> View Detailed Report
              </Link>
              <a href={downloadFixedZip(jobId!)} download={`fixed_${jobId}.zip`} className="btn-secondary">
                <Download size={18} strokeWidth={2} /> Download Results
              </a>
              <a href={downloadReportPdf(jobId!)} download={`report_${jobId}.pdf`} className="btn-secondary">
                <FileDown size={18} strokeWidth={2} /> Export Fixes
              </a>
            </div>

            <div className="card-premium" style={{ padding: '2rem', textAlign: 'center', marginBottom: '2.5rem' }}>
              <CheckCircle size={52} color="var(--pour-green)" style={{ marginBottom: '1.25rem' }} strokeWidth={2} />
              <h3 style={{ color: 'var(--text-primary)', marginBottom: '0.75rem', fontSize: '1.375rem', fontWeight: 600 }}>
                Analysis Complete
              </h3>
              <p style={{ color: 'var(--text-secondary)', lineHeight: 1.7, margin: 0 }}>
                Brain Agent has completed the accessibility analysis. Found{' '}
                <strong style={{ color: 'var(--pour-red)', fontWeight: 700 }}>{displayTotal} total issues</strong>{' '}
                across all POUR categories. Review the detailed report for specific recommendations and automated fixes.
              </p>
            </div>

            <IssueViewer jobId={jobId!} activeTab={activeTab} onTabChange={setActiveTab} />
          </>
        ) : (
          <>
            <h1 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem', fontWeight: 700, letterSpacing: '-0.02em' }}>Job Details</h1>
            <p style={{ color: 'var(--text-muted)', marginBottom: '2rem', fontSize: '0.9375rem' }}>Job ID: {jobId}</p>

            <div className="card-premium" style={{ padding: '1.75rem', marginBottom: '2rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.25rem' }}>
                {jobStatus.status === 'error' ? (
                  <XCircle size={28} color="var(--pour-red)" strokeWidth={2} />
                ) : (
                  <AlertCircle size={28} color="var(--pour-orange)" strokeWidth={2} />
                )}
                <div>
                  <h3 style={{ margin: 0, color: 'var(--text-primary)', textTransform: 'capitalize', fontWeight: 600, fontSize: '1.125rem' }}>
                    {jobStatus.status}
                  </h3>
                  <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.9375rem' }}>{jobStatus.message}</p>
                </div>
              </div>
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${jobStatus.progress}%` }} />
              </div>
              <p style={{ textAlign: 'center', marginTop: '0.75rem', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                {jobStatus.progress}% Complete
              </p>
              {jobStatus.summary && (
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                    gap: '1rem',
                    marginTop: '1.25rem',
                    padding: '1.25rem',
                    backgroundColor: 'var(--bg-elevated)',
                    borderRadius: 12,
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  {jobStatus.summary.total_issues != null && (
                    <div>
                      <strong style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Total Issues:</strong>{' '}
                      {jobStatus.summary.total_issues}
                    </div>
                  )}
                  {(jobStatus.summary.total_fixes != null || jobStatus.summary.issues_fixed != null) && (
                    <div>
                      <strong style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Fixed:</strong>{' '}
                      {jobStatus.summary.total_fixes ?? jobStatus.summary.issues_fixed}
                    </div>
                  )}
                  {jobStatus.summary.remaining_issues != null && (
                    <div>
                      <strong style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Remaining:</strong>{' '}
                      {jobStatus.summary.remaining_issues}
                    </div>
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
