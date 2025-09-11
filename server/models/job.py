from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime

class JobStatus(str, Enum):
    UPLOADED = "uploaded"
    PLANNING = "planning"
    FIXING = "fixing"
    VALIDATING = "validating"
    COMPLETE = "complete"
    ERROR = "error"

class Issue(BaseModel):
    id: str
    file_path: str
    line_start: int
    line_end: int
    category: str  # perceivable, operable, understandable, robust
    severity: str  # high, medium, low
    description: str
    code_snippet: str
    rule_id: Optional[str] = None
    # Enhanced code snippet data
    code_snippet_data: Optional[Dict[str, Any]] = None
    context_lines: Optional[int] = 3
    total_lines: Optional[int] = None

class Fix(BaseModel):
    issue_id: str
    file_path: str
    before_code: str
    after_code: str
    diff: str
    confidence: float
    applied: bool = False

class ValidationResult(BaseModel):
    file_path: str
    passed: bool
    errors: List[str]
    warnings: List[str]

class Job(BaseModel):
    id: str
    status: JobStatus
    progress: int = 0
    message: str = ""
    summary: Optional[Dict[str, Any]] = None
    created_at: datetime = datetime.now()
    completed_at: Optional[datetime] = None
    issues: List[Issue] = []
    fixes: List[Fix] = []
    validation_results: List[ValidationResult] = []
