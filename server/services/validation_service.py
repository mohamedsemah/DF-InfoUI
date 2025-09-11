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
        """Validate fixes using eslint, axe-core, and TypeScript compilation"""
        job_dir = self.data_dir / job_id
        fixed_dir = job_dir / "fixed"
        
        validation_results = {
            "passed": True,
            "remaining_issues": 0,
            "results": []
        }
        
        # Run TypeScript compilation validation
        ts_results = await self._run_typescript_compilation(fixed_dir)
        validation_results["results"].extend(ts_results)
        
        # Run eslint validation
        eslint_results = await self._run_eslint_validation(fixed_dir)
        validation_results["results"].extend(eslint_results)
        
        # Run axe-core validation
        axe_results = await self._run_axe_validation(fixed_dir)
        validation_results["results"].extend(axe_results)
        
        # Count remaining issues
        validation_results["remaining_issues"] = sum(
            1 for result in validation_results["results"] 
            if not result.passed
        )
        
        validation_results["passed"] = validation_results["remaining_issues"] == 0
        
        return validation_results
    
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
        """Run axe-core validation on HTML files"""
        results = []
        
        # Find all HTML files
        html_files = list(fixed_dir.rglob('*.html'))
        
        for file_path in html_files:
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
