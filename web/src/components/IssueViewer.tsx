import { useState } from 'react'
import { ChevronDown, ChevronRight, FileText, Code, CheckCircle } from 'lucide-react'

interface IssueViewerProps {
  jobId: string
  activeTab: 'perceivable' | 'operable' | 'understandable' | 'robust'
  onTabChange: (tab: 'perceivable' | 'operable' | 'understandable' | 'robust') => void
}

export function IssueViewer({ jobId, activeTab, onTabChange }: IssueViewerProps) {
  const [expandedIssues, setExpandedIssues] = useState<Set<string>>(new Set())

  // Mock data - in a real app, this would come from the API
  const mockIssues = {
    perceivable: [
      {
        id: '1',
        file_path: 'src/components/ImageGallery.tsx',
        line_start: 15,
        line_end: 15,
        category: 'perceivable',
        severity: 'high',
        description: 'Image missing alt attribute',
        code_snippet: '<img src="gallery-image.jpg" />',
        rule_id: 'img-alt'
      },
      {
        id: '2',
        file_path: 'src/styles/theme.css',
        line_start: 42,
        line_end: 42,
        category: 'perceivable',
        severity: 'medium',
        description: 'Potential color contrast issue',
        code_snippet: 'color: #999999;',
        rule_id: 'color-contrast'
      }
    ],
    operable: [
      {
        id: '3',
        file_path: 'src/components/Form.tsx',
        line_start: 8,
        line_end: 8,
        category: 'operable',
        severity: 'high',
        description: 'Input missing label or aria-label',
        code_snippet: '<input type="text" name="email" />',
        rule_id: 'label'
      }
    ],
    understandable: [
      {
        id: '4',
        file_path: 'src/components/Header.tsx',
        line_start: 23,
        line_end: 23,
        category: 'understandable',
        severity: 'medium',
        description: 'Heading level skipped',
        code_snippet: '<h3>Section Title</h3>',
        rule_id: 'heading-order'
      }
    ],
    robust: [
      {
        id: '5',
        file_path: 'src/components/Button.tsx',
        line_start: 12,
        line_end: 12,
        category: 'robust',
        severity: 'low',
        description: 'Missing ARIA role for custom button',
        code_snippet: '<div onClick={handleClick}>Click me</div>',
        rule_id: 'role'
      }
    ]
  }

  const tabs = [
    { key: 'perceivable', label: 'Perceivable', count: mockIssues.perceivable.length },
    { key: 'operable', label: 'Operable', count: mockIssues.operable.length },
    { key: 'understandable', label: 'Understandable', count: mockIssues.understandable.length },
    { key: 'robust', label: 'Robust', count: mockIssues.robust.length }
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
        {mockIssues[activeTab].length === 0 ? (
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
          mockIssues[activeTab].map(issue => (
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

                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '1rem',
                    marginTop: '1rem'
                  }}>
                    <div className="diff-section before">
                      <h4 style={{ margin: '0 0 0.5rem 0' }}>Before Fix</h4>
                      <div className="code-snippet">
                        {issue.code_snippet}
                      </div>
                    </div>
                    <div className="diff-section after">
                      <h4 style={{ margin: '0 0 0.5rem 0' }}>After Fix</h4>
                      <div className="code-snippet">
                        {issue.rule_id === 'img-alt' && issue.code_snippet.includes('<img') ? 
                          issue.code_snippet.replace('>', ' alt="Descriptive text for image">') :
                          issue.rule_id === 'label' && issue.code_snippet.includes('<input') ?
                          issue.code_snippet.replace('>', ' aria-label="Input field">') :
                          issue.code_snippet + ' /* Fixed */'
                        }
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
                    <strong>Fix Applied:</strong> {issue.rule_id === 'img-alt' ? 
                      'Added alt attribute to image' :
                      issue.rule_id === 'label' ?
                      'Added aria-label to input' :
                      'Applied accessibility fix'
                    }
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
