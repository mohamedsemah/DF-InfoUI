import os
import json
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
import aiofiles

class SSRService:
    """Service for Server-Side Rendering JSX/TSX files for axe-core validation"""
    
    def __init__(self):
        self.data_dir = Path(os.getenv("DATA_DIR", "/app/data"))
    
    async def render_jsx_tsx_files(self, job_id: str) -> List[Path]:
        """Render JSX/TSX files to HTML for axe-core validation"""
        job_dir = self.data_dir / job_id
        fixed_dir = job_dir / "fixed"
        rendered_dir = job_dir / "rendered"
        
        # Create rendered directory
        rendered_dir.mkdir(exist_ok=True)
        
        # Find all JSX/TSX files
        jsx_files = []
        for ext in ['*.jsx', '*.tsx']:
            jsx_files.extend(fixed_dir.rglob(ext))
        
        rendered_files = []
        
        for jsx_file in jsx_files:
            try:
                rendered_file = await self._render_jsx_to_html(jsx_file, rendered_dir)
                if rendered_file:
                    rendered_files.append(rendered_file)
            except Exception as e:
                print(f"Failed to render {jsx_file}: {e}")
        
        return rendered_files
    
    async def _render_jsx_to_html(self, jsx_file: Path, output_dir: Path) -> Optional[Path]:
        """Render a single JSX/TSX file to HTML"""
        try:
            # Create a Node.js script for JSX rendering
            render_script = f"""
            const fs = require('fs');
            const path = require('path');
            const React = require('react');
            const ReactDOMServer = require('react-dom/server');
            const babel = require('@babel/core');
            
            const inputFile = '{jsx_file}';
            const outputDir = '{output_dir}';
            
            try {{
                // Read the JSX/TSX file
                const jsxContent = fs.readFileSync(inputFile, 'utf8');
                
                // Transform JSX to JavaScript using Babel
                const transformedCode = babel.transform(jsxContent, {{
                    presets: [
                        ['@babel/preset-react', {{ runtime: 'automatic' }}],
                        ['@babel/preset-typescript', {{ isTSX: true, allExtensions: true }}]
                    ],
                    plugins: [
                        ['@babel/plugin-transform-modules-commonjs']
                    ]
                }}).code;
                
                // Create a wrapper to render the component
                const wrapperCode = `
                    const React = require('react');
                    const ReactDOMServer = require('react-dom/server');
                    
                    // Mock console to avoid errors
                    global.console = {{
                        log: () => {{}},
                        error: () => {{}},
                        warn: () => {{}}
                    }};
                    
                    // Mock window and document for browser APIs
                    global.window = {{
                        addEventListener: () => {{}},
                        removeEventListener: () => {{}}
                    }};
                    
                    global.document = {{
                        createElement: () => ({{}}),
                        getElementById: () => null,
                        querySelector: () => null,
                        addEventListener: () => {{}}
                    }};
                    
                    // Mock common React hooks and functions
                    const useState = (initial) => [initial, () => {{}}];
                    const useEffect = () => {{}};
                    const useCallback = (fn) => fn;
                    const useMemo = (fn) => fn();
                    
                    // Execute the transformed code
                    {transformedCode}
                    
                    // Try to render the component
                    try {{
                        // Look for default export or named exports
                        let Component = null;
                        
                        if (typeof module.exports !== 'undefined') {{
                            Component = module.exports.default || module.exports;
                        }}
                        
                        if (Component && typeof Component === 'function') {{
                            const html = ReactDOMServer.renderToString(React.createElement(Component));
                            
                            // Create a complete HTML document
                            const fullHtml = \`
                                <!DOCTYPE html>
                                <html lang="en">
                                <head>
                                    <meta charset="UTF-8">
                                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                                    <title>Rendered Component</title>
                                </head>
                                <body>
                                    <div id="root">\${html}</div>
                                </body>
                                </html>
                            \`;
                            
                            console.log(fullHtml);
                        }} else {{
                            // If no component found, create a basic HTML structure
                            const basicHtml = \`
                                <!DOCTYPE html>
                                <html lang="en">
                                <head>
                                    <meta charset="UTF-8">
                                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                                    <title>Rendered File</title>
                                </head>
                                <body>
                                    <div id="root">
                                        <!-- Rendered from {jsx_file.name} -->
                                        <div>Component content would be here</div>
                                    </div>
                                </body>
                                </html>
                            \`;
                            
                            console.log(basicHtml);
                        }}
                    }} catch (renderError) {{
                        // If rendering fails, create a basic HTML structure
                        const errorHtml = \`
                            <!DOCTYPE html>
                            <html lang="en">
                            <head>
                                <meta charset="UTF-8">
                                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                                <title>Rendered File</title>
                            </head>
                            <body>
                                <div id="root">
                                    <!-- Error rendering {jsx_file.name}: \${renderError.message} -->
                                    <div>Rendering error occurred</div>
                                </div>
                            </body>
                            </html>
                        \`;
                        
                        console.log(errorHtml);
                    }}
                `;
                
                // Write the wrapper script
                const scriptPath = path.join(outputDir, 'render_script.js');
                fs.writeFileSync(scriptPath, wrapperCode);
                
                // Execute the script
                const {{ spawn }} = require('child_process');
                const child = spawn('node', [scriptPath], {{
                    cwd: outputDir,
                    stdio: ['pipe', 'pipe', 'pipe']
                }});
                
                let output = '';
                let error = '';
                
                child.stdout.on('data', (data) => {{
                    output += data.toString();
                }});
                
                child.stderr.on('data', (data) => {{
                    error += data.toString();
                }});
                
                child.on('close', (code) => {{
                    if (code === 0 && output) {{
                        // Save the rendered HTML
                        const outputFile = path.join(outputDir, path.basename(inputFile, path.extname(inputFile)) + '.html');
                        fs.writeFileSync(outputFile, output);
                        console.log('Rendered:', outputFile);
                    }} else {{
                        console.error('Render failed:', error);
                    }}
                }});
                
            }} catch (error) {{
                console.error('SSR Error:', error.message);
            }}
            """
            
            # Write script to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(render_script)
                script_path = f.name
            
            try:
                # Run the script
                result = subprocess.run(
                    ['node', script_path],
                    capture_output=True,
                    text=True,
                    cwd=str(output_dir)
                )
                
                if result.returncode == 0:
                    # Find the generated HTML file
                    expected_html = output_dir / f"{jsx_file.stem}.html"
                    if expected_html.exists():
                        return expected_html
                else:
                    print(f"SSR rendering failed for {jsx_file}: {result.stderr}")
            
            finally:
                # Clean up script file
                os.unlink(script_path)
        
        except Exception as e:
            print(f"Error in SSR rendering for {jsx_file}: {e}")
        
        return None
    
    async def create_static_html_snapshots(self, job_id: str) -> List[Path]:
        """Create static HTML snapshots from JSX/TSX files as fallback"""
        job_dir = self.data_dir / job_id
        fixed_dir = job_dir / "fixed"
        snapshots_dir = job_dir / "snapshots"
        
        # Create snapshots directory
        snapshots_dir.mkdir(exist_ok=True)
        
        # Find all JSX/TSX files
        jsx_files = []
        for ext in ['*.jsx', '*.tsx']:
            jsx_files.extend(fixed_dir.rglob(ext))
        
        snapshot_files = []
        
        for jsx_file in jsx_files:
            try:
                snapshot_file = await self._create_html_snapshot(jsx_file, snapshots_dir)
                if snapshot_file:
                    snapshot_files.append(snapshot_file)
            except Exception as e:
                print(f"Failed to create snapshot for {jsx_file}: {e}")
        
        return snapshot_files
    
    async def _create_html_snapshot(self, jsx_file: Path, output_dir: Path) -> Optional[Path]:
        """Create a static HTML snapshot from JSX/TSX file"""
        try:
            # Read the JSX/TSX file
            async with aiofiles.open(jsx_file, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            # Extract JSX elements using regex (simplified approach)
            jsx_elements = self._extract_jsx_elements(content)
            
            # Create HTML structure
            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Snapshot of {jsx_file.name}</title>
</head>
<body>
    <div id="root">
        {jsx_elements}
    </div>
</body>
</html>"""
            
            # Save the snapshot
            snapshot_file = output_dir / f"{jsx_file.stem}_snapshot.html"
            async with aiofiles.open(snapshot_file, 'w', encoding='utf-8') as f:
                await f.write(html_content)
            
            return snapshot_file
        
        except Exception as e:
            print(f"Error creating snapshot for {jsx_file}: {e}")
            return None
    
    def _extract_jsx_elements(self, content: str) -> str:
        """Extract JSX elements and convert to basic HTML"""
        # This is a simplified extraction - in production, use proper JSX parsing
        import re
        
        # Find JSX elements
        jsx_pattern = r'<[^>]+>'
        jsx_elements = re.findall(jsx_pattern, content)
        
        # Convert JSX to HTML (basic conversion)
        html_elements = []
        for element in jsx_elements:
            # Convert className to class
            element = element.replace('className=', 'class=')
            # Convert JSX attributes to HTML
            element = element.replace('{', '').replace('}', '')
            html_elements.append(element)
        
        return '\n        '.join(html_elements) if html_elements else '<div>JSX content extracted</div>'
    
    async def cleanup_rendered_files(self, job_id: str) -> None:
        """Clean up temporary rendered files"""
        job_dir = self.data_dir / job_id
        rendered_dir = job_dir / "rendered"
        snapshots_dir = job_dir / "snapshots"
        
        try:
            if rendered_dir.exists():
                import shutil
                shutil.rmtree(rendered_dir)
            if snapshots_dir.exists():
                shutil.rmtree(snapshots_dir)
        except Exception as e:
            print(f"Error cleaning up rendered files: {e}")
