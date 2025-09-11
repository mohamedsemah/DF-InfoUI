import os
import re
import difflib
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import aiofiles
from models.job import Fix

class PatchService:
    """Service for line-aware patching with fuzzy matching fallback"""
    
    def __init__(self):
        self.data_dir = Path(os.getenv("DATA_DIR", "/app/data"))
    
    async def apply_patches_with_line_awareness(self, job_id: str, fixes: List[Fix]) -> Dict[str, Any]:
        """Apply fixes with line-aware patching and fuzzy matching fallback"""
        job_dir = self.data_dir / job_id
        fixed_dir = job_dir / "fixed"
        original_dir = job_dir / "original"
        
        # Copy original files to fixed directory
        if fixed_dir.exists():
            import shutil
            shutil.rmtree(fixed_dir)
        import shutil
        shutil.copytree(original_dir, fixed_dir)
        
        results = {
            "successful_patches": 0,
            "failed_patches": 0,
            "fuzzy_matches": 0,
            "patch_details": []
        }
        
        # Group fixes by file
        fixes_by_file = {}
        for fix in fixes:
            if fix.file_path not in fixes_by_file:
                fixes_by_file[fix.file_path] = []
            fixes_by_file[fix.file_path].append(fix)
        
        # Apply fixes file by file
        for file_path, file_fixes in fixes_by_file.items():
            file_result = await self._apply_file_patches(fixed_dir, file_path, file_fixes)
            results["successful_patches"] += file_result["successful"]
            results["failed_patches"] += file_result["failed"]
            results["fuzzy_matches"] += file_result["fuzzy"]
            results["patch_details"].extend(file_result["details"])
        
        return results
    
    async def _apply_file_patches(self, fixed_dir: Path, file_path: str, fixes: List[Fix]) -> Dict[str, Any]:
        """Apply patches to a single file with line awareness"""
        target_file = fixed_dir / file_path
        
        if not target_file.exists():
            return {
                "successful": 0,
                "failed": len(fixes),
                "fuzzy": 0,
                "details": [{"fix_id": fix.issue_id, "status": "failed", "reason": "file_not_found"} for fix in fixes]
            }
        
        try:
            # Read current file content
            async with aiofiles.open(target_file, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            lines = content.split('\n')
            result = {
                "successful": 0,
                "failed": 0,
                "fuzzy": 0,
                "details": []
            }
            
            # Sort fixes by line number (descending) to avoid line number shifts
            sorted_fixes = sorted(fixes, key=lambda x: x.line_start if hasattr(x, 'line_start') else 0, reverse=True)
            
            for fix in sorted_fixes:
                patch_result = await self._apply_single_patch(lines, fix)
                
                if patch_result["success"]:
                    result["successful"] += 1
                    result["details"].append({
                        "fix_id": fix.issue_id,
                        "status": "success",
                        "method": patch_result["method"]
                    })
                elif patch_result["fuzzy_success"]:
                    result["fuzzy"] += 1
                    result["details"].append({
                        "fix_id": fix.issue_id,
                        "status": "fuzzy_success",
                        "method": patch_result["method"],
                        "confidence": patch_result["confidence"]
                    })
                else:
                    result["failed"] += 1
                    result["details"].append({
                        "fix_id": fix.issue_id,
                        "status": "failed",
                        "reason": patch_result["reason"]
                    })
            
            # Write updated content back to file
            new_content = '\n'.join(lines)
            async with aiofiles.open(target_file, 'w', encoding='utf-8') as f:
                await f.write(new_content)
            
            return result
        
        except Exception as e:
            return {
                "successful": 0,
                "failed": len(fixes),
                "fuzzy": 0,
                "details": [{"fix_id": fix.issue_id, "status": "failed", "reason": f"file_error: {str(e)}"} for fix in fixes]
            }
    
    async def _apply_single_patch(self, lines: List[str], fix: Fix) -> Dict[str, Any]:
        """Apply a single patch with line awareness and fuzzy matching"""
        try:
            # Method 1: Exact string replacement
            if await self._try_exact_replacement(lines, fix):
                return {"success": True, "method": "exact_replacement"}
            
            # Method 2: Line-aware replacement
            if await self._try_line_aware_replacement(lines, fix):
                return {"success": True, "method": "line_aware"}
            
            # Method 3: Fuzzy matching
            fuzzy_result = await self._try_fuzzy_matching(lines, fix)
            if fuzzy_result["success"]:
                return {
                    "success": False,
                    "fuzzy_success": True,
                    "method": "fuzzy_matching",
                    "confidence": fuzzy_result["confidence"]
                }
            
            return {"success": False, "fuzzy_success": False, "reason": "no_match_found"}
        
        except Exception as e:
            return {"success": False, "fuzzy_success": False, "reason": f"patch_error: {str(e)}"}
    
    async def _try_exact_replacement(self, lines: List[str], fix: Fix) -> bool:
        """Try exact string replacement"""
        content = '\n'.join(lines)
        if fix.before_code in content:
            new_content = content.replace(fix.before_code, fix.after_code)
            new_lines = new_content.split('\n')
            lines.clear()
            lines.extend(new_lines)
            return True
        return False
    
    async def _try_line_aware_replacement(self, lines: List[str], fix: Fix) -> bool:
        """Try line-aware replacement based on line numbers"""
        if not hasattr(fix, 'line_start') or not hasattr(fix, 'line_end'):
            return False
        
        line_start = fix.line_start - 1  # Convert to 0-based index
        line_end = fix.line_end - 1
        
        if line_start < 0 or line_end >= len(lines):
            return False
        
        # Extract the relevant lines
        target_lines = lines[line_start:line_end + 1]
        target_content = '\n'.join(target_lines)
        
        # Check if the before code matches the target content
        if fix.before_code.strip() == target_content.strip():
            # Replace the lines
            new_lines = fix.after_code.split('\n')
            lines[line_start:line_end + 1] = new_lines
            return True
        
        return False
    
    async def _try_fuzzy_matching(self, lines: List[str], fix: Fix) -> Dict[str, Any]:
        """Try fuzzy matching to find similar code"""
        content = '\n'.join(lines)
        
        # Split content into chunks for fuzzy matching
        chunks = self._split_into_chunks(content, chunk_size=500)
        
        best_match = None
        best_ratio = 0.0
        
        for i, chunk in enumerate(chunks):
            ratio = difflib.SequenceMatcher(None, fix.before_code, chunk).ratio()
            if ratio > best_ratio and ratio > 0.6:  # Minimum similarity threshold
                best_ratio = ratio
                best_match = (i, chunk)
        
        if best_match and best_ratio > 0.6:
            # Apply fuzzy replacement
            chunk_index, matched_chunk = best_match
            new_content = content.replace(matched_chunk, fix.after_code)
            new_lines = new_content.split('\n')
            lines.clear()
            lines.extend(new_lines)
            
            return {"success": True, "confidence": best_ratio}
        
        return {"success": False, "confidence": 0.0}
    
    def _split_into_chunks(self, content: str, chunk_size: int = 500) -> List[str]:
        """Split content into overlapping chunks for fuzzy matching"""
        lines = content.split('\n')
        chunks = []
        
        for i in range(0, len(lines), chunk_size // 2):  # 50% overlap
            chunk_lines = lines[i:i + chunk_size]
            chunks.append('\n'.join(chunk_lines))
        
        return chunks
    
    async def generate_unified_diff(self, before_content: str, after_content: str) -> str:
        """Generate a unified diff between before and after content"""
        before_lines = before_content.splitlines(keepends=True)
        after_lines = after_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            before_lines,
            after_lines,
            fromfile='before',
            tofile='after',
            lineterm=''
        )
        
        return ''.join(diff)
    
    async def validate_patch_application(self, file_path: Path, fixes: List[Fix]) -> Dict[str, Any]:
        """Validate that patches were applied correctly"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            validation_results = {
                "file_path": str(file_path),
                "total_fixes": len(fixes),
                "applied_fixes": 0,
                "failed_fixes": 0,
                "details": []
            }
            
            for fix in fixes:
                # Check if the fix was applied by looking for the after_code
                if fix.after_code in content:
                    validation_results["applied_fixes"] += 1
                    validation_results["details"].append({
                        "fix_id": fix.issue_id,
                        "status": "applied",
                        "confidence": 1.0
                    })
                else:
                    validation_results["failed_fixes"] += 1
                    validation_results["details"].append({
                        "fix_id": fix.issue_id,
                        "status": "failed",
                        "reason": "after_code_not_found"
                    })
            
            return validation_results
        
        except Exception as e:
            return {
                "file_path": str(file_path),
                "total_fixes": len(fixes),
                "applied_fixes": 0,
                "failed_fixes": len(fixes),
                "error": str(e)
            }
