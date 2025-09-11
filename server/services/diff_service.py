import difflib
import re
from typing import List, Dict, Any, Tuple
from models.job import Fix

class DiffService:
    """Service for generating unified diffs and patch analysis"""
    
    def __init__(self):
        pass
    
    def generate_unified_diff(self, before_code: str, after_code: str, file_path: str, 
                            line_start: int = 1, context_lines: int = 3) -> str:
        """Generate unified diff between before and after code"""
        try:
            # Split code into lines
            before_lines = before_code.splitlines(keepends=True)
            after_lines = after_code.splitlines(keepends=True)
            
            # Generate unified diff
            diff = difflib.unified_diff(
                before_lines,
                after_lines,
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}",
                lineterm='',
                n=context_lines
            )
            
            # Convert to string and add line numbers
            diff_lines = list(diff)
            if not diff_lines:
                return ""
            
            # Add line number information
            result_lines = []
            current_line_before = line_start
            current_line_after = line_start
            
            for line in diff_lines:
                if line.startswith('@@'):
                    # Parse hunk header to get line numbers
                    hunk_match = re.match(r'@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@', line)
                    if hunk_match:
                        current_line_before = int(hunk_match.group(1))
                        current_line_after = int(hunk_match.group(3))
                        result_lines.append(line)
                elif line.startswith('---') or line.startswith('+++'):
                    result_lines.append(line)
                elif line.startswith('-'):
                    result_lines.append(f"{current_line_before:4d}:{line}")
                    current_line_before += 1
                elif line.startswith('+'):
                    result_lines.append(f"    {current_line_after:4d}:{line}")
                    current_line_after += 1
                else:
                    result_lines.append(f"{current_line_before:4d}:{line}")
                    current_line_before += 1
                    current_line_after += 1
            
            return '\n'.join(result_lines)
        
        except Exception as e:
            print(f"Error generating unified diff: {e}")
            return f"Error generating diff: {str(e)}"
    
    def generate_inline_diff(self, before_code: str, after_code: str) -> Dict[str, Any]:
        """Generate inline diff with character-level changes"""
        try:
            # Use difflib for character-level diff
            differ = difflib.unified_diff(
                before_code.splitlines(keepends=True),
                after_code.splitlines(keepends=True),
                lineterm=''
            )
            
            diff_lines = list(differ)
            
            # Process diff to create inline representation
            changes = []
            current_line = 0
            
            for line in diff_lines:
                if line.startswith('@@'):
                    # Parse line numbers from hunk header
                    hunk_match = re.match(r'@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@', line)
                    if hunk_match:
                        current_line = int(hunk_match.group(1))
                elif line.startswith('-'):
                    changes.append({
                        'type': 'removed',
                        'line': current_line,
                        'content': line[1:].rstrip('\n'),
                        'original': line
                    })
                    current_line += 1
                elif line.startswith('+'):
                    changes.append({
                        'type': 'added',
                        'line': current_line,
                        'content': line[1:].rstrip('\n'),
                        'original': line
                    })
                    current_line += 1
                elif line.startswith(' '):
                    current_line += 1
            
            return {
                'changes': changes,
                'total_changes': len(changes),
                'added_lines': len([c for c in changes if c['type'] == 'added']),
                'removed_lines': len([c for c in changes if c['type'] == 'removed'])
            }
        
        except Exception as e:
            print(f"Error generating inline diff: {e}")
            return {'error': str(e)}
    
    def generate_word_diff(self, before_code: str, after_code: str) -> str:
        """Generate word-level diff"""
        try:
            # Split into words for word-level diff
            before_words = before_code.split()
            after_words = after_code.split()
            
            # Generate word diff
            differ = difflib.unified_diff(
                before_words,
                after_words,
                fromfile="before",
                tofile="after",
                lineterm=""
            )
            
            return '\n'.join(differ)
        
        except Exception as e:
            print(f"Error generating word diff: {e}")
            return f"Error generating word diff: {str(e)}"
    
    def analyze_patch_complexity(self, before_code: str, after_code: str) -> Dict[str, Any]:
        """Analyze the complexity of a patch"""
        try:
            # Calculate basic metrics
            before_lines = len(before_code.splitlines())
            after_lines = len(after_code.splitlines())
            
            # Calculate similarity
            similarity = difflib.SequenceMatcher(None, before_code, after_code).ratio()
            
            # Count changes
            differ = difflib.unified_diff(
                before_code.splitlines(keepends=True),
                after_code.splitlines(keepends=True),
                lineterm=''
            )
            
            diff_lines = list(differ)
            added_lines = len([line for line in diff_lines if line.startswith('+') and not line.startswith('+++')])
            removed_lines = len([line for line in diff_lines if line.startswith('-') and not line.startswith('---')])
            
            # Calculate complexity score
            complexity_score = (added_lines + removed_lines) / max(before_lines, 1)
            
            return {
                'before_lines': before_lines,
                'after_lines': after_lines,
                'added_lines': added_lines,
                'removed_lines': removed_lines,
                'similarity': similarity,
                'complexity_score': complexity_score,
                'is_simple': complexity_score < 0.1,
                'is_moderate': 0.1 <= complexity_score < 0.3,
                'is_complex': complexity_score >= 0.3
            }
        
        except Exception as e:
            print(f"Error analyzing patch complexity: {e}")
            return {'error': str(e)}
    
    def generate_patch_summary(self, fix: Fix) -> Dict[str, Any]:
        """Generate a comprehensive summary of a patch"""
        try:
            # Generate different types of diffs
            unified_diff = self.generate_unified_diff(
                fix.before_code,
                fix.after_code,
                fix.file_path
            )
            
            inline_diff = self.generate_inline_diff(
                fix.before_code,
                fix.after_code
            )
            
            word_diff = self.generate_word_diff(
                fix.before_code,
                fix.after_code
            )
            
            # Analyze complexity
            complexity = self.analyze_patch_complexity(
                fix.before_code,
                fix.after_code
            )
            
            return {
                'unified_diff': unified_diff,
                'inline_diff': inline_diff,
                'word_diff': word_diff,
                'complexity': complexity,
                'confidence': fix.confidence,
                'applied': fix.applied,
                'file_path': fix.file_path,
                'issue_id': fix.issue_id
            }
        
        except Exception as e:
            print(f"Error generating patch summary: {e}")
            return {'error': str(e)}
    
    def validate_patch_safety(self, before_code: str, after_code: str) -> Dict[str, Any]:
        """Validate that a patch is safe to apply"""
        try:
            issues = []
            
            # Check for potential issues
            if len(after_code) == 0:
                issues.append("Patch removes all content")
            
            if len(after_code) > len(before_code) * 10:
                issues.append("Patch significantly increases file size")
            
            # Check for syntax preservation
            before_lines = before_code.splitlines()
            after_lines = after_code.splitlines()
            
            if len(after_lines) < len(before_lines) * 0.5:
                issues.append("Patch removes more than 50% of content")
            
            # Check for common patterns that might be problematic
            if re.search(r'<script[^>]*>', after_code) and not re.search(r'<script[^>]*>', before_code):
                issues.append("Patch adds script tags")
            
            if re.search(r'javascript:', after_code) and not re.search(r'javascript:', before_code):
                issues.append("Patch adds javascript: URLs")
            
            # Calculate safety score
            safety_score = max(0, 1 - (len(issues) * 0.2))
            
            return {
                'safe': len(issues) == 0,
                'safety_score': safety_score,
                'issues': issues,
                'recommendation': 'safe' if len(issues) == 0 else 'review_required'
            }
        
        except Exception as e:
            print(f"Error validating patch safety: {e}")
            return {'error': str(e)}
    
    def generate_patch_metadata(self, fix: Fix) -> Dict[str, Any]:
        """Generate comprehensive metadata for a patch"""
        try:
            # Generate all diff types
            unified_diff = self.generate_unified_diff(
                fix.before_code,
                fix.after_code,
                fix.file_path
            )
            
            # Analyze complexity and safety
            complexity = self.analyze_patch_complexity(
                fix.before_code,
                fix.after_code
            )
            
            safety = self.validate_patch_safety(
                fix.before_code,
                fix.after_code
            )
            
            # Generate statistics
            before_lines = len(fix.before_code.splitlines())
            after_lines = len(fix.after_code.splitlines())
            
            return {
                'file_path': fix.file_path,
                'issue_id': fix.issue_id,
                'unified_diff': unified_diff,
                'complexity': complexity,
                'safety': safety,
                'statistics': {
                    'before_lines': before_lines,
                    'after_lines': after_lines,
                    'line_change': after_lines - before_lines,
                    'confidence': fix.confidence,
                    'applied': fix.applied
                },
                'generated_at': self._get_current_timestamp()
            }
        
        except Exception as e:
            print(f"Error generating patch metadata: {e}")
            return {'error': str(e)}
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()
