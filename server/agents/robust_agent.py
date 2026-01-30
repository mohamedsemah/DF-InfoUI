import os
import json
import re
from typing import List, Dict, Any
import openai
from models.job import Issue, Fix

class RobustAgent:
    """Agent responsible for fixing robust accessibility issues"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your_openai_api_key_here":
            raise ValueError("OPENAI_API_KEY environment variable must be set to a valid API key")
        self.client = openai.OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-5.1")
        self.category = "robust"
    
    async def fix_issues(self, issues: List[Issue]) -> List[Fix]:
        """Fix robust accessibility issues"""
        fixes = []
        
        for issue in issues:
            if issue.category != self.category:
                continue
                
            if issue.rule_id == "role":
                fix = await self._fix_missing_role(issue)
                if fix:
                    fixes.append(fix)
            elif issue.rule_id == "aria-props":
                fix = await self._fix_aria_properties(issue)
                if fix:
                    fixes.append(fix)
            elif issue.rule_id == "valid-html":
                fix = await self._fix_valid_html(issue)
                if fix:
                    fixes.append(fix)
            elif issue.rule_id == "semantic-html":
                fix = await self._fix_semantic_html(issue)
                if fix:
                    fixes.append(fix)
            else:
                # Use LLM for other robust issues
                fix = await self._llm_fix_issue(issue)
                if fix:
                    fixes.append(fix)
        
        return fixes
    
    async def _fix_missing_role(self, issue: Issue) -> Fix:
        """Fix missing ARIA roles"""
        code = issue.code_snippet
        
        if '<div' in code and 'onClick' in code and 'role=' not in code:
            new_code = code.replace(
                '<div',
                '<div role="button"'
            )
            
            return Fix(
                issue_id=issue.id,
                file_path=issue.file_path,
                before_code=code,
                after_code=new_code,
                diff=self._create_diff(code, new_code),
                confidence=0.7,
                applied=True,
                line_start=issue.line_start,
                line_end=issue.line_end
            )
        
        return None
    
    async def _fix_aria_properties(self, issue: Issue) -> Fix:
        """Fix missing ARIA properties"""
        code = issue.code_snippet
        
        if 'role="button"' in code and 'tabindex' not in code:
            new_code = code.replace(
                'role="button"',
                'role="button" tabindex="0"'
            )
            
            return Fix(
                issue_id=issue.id,
                file_path=issue.file_path,
                before_code=code,
                after_code=new_code,
                diff=self._create_diff(code, new_code),
                confidence=0.6,
                applied=True,
                line_start=issue.line_start,
                line_end=issue.line_end
            )
        
        return None
    
    async def _fix_valid_html(self, issue: Issue) -> Fix:
        """Fix HTML validation issues"""
        code = issue.code_snippet
        
        # Fix common HTML validation issues
        if '<img' in code and 'alt=' not in code:
            new_code = code.replace(
                '<img',
                '<img alt=""'
            )
            
            return Fix(
                issue_id=issue.id,
                file_path=issue.file_path,
                before_code=code,
                after_code=new_code,
                diff=self._create_diff(code, new_code),
                confidence=0.8,
                applied=True,
                line_start=issue.line_start,
                line_end=issue.line_end
            )
        
        return None
    
    async def _fix_semantic_html(self, issue: Issue) -> Fix:
        """Fix semantic HTML issues"""
        code = issue.code_snippet
        
        # Replace div with semantic elements where appropriate
        if '<div class="header"' in code:
            new_code = code.replace(
                '<div class="header"',
                '<header'
            ).replace(
                '</div>',
                '</header>'
            )
            
            return Fix(
                issue_id=issue.id,
                file_path=issue.file_path,
                before_code=code,
                after_code=new_code,
                diff=self._create_diff(code, new_code),
                confidence=0.5,
                applied=True,
                line_start=issue.line_start,
                line_end=issue.line_end
            )
        
        return None
    
    async def _llm_fix_issue(self, issue: Issue) -> Fix:
        """Use LLM to fix a robust issue"""
        try:
            prompt = f"""
            Fix this robust accessibility issue:
            
            Issue: {issue.description}
            Code: {issue.code_snippet}
            File: {issue.file_path}
            Lines: {issue.line_start}-{issue.line_end}
            
            Focus on making content robust and compatible with assistive technologies.
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
                    {"role": "system", "content": "You are an expert in robust accessibility fixes. Focus on ARIA roles, semantic HTML, and assistive technology compatibility."},
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
                    applied=True,
                    line_start=issue.line_start,
                    line_end=issue.line_end
                )
        
        except Exception as e:
            print(f"LLM fix failed for robust issue {issue.id}: {e}")
        
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
