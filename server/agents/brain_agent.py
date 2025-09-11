import os
import re
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple
import openai
from models.job import Issue, Fix

class BrainAgent:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    
    async def analyze_files(self, job_id: str) -> List[Issue]:
        """Analyze files and detect accessibility issues"""
        from services.file_service import FileService
        
        file_service = FileService()
        files = file_service.get_original_files(job_id)
        all_issues = []
        
        for file_path in files:
            issues = await self._analyze_file(file_path)
            all_issues.extend(issues)
        
        return all_issues
    
    async def coordinate_fixing_process(self, job_id: str, issues: List[Issue]) -> Dict[str, Any]:
        """Coordinate the complete fixing process with POUR agents"""
        from agents.pour_agents import POURAgents
        from services.file_service import FileService
        from services.validation_service import ValidationService
        from services.report_service import ReportService
        
        # Initialize services
        pour_agents = POURAgents()
        file_service = FileService()
        validation_service = ValidationService()
        report_service = ReportService()
        
        # Step 1: Classify issues into POUR categories
        classified_issues = self._classify_issues(issues)
        
        # Step 2: Send issues to POUR agents and get fixes
        all_fixes = []
        agent_reports = {}
        
        for category, category_issues in classified_issues.items():
            if category_issues:
                print(f"Processing {len(category_issues)} {category} issues...")
                
                # Get fixes from the appropriate agent
                fixes = await self._get_fixes_from_agent(pour_agents, category, category_issues)
                all_fixes.extend(fixes)
                
                # Generate agent report
                agent_reports[category] = {
                    "issues_count": len(category_issues),
                    "fixes_count": len(fixes),
                    "fixes": fixes
                }
        
        # Step 3: Apply fixes to files
        await file_service.apply_patches(job_id, all_fixes)
        
        # Step 4: Validate fixes
        validation_results = await validation_service.validate_fixes(job_id)
        
        # Step 5: Generate final artifacts
        await file_service.create_fixed_zip(job_id)
        await report_service.generate_pdf_report(job_id, issues, all_fixes, validation_results)
        
        return {
            "total_issues": len(issues),
            "total_fixes": len(all_fixes),
            "agent_reports": agent_reports,
            "validation_results": validation_results
        }
    
    def _classify_issues(self, issues: List[Issue]) -> Dict[str, List[Issue]]:
        """Classify issues into POUR categories"""
        classified = {
            "perceivable": [],
            "operable": [],
            "understandable": [],
            "robust": []
        }
        
        for issue in issues:
            if issue.category in classified:
                classified[issue.category].append(issue)
        
        return classified
    
    async def _get_fixes_from_agent(self, pour_agents, category: str, issues: List[Issue]) -> List[Fix]:
        """Get fixes from the appropriate POUR agent"""
        if category == "perceivable":
            return await pour_agents.perceivable_agent.fix_issues(issues)
        elif category == "operable":
            return await pour_agents.operable_agent.fix_issues(issues)
        elif category == "understandable":
            return await pour_agents.understandable_agent.fix_issues(issues)
        elif category == "robust":
            return await pour_agents.robust_agent.fix_issues(issues)
        else:
            return []
    
    async def _analyze_file(self, file_path: Path) -> List[Issue]:
        """Analyze a single file for accessibility issues"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return []
        
        issues = []
        
        # Static analysis based on file type
        if file_path.suffix in ['.html', '.jsx', '.tsx']:
            issues.extend(await self._analyze_html_jsx(file_path, content))
        elif file_path.suffix in ['.js', '.ts']:
            issues.extend(await self._analyze_js_ts(file_path, content))
        elif file_path.suffix == '.css':
            issues.extend(await self._analyze_css(file_path, content))
        
        # Use LLM for additional analysis
        llm_issues = await self._llm_analyze_file(file_path, content)
        issues.extend(llm_issues)
        
        return issues
    
    async def _analyze_html_jsx(self, file_path: Path, content: str) -> List[Issue]:
        """Analyze HTML/JSX files for accessibility issues"""
        issues = []
        lines = content.split('\n')
        
        # Check for missing alt attributes
        for i, line in enumerate(lines):
            if re.search(r'<img[^>]*(?!alt=)', line) and 'alt=' not in line:
                issues.append(Issue(
                    id=f"{file_path.name}_{i+1}_missing_alt",
                    file_path=str(file_path),
                    line_start=i+1,
                    line_end=i+1,
                    category="perceivable",
                    severity="high",
                    description="Image missing alt attribute",
                    code_snippet=line.strip(),
                    rule_id="img-alt"
                ))
        
        # Check for missing form labels
        for i, line in enumerate(lines):
            if re.search(r'<input[^>]*(?!aria-label|id=.*for)', line) and 'label' not in line:
                issues.append(Issue(
                    id=f"{file_path.name}_{i+1}_missing_label",
                    file_path=str(file_path),
                    line_start=i+1,
                    line_end=i+1,
                    category="operable",
                    severity="high",
                    description="Input missing label or aria-label",
                    code_snippet=line.strip(),
                    rule_id="label"
                ))
        
        # Check for missing heading hierarchy
        headings = []
        for i, line in enumerate(lines):
            heading_match = re.search(r'<h([1-6])', line)
            if heading_match:
                level = int(heading_match.group(1))
                headings.append((i+1, level))
        
        for i, (line_num, level) in enumerate(headings):
            if i > 0 and level > headings[i-1][1] + 1:
                issues.append(Issue(
                    id=f"{file_path.name}_{line_num}_heading_skip",
                    file_path=str(file_path),
                    line_start=line_num,
                    line_end=line_num,
                    category="understandable",
                    severity="medium",
                    description="Heading level skipped",
                    code_snippet=lines[line_num-1].strip(),
                    rule_id="heading-order"
                ))
        
        return issues
    
    async def _analyze_js_ts(self, file_path: Path, content: str) -> List[Issue]:
        """Analyze JS/TS files for accessibility issues"""
        issues = []
        lines = content.split('\n')
        
        # Check for missing ARIA attributes in event handlers
        for i, line in enumerate(lines):
            if 'onClick' in line and 'aria-label' not in line and 'aria-labelledby' not in line:
                if re.search(r'<[^>]*onClick', line):
                    issues.append(Issue(
                        id=f"{file_path.name}_{i+1}_missing_aria",
                        file_path=str(file_path),
                        line_start=i+1,
                        line_end=i+1,
                        category="operable",
                        severity="medium",
                        description="Interactive element missing ARIA label",
                        code_snippet=line.strip(),
                        rule_id="aria-label"
                    ))
        
        return issues
    
    async def _analyze_css(self, file_path: Path, content: str) -> List[Issue]:
        """Analyze CSS files for accessibility issues"""
        issues = []
        lines = content.split('\n')
        
        # Check for color contrast issues (simplified)
        for i, line in enumerate(lines):
            if 'color:' in line and 'background' not in line.lower():
                # This is a simplified check - in production, use proper color contrast analysis
                issues.append(Issue(
                    id=f"{file_path.name}_{i+1}_color_contrast",
                    file_path=str(file_path),
                    line_start=i+1,
                    line_end=i+1,
                    category="perceivable",
                    severity="medium",
                    description="Potential color contrast issue - verify with tools",
                    code_snippet=line.strip(),
                    rule_id="color-contrast"
                ))
        
        return issues
    
    async def _llm_analyze_file(self, file_path: Path, content: str) -> List[Issue]:
        """Use LLM to analyze file for accessibility issues"""
        try:
            prompt = f"""
            Analyze this {file_path.suffix} file for accessibility issues. Focus on WCAG 2.1 guidelines.
            Return a JSON array of issues with this structure:
            [
                {{
                    "id": "unique_id",
                    "file_path": "{file_path}",
                    "line_start": line_number,
                    "line_end": line_number,
                    "category": "perceivable|operable|understandable|robust",
                    "severity": "high|medium|low",
                    "description": "Issue description",
                    "code_snippet": "relevant code",
                    "rule_id": "wcag_rule_id"
                }}
            ]
            
            File content:
            {content[:2000]}  # Limit content to avoid token limits
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an accessibility expert. Analyze code for WCAG 2.1 compliance issues."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            result = response.choices[0].message.content
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                issues_data = json.loads(json_match.group())
                return [Issue(**issue) for issue in issues_data]
            
        except Exception as e:
            print(f"LLM analysis failed for {file_path}: {e}")
        
        return []
    
    async def create_work_plan(self, issues: List[Issue]) -> Dict[str, List[Issue]]:
        """Create work plan by categorizing issues for POUR agents"""
        plan = {
            "perceivable": [],
            "operable": [],
            "understandable": [],
            "robust": []
        }
        
        for issue in issues:
            if issue.category in plan:
                plan[issue.category].append(issue)
        
        return plan
