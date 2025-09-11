import os
from pathlib import Path
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from models.job import Issue, Fix, ValidationResult

class ReportService:
    def __init__(self):
        self.data_dir = Path(os.getenv("DATA_DIR", "/app/data"))
    
    async def generate_pdf_report(self, job_id: str, issues: List[Issue], fixes: List[Fix], validation_results: Dict[str, Any]) -> Path:
        """Generate PDF report with accessibility analysis and fixes"""
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
