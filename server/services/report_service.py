import os
from pathlib import Path
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from models.job import Issue, Fix, ValidationResult

# Try to import WeasyPrint, fallback to reportlab if not available
try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

class ReportService:
    def __init__(self):
        self.data_dir = Path(os.getenv("DATA_DIR", "/app/data"))
    
    async def generate_pdf_report(self, job_id: str, issues: List[Issue], fixes: List[Fix], validation_results: Dict[str, Any]) -> Path:
        """Generate PDF report with accessibility analysis and fixes"""
        job_dir = self.data_dir / job_id
        pdf_path = job_dir / "report.pdf"
        
        # Try WeasyPrint first, fallback to reportlab
        if WEASYPRINT_AVAILABLE:
            try:
                return await self._generate_weasyprint_pdf(job_id, issues, fixes, validation_results)
            except Exception as e:
                print(f"WeasyPrint failed, falling back to reportlab: {e}")
        
        return await self._generate_reportlab_pdf(job_id, issues, fixes, validation_results)
    
    async def _generate_weasyprint_pdf(self, job_id: str, issues: List[Issue], fixes: List[Fix], validation_results: Dict[str, Any]) -> Path:
        """Generate PDF using WeasyPrint"""
        job_dir = self.data_dir / job_id
        pdf_path = job_dir / "report.pdf"
        
        # Generate HTML content
        html_content = self._generate_html_report(issues, fixes, validation_results)
        
        # Generate CSS
        css_content = self._generate_css_styles()
        
        # Create PDF
        html_doc = HTML(string=html_content)
        css_doc = CSS(string=css_content)
        
        html_doc.write_pdf(pdf_path, stylesheets=[css_doc])
        
        return pdf_path
    
    async def _generate_reportlab_pdf(self, job_id: str, issues: List[Issue], fixes: List[Fix], validation_results: Dict[str, Any]) -> Path:
        """Generate PDF using reportlab (fallback)"""
        job_dir = self.data_dir / job_id
        pdf_path = job_dir / "report.pdf"
        
        # Create PDF document
        doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center
        )
        story.append(Paragraph("DF-InfoUI Accessibility Report", title_style))
        story.append(Spacer(1, 20))
        
        # Summary section
        story.append(Paragraph("Summary", styles['Heading2']))
        summary_data = [
            ['Total Issues Found', str(len(issues))],
            ['Issues Fixed', str(len(fixes))],
            ['Validation Passed', 'Yes' if validation_results.get('passed', False) else 'No'],
            ['Remaining Issues', str(validation_results.get('remaining_issues', 0))]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Issues by category
        story.append(Paragraph("Issues by Category", styles['Heading2']))
        categories = {}
        for issue in issues:
            if issue.category not in categories:
                categories[issue.category] = []
            categories[issue.category].append(issue)
        
        for category, category_issues in categories.items():
            story.append(Paragraph(f"{category.title()} Issues ({len(category_issues)})", styles['Heading3']))
            
            for issue in category_issues:
                # Issue details
                issue_text = f"""
                <b>File:</b> {Path(issue.file_path).name}<br/>
                <b>Lines:</b> {issue.line_start}-{issue.line_end}<br/>
                <b>Severity:</b> {issue.severity}<br/>
                <b>Description:</b> {issue.description}<br/>
                <b>Code:</b><br/>
                <font name="Courier">{issue.code_snippet}</font>
                """
                story.append(Paragraph(issue_text, styles['Normal']))
                story.append(Spacer(1, 10))
        
        story.append(PageBreak())
        
        # Fixes section
        story.append(Paragraph("Applied Fixes", styles['Heading2']))
        
        for fix in fixes:
            if fix.applied:
                fix_text = f"""
                <b>File:</b> {Path(fix.file_path).name}<br/>
                <b>Confidence:</b> {fix.confidence:.1%}<br/>
                <b>Before:</b><br/>
                <font name="Courier">{fix.before_code}</font><br/>
                <b>After:</b><br/>
                <font name="Courier">{fix.after_code}</font><br/>
                <b>Diff:</b><br/>
                <font name="Courier">{fix.diff}</font>
                """
                story.append(Paragraph(fix_text, styles['Normal']))
                story.append(Spacer(1, 15))
        
        story.append(PageBreak())
        
        # Validation results
        story.append(Paragraph("Validation Results", styles['Heading2']))
        
        if validation_results.get('results'):
            for result in validation_results['results']:
                status = "PASSED" if result.passed else "FAILED"
                status_color = colors.green if result.passed else colors.red
                
                result_text = f"""
                <b>File:</b> {Path(result.file_path).name}<br/>
                <b>Status:</b> <font color="{status_color}">{status}</font><br/>
                """
                
                if result.errors:
                    result_text += f"<b>Errors:</b><br/>"
                    for error in result.errors:
                        result_text += f"• {error}<br/>"
                
                if result.warnings:
                    result_text += f"<b>Warnings:</b><br/>"
                    for warning in result.warnings:
                        result_text += f"• {warning}<br/>"
                
                story.append(Paragraph(result_text, styles['Normal']))
                story.append(Spacer(1, 10))
        
        # Build PDF
        doc.build(story)
        
        return pdf_path
    
    def _generate_html_report(self, issues: List[Issue], fixes: List[Fix], validation_results: Dict[str, Any]) -> str:
        """Generate HTML content for WeasyPrint PDF"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>DF-InfoUI Accessibility Report</title>
        </head>
        <body>
            <div class="header">
                <h1>DF-InfoUI Accessibility Report</h1>
                <p class="subtitle">Adaptive Multi-Agent Accessibility Evaluator & Fixer</p>
            </div>
            
            <div class="summary">
                <h2>Summary</h2>
                <div class="summary-grid">
                    <div class="summary-item">
                        <strong>Total Issues Found:</strong> {len(issues)}
                    </div>
                    <div class="summary-item">
                        <strong>Issues Fixed:</strong> {len(fixes)}
                    </div>
                    <div class="summary-item">
                        <strong>Validation Passed:</strong> {'Yes' if validation_results.get('passed', False) else 'No'}
                    </div>
                    <div class="summary-item">
                        <strong>Remaining Issues:</strong> {validation_results.get('remaining_issues', 0)}
                    </div>
                </div>
            </div>
            
            <div class="issues-section">
                <h2>Issues by Category</h2>
                {self._generate_issues_by_category(issues)}
            </div>
            
            <div class="fixes-section">
                <h2>Applied Fixes</h2>
                {self._generate_fixes_html(fixes)}
            </div>
            
            <div class="validation-section">
                <h2>Validation Results</h2>
                {self._generate_validation_html(validation_results)}
            </div>
        </body>
        </html>
        """
        return html
    
    def _generate_css_styles(self) -> str:
        """Generate CSS styles for WeasyPrint PDF"""
        return """
        @page {
            size: A4;
            margin: 2cm;
        }
        
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }
        
        .header {
            text-align: center;
            margin-bottom: 2rem;
            border-bottom: 2px solid #007acc;
            padding-bottom: 1rem;
        }
        
        .header h1 {
            color: #007acc;
            margin: 0;
            font-size: 2.5em;
        }
        
        .subtitle {
            color: #666;
            font-size: 1.2em;
            margin: 0.5rem 0 0 0;
        }
        
        .summary {
            margin-bottom: 2rem;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
            margin-top: 1rem;
        }
        
        .summary-item {
            background: #f5f5f5;
            padding: 1rem;
            border-radius: 4px;
            border-left: 4px solid #007acc;
        }
        
        .issues-section, .fixes-section, .validation-section {
            margin-bottom: 2rem;
        }
        
        .category {
            margin-bottom: 1.5rem;
        }
        
        .category h3 {
            color: #007acc;
            background: #f0f8ff;
            padding: 0.5rem;
            border-radius: 4px;
            margin: 0 0 1rem 0;
        }
        
        .issue {
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        .issue-header {
            font-weight: bold;
            color: #d32f2f;
            margin-bottom: 0.5rem;
        }
        
        .issue-details {
            font-size: 0.9em;
            color: #666;
        }
        
        .code-snippet {
            background: #f8f8f8;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 0.5rem;
            font-family: 'Courier New', monospace;
            font-size: 0.8em;
            margin: 0.5rem 0;
            white-space: pre-wrap;
        }
        
        .fix {
            background: #f0f8f0;
            border: 1px solid #4caf50;
            border-radius: 4px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        .fix-header {
            font-weight: bold;
            color: #2e7d32;
            margin-bottom: 0.5rem;
        }
        
        .before-after {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin: 1rem 0;
        }
        
        .before, .after {
            background: #f8f8f8;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 0.5rem;
        }
        
        .before h4, .after h4 {
            margin: 0 0 0.5rem 0;
            font-size: 0.9em;
            color: #666;
        }
        
        .validation-result {
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        .validation-passed {
            border-left: 4px solid #4caf50;
        }
        
        .validation-failed {
            border-left: 4px solid #f44336;
        }
        
        .validation-status {
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        
        .passed {
            color: #4caf50;
        }
        
        .failed {
            color: #f44336;
        }
        
        .errors, .warnings {
            margin-top: 0.5rem;
        }
        
        .errors ul, .warnings ul {
            margin: 0.5rem 0;
            padding-left: 1.5rem;
        }
        
        .errors li {
            color: #f44336;
        }
        
        .warnings li {
            color: #ff9800;
        }
        
        .validation-summary {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .summary-stats {
            display: flex;
            gap: 20px;
            margin-bottom: 15px;
        }
        
        .stat {
            background-color: white;
            padding: 10px 15px;
            border-radius: 4px;
            border-left: 4px solid #007bff;
        }
        
        .issues-by-type, .issues-by-severity, .validation-tools {
            margin-bottom: 15px;
        }
        
        .issues-by-type ul, .issues-by-severity ul {
            margin: 5px 0;
            padding-left: 20px;
        }
        
        .validation-details {
            margin-top: 20px;
        }
        """
    
    def _generate_issues_by_category(self, issues: List[Issue]) -> str:
        """Generate HTML for issues grouped by category"""
        categories = {
            'perceivable': [],
            'operable': [],
            'understandable': [],
            'robust': []
        }
        
        for issue in issues:
            if issue.category in categories:
                categories[issue.category].append(issue)
        
        html = ""
        for category, category_issues in categories.items():
            if category_issues:
                html += f"""
                <div class="category">
                    <h3>{category.title()} Issues ({len(category_issues)})</h3>
                """
                for issue in category_issues:
                    html += f"""
                    <div class="issue">
                        <div class="issue-header">{issue.rule_id or 'Unknown Rule'}</div>
                        <div class="issue-details">
                            <strong>File:</strong> {Path(issue.file_path).name}<br>
                            <strong>Lines:</strong> {issue.line_start}-{issue.line_end}<br>
                            <strong>Severity:</strong> {issue.severity}<br>
                            <strong>Description:</strong> {issue.description}
                        </div>
                        <div class="code-snippet">{issue.code_snippet}</div>
                    </div>
                    """
                html += "</div>"
        
        return html
    
    def _generate_fixes_html(self, fixes: List[Fix]) -> str:
        """Generate HTML for applied fixes"""
        html = ""
        for fix in fixes:
            if fix.applied:
                html += f"""
                <div class="fix">
                    <div class="fix-header">Fix for {Path(fix.file_path).name}</div>
                    <div class="fix-details">
                        <strong>Confidence:</strong> {fix.confidence:.1%}<br>
                        <strong>Applied:</strong> {'Yes' if fix.applied else 'No'}
                    </div>
                    <div class="before-after">
                        <div class="before">
                            <h4>Before</h4>
                            <div class="code-snippet">{fix.before_code}</div>
                        </div>
                        <div class="after">
                            <h4>After</h4>
                            <div class="code-snippet">{fix.after_code}</div>
                        </div>
                    </div>
                    <div class="code-snippet"><strong>Diff:</strong><br>{fix.diff}</div>
                </div>
                """
        return html
    
    def _generate_validation_html(self, validation_results: Dict[str, Any]) -> str:
        """Generate HTML for validation results with enhanced summary"""
        html = ""
        
        # Add validation summary if available
        if validation_results.get('summary'):
            summary = validation_results['summary']
            html += f"""
            <div class="validation-summary">
                <h3>Validation Summary</h3>
                <div class="summary-stats">
                    <div class="stat">
                        <strong>Files Checked:</strong> {summary.get('total_files_checked', 0)}
                    </div>
                    <div class="stat">
                        <strong>Files with Issues:</strong> {summary.get('files_with_issues', 0)}
                    </div>
                    <div class="stat">
                        <strong>Compliance Score:</strong> {summary.get('compliance_score', 0):.1%}
                    </div>
                </div>
            """
            
            # Add issues by type
            if summary.get('issues_by_type'):
                html += """
                <div class="issues-by-type">
                    <h4>Issues by Type</h4>
                    <ul>
                """
                for issue_type, count in summary['issues_by_type'].items():
                    html += f"<li><strong>{issue_type.replace('_', ' ').title()}:</strong> {count}</li>"
                html += "</ul></div>"
            
            # Add issues by severity
            if summary.get('issues_by_severity'):
                html += """
                <div class="issues-by-severity">
                    <h4>Issues by Severity</h4>
                    <ul>
                """
                for severity, count in summary['issues_by_severity'].items():
                    html += f"<li><strong>{severity.title()}:</strong> {count}</li>"
                html += "</ul></div>"
            
            # Add validation tools used
            if summary.get('validation_tools_used'):
                html += f"""
                <div class="validation-tools">
                    <h4>Validation Tools Used</h4>
                    <p>{', '.join(summary['validation_tools_used'])}</p>
                </div>
                """
            
            html += "</div>"
        
        # Add detailed validation results
        if validation_results.get('results'):
            html += "<div class="validation-details"><h3>Detailed Validation Results</h3>"
            for result in validation_results['results']:
                status_class = "validation-passed" if result.passed else "validation-failed"
                status_text = "PASSED" if result.passed else "FAILED"
                status_color = "passed" if result.passed else "failed"
                
                html += f"""
                <div class="validation-result {status_class}">
                    <div class="validation-status {status_color}">
                        {Path(result.file_path).name} - {status_text}
                    </div>
                """
                
                if result.errors:
                    html += f"""
                    <div class="errors">
                        <strong>Errors:</strong>
                        <ul>
                    """
                    for error in result.errors:
                        html += f"<li>{error}</li>"
                    html += "</ul></div>"
                
                if result.warnings:
                    html += f"""
                    <div class="warnings">
                        <strong>Warnings:</strong>
                        <ul>
                    """
                    for warning in result.warnings:
                        html += f"<li>{warning}</li>"
                    html += "</ul></div>"
                
                html += "</div>"
            html += "</div>"
        
        return html
