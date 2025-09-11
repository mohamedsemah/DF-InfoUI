import os
import json
import re
from typing import List, Dict, Any
import openai
from models.job import Issue, Fix

class OperableAgent:
    """Agent responsible for fixing operable accessibility issues"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        self.category = "operable"
    
    async def fix_issues(self, issues: List[Issue]) -> List[Fix]:
        """Fix operable accessibility issues"""
        fixes = []
        
        for issue in issues:
            if issue.category != self.category:
                continue
                
            if issue.rule_id == "label":
                fix = await self._fix_missing_label(issue)
                if fix:
                    fixes.append(fix)
            elif issue.rule_id == "aria-label":
                fix = await self._fix_missing_aria_label(issue)
                if fix:
                    fixes.append(fix)
            elif issue.rule_id == "keyboard-navigation":
                fix = await self._fix_keyboard_navigation(issue)
                if fix:
                    fixes.append(fix)
            elif issue.rule_id == "focus-management":
                fix = await self._fix_focus_management(issue)
                if fix:
                    fixes.append(fix)
            else:
                # Use LLM for other operable issues
                fix = await self._llm_fix_issue(issue)
                if fix:
                    fixes.append(fix)
        
        return fixes
    
    async def _fix_missing_label(self, issue: Issue) -> Fix:
        """Fix missing form labels"""
        code = issue.code_snippet
        
        if '<input' in code and 'aria-label' not in code and 'id=' not in code:
            input_match = re.search(r'<input([^>]*)>', code)
            if input_match:
                attributes = input_match.group(1)
                new_code = code.replace(
                    f'<input{attributes}>',
                    f'<input{attributes} aria-label="Input field">'
                )
                
                return Fix(
                    issue_id=issue.id,
                    file_path=issue.file_path,
                    before_code=code,
                    after_code=new_code,
                    diff=self._create_diff(code, new_code),
                    confidence=0.7,
                    applied=True
                )
        
        return None
    
    async def _fix_missing_aria_label(self, issue: Issue) -> Fix:
        """Fix missing ARIA labels on interactive elements"""
        code = issue.code_snippet
        
        if 'onClick' in code and 'aria-label' not in code:
            new_code = code.replace(
                'onClick',
                'aria-label="Interactive element" onClick'
            )
            
            return Fix(
                issue_id=issue.id,
                file_path=issue.file_path,
                before_code=code,
                after_code=new_code,
                diff=self._create_diff(code, new_code),
                confidence=0.6,
                applied=True
            )
        
        return None
    
    async def _fix_keyboard_navigation(self, issue: Issue) -> Fix:
        """Fix keyboard navigation issues"""
        code = issue.code_snippet
        
        if '<button' in code and 'tabindex' not in code:
            new_code = code.replace('>', ' tabindex="0">')
            
            return Fix(
                issue_id=issue.id,
                file_path=issue.file_path,
                before_code=code,
                after_code=new_code,
                diff=self._create_diff(code, new_code),
                confidence=0.5,
                applied=True
            )
        
        return None
    
    async def _fix_focus_management(self, issue: Issue) -> Fix:
        """Fix focus management issues"""
        code = issue.code_snippet
        
        # Add focus management attributes
        if 'onClick' in code and 'onFocus' not in code:
            new_code = code.replace(
                'onClick',
                'onFocus onBlur onClick'
            )
            
            return Fix(
                issue_id=issue.id,
                file_path=issue.file_path,
                before_code=code,
                after_code=new_code,
                diff=self._create_diff(code, new_code),
                confidence=0.4,
                applied=True
            )
        
        return None
    
    async def _llm_fix_issue(self, issue: Issue) -> Fix:
        """Use LLM to fix an operable issue"""
        try:
            prompt = f"""
            Fix this operable accessibility issue:
            
            Issue: {issue.description}
            Code: {issue.code_snippet}
            File: {issue.file_path}
            Lines: {issue.line_start}-{issue.line_end}
            
            Focus on making content operable by users with motor impairments and keyboard users.
            Return a JSON object with this structure:
            {{
                "before_code": "original code",
                "after_code": "fixed code",
                "confidence": 0.0-1.0,
                "explanation": "brief explanation of the fix"
            }}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert in operable accessibility fixes. Focus on keyboard navigation, focus management, and motor accessibility."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            result = response.choices[0].message.content
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                fix_data = json.loads(json_match.group())
                
                return Fix(
                    issue_id=issue.id,
                    file_path=issue.file_path,
                    before_code=fix_data["before_code"],
                    after_code=fix_data["after_code"],
                    diff=self._create_diff(fix_data["before_code"], fix_data["after_code"]),
                    confidence=fix_data["confidence"],
                    applied=True
                )
        
        except Exception as e:
            print(f"LLM fix failed for operable issue {issue.id}: {e}")
        
        return None
    
    def _create_diff(self, before: str, after: str) -> str:
        """Create a simple diff between before and after code"""
        before_lines = before.split('\n')
        after_lines = after.split('\n')
        
        diff_lines = []
        for i, (b, a) in enumerate(zip(before_lines, after_lines)):
            if b != a:
                diff_lines.append(f"- {b}")
                diff_lines.append(f"+ {a}")
            else:
                diff_lines.append(f"  {b}")
        
        return '\n'.join(diff_lines)
