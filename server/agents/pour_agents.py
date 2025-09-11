from typing import List
from models.job import Issue, Fix
from .perceivable_agent import PerceivableAgent
from .operable_agent import OperableAgent
from .understandable_agent import UnderstandableAgent
from .robust_agent import RobustAgent

class POURAgents:
    def __init__(self):
        self.perceivable_agent = PerceivableAgent()
        self.operable_agent = OperableAgent()
        self.understandable_agent = UnderstandableAgent()
        self.robust_agent = RobustAgent()
    
    async def fix_issues(self, job_id: str, issues: List[Issue]) -> List[Fix]:
        """Fix issues using POUR agents"""
        fixes = []
        
        # Group issues by category
        perceivable_issues = [i for i in issues if i.category == "perceivable"]
        operable_issues = [i for i in issues if i.category == "operable"]
        understandable_issues = [i for i in issues if i.category == "understandable"]
        robust_issues = [i for i in issues if i.category == "robust"]
        
        # Process each category with dedicated agents
        if perceivable_issues:
            fixes.extend(await self.perceivable_agent.fix_issues(perceivable_issues))
        
        if operable_issues:
            fixes.extend(await self.operable_agent.fix_issues(operable_issues))
        
        if understandable_issues:
            fixes.extend(await self.understandable_agent.fix_issues(understandable_issues))
        
        if robust_issues:
            fixes.extend(await self.robust_agent.fix_issues(robust_issues))
        
        return fixes
