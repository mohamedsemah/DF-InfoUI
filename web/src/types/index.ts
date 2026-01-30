export interface JobStatus {
  job_id: string
  status: 'uploaded' | 'planning' | 'fixing' | 'validating' | 'complete' | 'error'
  progress: number
  message: string
  summary?: {
    total_issues?: number
    total_fixes?: number
    issues_fixed?: number
    validation_passed?: boolean
    remaining_issues?: number
    issues_by_category?: Record<string, number>
    fixes_by_category?: Record<string, number>
    issues_by_severity?: Record<string, number>
  }
}

export interface Issue {
  id: string
  file_path: string
  line_start: number
  line_end: number
  category: 'perceivable' | 'operable' | 'understandable' | 'robust'
  severity: 'high' | 'medium' | 'low'
  description: string
  code_snippet: string
  rule_id?: string
}

export interface Fix {
  issue_id: string
  file_path: string
  before_code: string
  after_code: string
  diff: string
  confidence: number
  applied: boolean
}

export interface ValidationResult {
  file_path: string
  passed: boolean
  errors: string[]
  warnings: string[]
}
