import os
import json
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Tuple
import asyncio
from models.job import Issue

class ASTService:
    """Service for AST analysis using Babel and PostCSS via node subprocess"""
    
    def __init__(self):
        self.data_dir = Path(os.getenv("DATA_DIR", "/app/data"))
    
    async def analyze_files_ast(self, job_id: str) -> List[Issue]:
        """Analyze files using AST parsing for better issue detection"""
        job_dir = self.data_dir / job_id
        original_dir = job_dir / "original"
        
        all_issues = []
        
        # Analyze JavaScript/TypeScript files with Babel
        js_files = []
        for ext in ['*.js', '*.jsx', '*.ts', '*.tsx']:
            js_files.extend(original_dir.rglob(ext))
        
        for file_path in js_files:
            issues = await self._analyze_js_ts_ast(file_path)
            all_issues.extend(issues)
        
        # Analyze CSS files with PostCSS
        css_files = list(original_dir.rglob('*.css'))
        for file_path in css_files:
            issues = await self._analyze_css_ast(file_path)
            all_issues.extend(issues)
        
        return all_issues
    
    async def _analyze_js_ts_ast(self, file_path: Path) -> List[Issue]:
        """Analyze JS/TS/JSX/TSX files using Babel AST with esprima fallback"""
        try:
            # Try Babel first, fallback to esprima if needed
            issues = await self._analyze_with_babel(file_path)
            if not issues:
                issues = await self._analyze_with_esprima(file_path)
            return issues
        except Exception as e:
            print(f"Error analyzing {file_path} with AST: {e}")
            return []
    
    async def _analyze_with_babel(self, file_path: Path) -> List[Issue]:
        """Analyze using Babel parser"""
        try:
            # Create a Node.js script for Babel AST analysis
            babel_script = f"""
            const fs = require('fs');
            const babel = require('@babel/core');
            const parser = require('@babel/parser');
            const traverse = require('@babel/traverse').default;
            
            const filePath = '{file_path}';
            const content = fs.readFileSync(filePath, 'utf8');
            
            const issues = [];
            
            try {{
                // Parse the file
                const ast = parser.parse(content, {{
                    sourceType: 'module',
                    plugins: ['jsx', 'typescript', 'decorators-legacy', 'classProperties']
                }});
                
                // Traverse AST to find accessibility issues
                traverse(ast, {{
                    // Check for missing alt attributes in JSX
                    JSXElement(path) {{
                        const {{ openingElement }} = path.node;
                        if (openingElement.name.name === 'img') {{
                            const hasAlt = openingElement.attributes.some(attr => 
                                attr.type === 'JSXAttribute' && attr.name.name === 'alt'
                            );
                            if (!hasAlt) {{
                                issues.push({{
                                    id: `${{filePath}}_${{path.node.loc.start.line}}_missing_alt`,
                                    file_path: filePath,
                                    line_start: path.node.loc.start.line,
                                    line_end: path.node.loc.end.line,
                                    category: 'perceivable',
                                    severity: 'high',
                                    description: 'Image missing alt attribute',
                                    code_snippet: content.split('\\n')[path.node.loc.start.line - 1].trim(),
                                    rule_id: 'img-alt'
                                }});
                            }}
                        }}
                        
                        // Check for missing labels on form elements
                        if (['input', 'textarea', 'select'].includes(openingElement.name.name)) {{
                            const hasLabel = openingElement.attributes.some(attr => 
                                attr.type === 'JSXAttribute' && 
                                (attr.name.name === 'aria-label' || attr.name.name === 'aria-labelledby')
                            );
                            if (!hasLabel) {{
                                issues.push({{
                                    id: `${{filePath}}_${{path.node.loc.start.line}}_missing_label`,
                                    file_path: filePath,
                                    line_start: path.node.loc.start.line,
                                    line_end: path.node.loc.end.line,
                                    category: 'operable',
                                    severity: 'high',
                                    description: 'Form element missing label or aria-label',
                                    code_snippet: content.split('\\n')[path.node.loc.start.line - 1].trim(),
                                    rule_id: 'label'
                                }});
                            }}
                        }}
                    }},
                    
                    // Check for onClick handlers without ARIA labels
                    CallExpression(path) {{
                        if (path.node.callee.property && path.node.callee.property.name === 'onClick') {{
                            const parent = path.findParent(p => p.isJSXElement());
                            if (parent) {{
                                const hasAriaLabel = parent.node.openingElement.attributes.some(attr => 
                                    attr.type === 'JSXAttribute' && 
                                    (attr.name.name === 'aria-label' || attr.name.name === 'aria-labelledby')
                                );
                                if (!hasAriaLabel) {{
                                    issues.push({{
                                        id: `${{filePath}}_${{path.node.loc.start.line}}_missing_aria`,
                                        file_path: filePath,
                                        line_start: path.node.loc.start.line,
                                        line_end: path.node.loc.end.line,
                                        category: 'operable',
                                        severity: 'medium',
                                        description: 'Interactive element missing ARIA label',
                                        code_snippet: content.split('\\n')[path.node.loc.start.line - 1].trim(),
                                        rule_id: 'aria-label'
                                    }});
                                }}
                            }}
                        }}
                    }},
                    
                    // Check for heading hierarchy
                    JSXElement(path) {{
                        const {{ openingElement }} = path.node;
                        const headingMatch = openingElement.name.name.match(/^h([1-6])$/);
                        if (headingMatch) {{
                            const level = parseInt(headingMatch[1]);
                            // This is a simplified check - in production, you'd track heading hierarchy
                            if (level > 1) {{
                                issues.push({{
                                    id: `${{filePath}}_${{path.node.loc.start.line}}_heading_check`,
                                    file_path: filePath,
                                    line_start: path.node.loc.start.line,
                                    line_end: path.node.loc.end.line,
                                    category: 'understandable',
                                    severity: 'medium',
                                    description: 'Verify heading hierarchy is logical',
                                    code_snippet: content.split('\\n')[path.node.loc.start.line - 1].trim(),
                                    rule_id: 'heading-order'
                                }});
                            }}
                        }}
                    }}
                }});
                
            }} catch (error) {{
                console.error('Babel parsing error:', error.message);
            }}
            
            console.log(JSON.stringify(issues));
            """
            
            # Write script to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(babel_script)
                script_path = f.name
            
            try:
                # Run the script
                result = subprocess.run(
                    ['node', script_path],
                    capture_output=True,
                    text=True,
                    cwd=str(file_path.parent)
                )
                
                if result.returncode == 0:
                    issues_data = json.loads(result.stdout)
                    issues = []
                    
                    for issue_data in issues_data:
                        # Extract enhanced code snippet data
                        snippet_data = await self.extract_code_snippets(
                            Path(issue_data['file_path']),
                            issue_data['line_start'],
                            issue_data['line_end']
                        )
                        
                        issue = Issue(
                            id=issue_data['id'],
                            file_path=issue_data['file_path'],
                            line_start=issue_data['line_start'],
                            line_end=issue_data['line_end'],
                            category=issue_data['category'],
                            severity=issue_data['severity'],
                            description=issue_data['description'],
                            code_snippet=issue_data['code_snippet'],
                            rule_id=issue_data['rule_id'],
                            code_snippet_data=snippet_data,
                            context_lines=snippet_data.get('context_lines', 3),
                            total_lines=snippet_data.get('total_lines')
                        )
                        issues.append(issue)
                    
                    return issues
                else:
                    print(f"Babel AST analysis failed for {file_path}: {result.stderr}")
                    return []
            
            finally:
                # Clean up script file
                os.unlink(script_path)
        
        except Exception as e:
            print(f"Error in AST analysis for {file_path}: {e}")
            return []
    
    async def _analyze_with_esprima(self, file_path: Path) -> List[Issue]:
        """Analyze using esprima parser as fallback"""
        try:
            # Create a Node.js script for esprima AST analysis
            esprima_script = f"""
            const fs = require('fs');
            const esprima = require('esprima');
            
            const filePath = '{file_path}';
            const content = fs.readFileSync(filePath, 'utf8');
            
            const issues = [];
            
            try {{
                // Parse the file with esprima
                const ast = esprima.parseScript(content, {{
                    loc: true,
                    range: true,
                    tokens: true,
                    comment: true
                }});
                
                // Simple accessibility checks
                function checkAccessibility(node) {{
                    if (node.type === 'CallExpression') {{
                        if (node.callee && node.callee.name === 'document') {{
                            if (node.arguments && node.arguments.length > 0) {{
                                const arg = node.arguments[0];
                                if (arg.type === 'Literal' && typeof arg.value === 'string') {{
                                    if (arg.value.includes('getElementById') && !arg.value.includes('aria-')) {{
                                        issues.push({{
                                            id: `${{filePath}}_${{node.loc.start.line}}_missing_aria`,
                                            file_path: filePath,
                                            line_start: node.loc.start.line,
                                            line_end: node.loc.end.line,
                                            category: 'operable',
                                            severity: 'medium',
                                            description: 'Element may need ARIA attributes for accessibility',
                                            code_snippet: content.split('\\n').slice(node.loc.start.line - 1, node.loc.end.line).join('\\n'),
                                            rule_id: 'aria-required'
                                        }});
                                    }}
                                }}
                            }}
                        }}
                    }}
                    
                    if (node.type === 'Literal' && typeof node.value === 'string') {{
                        if (node.value.includes('onclick') || node.value.includes('onkeydown')) {{
                            issues.push({{
                                id: `${{filePath}}_${{node.loc.start.line}}_event_handler`,
                                file_path: filePath,
                                line_start: node.loc.start.line,
                                line_end: node.loc.end.line,
                                category: 'operable',
                                severity: 'high',
                                description: 'Event handlers should be accessible via keyboard',
                                code_snippet: content.split('\\n').slice(node.loc.start.line - 1, node.loc.end.line).join('\\n'),
                                rule_id: 'keyboard-accessible'
                            }});
                        }}
                    }}
                }}
                
                // Traverse AST
                function traverse(node) {{
                    if (node && typeof node === 'object') {{
                        checkAccessibility(node);
                        for (const key in node) {{
                            if (node.hasOwnProperty(key) && typeof node[key] === 'object') {{
                                traverse(node[key]);
                            }}
                        }}
                    }}
                }}
                
                traverse(ast);
                
                console.log(JSON.stringify(issues));
                
            }} catch (error) {{
                console.error('Esprima parsing error:', error.message);
                console.log('[]');
            }}
            """
            
            # Write script to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(esprima_script)
                script_path = f.name
            
            try:
                # Run the script
                result = subprocess.run(
                    ['node', script_path],
                    capture_output=True,
                    text=True,
                    cwd=str(file_path.parent)
                )
                
                if result.returncode == 0:
                    issues_data = json.loads(result.stdout)
                    issues = []
                    
                    for issue_data in issues_data:
                        # Extract enhanced code snippet data
                        snippet_data = await self.extract_code_snippets(
                            Path(issue_data['file_path']),
                            issue_data['line_start'],
                            issue_data['line_end']
                        )
                        
                        issue = Issue(
                            id=issue_data['id'],
                            file_path=issue_data['file_path'],
                            line_start=issue_data['line_start'],
                            line_end=issue_data['line_end'],
                            category=issue_data['category'],
                            severity=issue_data['severity'],
                            description=issue_data['description'],
                            code_snippet=issue_data['code_snippet'],
                            rule_id=issue_data['rule_id'],
                            code_snippet_data=snippet_data,
                            context_lines=snippet_data.get('context_lines', 3),
                            total_lines=snippet_data.get('total_lines')
                        )
                        issues.append(issue)
                    
                    return issues
                else:
                    print(f"Esprima analysis failed for {file_path}: {result.stderr}")
                    return []
            
            finally:
                # Clean up script file
                os.unlink(script_path)
        
        except Exception as e:
            print(f"Error analyzing {file_path} with esprima: {e}")
            return []
    
    async def _analyze_css_ast(self, file_path: Path) -> List[Issue]:
        """Analyze CSS files using PostCSS AST"""
        try:
            # Create a Node.js script for PostCSS analysis
            postcss_script = f"""
            const fs = require('fs');
            const postcss = require('postcss');
            const postcssParser = require('postcss/lib/parser');
            
            const filePath = '{file_path}';
            const content = fs.readFileSync(filePath, 'utf8');
            
            const issues = [];
            
            try {{
                // Parse CSS
                const root = postcssParser(content);
                
                // Traverse CSS AST
                root.walkRules(rule => {{
                    // Check for color contrast issues
                    rule.walkDecls(decl => {{
                        if (decl.prop === 'color') {{
                            // Check if there's a corresponding background color
                            const hasBackground = rule.nodes.some(node => 
                                node.type === 'decl' && 
                                (node.prop === 'background-color' || node.prop === 'background')
                            );
                            
                            if (!hasBackground) {{
                                issues.push({{
                                    id: `${{filePath}}_${{decl.source.start.line}}_color_contrast`,
                                    file_path: filePath,
                                    line_start: decl.source.start.line,
                                    line_end: decl.source.end.line,
                                    category: 'perceivable',
                                    severity: 'medium',
                                    description: 'Color without background - verify contrast ratio',
                                    code_snippet: decl.toString(),
                                    rule_id: 'color-contrast'
                                }});
                            }}
                        }}
                        
                        // Check for small font sizes
                        if (decl.prop === 'font-size') {{
                            const fontSize = parseFloat(decl.value);
                            if (fontSize < 12) {{
                                issues.push({{
                                    id: `${{filePath}}_${{decl.source.start.line}}_small_font`,
                                    file_path: filePath,
                                    line_start: decl.source.start.line,
                                    line_end: decl.source.end.line,
                                    category: 'perceivable',
                                    severity: 'medium',
                                    description: 'Font size may be too small for accessibility',
                                    code_snippet: decl.toString(),
                                    rule_id: 'font-size'
                                }});
                            }}
                        }}
                        
                        // Check for missing focus styles
                        if (decl.prop === 'outline' && decl.value === 'none') {{
                            const hasFocus = rule.nodes.some(node => 
                                node.type === 'decl' && node.prop === 'outline' && node.value !== 'none'
                            );
                            
                            if (!hasFocus) {{
                                issues.push({{
                                    id: `${{filePath}}_${{decl.source.start.line}}_missing_focus`,
                                    file_path: filePath,
                                    line_start: decl.source.start.line,
                                    line_end: decl.source.end.line,
                                    category: 'operable',
                                    severity: 'high',
                                    description: 'Removed outline without providing focus alternative',
                                    code_snippet: decl.toString(),
                                    rule_id: 'focus-visible'
                                }});
                            }}
                        }}
                    }});
                }});
                
            }} catch (error) {{
                console.error('PostCSS parsing error:', error.message);
            }}
            
            console.log(JSON.stringify(issues));
            """
            
            # Write script to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(postcss_script)
                script_path = f.name
            
            try:
                # Run the script
                result = subprocess.run(
                    ['node', script_path],
                    capture_output=True,
                    text=True,
                    cwd=str(file_path.parent)
                )
                
                if result.returncode == 0:
                    issues_data = json.loads(result.stdout)
                    issues = []
                    
                    for issue_data in issues_data:
                        # Extract enhanced code snippet data
                        snippet_data = await self.extract_code_snippets(
                            Path(issue_data['file_path']),
                            issue_data['line_start'],
                            issue_data['line_end']
                        )
                        
                        issue = Issue(
                            id=issue_data['id'],
                            file_path=issue_data['file_path'],
                            line_start=issue_data['line_start'],
                            line_end=issue_data['line_end'],
                            category=issue_data['category'],
                            severity=issue_data['severity'],
                            description=issue_data['description'],
                            code_snippet=issue_data['code_snippet'],
                            rule_id=issue_data['rule_id'],
                            code_snippet_data=snippet_data,
                            context_lines=snippet_data.get('context_lines', 3),
                            total_lines=snippet_data.get('total_lines')
                        )
                        issues.append(issue)
                    
                    return issues
                else:
                    print(f"PostCSS AST analysis failed for {file_path}: {result.stderr}")
                    return []
            
            finally:
                # Clean up script file
                os.unlink(script_path)
        
        except Exception as e:
            print(f"Error in PostCSS analysis for {file_path}: {e}")
            return []
    
    async def extract_code_snippets(self, file_path: Path, line_start: int, line_end: int, context_lines: int = 3) -> Dict[str, Any]:
        """Extract code snippet with proper line ranges and context"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            
            # Ensure line numbers are within bounds
            line_start = max(1, line_start)
            line_end = min(total_lines, line_end)
            
            # Add context lines before and after
            context_start = max(1, line_start - context_lines)
            context_end = min(total_lines, line_end + context_lines)
            
            # Extract the relevant lines (1-indexed to 0-indexed)
            snippet_lines = lines[line_start-1:line_end]
            context_lines_before = lines[context_start-1:line_start-1] if context_start < line_start else []
            context_lines_after = lines[line_end:context_end] if line_end < context_end else []
            
            # Create enhanced snippet with line numbers and context
            snippet_data = {
                "file_path": str(file_path),
                "line_start": line_start,
                "line_end": line_end,
                "total_lines": total_lines,
                "context_lines": context_lines,
                "code_snippet": ''.join(snippet_lines).strip(),
                "context_before": ''.join(context_lines_before).strip(),
                "context_after": ''.join(context_lines_after).strip(),
                "full_context": ''.join(lines[context_start-1:context_end]).strip(),
                "line_numbers": list(range(line_start, line_end + 1)),
                "context_line_numbers": {
                    "before": list(range(context_start, line_start)) if context_start < line_start else [],
                    "after": list(range(line_end + 1, context_end + 1)) if line_end < context_end else []
                }
            }
            
            return snippet_data
        
        except Exception as e:
            print(f"Error extracting code snippet from {file_path}: {e}")
            return {
                "file_path": str(file_path),
                "line_start": line_start,
                "line_end": line_end,
                "error": str(e),
                "code_snippet": ""
            }
    
    async def extract_code_snippet_simple(self, file_path: Path, line_start: int, line_end: int) -> str:
        """Simple code snippet extraction for backward compatibility"""
        snippet_data = await self.extract_code_snippets(file_path, line_start, line_end)
        return snippet_data.get("code_snippet", "")
