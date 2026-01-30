import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronDown, ChevronRight, FileText, CheckCircle, X, ExternalLink, Bot, AlertTriangle } from 'lucide-react'
import { getJobReport } from '../services/api'

interface IssueViewerProps {
  jobId: string
  activeTab: 'perceivable' | 'operable' | 'understandable' | 'robust'
  onTabChange: (tab: 'perceivable' | 'operable' | 'understandable' | 'robust') => void
}

const POUR_ICONS = {
  perceivable: '👁',
  operable: '👆',
  understandable: '📄',
  robust: '✓'
} as const

function wcagLabel(ruleId: string | undefined, category: string): string {
  if (ruleId) return `WCAG 2.1 Success Criterion ${ruleId}`
  const map: Record<string, string> = {
    perceivable: '1.1.1 (Non-text Content)',
    operable: '2.1.1 (Keyboard)',
    understandable: '3.1.1 (Language of Page)',
    robust: '4.1.2 (Name, Role, Value)'
  }
  return `WCAG 2.1 Success Criterion ${map[category] || 'N/A'}`
}

export function IssueViewer({ jobId, activeTab, onTabChange }: IssueViewerProps) {
  const [expandedIssues, setExpandedIssues] = useState<Set<string>>(new Set())
  const [dismissedIds, setDismissedIds] = useState<Set<string>>(new Set())
  const [appliedIds, setAppliedIds] = useState<Set<string>>(new Set())

  const { data: reportData, isLoading, error } = useQuery({
    queryKey: ['jobReport', jobId],
    queryFn: () => getJobReport(jobId),
    enabled: !!jobId
  })

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        <p style={{ color: 'var(--text-muted)' }}>Loading fixes...</p>
      </div>
    )
  }

  if (error || !reportData) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        <p style={{ color: 'var(--text-muted)' }}>Failed to load report data.</p>
      </div>
    )
  }

  const issuesByCategory = {
    perceivable: reportData.issues?.filter((i: { category: string }) => i.category === 'perceivable') || [],
    operable: reportData.issues?.filter((i: { category: string }) => i.category === 'operable') || [],
    understandable: reportData.issues?.filter((i: { category: string }) => i.category === 'understandable') || [],
    robust: reportData.issues?.filter((i: { category: string }) => i.category === 'robust') || []
  }

  const currentCategoryFixes = reportData.fixes?.filter((fix: { issue_id: string }) => {
    const issue = reportData.issues?.find((i: { id: string }) => i.id === fix.issue_id)
    return issue?.category === activeTab
  }) || []

  const tabs = [
    { key: 'perceivable' as const, label: 'Perceivable', count: issuesByCategory.perceivable.length, icon: POUR_ICONS.perceivable },
    { key: 'operable' as const, label: 'Operable', count: issuesByCategory.operable.length, icon: POUR_ICONS.operable },
    { key: 'understandable' as const, label: 'Understandable', count: issuesByCategory.understandable.length, icon: POUR_ICONS.understandable },
    { key: 'robust' as const, label: 'Robust', count: issuesByCategory.robust.length, icon: POUR_ICONS.robust }
  ]

  const toggleIssue = (issueId: string) => {
    setExpandedIssues(prev => {
      const next = new Set(prev)
      if (next.has(issueId)) next.delete(issueId)
      else next.add(issueId)
      return next
    })
  }

  const handleDismiss = (issueId: string) => {
    setDismissedIds(prev => new Set(prev).add(issueId))
  }

  const handleApplyFix = (issueId: string) => {
    setAppliedIds(prev => new Set(prev).add(issueId))
  }

  const getSeverityTag = (severity: string) => {
    const s = (severity || 'medium').toLowerCase()
    if (s === 'high' || s === 'critical') return { label: 'HIGH SEVERITY', class: 'high' }
    if (s === 'medium') return { label: 'MEDIUM SEVERITY', class: 'medium' }
    return { label: 'LOW SEVERITY', class: 'low' }
  }

  const currentIssues = issuesByCategory[activeTab].filter((i: { id: string }) => !dismissedIds.has(i.id))

  return (
    <div style={{ marginTop: '2rem' }}>
      <h2 className="gradient-text" style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>
        Neuron Fixes
      </h2>
      <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem', fontSize: '0.95rem' }}>
        AI-generated accessibility fixes for your code
      </p>

      <div className="report-tabs" style={{ marginBottom: '1.5rem' }}>
        {tabs.map(tab => (
          <button
            key={tab.key}
            className={`report-tab ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => onTabChange(tab.key)}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <span>{tab.icon}</span>
            {tab.label}
            <span style={{ fontSize: '0.85rem', opacity: 0.9 }}>{tab.count}</span>
          </button>
        ))}
      </div>

      {currentIssues.length === 0 ? (
        <div className="summary-card" style={{ padding: '2rem', textAlign: 'center' }}>
          <CheckCircle size={48} color="var(--pour-green)" style={{ marginBottom: '1rem' }} />
          <h3 style={{ color: 'white', marginBottom: '0.5rem' }}>No {activeTab} issues to fix</h3>
          <p style={{ color: 'var(--text-muted)' }}>All issues in this category have been addressed or dismissed.</p>
        </div>
      ) : (
        currentIssues.map((issue: { id: string; file_path: string; description: string; severity: string; rule_id?: string; code_snippet?: string; category: string }) => {
          const fix = currentCategoryFixes.find((f: { issue_id: string }) => f.issue_id === issue.id)
          const isExpanded = expandedIssues.has(issue.id)
          const applied = appliedIds.has(issue.id)
          const severityTag = getSeverityTag(issue.severity)

          return (
            <div
              key={issue.id}
              className="summary-card"
              style={{
                padding: '1.5rem',
                marginBottom: '1rem',
                borderLeft: '4px solid var(--border)',
                borderLeftColor: issue.severity === 'high' ? 'var(--pour-red)' : issue.severity === 'medium' ? 'var(--pour-orange)' : 'var(--pour-blue)'
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '0.75rem',
                  cursor: 'pointer'
                }}
                onClick={() => toggleIssue(issue.id)}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
                    {isExpanded ? <ChevronDown size={18} color="var(--text-muted)" /> : <ChevronRight size={18} color="var(--text-muted)" />}
                    <AlertTriangle size={18} color="var(--pour-orange)" />
                    <span style={{ color: 'var(--accent-blue)', fontSize: '0.9rem' }}>
                      {wcagLabel(issue.rule_id, issue.category)}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                    <FileText size={14} style={{ marginRight: '0.25rem', verticalAlign: 'middle' }} />
                    {issue.file_path}
                  </div>
                  <p style={{ color: 'white', margin: 0, fontSize: '0.95rem' }}>{issue.description}</p>
                  <span className={`severity-tag ${severityTag.class}`} style={{ marginTop: '0.5rem', display: 'inline-block' }}>
                    {severityTag.label}
                  </span>
                </div>
              </div>

              {isExpanded && (
                <div style={{ marginTop: '1.25rem', paddingTop: '1.25rem', borderTop: '1px solid var(--border)' }}>
                  {fix ? (
                    <>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                        <div>
                          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>Before</div>
                          <div className="code-block" style={{ padding: '1rem' }}>
                            <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all', fontSize: '0.85rem' }}>
                              {fix.before_code || issue.code_snippet || '(no snippet)'}
                            </pre>
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: '0.8rem', color: 'var(--pour-green)', marginBottom: '0.35rem' }}>After</div>
                          <div className="code-block" style={{ padding: '1rem', borderColor: 'var(--pour-green)' }}>
                            <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all', fontSize: '0.85rem' }}>
                              {fix.after_code}
                            </pre>
                          </div>
                        </div>
                      </div>

                      <div style={{
                        padding: '1rem',
                        backgroundColor: 'var(--bg-elevated)',
                        borderRadius: 8,
                        marginBottom: '1rem'
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                          <Bot size={16} />
                          AI Explanation
                        </div>
                        <p style={{ margin: 0, color: 'white', fontSize: '0.9rem', lineHeight: 1.5 }}>
                          {fix.confidence != null && fix.confidence > 0.7
                            ? 'Added or updated attributes to meet WCAG requirements for this criterion.'
                            : 'Suggested change to improve accessibility compliance.'}
                        </p>
                      </div>

                      <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
                        {applied || fix.applied ? (
                          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 1rem', backgroundColor: 'var(--pour-green)', color: 'white', borderRadius: 8, fontSize: '0.9rem' }}>
                            <CheckCircle size={18} /> Applied
                          </span>
                        ) : (
                          <button className="btn-primary" style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }} onClick={(e) => { e.stopPropagation(); handleApplyFix(issue.id); }}>
                            <CheckCircle size={16} /> Apply Fix
                          </button>
                        )}
                        <button className="btn-secondary" style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }} onClick={(e) => { e.stopPropagation(); handleDismiss(issue.id); }}>
                          <X size={16} /> Dismiss
                        </button>
                        <a
                          href={`https://www.w3.org/WAI/WCAG21/quickref/`}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ marginLeft: 'auto', fontSize: '0.9rem', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
                          onClick={e => e.stopPropagation()}
                        >
                          View More Details <ExternalLink size={14} />
                        </a>
                      </div>
                    </>
                  ) : (
                    <div style={{ padding: '1rem', backgroundColor: 'var(--bg-elevated)', borderRadius: 8, color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                      No automated fix available for this issue. Consider addressing it manually.
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })
      )}
    </div>
  )
}
