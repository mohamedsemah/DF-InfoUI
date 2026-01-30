import os
import re
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple
import openai
import aiofiles
from models.job import Issue, Fix

class BrainAgent:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your_openai_api_key_here":
            raise ValueError("OPENAI_API_KEY environment variable must be set to a valid API key")
        self.client = openai.OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-5.1")
    
    async def analyze_files(self, job_id: str) -> List[Issue]:
        """Analyze files and detect accessibility issues using AST analysis"""
        from services.file_service import FileService
        from services.ast_service import ASTService
        
        file_service = FileService()
        ast_service = ASTService()
        
        # Use AST analysis for better issue detection
        ast_issues = await ast_service.analyze_files_ast(job_id)
        
        # Also run traditional regex-based analysis as fallback
        files = file_service.get_original_files(job_id)
        regex_issues = []
        
        for file_path in files:
            issues = await self._analyze_file(file_path)
            regex_issues.extend(issues)
        
        # Combine and deduplicate issues
        all_issues = self._deduplicate_issues(ast_issues + regex_issues)
        
        return all_issues
    
    def _deduplicate_issues(self, issues: List[Issue]) -> List[Issue]:
        """Remove duplicate issues based on file path and line number"""
        seen = set()
        unique_issues = []
        
        for issue in issues:
            key = (issue.file_path, issue.line_start, issue.rule_id)
            if key not in seen:
                seen.add(key)
                unique_issues.append(issue)
        
        return unique_issues
    
    async def coordinate_fixing_process(self, job_id: str, issues: List[Issue]) -> Dict[str, Any]:
        """Coordinate the complete fixing process with POUR agents"""
        from agents.pour_agents import POURAgents
        from services.file_service import FileService
        from services.validation_service import ValidationService
        from services.report_service import ReportService
        from services.performance_service import PerformanceService
        
        # Initialize services
        pour_agents = POURAgents()
        file_service = FileService()
        validation_service = ValidationService()
        report_service = ReportService()
        performance_service = PerformanceService()
        
        # Step 1: Generate work plan and classify issues into POUR categories
        work_plan = await performance_service.monitor_performance(
            "work_plan_generation", 
            self._generate_work_plan, 
            issues
        )
        classified_issues = self._classify_issues(issues)
        
        # Step 2: Send issues to POUR agents and get fixes
        all_fixes = []
        agent_reports = {}
        
        for category, category_issues in classified_issues.items():
            if category_issues:
                print(f"Processing {len(category_issues)} {category} issues...")
                
                # Get fixes from the appropriate agent with performance monitoring
                fixes = await performance_service.monitor_performance(
                    f"pour_agent_{category}",
                    self._get_fixes_from_agent,
                    pour_agents, 
                    category, 
                    category_issues
                )
                all_fixes.extend(fixes)
                
                # Generate agent report
                agent_reports[category] = {
                    "issues_count": len(category_issues),
                    "fixes_count": len(fixes),
                    "fixes": fixes
                }
        
        # Step 3: Apply fixes to files with line-aware patching
        await performance_service.monitor_performance(
            "patch_application",
            file_service.apply_patches_with_line_awareness,
            job_id, 
            all_fixes
        )
        
        # Step 4: Validate fixes
        validation_results = await performance_service.monitor_performance(
            "validation",
            validation_service.validate_fixes,
            job_id
        )
        
        # Step 5: Check for residual issues and re-route if needed
        if validation_results.get("remaining_issues", 0) > 0:
            print("Residual issues found, attempting re-routing...")
            residual_fixes = await self._handle_residual_issues(job_id, validation_results, pour_agents)
            if residual_fixes:
                await file_service.apply_patches_with_line_awareness(job_id, residual_fixes)
                validation_results = await validation_service.validate_fixes(job_id)
        
        # Step 6: Generate final artifacts
        await performance_service.monitor_performance(
            "create_fixed_zip",
            file_service.create_fixed_zip,
            job_id
        )
        await performance_service.monitor_performance(
            "generate_pdf_report",
            report_service.generate_pdf_report,
            job_id, 
            issues, 
            all_fixes, 
            validation_results
        )
        
        # Step 7: Save enhanced metadata for frontend
        report_data = {
            # Core data
            "work_plan": work_plan,
            "issues": [issue.dict() for issue in issues],
            "fixes": [fix.dict() for fix in all_fixes],
            "validation_results": validation_results,
            "agent_reports": agent_reports,
            
            # Enhanced metadata for frontend
            "summary": {
                "total_issues": len(issues),
                "total_fixes": len(all_fixes),
                "issues_by_category": self._categorize_issues_for_summary(issues),
                "issues_by_severity": self._categorize_issues_by_severity(issues),
                "fixes_by_category": self._categorize_fixes_for_summary(all_fixes, issues),
                "validation_passed": validation_results.get("passed", False),
                "remaining_issues": validation_results.get("remaining_issues", 0),
                "compliance_score": validation_results.get("summary", {}).get("compliance_score", 0.0),
                "processing_time": self._calculate_processing_time(),
                "files_processed": len(set(issue.file_path for issue in issues))
            },
            
            # Performance metrics
            "performance_metrics": await self._get_performance_metrics(job_id),
            
            # Accessibility compliance details
            "accessibility_compliance": {
                "wcag_level": self._determine_wcag_level(validation_results),
                "pour_compliance": self._calculate_pour_compliance(issues, all_fixes),
                "critical_issues": [issue.dict() for issue in issues if issue.severity == "high"],
                "recommendations": self._generate_recommendations(issues, validation_results)
            },
            
            # File analysis details
            "file_analysis": {
                "supported_files": self._get_supported_files(job_id),
                "file_types": self._analyze_file_types(issues),
                "complexity_score": self._calculate_complexity_score(issues)
            },
            
            # Agent performance
            "agent_performance": {
                "brain_agent": {
                    "issues_detected": len(issues),
                    "work_plan_generated": work_plan is not None,
                    "coordination_successful": len(all_fixes) > 0
                },
                "pour_agents": {
                    category: {
                        "issues_processed": report["issues_count"],
                        "fixes_generated": report["fixes_count"],
                        "success_rate": report["fixes_count"] / report["issues_count"] if report["issues_count"] > 0 else 0
                    }
                    for category, report in agent_reports.items()
                }
            },
            
            # Timestamps
            "timestamps": {
                "created_at": self._get_job_creation_time(job_id),
                "completed_at": self._get_current_timestamp(),
                "processing_duration": self._calculate_processing_time()
            }
        }
        
        # Save as report.json for frontend consumption
        report_json_path = file_service.get_report_json_path(job_id)
        async with aiofiles.open(report_json_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(report_data, indent=2, default=str))
        
        # Also save as metadata.json for internal use
        await file_service.save_job_metadata(job_id, report_data)
        
        return {
            "total_issues": len(issues),
            "total_fixes": len(all_fixes),
            "agent_reports": agent_reports,
            "validation_results": validation_results,
            "work_plan": work_plan
        }
    
    def _categorize_issues_for_summary(self, issues: List[Issue]) -> Dict[str, int]:
        """Categorize issues for summary display"""
        categories = {}
        for issue in issues:
            categories[issue.category] = categories.get(issue.category, 0) + 1
        return categories
    
    def _categorize_issues_by_severity(self, issues: List[Issue]) -> Dict[str, int]:
        """Categorize issues by severity for summary display"""
        severities = {}
        for issue in issues:
            severities[issue.severity] = severities.get(issue.severity, 0) + 1
        return severities
    
    def _categorize_fixes_for_summary(self, fixes: List[Fix], issues: List[Issue]) -> Dict[str, int]:
        """Categorize fixes by category for summary display"""
        categories = {}
        issue_map = {issue.id: issue for issue in issues}
        
        for fix in fixes:
            issue = issue_map.get(fix.issue_id)
            if issue:
                categories[issue.category] = categories.get(issue.category, 0) + 1
        return categories
    
    def _calculate_processing_time(self) -> float:
        """Calculate processing time (placeholder)"""
        return 0.0  # This would be calculated based on actual timing
    
    async def _get_performance_metrics(self, job_id: str) -> Dict[str, Any]:
        """Get performance metrics for the job"""
        from services.performance_service import PerformanceService
        performance_service = PerformanceService()
        return await performance_service.get_job_metrics(job_id)
    
    def _determine_wcag_level(self, validation_results: Dict[str, Any]) -> str:
        """Determine WCAG compliance level"""
        remaining_issues = validation_results.get("remaining_issues", 0)
        if remaining_issues == 0:
            return "AAA"
        elif remaining_issues <= 5:
            return "AA"
        else:
            return "A"
    
    def _calculate_pour_compliance(self, issues: List[Issue], fixes: List[Fix]) -> Dict[str, float]:
        """Calculate POUR compliance scores"""
        categories = ["perceivable", "operable", "understandable", "robust"]
        compliance = {}
        
        for category in categories:
            category_issues = [i for i in issues if i.category == category]
            category_fixes = [f for f in fixes if any(i.category == category for i in issues if i.id == f.issue_id)]
            
            if category_issues:
                compliance[category] = len(category_fixes) / len(category_issues)
            else:
                compliance[category] = 1.0
        
        return compliance
    
    def _generate_recommendations(self, issues: List[Issue], validation_results: Dict[str, Any]) -> List[str]:
        """Generate accessibility recommendations"""
        recommendations = []
        
        if validation_results.get("remaining_issues", 0) > 0:
            recommendations.append("Review and address remaining accessibility issues")
        
        high_severity_issues = [i for i in issues if i.severity == "high"]
        if high_severity_issues:
            recommendations.append(f"Address {len(high_severity_issues)} high-severity accessibility issues")
        
        if any(i.category == "perceivable" for i in issues):
            recommendations.append("Ensure all images have descriptive alt text")
        
        if any(i.category == "operable" for i in issues):
            recommendations.append("Verify keyboard navigation and focus management")
        
        return recommendations
    
    def _get_supported_files(self, job_id: str) -> List[str]:
        """Get list of supported file types in the job"""
        from services.file_service import FileService
        file_service = FileService()
        files = file_service.get_original_files(job_id)
        return list(set(f.suffix for f in files))
    
    def _analyze_file_types(self, issues: List[Issue]) -> Dict[str, int]:
        """Analyze file types from issues"""
        file_types = {}
        for issue in issues:
            file_ext = Path(issue.file_path).suffix
            file_types[file_ext] = file_types.get(file_ext, 0) + 1
        return file_types
    
    def _calculate_complexity_score(self, issues: List[Issue]) -> float:
        """Calculate complexity score based on issues"""
        if not issues:
            return 0.0
        
        # Simple complexity calculation based on issue count and severity
        severity_weights = {"high": 3, "medium": 2, "low": 1}
        total_weight = sum(severity_weights.get(issue.severity, 1) for issue in issues)
        return min(total_weight / len(issues), 3.0)  # Normalize to 0-3 scale
    
    def _get_job_creation_time(self, job_id: str) -> str:
        """Get job creation time (placeholder)"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    async def _generate_work_plan(self, issues: List[Issue]) -> Dict[str, Any]:
        """Generate a detailed structured work plan for POUR agents"""
        from services.work_plan_service import WorkPlanService
        
        work_plan_service = WorkPlanService()
        return work_plan_service.generate_work_plan(issues)
    
    async def _handle_residual_issues(self, job_id: str, validation_results: Dict[str, Any], pour_agents) -> List[Fix]:
        """Handle residual issues by re-routing to appropriate agents"""
        from services.rerouting_service import ReroutingService
        
        rerouting_service = ReroutingService()
        
        # Analyze validation results to identify residual issues
        residual_issues = await rerouting_service.analyze_residual_issues(job_id, validation_results)
        
        if not residual_issues:
            print("No residual issues found for re-routing")
            return []
        
        print(f"Found {len(residual_issues)} residual issues for re-routing")
        
        # Re-route issues to appropriate POUR agents
        rerouted_fixes = await rerouting_service.reroute_issues(job_id, residual_issues, pour_agents)
        
        if rerouted_fixes:
            print(f"Generated {len(rerouted_fixes)} re-routed fixes")
            
            # Validate the re-routed fixes
            validation_result = await rerouting_service.validate_rerouted_fixes(job_id, rerouted_fixes)
            
            if validation_result["success"]:
                print("Re-routed fixes successfully resolved remaining issues")
            else:
                print(f"Re-routed fixes still leave {validation_result['remaining_issues']} issues unresolved")
        
        return rerouted_fixes
    
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
