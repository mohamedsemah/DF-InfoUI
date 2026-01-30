import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import aiofiles
from models.job import Issue, Fix, ValidationResult

class ReroutingService:
    """Service for handling residual issues and re-routing them to appropriate agents"""
    
    def __init__(self):
        from utils.path_utils import get_data_dir
        self.data_dir = get_data_dir()
    
    async def analyze_residual_issues(self, job_id: str, validation_results: Dict[str, Any]) -> List[Issue]:
        """Analyze validation results to identify residual issues that need re-routing"""
        residual_issues = []
        
        for result in validation_results.get("results", []):
            if not result.passed and result.errors:
                # Convert validation errors back to issues for re-routing
                for error in result.errors:
                    issue = await self._convert_validation_error_to_issue(result, error)
                    if issue:
                        residual_issues.append(issue)
        
        return residual_issues
    
    async def _convert_validation_error_to_issue(self, validation_result: ValidationResult, error: str) -> Optional[Issue]:
        """Convert a validation error back to an Issue for re-routing"""
        file_path = Path(validation_result.file_path)
        
        # Extract line number from error message if available
        line_match = re.search(r'Line (\d+)', error)
        line_number = int(line_match.group(1)) if line_match else 1
        
        # Categorize error based on content
        category = self._categorize_error(error)
        severity = self._determine_severity(error)
        rule_id = self._extract_rule_id(error)
        
        # Read the problematic code snippet
        code_snippet = await self._extract_code_snippet(file_path, line_number)
        
        return Issue(
            id=f"residual_{file_path.name}_{line_number}_{rule_id}",
            file_path=str(file_path),
            line_start=line_number,
            line_end=line_number,
            category=category,
            severity=severity,
            description=f"Residual issue: {error}",
            code_snippet=code_snippet,
            rule_id=rule_id
        )
    
    def _categorize_error(self, error: str) -> str:
        """Categorize error into POUR category based on error content"""
        error_lower = error.lower()
        
        # Perceivable issues
        if any(keyword in error_lower for keyword in ['alt', 'color', 'contrast', 'text', 'image', 'visual']):
            return "perceivable"
        
        # Operable issues
        if any(keyword in error_lower for keyword in ['keyboard', 'focus', 'click', 'button', 'input', 'aria-label', 'tabindex']):
            return "operable"
        
        # Understandable issues
        if any(keyword in error_lower for keyword in ['heading', 'form', 'label', 'instruction', 'error', 'language']):
            return "understandable"
        
        # Robust issues
        if any(keyword in error_lower for keyword in ['role', 'aria-', 'semantic', 'html', 'valid']):
            return "robust"
        
        # Default to operable for interactive elements
        return "operable"
    
    def _determine_severity(self, error: str) -> str:
        """Determine severity based on error content"""
        error_lower = error.lower()
        
        if any(keyword in error_lower for keyword in ['error', 'required', 'missing', 'invalid']):
            return "high"
        elif any(keyword in error_lower for keyword in ['warning', 'suggest', 'recommend']):
            return "medium"
        else:
            return "low"
    
    def _extract_rule_id(self, error: str) -> str:
        """Extract rule ID from error message"""
        # Common rule patterns
        if 'alt' in error.lower():
            return "img-alt"
        elif 'aria-label' in error.lower():
            return "aria-label"
        elif 'heading' in error.lower():
            return "heading-order"
        elif 'color' in error.lower():
            return "color-contrast"
        elif 'focus' in error.lower():
            return "focus-visible"
        elif 'role' in error.lower():
            return "role"
        else:
            return "unknown"
    
    async def _extract_code_snippet(self, file_path: Path, line_number: int) -> str:
        """Extract code snippet around the problematic line"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                lines = await f.readlines()
            
            # Get context around the line (3 lines before and after)
            start_line = max(0, line_number - 4)
            end_line = min(len(lines), line_number + 3)
            
            snippet_lines = lines[start_line:end_line]
            return ''.join(snippet_lines).strip()
        
        except Exception as e:
            print(f"Error extracting code snippet from {file_path}: {e}")
            return ""
    
    async def reroute_issues(self, job_id: str, residual_issues: List[Issue], pour_agents) -> List[Fix]:
        """Re-route residual issues to appropriate POUR agents"""
        if not residual_issues:
            return []
        
        print(f"Re-routing {len(residual_issues)} residual issues...")
        
        # Group issues by category
        issues_by_category = {
            "perceivable": [],
            "operable": [],
            "understandable": [],
            "robust": []
        }
        
        for issue in residual_issues:
            if issue.category in issues_by_category:
                issues_by_category[issue.category].append(issue)
        
        # Re-route to appropriate agents
        rerouted_fixes = []
        
        for category, category_issues in issues_by_category.items():
            if category_issues:
                print(f"Re-routing {len(category_issues)} {category} issues...")
                
                # Get fixes from the appropriate agent
                fixes = await self._get_fixes_from_agent(pour_agents, category, category_issues)
                rerouted_fixes.extend(fixes)
        
        return rerouted_fixes
    
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
    
    async def validate_rerouted_fixes(self, job_id: str, rerouted_fixes: List[Fix]) -> Dict[str, Any]:
        """Validate the re-routed fixes to ensure they resolved the issues"""
        if not rerouted_fixes:
            return {"success": True, "message": "No fixes to validate"}
        
        # Apply the re-routed fixes
        from services.file_service import FileService
        file_service = FileService()
        
        apply_result = await file_service.apply_patches_with_line_awareness(job_id, rerouted_fixes)
        
        # Validate the fixes
        from services.validation_service import ValidationService
        validation_service = ValidationService()
        
        validation_results = await validation_service.validate_fixes(job_id)
        
        return {
            "success": validation_results.get("passed", False),
            "remaining_issues": validation_results.get("remaining_issues", 0),
            "applied_fixes": apply_result.get("successful_patches", 0),
            "failed_fixes": apply_result.get("failed_patches", 0),
            "fuzzy_matches": apply_result.get("fuzzy_matches", 0),
            "validation_results": validation_results
        }
    
    async def create_rerouting_report(self, job_id: str, original_issues: int, residual_issues: List[Issue], rerouted_fixes: List[Fix], validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comprehensive report of the re-routing process"""
        return {
            "original_issues": original_issues,
            "residual_issues": len(residual_issues),
            "rerouted_fixes": len(rerouted_fixes),
            "successful_reroutes": len([f for f in rerouted_fixes if f.applied]),
            "failed_reroutes": len([f for f in rerouted_fixes if not f.applied]),
            "final_validation_passed": validation_results.get("success", False),
            "final_remaining_issues": validation_results.get("remaining_issues", 0),
            "rerouting_summary": {
                "perceivable": len([i for i in residual_issues if i.category == "perceivable"]),
                "operable": len([i for i in residual_issues if i.category == "operable"]),
                "understandable": len([i for i in residual_issues if i.category == "understandable"]),
                "robust": len([i for i in residual_issues if i.category == "robust"])
            }
        }
