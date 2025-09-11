import os
import json
import re
from typing import List, Dict, Any
import openai
from models.job import Issue, Fix

class UnderstandableAgent:
    """Agent responsible for fixing understandable accessibility issues"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        self.category = "understandable"
    
    async def fix_issues(self, issues: List[Issue]) -> List[Fix]:
        """Fix understandable accessibility issues"""
        fixes = []
        
        for issue in issues:
            if issue.category != self.category:
                continue
                
            if issue.rule_id == "heading-order":
                fix = await self._fix_heading_order(issue)
                if fix:
                    fixes.append(fix)
            elif issue.rule_id == "form-instructions":
                fix = await self._fix_form_instructions(issue)
                if fix:
                    fixes.append(fix)
            elif issue.rule_id == "error-identification":
                fix = await self._fix_error_identification(issue)
                if fix:
                    fixes.append(fix)
            elif issue.rule_id == "language-identification":
                fix = await self._fix_language_identification(issue)
                if fix:
                    fixes.append(fix)
            else:
                # Use LLM for other understandable issues
                fix = await self._llm_fix_issue(issue)
                if fix:
                    fixes.append(fix)
        
        return fixes
    
    async def _fix_heading_order(self, issue: Issue) -> Fix:
        """Fix heading order issues"""
        code = issue.code_snippet
        
        heading_match = re.search(r'<h([1-6])', code)
        if heading_match:
            current_level = int(heading_match.group(1))
            # Suggest reducing the level by 1
            new_level = max(1, current_level - 1)
            new_code = code.replace(f'<h{current_level}', f'<h{new_level}')
            
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
    
    async def _fix_form_instructions(self, issue: Issue) -> Fix:
        """Fix missing form instructions"""
        code = issue.code_snippet
        
        if '<input' in code and 'aria-describedby' not in code:
            # Add instruction text and aria-describedby
            new_code = code.replace(
                '>',
                ' aria-describedby="instruction-text">'
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
    
    async def _fix_error_identification(self, issue: Issue) -> Fix:
        """Fix error identification issues"""
        code = issue.code_snippet
        
        if 'error' in code.lower() and 'aria-invalid' not in code:
            new_code = code.replace(
                '>',
                ' aria-invalid="true" aria-describedby="error-message">'
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
    
    async def _fix_language_identification(self, issue: Issue) -> Fix:
        """Fix language identification issues"""
        code = issue.code_snippet
        
        if '<html' in code and 'lang=' not in code:
            new_code = code.replace(
                '<html',
                '<html lang="en"'
            )
            
            return Fix(
                issue_id=issue.id,
                file_path=issue.file_path,
                before_code=code,
                after_code=new_code,
                diff=self._create_diff(code, new_code),
                confidence=0.8,
                applied=True
            )
        
        return None
    
    async def _llm_fix_issue(self, issue: Issue) -> Fix:
        """Use LLM to fix an understandable issue"""
        try:
            prompt = f"""
            Fix this understandable accessibility issue:
            
            Issue: {issue.description}
            Code: {issue.code_snippet}
            File: {issue.file_path}
            Lines: {issue.line_start}-{issue.line_end}
            
            Focus on making content understandable to users with cognitive impairments.
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
                    {"role": "system", "content": "You are an expert in understandable accessibility fixes. Focus on clear instructions, error handling, and cognitive accessibility."},
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
            print(f"LLM fix failed for understandable issue {issue.id}: {e}")
        
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
