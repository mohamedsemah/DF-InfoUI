import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronDown, ChevronRight, FileText, Code, CheckCircle } from 'lucide-react'
import { getJobReport } from '../services/api'

interface IssueViewerProps {
  jobId: string
  activeTab: 'perceivable' | 'operable' | 'understandable' | 'robust'
  onTabChange: (tab: 'perceivable' | 'operable' | 'understandable' | 'robust') => void
}

export function IssueViewer({ jobId, activeTab, onTabChange }: IssueViewerProps) {
  const [expandedIssues, setExpandedIssues] = useState<Set<string>>(new Set())

  // Fetch real data from API
  const { data: reportData, isLoading, error } = useQuery({
    queryKey: ['jobReport', jobId],
    queryFn: () => getJobReport(jobId),
    enabled: !!jobId
  })

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>⏳</div>
        <h3>Loading report data...</h3>
      </div>
    )
  }

  if (error || !reportData) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>❌</div>
        <h3>Failed to load report data</h3>
        <p>Please try refreshing the page.</p>
      </div>
    )
  }

  // Organize issues by category
  const issuesByCategory = {
    perceivable: reportData.issues?.filter((issue: any) => issue.category === 'perceivable') || [],
    operable: reportData.issues?.filter((issue: any) => issue.category === 'operable') || [],
    understandable: reportData.issues?.filter((issue: any) => issue.category === 'understandable') || [],
    robust: reportData.issues?.filter((issue: any) => issue.category === 'robust') || []
  }

  // Get fixes for the current category
  const currentCategoryFixes = reportData.fixes?.filter((fix: any) => {
    const issue = reportData.issues?.find((i: any) => i.id === fix.issue_id)
    return issue?.category === activeTab
  }) || []

  const tabs = [
    { key: 'perceivable', label: 'Perceivable', count: issuesByCategory.perceivable.length },
    { key: 'operable', label: 'Operable', count: issuesByCategory.operable.length },
    { key: 'understandable', label: 'Understandable', count: issuesByCategory.understandable.length },
    { key: 'robust', label: 'Robust', count: issuesByCategory.robust.length }
  ] as const

  const toggleIssue = (issueId: string) => {
    const newExpanded = new Set(expandedIssues)
    if (newExpanded.has(issueId)) {
      newExpanded.delete(issueId)
    } else {
      newExpanded.add(issueId)
    }
    setExpandedIssues(newExpanded)
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return '#d32f2f'
      case 'medium':
        return '#f57c00'
      case 'low':
        return '#1976d2'
      default:
        return '#666'
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high':
        return '🔴'
      case 'medium':
        return '🟡'
      case 'low':
        return '🔵'
      default:
        return '⚪'
    }
  }

  return (
    <div style={{ marginTop: '2rem' }}>
      <h2>Accessibility Issues</h2>
      
      {/* Tabs */}
      <div className="tab-container">
        {tabs.map(tab => (
          <div
            key={tab.key}
            className={`tab ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => onTabChange(tab.key)}
            style={{ cursor: 'pointer' }}
          >
            {tab.label} ({tab.count})
          </div>
        ))}
      </div>

      {/* Issues List */}
      <div>
        {issuesByCategory[activeTab].length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '2rem',
            color: '#666',
            backgroundColor: '#f5f5f5',
            borderRadius: '8px'
          }}>
            <CheckCircle size={48} style={{ color: '#2e7d32', marginBottom: '1rem' }} />
            <h3>No {activeTab} issues found!</h3>
            <p>Great job! Your code meets the {activeTab} accessibility guidelines.</p>
          </div>
        ) : (
          issuesByCategory[activeTab].map(issue => {
            // Find the corresponding fix for this issue
            const fix = currentCategoryFixes.find((f: any) => f.issue_id === issue.id)
            
            return (
            <div key={issue.id} className={`issue-card ${issue.severity}`}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  cursor: 'pointer'
                }}
                onClick={() => toggleIssue(issue.id)}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  {expandedIssues.has(issue.id) ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span>{getSeverityIcon(issue.severity)}</span>
                      <strong>{issue.description}</strong>
                      <span style={{
                        fontSize: '0.8rem',
                        color: getSeverityColor(issue.severity),
                        textTransform: 'uppercase'
                      }}>
                        {issue.severity}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.9rem', color: '#666', marginTop: '0.25rem' }}>
                      <FileText size={14} style={{ marginRight: '0.25rem' }} />
                      {issue.file_path} (lines {issue.line_start}-{issue.line_end})
                    </div>
                  </div>
                </div>
              </div>

              {expandedIssues.has(issue.id) && (
                <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid #eee' }}>
                  <div style={{ marginBottom: '1rem' }}>
                    <h4 style={{ margin: '0 0 0.5rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <Code size={16} />
                      Code Snippet
                    </h4>
                    <div className="code-snippet">
                      {issue.code_snippet}
                    </div>
                  </div>

                  {fix ? (
                    <>
                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: '1fr 1fr',
                        gap: '1rem',
                        marginTop: '1rem'
                      }}>
                        <div className="diff-section before">
                          <h4 style={{ margin: '0 0 0.5rem 0' }}>Before Fix</h4>
                          <div className="code-snippet">
                            {fix.before_code}
                          </div>
                        </div>
                        <div className="diff-section after">
                          <h4 style={{ margin: '0 0 0.5rem 0' }}>After Fix</h4>
                          <div className="code-snippet">
                            {fix.after_code}
                          </div>
                        </div>
                      </div>

                      <div style={{
                        marginTop: '1rem',
                        padding: '0.75rem',
                        backgroundColor: '#e8f5e8',
                        borderRadius: '4px',
                        fontSize: '0.9rem'
                      }}>
                        <strong>Fix Applied:</strong> {fix.applied ? 'Successfully applied' : 'Failed to apply'}
                        {fix.confidence && (
                          <span style={{ marginLeft: '1rem' }}>
                            <strong>Confidence:</strong> {(fix.confidence * 100).toFixed(1)}%
                          </span>
                        )}
                      </div>

                      {fix.diff && (
                        <div style={{
                          marginTop: '1rem',
                          padding: '0.75rem',
                          backgroundColor: '#f5f5f5',
                          borderRadius: '4px',
                          fontSize: '0.9rem'
                        }}>
                          <h4 style={{ margin: '0 0 0.5rem 0' }}>Diff</h4>
                          <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                            {fix.diff}
                          </pre>
                        </div>
                      )}
                    </>
                  ) : (
                    <div style={{
                      marginTop: '1rem',
                      padding: '0.75rem',
                      backgroundColor: '#fff3cd',
                      borderRadius: '4px',
                      fontSize: '0.9rem'
                    }}>
                      <strong>No fix available</strong> - This issue was detected but no fix could be generated.
                    </div>
                  )}
                </div>
              )}
            </div>
            )
          })
        )}
      </div>
    </div>
  )
}
