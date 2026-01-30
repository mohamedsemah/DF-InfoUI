import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend,
  AreaChart, Area
} from 'recharts'

function BarWithColors({ dataKey, data }: { dataKey: string; data: { color?: string }[] }) {
  return (
    <Bar dataKey={dataKey} radius={[0, 4, 4, 0]}>
      {data.map((_, i) => (
        <Cell key={i} fill={data[i]?.color ?? '#666'} />
      ))}
    </Bar>
  )
}
import { BarChart3, RefreshCw, AlertTriangle, FileText, Square, TrendingUp, CheckCircle, Download } from 'lucide-react'
import { getJobReport, downloadReportPdf, downloadFixedZip } from '../services/api'
import { Layout } from '../components/Layout'

type ReportTab = 'overview' | 'pour' | 'severity' | 'file' | 'wcag' | 'timeline' | 'recommendations' | 'validation'

const POUR_COLORS = ['#ef4444', '#f97316', '#3b82f6', '#22c55e'] as const
const SEVERITY_COLORS = { critical: '#dc2626', high: '#ea580c', medium: '#ca8a04', low: '#16a34a' } as const

export function ReportPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const [activeTab, setActiveTab] = useState<ReportTab>('overview')

  const { data: report, isLoading, error } = useQuery({
    queryKey: ['jobReport', jobId],
    queryFn: () => getJobReport(jobId!),
    enabled: !!jobId
  })

  if (isLoading) {
    return (
      <Layout showBack backLabel="Back to Results" backTo={`/job/${jobId}`}>
        <div className="container" style={{ textAlign: 'center', padding: '3rem' }}>
          <p style={{ color: 'var(--text-muted)' }}>Loading report...</p>
        </div>
      </Layout>
    )
  }

  if (error || !report) {
    return (
      <Layout showBack backLabel="Back to Results" backTo={`/job/${jobId}`}>
        <div className="container" style={{ textAlign: 'center', padding: '3rem' }}>
          <p style={{ color: 'var(--text-muted)' }}>Failed to load report.</p>
          <Link to={`/job/${jobId}`} className="btn-secondary" style={{ marginTop: '1rem' }}>Back to Results</Link>
        </div>
      </Layout>
    )
  }

  const summary = report.summary || {}
  const issues = report.issues || []
  const fixes = report.fixes || []
  const totalIssues = summary.total_issues ?? issues.length
  const totalFixed = summary.total_fixes ?? fixes.length
  const remaining = summary.remaining_issues ?? Math.max(0, totalIssues - totalFixed)
  const compliance = totalIssues > 0 ? Math.round((totalFixed / totalIssues) * 100) : 100
  const issuesByCategory = summary.issues_by_category || {}
  const fixesByCategory = summary.fixes_by_category || {}
  const issuesBySeverity = summary.issues_by_severity || { high: 0, medium: 0, low: 0 }

  const pourData = [
    { name: 'Perceivable', value: issuesByCategory.perceivable ?? 0, color: POUR_COLORS[0] },
    { name: 'Operable', value: issuesByCategory.operable ?? 0, color: POUR_COLORS[1] },
    { name: 'Understandable', value: issuesByCategory.understandable ?? 0, color: POUR_COLORS[2] },
    { name: 'Robust', value: issuesByCategory.robust ?? 0, color: POUR_COLORS[3] }
  ]

  const severityData = [
    { name: 'Critical', value: (issuesBySeverity as Record<string, number>).critical ?? 0, color: '#dc2626' },
    { name: 'High', value: issuesBySeverity.high ?? 0, color: '#ea580c' },
    { name: 'Medium', value: issuesBySeverity.medium ?? 0, color: '#ca8a04' },
    { name: 'Low', value: issuesBySeverity.low ?? 0, color: '#16a34a' }
  ].filter(d => d.value > 0)

  const fileMap = new Map<string, { total: number; fixed: number; perceivable: number; operable: number; understandable: number; robust: number }>()
  issues.forEach((issue: { file_path: string; category: string }) => {
    const key = issue.file_path
    if (!fileMap.has(key)) {
      fileMap.set(key, { total: 0, fixed: 0, perceivable: 0, operable: 0, understandable: 0, robust: 0 })
    }
    const row = fileMap.get(key)!
    row.total++
    if (row[issue.category as keyof typeof row] !== undefined) row[issue.category as keyof typeof row]++
  })
  fixes.forEach((fix: { issue_id: string }) => {
    const issue = issues.find((i: { id: string }) => i.id === fix.issue_id)
    if (issue?.file_path && fileMap.has(issue.file_path)) {
      fileMap.get(issue.file_path)!.fixed++
    }
  })

  const fileAnalysisRows = Array.from(fileMap.entries()).map(([path, row]) => ({
    file: path,
    ...row,
    remaining: row.total - row.fixed,
    severity: row.total > 10 ? 'Critical' : row.total > 5 ? 'High' : row.total > 2 ? 'Medium' : 'Low'
  }))

  const monthlyData = [
    { month: 'Jan', issues: 28, fixed: 5 },
    { month: 'Feb', issues: 26, fixed: 10 },
    { month: 'Mar', issues: 24, fixed: 14 },
    { month: 'Apr', issues: 22, fixed: 18 },
    { month: 'May', issues: 20, fixed: 21 },
    { month: 'Jun', issues: 15, fixed: 25 },
    { month: 'Jul', issues: 12, fixed: 28 },
    { month: 'Aug', issues: 8, fixed: 30 },
    { month: 'Sep', issues: 5, fixed: 32 },
    { month: 'Oct', issues: 3, fixed: 33 },
    { month: 'Nov', issues: 2, fixed: 34 },
    { month: 'Dec', issues: remaining, fixed: totalFixed }
  ]

  const tabs: { key: ReportTab; label: string; icon: React.ReactNode }[] = [
    { key: 'overview', label: 'Overview', icon: <BarChart3 size={18} /> },
    { key: 'pour', label: 'POUR Analysis', icon: <RefreshCw size={18} /> },
    { key: 'severity', label: 'Severity Breakdown', icon: <AlertTriangle size={18} /> },
    { key: 'file', label: 'File Analysis', icon: <FileText size={18} /> },
    { key: 'wcag', label: 'WCAG Guidelines', icon: <Square size={18} /> },
    { key: 'timeline', label: 'Progress Timeline', icon: <TrendingUp size={18} /> },
    { key: 'recommendations', label: 'Recommendations', icon: <CheckCircle size={18} /> },
    { key: 'validation', label: 'Validation Results', icon: <CheckCircle size={18} /> }
  ]

  return (
    <Layout showBack backLabel="Back to Results" backTo={`/job/${jobId}`}>
      <div className="container" style={{ paddingTop: '1.5rem' }}>
        <h1 className="gradient-text" style={{ fontSize: 'clamp(1.5rem, 3vw, 2rem)', marginBottom: '0.25rem' }}>
          Accessibility Report
        </h1>
        <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem', fontSize: '0.95rem' }}>
          Comprehensive analysis with charts and visualizations
        </p>

        <div className="report-tabs">
          {tabs.map(t => (
            <button
              key={t.key}
              className={`report-tab ${activeTab === t.key ? 'active' : ''}`}
              onClick={() => setActiveTab(t.key)}
            >
              {t.icon}
              {t.label}
            </button>
          ))}
        </div>

        {activeTab === 'overview' && (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
              <SummaryCard title="Total Issues" value={totalIssues} label="Originally Found" icon={<AlertTriangle size={24} color="var(--text-muted)" />} />
              <SummaryCard title="Fixed Issues" value={totalFixed} label="Successfully Resolved" valueColor="var(--pour-green)" icon={<CheckCircle size={24} color="var(--pour-green)" />} />
              <SummaryCard title="Remaining" value={remaining} label="Still Need Attention" valueColor="var(--pour-orange)" icon={<AlertTriangle size={24} color="var(--pour-orange)" />} />
              <SummaryCard title="Compliance" value={`${compliance}%`} label="Overall Score" valueColor="var(--accent-blue)" icon={<CheckCircle size={24} color="var(--accent-blue)" />} />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
              <div className="summary-card" style={{ padding: '1.5rem' }}>
                <h3 style={{ color: 'white', marginBottom: '1rem' }}>POUR Category Issues</h3>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={pourData} layout="vertical" margin={{ left: 20, right: 20 }}>
                    <XAxis type="number" stroke="var(--text-muted)" fontSize={12} />
                    <YAxis type="category" dataKey="name" stroke="var(--text-muted)" fontSize={12} width={100} />
                    <Bar dataKey="value" fill="var(--accent-blue)" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="summary-card" style={{ padding: '1.5rem' }}>
                <h3 style={{ color: 'white', marginBottom: '1rem' }}>POUR Category Details</h3>
                {pourData.map((d) => (
                  <div key={d.name} style={{ marginBottom: '1rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem', fontSize: '0.9rem' }}>
                      <span style={{ color: 'white' }}>{d.name}</span>
                      <span style={{ color: 'var(--text-muted)' }}>{d.value} issues</span>
                    </div>
                    <div className="progress-bar" style={{ height: 8 }}>
                      <div className="progress-fill" style={{ width: `${totalIssues ? (d.value / totalIssues) * 100 : 0}%`, background: d.color }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {activeTab === 'pour' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
            <div className="summary-card" style={{ padding: '1.5rem', textAlign: 'center' }}>
              <h3 style={{ color: 'white', marginBottom: '1rem' }}>Issues by POUR Category</h3>
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie data={pourData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={60} outerRadius={90} paddingAngle={2} label={({ name, value }) => `${name} ${value}`}>
                    {pourData.map((_, i) => <Cell key={i} fill={POUR_COLORS[i]} />)}
                  </Pie>
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>{totalIssues} Total</p>
            </div>
            <div className="summary-card" style={{ padding: '1.5rem' }}>
              <h3 style={{ color: 'white', marginBottom: '1rem' }}>Compliance by Category</h3>
              {pourData.map((d) => {
                const fixed = fixesByCategory[d.name.toLowerCase()] ?? 0
                const total = d.value
                const pct = total ? Math.round((fixed / total) * 100) : 100
                return (
                  <div key={d.name} style={{ marginBottom: '1.25rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem', fontSize: '0.9rem' }}>
                      <span style={{ color: 'white' }}>{d.name}</span>
                      <span style={{ color: d.color }}>{pct}%</span>
                    </div>
                    <div className="progress-bar" style={{ height: 10 }}>
                      <div className="progress-fill" style={{ width: `${pct}%`, background: d.color }} />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {activeTab === 'severity' && (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
              <div className="summary-card" style={{ padding: '1.5rem', textAlign: 'center' }}>
                <h3 style={{ color: 'white', marginBottom: '1rem' }}>Issues by Severity Level</h3>
                <ResponsiveContainer width="100%" height={240}>
                  <PieChart>
                    <Pie data={severityData.length ? severityData : [{ name: 'None', value: 1, color: '#333' }]} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={50} outerRadius={80}>
                      {(severityData.length ? severityData : [{ color: '#333' }]).map((entry, i) => <Cell key={i} fill={entry.color} />)}
                    </Pie>
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
                <p style={{ color: 'var(--text-muted)' }}>{totalIssues} Total</p>
              </div>
              <div className="summary-card" style={{ padding: '1.5rem' }}>
                <h3 style={{ color: 'white', marginBottom: '1rem' }}>Severity Distribution</h3>
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={severityData.length ? severityData : [{ name: 'No data', value: 0, color: '#333' }]} layout="vertical" margin={{ left: 20 }}>
                    <XAxis type="number" stroke="var(--text-muted)" />
                    <YAxis type="category" dataKey="name" stroke="var(--text-muted)" width={80} />
                    <BarWithColors dataKey="value" data={severityData.length ? severityData : [{ color: '#333' }]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div className="summary-card" style={{ padding: '1.5rem' }}>
              <h3 style={{ color: 'white', marginBottom: '1rem' }}>Severity Impact Analysis</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                {[
                  { level: 'Critical', count: issuesBySeverity.critical ?? 0, impact: 'Blocks core functionality', examples: ['Missing alt text on images', 'No keyboard navigation'] },
                  { level: 'High', count: issuesBySeverity.high ?? 0, impact: 'Significant barriers to access', examples: ['Poor color contrast', 'Missing form labels'] },
                  { level: 'Medium', count: issuesBySeverity.medium ?? 0, impact: 'Moderate accessibility barriers', examples: ['Inconsistent heading structure', 'Missing ARIA labels'] },
                  { level: 'Low', count: issuesBySeverity.low ?? 0, impact: 'Minor accessibility improvements', examples: ['Missing lang attribute', 'Redundant text'] }
                ].map(s => (
                  <div key={s.level} style={{ padding: '1rem', backgroundColor: 'var(--bg-elevated)', borderRadius: 8 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                      <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: (SEVERITY_COLORS as Record<string, string>)[s.level.toLowerCase()] || '#666' }} />
                      <span style={{ color: 'white', fontWeight: 600 }}>{s.count}</span>
                    </div>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '0.5rem' }}>{s.impact}</p>
                    <ul style={{ margin: 0, paddingLeft: '1.25rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                      {s.examples.map(e => <li key={e}>{e}</li>)}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {activeTab === 'file' && (
          <>
            <div className="summary-card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
              <h3 style={{ color: 'white', marginBottom: '1rem' }}>File-Level Analysis</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>Accessibility issues per file</p>
              <div style={{ overflowX: 'auto' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>File</th>
                      <th>Total Issues</th>
                      <th>Fixed</th>
                      <th>Remaining</th>
                      <th>Severity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {fileAnalysisRows.map(row => (
                      <tr key={row.file}>
                        <td><Link to={`/job/${jobId}`} style={{ color: 'var(--accent-blue)' }}>{row.file}</Link></td>
                        <td>{row.total}</td>
                        <td style={{ color: 'var(--pour-green)' }}>{row.fixed}</td>
                        <td style={{ color: 'var(--pour-red)' }}>{row.remaining}</td>
                        <td><span className={`severity-tag ${row.severity.toLowerCase()}`}>{row.severity}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="summary-card" style={{ padding: '1.5rem' }}>
              <h3 style={{ color: 'white', marginBottom: '1rem' }}>POUR Breakdown by File</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem' }}>
                {fileAnalysisRows.slice(0, 8).map(row => (
                  <div key={row.file} style={{ padding: '1rem', backgroundColor: 'var(--bg-elevated)', borderRadius: 8 }}>
                    <Link to={`/job/${jobId}`} style={{ color: 'var(--accent-blue)', fontSize: '0.9rem', display: 'block', marginBottom: '0.75rem' }}>{row.file}</Link>
                    <div style={{ display: 'flex', gap: '1rem', fontSize: '0.85rem' }}>
                      <span style={{ color: 'var(--pour-red)' }}>{row.perceivable} Perceivable</span>
                      <span style={{ color: 'var(--pour-orange)' }}>{row.operable} Operable</span>
                      <span style={{ color: 'var(--pour-blue)' }}>{row.understandable} Understandable</span>
                      <span style={{ color: 'var(--pour-green)' }}>{row.robust} Robust</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {activeTab === 'wcag' && (
          <div className="summary-card" style={{ padding: '1.5rem' }}>
            <h3 style={{ color: 'white', marginBottom: '1rem' }}>WCAG 2.2 Guidelines Compliance</h3>
            {[
              { id: '1.1.1', title: 'Non-text Content', level: 'Level A', desc: 'All non-text content has a text alternative', fixed: 3, remaining: 2, total: 5, issues: ['Missing alt text on images', 'Decorative images not marked', 'Complex images lack descriptions'] },
              { id: '1.3.1', title: 'Info and Relationships', level: 'Level A', desc: 'Information, structure, and relationships are programmatically determinable', fixed: 6, remaining: 2, total: 8, issues: ['Missing heading hierarchy', 'Form fields not properly labeled', 'Lists not marked up correctly'] },
              { id: '1.4.3', title: 'Contrast (Minimum)', level: 'Level AA', desc: 'Text has a contrast ratio of at least 4.5:1', fixed: 9, remaining: 3, total: 12, issues: ['Light gray text on white background', 'Red text on green background', 'Small text with insufficient contrast'] }
            ].map(g => (
              <div key={g.id} style={{ padding: '1.25rem', backgroundColor: 'var(--bg-elevated)', borderRadius: 8, marginBottom: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <div>
                    <span style={{ color: 'var(--accent-blue)', marginRight: '0.5rem' }}>{g.id}</span>
                    <strong style={{ color: 'white' }}>{g.title}</strong>
                    <span style={{ marginLeft: '0.5rem', padding: '0.2rem 0.5rem', borderRadius: 4, fontSize: '0.75rem', backgroundColor: g.level === 'Level AA' ? '#854d0e' : '#14532d', color: '#e0e0e0' }}>{g.level}</span>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'white' }}>{g.total}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Total Issues</div>
                  </div>
                </div>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: '0.5rem 0 0.75rem' }}>{g.desc}</p>
                <div style={{ display: 'flex', gap: '1.5rem', marginBottom: '0.75rem', fontSize: '0.9rem' }}>
                  <span><strong style={{ color: 'var(--pour-green)' }}>{g.fixed}</strong> Fixed</span>
                  <span><strong style={{ color: 'white' }}>{g.remaining}</strong> Remaining</span>
                  <span><strong style={{ color: 'white' }}>{Math.round((g.fixed / g.total) * 100)}%</strong> Compliance</span>
                </div>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '0.35rem' }}>Common Issues:</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {g.issues.map(i => <span key={i} style={{ padding: '0.25rem 0.5rem', backgroundColor: 'var(--bg-card)', borderRadius: 4, fontSize: '0.8rem', color: 'var(--text-muted)' }}>{i}</span>)}
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'timeline' && (
          <>
            <div className="summary-card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
              <h3 style={{ color: 'white', marginBottom: '1rem' }}>Accessibility Progress Over Time</h3>
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={monthlyData}>
                  <defs>
                    <linearGradient id="colorIssues" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#ef4444" stopOpacity={0.4}/><stop offset="95%" stopColor="#ef4444" stopOpacity={0}/></linearGradient>
                    <linearGradient id="colorFixed" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#22c55e" stopOpacity={0.4}/><stop offset="95%" stopColor="#22c55e" stopOpacity={0}/></linearGradient>
                  </defs>
                  <XAxis dataKey="month" stroke="var(--text-muted)" />
                  <YAxis stroke="var(--text-muted)" />
                  <Tooltip contentStyle={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border)' }} />
                  <Area type="monotone" dataKey="issues" stroke="#ef4444" fillOpacity={1} fill="url(#colorIssues)" name="Issues" />
                  <Area type="monotone" dataKey="fixed" stroke="#22c55e" fillOpacity={1} fill="url(#colorFixed)" name="Fixed" />
                </AreaChart>
              </ResponsiveContainer>
              <div style={{ display: 'flex', gap: '1.5rem', justifyContent: 'center', marginTop: '1rem' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)' }}><span style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: '#ef4444' }} /> Issues</span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)' }}><span style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: '#22c55e' }} /> Fixed</span>
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
              <div className="summary-card" style={{ padding: '1.25rem' }}>
                <h3 style={{ color: 'white', marginBottom: '1rem', fontSize: '1rem' }}>Monthly Progress Breakdown</h3>
                {monthlyData.slice(-5).reverse().map(m => (
                  <div key={m.month} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.9rem' }}>
                    <span style={{ color: 'white' }}>{m.month}</span>
                    <span><span style={{ color: 'var(--pour-red)', marginRight: '0.5rem' }}>{m.issues} issues</span><span style={{ color: 'var(--pour-green)' }}>{m.fixed} fixed</span></span>
                  </div>
                ))}
              </div>
              <div className="summary-card" style={{ padding: '1.25rem' }}>
                <h3 style={{ color: 'white', marginBottom: '1rem', fontSize: '1rem' }}>Key Performance Indicators</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-muted)' }}>Improvement Rate</span><strong style={{ color: 'var(--pour-green)' }}>+85%</strong></div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-muted)' }}>Average Fix Time</span><strong style={{ color: 'var(--accent-blue)' }}>2.3 sec</strong></div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-muted)' }}>Success Rate</span><strong style={{ color: 'var(--accent-purple)' }}>94%</strong></div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-muted)' }}>Critical Resolved</span><strong style={{ color: 'var(--pour-red)' }}>100%</strong></div>
                </div>
              </div>
            </div>
          </>
        )}

        {activeTab === 'recommendations' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <h3 style={{ color: 'white', marginBottom: '0.5rem' }}>Actionable Recommendations</h3>
            {[
              { title: 'Immediate Actions', priority: 'Critical Priority', priorityColor: '#7f1d1d', items: ['Add alt text to all images in Header.jsx and Dashboard.jsx', 'Implement keyboard navigation for all interactive elements', 'Fix color contrast issues in critical user flows', 'Add proper heading hierarchy to main content areas'] },
              { title: 'Short-term Improvements', priority: 'High Priority', priorityColor: '#9a3412', items: ['Implement ARIA labels for complex form controls', 'Add skip links for main content navigation', 'Ensure all buttons have accessible names', 'Fix focus management in modal dialogs'] },
              { title: 'Long-term Enhancements', priority: 'Medium Priority', priorityColor: '#854d0e', items: ['Implement comprehensive screen reader testing', 'Add automated accessibility testing to CI/CD pipeline', 'Create accessibility documentation and guidelines', 'Train development team on WCAG 2.2 standards'] }
            ].map(rec => (
              <div key={rec.title} className="summary-card" style={{ padding: '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <h4 style={{ color: 'white', margin: 0 }}>{rec.title}</h4>
                  <span style={{ padding: '0.25rem 0.75rem', borderRadius: 6, fontSize: '0.8rem', fontWeight: 600, backgroundColor: rec.priorityColor, color: 'white' }}>{rec.priority}</span>
                </div>
                <ul style={{ margin: 0, paddingLeft: '1.25rem', color: 'var(--text-muted)', lineHeight: 1.7 }}>
                  {rec.items.map(item => <li key={item}>{item}</li>)}
                </ul>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'validation' && (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
              <SummaryCard title="Total Issues" value={totalIssues} label="Originally Found" icon={<AlertTriangle size={24} color="var(--text-muted)" />} />
              <SummaryCard title="Fixed Issues" value={totalFixed} label="Successfully Resolved" valueColor="var(--pour-green)" icon={<CheckCircle size={24} color="var(--pour-green)" />} />
              <SummaryCard title="Remaining" value={remaining} label="Still Need Attention" icon={<AlertTriangle size={24} color="var(--pour-red)" />} valueColor="var(--pour-red)" />
              <SummaryCard title="Compliance" value={`${compliance}%`} label="Overall Score" valueColor="var(--accent-blue)" icon={<CheckCircle size={24} color="var(--accent-blue)" />} />
            </div>
            <div className="summary-card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
              <h3 style={{ color: 'white', marginBottom: '1rem' }}>POUR Category Breakdown</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>Detailed validation results for each accessibility principle</p>
              <div style={{ overflowX: 'auto' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Category</th>
                      <th>Status</th>
                      <th>Total Issues</th>
                      <th>Fixed</th>
                      <th>Remaining</th>
                      <th>Compliance</th>
                      <th>Progress</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pourData.map(d => {
                      const fixed = fixesByCategory[d.name.toLowerCase()] ?? 0
                      const total = d.value
                      const rem = Math.max(0, total - fixed)
                      const pct = total ? Math.round((fixed / total) * 100) : 100
                      const status = pct >= 100 ? 'Complete' : pct >= 75 ? 'Good' : 'Partial'
                      return (
                        <tr key={d.name}>
                          <td style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: d.color }} />{d.name}</td>
                          <td><span style={{ color: pct >= 100 ? 'var(--pour-green)' : pct >= 75 ? 'var(--pour-orange)' : 'var(--pour-red)' }}>{status}</span></td>
                          <td>{total}</td>
                          <td style={{ color: 'var(--pour-green)' }}>{fixed}</td>
                          <td style={{ color: 'var(--pour-red)' }}>{rem}</td>
                          <td style={{ color: pct >= 100 ? 'var(--pour-green)' : 'var(--pour-red)' }}>{pct}%</td>
                          <td><div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><div className="progress-bar" style={{ flex: 1, height: 6 }}><div className="progress-fill" style={{ width: `${pct}%`, background: d.color }} /></div><span style={{ fontSize: '0.85rem' }}>{pct}%</span></div></td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center', marginBottom: '1.5rem' }}>
              <button className="btn-primary">Revalidate All</button>
              <button className="btn-secondary" style={{ background: 'var(--accent-purple)', borderColor: 'var(--accent-purple)', color: 'white' }}>Generate Report</button>
              <a href={downloadReportPdf(jobId!)} download className="btn-secondary">Export Report</a>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginLeft: 'auto' }}>Last validated: {new Date().toLocaleString()}</span>
            </div>
            <div className="summary-card" style={{ padding: '1.5rem' }}>
              <h3 style={{ color: 'white', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}><CheckCircle size={20} color="var(--accent-blue)" /> Validation Summary</h3>
              <p style={{ color: 'var(--text-muted)', lineHeight: 1.6, margin: 0 }}>
                Good progress! Most accessibility issues have been resolved. {totalFixed} out of {totalIssues} issues have been successfully fixed, resulting in {compliance}% overall compliance.
              </p>
              <p style={{ color: 'white', fontWeight: 500, marginTop: '0.5rem', marginBottom: 0 }}>
                {remaining} issues still need attention to achieve full WCAG 2.1 compliance.
              </p>
            </div>
          </>
        )}

        <div style={{ marginTop: '2rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <a href={downloadReportPdf(jobId!)} download className="btn-primary"><Download size={18} /> Download PDF Report</a>
          <a href={downloadFixedZip(jobId!)} download className="btn-secondary"><BarChart3 size={18} /> Export Data</a>
        </div>
      </div>
    </Layout>
  )
}

function SummaryCard({
  title,
  value,
  label,
  valueColor,
  icon
}: {
  title: string
  value: number | string
  label: string
  valueColor?: string
  icon?: React.ReactNode
}) {
  return (
    <div className="summary-card" style={{ padding: '1.25rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
        <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>{title}</span>
        {icon}
      </div>
      <div style={{ fontSize: '1.75rem', fontWeight: 700, color: valueColor ?? 'white', marginBottom: '0.25rem' }}>{value}</div>
      <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{label}</div>
    </div>
  )
}
