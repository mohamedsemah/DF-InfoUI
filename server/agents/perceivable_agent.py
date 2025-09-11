import os
import json
import re
from typing import List, Dict, Any
import openai
from models.job import Issue, Fix

class PerceivableAgent:
    """Agent responsible for fixing perceivable accessibility issues"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        self.category = "perceivable"
    
    async def fix_issues(self, issues: List[Issue]) -> List[Fix]:
        """Fix perceivable accessibility issues"""
        fixes = []
        
        for issue in issues:
            if issue.category != self.category:
                continue
                
            if issue.rule_id == "img-alt":
                fix = await self._fix_missing_alt_text(issue)
                if fix:
                    fixes.append(fix)
            elif issue.rule_id == "color-contrast":
                fix = await self._fix_color_contrast(issue)
                if fix:
                    fixes.append(fix)
            elif issue.rule_id == "text-alternatives":
                fix = await self._fix_missing_text_alternatives(issue)
                if fix:
                    fixes.append(fix)
            else:
                # Use LLM for other perceivable issues
                fix = await self._llm_fix_issue(issue)
                if fix:
                    fixes.append(fix)
        
        return fixes
    
    async def _fix_missing_alt_text(self, issue: Issue) -> Fix:
        """Fix missing alt text for images"""
        code = issue.code_snippet
        
        if '<img' in code and 'alt=' not in code:
            img_match = re.search(r'<img([^>]*)>', code)
            if img_match:
                attributes = img_match.group(1)
                new_code = code.replace(
                    f'<img{attributes}>',
                    f'<img{attributes} alt="Descriptive text for image">'
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
    
    async def _fix_color_contrast(self, issue: Issue) -> Fix:
        """Fix color contrast issues"""
        code = issue.code_snippet
        
        if 'color:' in code:
            # Add a comment suggesting manual review
            new_code = code + ' /* TODO: Verify color contrast ratio meets WCAG AA standards */'
            
            return Fix(
                issue_id=issue.id,
                file_path=issue.file_path,
                before_code=code,
                after_code=new_code,
                diff=self._create_diff(code, new_code),
                confidence=0.3,
                applied=True
            )
        
        return None
    
    async def _fix_missing_text_alternatives(self, issue: Issue) -> Fix:
        """Fix missing text alternatives for non-text content"""
        code = issue.code_snippet
        
        # This is a placeholder - real implementation would analyze the specific content
        if '<svg' in code or '<canvas' in code:
            new_code = code.replace('>', ' aria-label="Descriptive text for visual content">')
            
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
    
    async def _llm_fix_issue(self, issue: Issue) -> Fix:
        """Use LLM to fix a perceivable issue"""
        try:
            prompt = f"""
            Fix this perceivable accessibility issue:
            
            Issue: {issue.description}
            Code: {issue.code_snippet}
            File: {issue.file_path}
            Lines: {issue.line_start}-{issue.line_end}
            
            Focus on making content perceivable to users with visual impairments.
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
                    {"role": "system", "content": "You are an expert in perceivable accessibility fixes. Focus on visual content, color contrast, and text alternatives."},
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
            print(f"LLM fix failed for perceivable issue {issue.id}: {e}")
        
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
