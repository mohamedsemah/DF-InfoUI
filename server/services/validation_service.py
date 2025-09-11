import os
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any
from models.job import ValidationResult

class ValidationService:
    def __init__(self):
        self.data_dir = Path(os.getenv("DATA_DIR", "/app/data"))
    
    async def validate_fixes(self, job_id: str) -> Dict[str, Any]:
        """Validate fixes using comprehensive validation collection"""
        job_dir = self.data_dir / job_id
        fixed_dir = job_dir / "fixed"
        
        validation_results = {
            "passed": True,
            "remaining_issues": 0,
            "results": [],
            "summary": {
                "total_files_checked": 0,
                "files_with_issues": 0,
                "issues_by_type": {},
                "issues_by_severity": {"high": 0, "medium": 0, "low": 0},
                "validation_tools_used": [],
                "compliance_score": 0.0
            }
        }
        
        # Run comprehensive validation
        validation_tasks = [
            ("TypeScript Compilation", self._run_typescript_compilation(fixed_dir)),
            ("ESLint Accessibility", self._run_eslint_validation(fixed_dir)),
            ("Axe-Core Validation", self._run_axe_validation(fixed_dir)),
            ("HTML Validation", self._run_html_validation(fixed_dir)),
            ("CSS Validation", self._run_css_validation(fixed_dir))
        ]
        
        # Execute all validation tasks
        for tool_name, task in validation_tasks:
            try:
                results = await task
                validation_results["results"].extend(results)
                validation_results["summary"]["validation_tools_used"].append(tool_name)
            except Exception as e:
                print(f"Validation tool {tool_name} failed: {e}")
                # Add a failed result for this tool
                validation_results["results"].append(ValidationResult(
                    file_path="system",
                    passed=False,
                    errors=[f"{tool_name} validation failed: {str(e)}"],
                    warnings=[]
                ))
        
        # Analyze results comprehensively
        validation_results.update(await self._analyze_validation_results(validation_results["results"]))
        
        return validation_results
    
    async def _analyze_validation_results(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """Analyze validation results to provide comprehensive insights"""
        analysis = {
            "remaining_issues": 0,
            "passed": True,
            "summary": {
                "total_files_checked": len(set(r.file_path for r in results)),
                "files_with_issues": 0,
                "issues_by_type": {},
                "issues_by_severity": {"high": 0, "medium": 0, "low": 0},
                "compliance_score": 0.0
            }
        }
        
        files_with_issues = set()
        total_issues = 0
        
        for result in results:
            if not result.passed:
                files_with_issues.add(result.file_path)
                total_issues += len(result.errors) + len(result.warnings)
                
                # Categorize issues by type
                for error in result.errors:
                    issue_type = self._categorize_issue_type(error)
                    analysis["summary"]["issues_by_type"][issue_type] = \
                        analysis["summary"]["issues_by_type"].get(issue_type, 0) + 1
                    
                    # Categorize by severity
                    severity = self._determine_issue_severity(error)
                    analysis["summary"]["issues_by_severity"][severity] += 1
        
        analysis["remaining_issues"] = total_issues
        analysis["passed"] = total_issues == 0
        analysis["summary"]["files_with_issues"] = len(files_with_issues)
        
        # Calculate compliance score
        total_files = analysis["summary"]["total_files_checked"]
        if total_files > 0:
            analysis["summary"]["compliance_score"] = (total_files - len(files_with_issues)) / total_files
        
        return analysis
    
    def _categorize_issue_type(self, error: str) -> str:
        """Categorize validation error by type"""
        error_lower = error.lower()
        
        if any(keyword in error_lower for keyword in ['alt', 'image', 'img']):
            return "image_accessibility"
        elif any(keyword in error_lower for keyword in ['aria', 'role', 'label']):
            return "aria_accessibility"
        elif any(keyword in error_lower for keyword in ['keyboard', 'focus', 'tabindex']):
            return "keyboard_accessibility"
        elif any(keyword in error_lower for keyword in ['color', 'contrast']):
            return "visual_accessibility"
        elif any(keyword in error_lower for keyword in ['heading', 'h1', 'h2', 'h3']):
            return "semantic_structure"
        elif any(keyword in error_lower for keyword in ['form', 'input', 'label']):
            return "form_accessibility"
        elif any(keyword in error_lower for keyword in ['link', 'href']):
            return "link_accessibility"
        elif any(keyword in error_lower for keyword in ['syntax', 'parse', 'compile']):
            return "syntax_error"
        else:
            return "other"
    
    def _determine_issue_severity(self, error: str) -> str:
        """Determine issue severity based on error content"""
        error_lower = error.lower()
        
        # High severity keywords
        if any(keyword in error_lower for keyword in [
            'critical', 'error', 'missing alt', 'no label', 'keyboard trap',
            'color contrast', 'focus management'
        ]):
            return "high"
        
        # Medium severity keywords
        elif any(keyword in error_lower for keyword in [
            'warning', 'aria', 'semantic', 'heading', 'form'
        ]):
            return "medium"
        
        # Low severity keywords
        else:
            return "low"
    
    async def _run_eslint_validation(self, fixed_dir: Path) -> List[ValidationResult]:
        """Run eslint with jsx-a11y plugin on fixed files"""
        results = []
        
        # Find all JS/JSX/TS/TSX files
        js_files = []
        for ext in ['*.js', '*.jsx', '*.ts', '*.tsx']:
            js_files.extend(fixed_dir.rglob(ext))
        
        for file_path in js_files:
            try:
                # Run eslint on the file
                cmd = [
                    'eslint',
                    '--config', '/dev/null',
                    '--env', 'browser,es6',
                    '--parser-options', '{"ecmaVersion": 2020, "sourceType": "module", "ecmaFeatures": {"jsx": true}}',
                    '--plugin', 'jsx-a11y',
                    '--rule', 'jsx-a11y/alt-text: error',
                    '--rule', 'jsx-a11y/aria-props: error',
                    '--rule', 'jsx-a11y/aria-proptypes: error',
                    '--rule', 'jsx-a11y/aria-unsupported-elements: error',
                    '--rule', 'jsx-a11y/role-has-required-aria-props: error',
                    '--rule', 'jsx-a11y/role-supports-aria-props: error',
                    '--format', 'json',
                    str(file_path)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=fixed_dir)
                
                if result.returncode == 0:
                    # No errors
                    results.append(ValidationResult(
                        file_path=str(file_path),
                        passed=True,
                        errors=[],
                        warnings=[]
                    ))
                else:
                    # Parse eslint output
                    try:
                        eslint_output = json.loads(result.stdout)
                        errors = []
                        warnings = []
                        
                        for file_result in eslint_output:
                            for message in file_result.get('messages', []):
                                if message['severity'] == 2:  # Error
                                    errors.append(f"Line {message['line']}: {message['message']}")
                                elif message['severity'] == 1:  # Warning
                                    warnings.append(f"Line {message['line']}: {message['message']}")
                        
                        results.append(ValidationResult(
                            file_path=str(file_path),
                            passed=len(errors) == 0,
                            errors=errors,
                            warnings=warnings
                        ))
                    except json.JSONDecodeError:
                        # Fallback if JSON parsing fails
                        results.append(ValidationResult(
                            file_path=str(file_path),
                            passed=False,
                            errors=[result.stderr],
                            warnings=[]
                        ))
            
            except Exception as e:
                results.append(ValidationResult(
                    file_path=str(file_path),
                    passed=False,
                    errors=[f"Validation failed: {str(e)}"],
                    warnings=[]
                ))
        
        return results
    
    async def _run_axe_validation(self, fixed_dir: Path) -> List[ValidationResult]:
        """Run axe-core validation on HTML files and rendered JSX/TSX files"""
        results = []
        
        # Find all HTML files
        html_files = list(fixed_dir.rglob('*.html'))
        
        # Find JSX/TSX files and render them for axe-core validation
        from services.ssr_service import SSRService
        ssr_service = SSRService()
        
        # Extract job_id from the path
        job_id = fixed_dir.parent.name
        rendered_files = await ssr_service.render_jsx_tsx_files(job_id)
        
        # Add rendered files to validation list
        all_files = html_files + rendered_files
        
        for file_path in all_files:
            try:
                # Create a simple axe-core validation script
                axe_script = f"""
                const fs = require('fs');
                const {{ JSDOM }} = require('jsdom');
                const axe = require('axe-core');
                
                const html = fs.readFileSync('{file_path}', 'utf8');
                const dom = new JSDOM(html);
                const window = dom.window;
                const document = window.document;
                
                axe.run(document, (err, results) => {{
                    if (err) {{
                        console.log(JSON.stringify({{error: err.message}}));
                    }} else {{
                        console.log(JSON.stringify(results));
                    }}
                }});
                """
                
                # Write script to temporary file
                script_path = fixed_dir / 'axe_validation.js'
                with open(script_path, 'w') as f:
                    f.write(axe_script)
                
                # Run the script
                result = subprocess.run(
                    ['node', str(script_path)],
                    capture_output=True,
                    text=True,
                    cwd=fixed_dir
                )
                
                # Clean up script
                script_path.unlink()
                
                if result.returncode == 0:
                    try:
                        axe_output = json.loads(result.stdout)
                        
                        if 'error' in axe_output:
                            results.append(ValidationResult(
                                file_path=str(file_path),
                                passed=False,
                                errors=[axe_output['error']],
                                warnings=[]
                            ))
                        else:
                            violations = axe_output.get('violations', [])
                            errors = []
                            warnings = []
                            
                            for violation in violations:
                                for node in violation.get('nodes', []):
                                    errors.append(f"{violation['description']}: {node['html']}")
                            
                            results.append(ValidationResult(
                                file_path=str(file_path),
                                passed=len(violations) == 0,
                                errors=errors,
                                warnings=warnings
                            ))
                    except json.JSONDecodeError:
                        results.append(ValidationResult(
                            file_path=str(file_path),
                            passed=False,
                            errors=[result.stderr],
                            warnings=[]
                        ))
                else:
                    results.append(ValidationResult(
                        file_path=str(file_path),
                        passed=False,
                        errors=[result.stderr],
                        warnings=[]
                    ))
            
            except Exception as e:
                results.append(ValidationResult(
                    file_path=str(file_path),
                    passed=False,
                    errors=[f"Axe validation failed: {str(e)}"],
                    warnings=[]
                ))
        
        return results
    
    async def _run_typescript_compilation(self, fixed_dir: Path) -> List[ValidationResult]:
        """Run TypeScript compilation to validate syntax correctness"""
        results = []
        
        # Find all TypeScript files
        ts_files = []
        for ext in ['*.ts', '*.tsx']:
            ts_files.extend(fixed_dir.rglob(ext))
        
        if not ts_files:
            return results
        
        try:
            # Create a temporary tsconfig.json for compilation
            tsconfig = {
                "compilerOptions": {
                    "target": "ES2020",
                    "module": "ESNext",
                    "moduleResolution": "node",
                    "jsx": "react-jsx",
                    "strict": True,
                    "esModuleInterop": True,
                    "skipLibCheck": True,
                    "forceConsistentCasingInFileNames": True,
                    "allowSyntheticDefaultImports": True,
                    "resolveJsonModule": True,
                    "isolatedModules": True,
                    "noEmit": True
                },
                "include": ["**/*.ts", "**/*.tsx"],
                "exclude": ["node_modules", "dist"]
            }
            
            tsconfig_path = fixed_dir / "tsconfig.json"
            with open(tsconfig_path, 'w') as f:
                json.dump(tsconfig, f, indent=2)
            
            # Run TypeScript compiler
            cmd = ['npx', 'tsc', '--noEmit', '--project', str(tsconfig_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=fixed_dir)
            
            # Clean up tsconfig
            tsconfig_path.unlink()
            
            if result.returncode == 0:
                # No errors
                for ts_file in ts_files:
                    results.append(ValidationResult(
                        file_path=str(ts_file),
                        passed=True,
                        errors=[],
                        warnings=[]
                    ))
            else:
                # Parse TypeScript errors
                error_lines = result.stderr.split('\n')
                current_file = None
                current_errors = []
                
                for line in error_lines:
                    if line.strip() and not line.startswith(' '):
                        # New file error
                        if current_file and current_errors:
                            results.append(ValidationResult(
                                file_path=current_file,
                                passed=False,
                                errors=current_errors,
                                warnings=[]
                            ))
                        current_file = line.split('(')[0].strip()
                        current_errors = []
                    elif line.strip() and current_file:
                        current_errors.append(line.strip())
                
                # Add the last file's errors
                if current_file and current_errors:
                    results.append(ValidationResult(
                        file_path=current_file,
                        passed=False,
                        errors=current_errors,
                        warnings=[]
                    ))
        
        except Exception as e:
            # If TypeScript compilation fails entirely, mark all TS files as failed
            for ts_file in ts_files:
                results.append(ValidationResult(
                    file_path=str(ts_file),
                    passed=False,
                    errors=[f"TypeScript compilation failed: {str(e)}"],
                    warnings=[]
                ))
        
        return results
    
    async def _run_html_validation(self, fixed_dir: Path) -> List[ValidationResult]:
        """Run HTML validation on fixed files"""
        results = []
        
        # Find all HTML files
        html_files = list(fixed_dir.rglob('*.html'))
        
        for file_path in html_files:
            try:
                # Basic HTML structure validation
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                errors = []
                warnings = []
                
                # Check for basic HTML structure
                if not content.strip().startswith('<!DOCTYPE'):
                    warnings.append("Missing DOCTYPE declaration")
                
                if '<html' not in content:
                    errors.append("Missing <html> tag")
                
                if '<head>' not in content:
                    errors.append("Missing <head> section")
                
                if '<body>' not in content:
                    errors.append("Missing <body> section")
                
                # Check for accessibility attributes
                if '<img' in content and 'alt=' not in content:
                    errors.append("Images missing alt attributes")
                
                if '<input' in content and 'type=' not in content:
                    warnings.append("Input elements missing type attributes")
                
                results.append(ValidationResult(
                    file_path=str(file_path),
                    passed=len(errors) == 0,
                    errors=errors,
                    warnings=warnings
                ))
                
            except Exception as e:
                results.append(ValidationResult(
                    file_path=str(file_path),
                    passed=False,
                    errors=[f"HTML validation failed: {str(e)}"],
                    warnings=[]
                ))
        
        return results
    
    async def _run_css_validation(self, fixed_dir: Path) -> List[ValidationResult]:
        """Run CSS validation on fixed files"""
        results = []
        
        # Find all CSS files
        css_files = list(fixed_dir.rglob('*.css'))
        
        for file_path in css_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                errors = []
                warnings = []
                
                # Basic CSS syntax validation
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    line = line.strip()
                    if not line or line.startswith('/*') or line.startswith('*'):
                        continue
                    
                    # Check for unclosed brackets
                    if '{' in line and '}' not in line:
                        # Check if closing bracket is in next few lines
                        found_closing = False
                        for j in range(i, min(i + 10, len(lines))):
                            if '}' in lines[j]:
                                found_closing = True
                                break
                        if not found_closing:
                            errors.append(f"Unclosed CSS rule at line {i}")
                    
                    # Check for common CSS issues
                    if 'color:' in line and 'background-color:' not in line:
                        if any(color in line.lower() for color in ['#000', 'black', 'rgb(0,0,0)']):
                            warnings.append(f"Potential contrast issue at line {i}: dark text without background")
                
                results.append(ValidationResult(
                    file_path=str(file_path),
                    passed=len(errors) == 0,
                    errors=errors,
                    warnings=warnings
                ))
                
            except Exception as e:
                results.append(ValidationResult(
                    file_path=str(file_path),
                    passed=False,
                    errors=[f"CSS validation failed: {str(e)}"],
                    warnings=[]
                ))
        
        return results
