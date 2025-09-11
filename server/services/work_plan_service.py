import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from models.job import Issue

class WorkPlanService:
    """Service for generating detailed work plans for POUR agents"""
    
    def __init__(self):
        pass
    
    def generate_work_plan(self, issues: List[Issue]) -> Dict[str, Any]:
        """Generate a comprehensive work plan that assigns issues to POUR neurons"""
        
        # Classify issues by POUR category
        classified_issues = self._classify_issues_by_pour(issues)
        
        # Calculate priorities and estimated times
        work_plan = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_issues": len(issues),
                "version": "1.0"
            },
            "execution_plan": {
                "strategy": "sequential_by_priority",
                "estimated_total_time_minutes": 0,
                "parallel_execution": False
            },
            "pour_assignments": {},
            "priority_matrix": self._calculate_priority_matrix(classified_issues),
            "dependencies": self._analyze_dependencies(classified_issues),
            "resource_requirements": self._calculate_resource_requirements(classified_issues)
        }
        
        # Generate detailed assignments for each POUR category
        for category, category_issues in classified_issues.items():
            if category_issues:
                work_plan["pour_assignments"][category] = self._create_pour_assignment(
                    category, category_issues
                )
                work_plan["execution_plan"]["estimated_total_time_minutes"] += \
                    work_plan["pour_assignments"][category]["estimated_time_minutes"]
        
        return work_plan
    
    def _classify_issues_by_pour(self, issues: List[Issue]) -> Dict[str, List[Issue]]:
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
            else:
                # Default classification based on issue content
                category = self._infer_category_from_issue(issue)
                if category in classified:
                    classified[category].append(issue)
        
        return classified
    
    def _infer_category_from_issue(self, issue: Issue) -> str:
        """Infer POUR category from issue content when not explicitly set"""
        description_lower = issue.description.lower()
        code_lower = issue.code_snippet.lower()
        
        # Perceivable indicators
        if any(keyword in description_lower or keyword in code_lower for keyword in 
               ['alt', 'color', 'contrast', 'text', 'image', 'visual', 'font', 'size']):
            return "perceivable"
        
        # Operable indicators
        if any(keyword in description_lower or keyword in code_lower for keyword in 
               ['keyboard', 'focus', 'click', 'button', 'input', 'aria-label', 'tabindex', 'navigation']):
            return "operable"
        
        # Understandable indicators
        if any(keyword in description_lower or keyword in code_lower for keyword in 
               ['heading', 'form', 'label', 'instruction', 'error', 'language', 'content']):
            return "understandable"
        
        # Robust indicators
        if any(keyword in description_lower or keyword in code_lower for keyword in 
               ['role', 'aria-', 'semantic', 'html', 'valid', 'structure']):
            return "robust"
        
        # Default to operable for interactive elements
        return "operable"
    
    def _create_pour_assignment(self, category: str, issues: List[Issue]) -> Dict[str, Any]:
        """Create detailed assignment for a POUR category"""
        
        # Group issues by severity and file
        issues_by_severity = self._group_by_severity(issues)
        issues_by_file = self._group_by_file(issues)
        
        # Calculate estimated time based on complexity
        estimated_time = self._calculate_category_time(issues)
        
        # Generate specific tasks for each issue
        tasks = []
        for issue in issues:
            task = self._create_issue_task(issue)
            tasks.append(task)
        
        return {
            "category": category,
            "agent": f"{category}_agent",
            "total_issues": len(issues),
            "issues_by_severity": issues_by_severity,
            "issues_by_file": issues_by_file,
            "estimated_time_minutes": estimated_time,
            "complexity_score": self._calculate_complexity_score(issues),
            "tasks": tasks,
            "dependencies": self._get_category_dependencies(category, issues),
            "success_criteria": self._get_success_criteria(category),
            "validation_rules": self._get_validation_rules(category)
        }
    
    def _group_by_severity(self, issues: List[Issue]) -> Dict[str, List[Issue]]:
        """Group issues by severity level"""
        grouped = {"high": [], "medium": [], "low": []}
        for issue in issues:
            if issue.severity in grouped:
                grouped[issue.severity].append(issue)
        return grouped
    
    def _group_by_file(self, issues: List[Issue]) -> Dict[str, List[Issue]]:
        """Group issues by file path"""
        grouped = {}
        for issue in issues:
            file_path = issue.file_path
            if file_path not in grouped:
                grouped[file_path] = []
            grouped[file_path].append(issue)
        return grouped
    
    def _calculate_category_time(self, issues: List[Issue]) -> float:
        """Calculate estimated time for fixing issues in a category"""
        base_time = 0.5  # Base time per issue in minutes
        
        time_multipliers = {
            "high": 2.0,
            "medium": 1.0,
            "low": 0.5
        }
        
        total_time = 0
        for issue in issues:
            multiplier = time_multipliers.get(issue.severity, 1.0)
            total_time += base_time * multiplier
        
        return total_time
    
    def _calculate_complexity_score(self, issues: List[Issue]) -> float:
        """Calculate complexity score for a category (0-1)"""
        if not issues:
            return 0.0
        
        # Factors that increase complexity
        high_severity_count = len([i for i in issues if i.severity == "high"])
        unique_files = len(set(i.file_path for i in issues))
        avg_code_length = sum(len(i.code_snippet) for i in issues) / len(issues)
        
        # Normalize factors
        severity_factor = min(high_severity_count / len(issues), 1.0)
        file_factor = min(unique_files / 10, 1.0)  # Assume 10+ files is max complexity
        length_factor = min(avg_code_length / 1000, 1.0)  # Assume 1000 chars is max
        
        # Weighted average
        complexity = (severity_factor * 0.4 + file_factor * 0.3 + length_factor * 0.3)
        return min(complexity, 1.0)
    
    def _create_issue_task(self, issue: Issue) -> Dict[str, Any]:
        """Create a detailed task for a specific issue"""
        return {
            "issue_id": issue.id,
            "file_path": issue.file_path,
            "line_range": f"{issue.line_start}-{issue.line_end}",
            "severity": issue.severity,
            "description": issue.description,
            "rule_id": issue.rule_id,
            "code_snippet": issue.code_snippet,
            "estimated_fix_time_minutes": self._estimate_fix_time(issue),
            "required_skills": self._get_required_skills(issue),
            "expected_output": self._get_expected_output(issue),
            "validation_checks": self._get_validation_checks(issue)
        }
    
    def _estimate_fix_time(self, issue: Issue) -> float:
        """Estimate time to fix a specific issue"""
        base_times = {
            "high": 2.0,
            "medium": 1.0,
            "low": 0.5
        }
        
        base_time = base_times.get(issue.severity, 1.0)
        
        # Adjust based on code complexity
        code_length = len(issue.code_snippet)
        if code_length > 500:
            base_time *= 1.5
        elif code_length > 200:
            base_time *= 1.2
        
        return base_time
    
    def _get_required_skills(self, issue: Issue) -> List[str]:
        """Get required skills for fixing an issue"""
        skills = []
        
        if issue.category == "perceivable":
            skills.extend(["visual design", "color theory", "alt text writing"])
        elif issue.category == "operable":
            skills.extend(["keyboard navigation", "ARIA", "interaction design"])
        elif issue.category == "understandable":
            skills.extend(["content strategy", "information architecture", "UX writing"])
        elif issue.category == "robust":
            skills.extend(["HTML semantics", "ARIA", "standards compliance"])
        
        # Add technical skills based on file type
        if issue.file_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
            skills.append("JavaScript/TypeScript")
        elif issue.file_path.endswith('.css'):
            skills.append("CSS")
        elif issue.file_path.endswith('.html'):
            skills.append("HTML")
        
        return list(set(skills))  # Remove duplicates
    
    def _get_expected_output(self, issue: Issue) -> Dict[str, Any]:
        """Get expected output format for an issue fix"""
        return {
            "before_code": "Original problematic code",
            "after_code": "Fixed accessible code",
            "unified_diff": "Standard unified diff format",
            "confidence_score": "0.0-1.0 confidence in the fix",
            "explanation": "Brief explanation of the fix",
            "validation_notes": "Notes for validation phase"
        }
    
    def _get_validation_checks(self, issue: Issue) -> List[str]:
        """Get validation checks for an issue fix"""
        checks = []
        
        if issue.category == "perceivable":
            checks.extend([
                "Color contrast ratio meets WCAG standards",
                "Alt text is descriptive and meaningful",
                "Text is readable and properly sized"
            ])
        elif issue.category == "operable":
            checks.extend([
                "Keyboard navigation works correctly",
                "Focus indicators are visible",
                "ARIA labels are properly implemented"
            ])
        elif issue.category == "understandable":
            checks.extend([
                "Content is clear and understandable",
                "Form labels are properly associated",
                "Error messages are helpful"
            ])
        elif issue.category == "robust":
            checks.extend([
                "HTML is semantically correct",
                "ARIA roles are appropriate",
                "Code follows standards"
            ])
        
        return checks
    
    def _calculate_priority_matrix(self, classified_issues: Dict[str, List[Issue]]) -> Dict[str, Any]:
        """Calculate priority matrix for all categories"""
        matrix = {}
        
        for category, issues in classified_issues.items():
            if issues:
                high_priority = len([i for i in issues if i.severity == "high"])
                medium_priority = len([i for i in issues if i.severity == "medium"])
                low_priority = len([i for i in issues if i.severity == "low"])
                
                matrix[category] = {
                    "high_priority_count": high_priority,
                    "medium_priority_count": medium_priority,
                    "low_priority_count": low_priority,
                    "priority_score": (high_priority * 3 + medium_priority * 2 + low_priority * 1),
                    "recommended_order": self._get_recommended_order(category, high_priority, medium_priority, low_priority)
                }
        
        return matrix
    
    def _get_recommended_order(self, category: str, high: int, medium: int, low: int) -> int:
        """Get recommended processing order for a category"""
        # Higher priority scores get lower order numbers (processed first)
        priority_score = high * 3 + medium * 2 + low * 1
        
        # POUR-specific ordering preferences
        category_weights = {
            "perceivable": 1,  # Most fundamental
            "operable": 2,
            "understandable": 3,
            "robust": 4
        }
        
        return priority_score * category_weights.get(category, 5)
    
    def _analyze_dependencies(self, classified_issues: Dict[str, List[Issue]]) -> Dict[str, Any]:
        """Analyze dependencies between categories and issues"""
        dependencies = {
            "category_dependencies": {},
            "file_dependencies": {},
            "issue_dependencies": []
        }
        
        # Analyze file dependencies
        all_files = set()
        for issues in classified_issues.values():
            for issue in issues:
                all_files.add(issue.file_path)
        
        dependencies["file_dependencies"] = {
            "total_files": len(all_files),
            "files_with_multiple_categories": self._find_files_with_multiple_categories(classified_issues)
        }
        
        return dependencies
    
    def _find_files_with_multiple_categories(self, classified_issues: Dict[str, List[Issue]]) -> List[str]:
        """Find files that have issues in multiple POUR categories"""
        file_categories = {}
        
        for category, issues in classified_issues.items():
            for issue in issues:
                if issue.file_path not in file_categories:
                    file_categories[issue.file_path] = set()
                file_categories[issue.file_path].add(category)
        
        return [file_path for file_path, categories in file_categories.items() if len(categories) > 1]
    
    def _get_category_dependencies(self, category: str, issues: List[Issue]) -> List[str]:
        """Get dependencies for a specific category"""
        dependencies = []
        
        if category == "operable":
            dependencies.append("perceivable")  # Need to see content to make it operable
        elif category == "understandable":
            dependencies.extend(["perceivable", "operable"])  # Need content and interaction
        elif category == "robust":
            dependencies.extend(["perceivable", "operable", "understandable"])  # Builds on all others
        
        return dependencies
    
    def _get_success_criteria(self, category: str) -> List[str]:
        """Get success criteria for a POUR category"""
        criteria = {
            "perceivable": [
                "All images have appropriate alt text",
                "Color contrast meets WCAG AA standards",
                "Text is readable and properly sized",
                "Visual content is perceivable to screen readers"
            ],
            "operable": [
                "All functionality is keyboard accessible",
                "Focus indicators are visible and logical",
                "ARIA labels are properly implemented",
                "Interactive elements are reachable and usable"
            ],
            "understandable": [
                "Content is clear and understandable",
                "Form labels are properly associated",
                "Error messages are helpful and clear",
                "Navigation is intuitive and consistent"
            ],
            "robust": [
                "HTML is semantically correct",
                "ARIA roles are appropriate and valid",
                "Code follows web standards",
                "Compatible with assistive technologies"
            ]
        }
        
        return criteria.get(category, [])
    
    def _get_validation_rules(self, category: str) -> List[str]:
        """Get validation rules for a POUR category"""
        rules = {
            "perceivable": [
                "eslint-plugin-jsx-a11y/alt-text",
                "eslint-plugin-jsx-a11y/color-contrast",
                "axe-core color-contrast"
            ],
            "operable": [
                "eslint-plugin-jsx-a11y/keyboard-navigation",
                "eslint-plugin-jsx-a11y/focus-management",
                "axe-core keyboard"
            ],
            "understandable": [
                "eslint-plugin-jsx-a11y/heading-order",
                "eslint-plugin-jsx-a11y/form-labels",
                "axe-core language"
            ],
            "robust": [
                "eslint-plugin-jsx-a11y/aria-roles",
                "eslint-plugin-jsx-a11y/aria-props",
                "axe-core semantics"
            ]
        }
        
        return rules.get(category, [])
    
    def _calculate_resource_requirements(self, classified_issues: Dict[str, List[Issue]]) -> Dict[str, Any]:
        """Calculate resource requirements for the work plan"""
        total_issues = sum(len(issues) for issues in classified_issues.values())
        
        return {
            "estimated_total_time_minutes": sum(
                self._calculate_category_time(issues) 
                for issues in classified_issues.values()
            ),
            "memory_requirements": "Low to Medium",
            "cpu_requirements": "Medium",
            "concurrent_agents": min(len([cat for cat, issues in classified_issues.items() if issues]), 4),
            "validation_tools": ["eslint", "axe-core", "typescript"],
            "complexity_level": self._get_overall_complexity(classified_issues)
        }
    
    def _get_overall_complexity(self, classified_issues: Dict[str, List[Issue]]) -> str:
        """Get overall complexity level"""
        total_issues = sum(len(issues) for issues in classified_issues.values())
        
        if total_issues == 0:
            return "None"
        elif total_issues < 10:
            return "Low"
        elif total_issues < 50:
            return "Medium"
        else:
            return "High"
