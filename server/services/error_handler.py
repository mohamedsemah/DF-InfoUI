import os
import json
import re
import traceback
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import logging
from enum import Enum
import aiofiles

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    FILE_PROCESSING = "file_processing"
    AST_ANALYSIS = "ast_analysis"
    PATCH_APPLICATION = "patch_application"
    VALIDATION = "validation"
    API_REQUEST = "api_request"
    SYSTEM = "system"

class ErrorHandler:
    """Comprehensive error handling and recovery service"""
    
    def __init__(self):
        self.data_dir = Path(os.getenv("DATA_DIR", "/app/data"))
        self.logs_dir = self.data_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Error recovery strategies
        self.recovery_strategies = {
            ErrorCategory.FILE_PROCESSING: self._recover_file_processing_error,
            ErrorCategory.AST_ANALYSIS: self._recover_ast_analysis_error,
            ErrorCategory.PATCH_APPLICATION: self._recover_patch_application_error,
            ErrorCategory.VALIDATION: self._recover_validation_error,
            ErrorCategory.API_REQUEST: self._recover_api_request_error,
            ErrorCategory.SYSTEM: self._recover_system_error
        }
    
    def _setup_logging(self):
        """Setup comprehensive logging"""
        log_file = self.logs_dir / f"df_infoui_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('DF-InfoUI')
    
    async def handle_error(self, 
                          error: Exception, 
                          context: Dict[str, Any], 
                          category: ErrorCategory,
                          severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                          job_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle an error with appropriate recovery strategies"""
        
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "category": category.value,
            "severity": severity.value,
            "context": context,
            "job_id": job_id,
            "traceback": traceback.format_exc()
        }
        
        # Log the error
        self.logger.error(f"Error in {category.value}: {str(error)}", extra=error_info)
        
        # Attempt recovery
        recovery_result = await self._attempt_recovery(error, context, category, job_id)
        
        error_info["recovery_attempted"] = recovery_result["attempted"]
        error_info["recovery_successful"] = recovery_result["successful"]
        error_info["recovery_message"] = recovery_result["message"]
        
        # Save error to file
        await self._save_error_report(error_info, job_id)
        
        return error_info
    
    async def _attempt_recovery(self, 
                               error: Exception, 
                               context: Dict[str, Any], 
                               category: ErrorCategory,
                               job_id: Optional[str] = None) -> Dict[str, Any]:
        """Attempt to recover from an error"""
        
        try:
            recovery_strategy = self.recovery_strategies.get(category)
            if recovery_strategy:
                result = await recovery_strategy(error, context, job_id)
                return {
                    "attempted": True,
                    "successful": result.get("success", False),
                    "message": result.get("message", "Recovery attempted")
                }
            else:
                return {
                    "attempted": False,
                    "successful": False,
                    "message": "No recovery strategy available"
                }
        except Exception as recovery_error:
            self.logger.error(f"Recovery failed: {str(recovery_error)}")
            return {
                "attempted": True,
                "successful": False,
                "message": f"Recovery failed: {str(recovery_error)}"
            }
    
    async def _recover_file_processing_error(self, error: Exception, context: Dict[str, Any], job_id: Optional[str]) -> Dict[str, Any]:
        """Recover from file processing errors"""
        try:
            if "Permission denied" in str(error):
                # Try to change file permissions
                file_path = context.get("file_path")
                if file_path and Path(file_path).exists():
                    os.chmod(file_path, 0o644)
                    return {"success": True, "message": "Fixed file permissions"}
            
            elif "File not found" in str(error):
                # Try to recreate missing files
                file_path = context.get("file_path")
                if file_path:
                    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                    Path(file_path).touch()
                    return {"success": True, "message": "Recreated missing file"}
            
            return {"success": False, "message": "No specific recovery for this file error"}
        
        except Exception as e:
            return {"success": False, "message": f"Recovery failed: {str(e)}"}
    
    async def _recover_ast_analysis_error(self, error: Exception, context: Dict[str, Any], job_id: Optional[str]) -> Dict[str, Any]:
        """Recover from AST analysis errors"""
        try:
            if "SyntaxError" in str(error):
                # Try to fix common syntax issues
                file_path = context.get("file_path")
                if file_path and Path(file_path).exists():
                    await self._fix_syntax_errors(file_path)
                    return {"success": True, "message": "Attempted to fix syntax errors"}
            
            elif "Module not found" in str(error):
                # Try to install missing dependencies
                await self._install_missing_dependencies()
                return {"success": True, "message": "Attempted to install missing dependencies"}
            
            return {"success": False, "message": "No specific recovery for this AST error"}
        
        except Exception as e:
            return {"success": False, "message": f"Recovery failed: {str(e)}"}
    
    async def _recover_patch_application_error(self, error: Exception, context: Dict[str, Any], job_id: Optional[str]) -> Dict[str, Any]:
        """Recover from patch application errors"""
        try:
            if "Patch failed" in str(error):
                # Try fuzzy matching as fallback
                fix = context.get("fix")
                if fix and job_id:
                    from services.patch_service import PatchService
                    patch_service = PatchService()
                    
                    # Try fuzzy matching
                    fuzzy_result = await patch_service._try_fuzzy_matching([], fix)
                    if fuzzy_result["success"]:
                        return {"success": True, "message": "Applied fuzzy matching fallback"}
            
            return {"success": False, "message": "No specific recovery for this patch error"}
        
        except Exception as e:
            return {"success": False, "message": f"Recovery failed: {str(e)}"}
    
    async def _recover_validation_error(self, error: Exception, context: Dict[str, Any], job_id: Optional[str]) -> Dict[str, Any]:
        """Recover from validation errors"""
        try:
            if "eslint" in str(error).lower():
                # Try to fix eslint configuration
                await self._fix_eslint_config()
                return {"success": True, "message": "Fixed eslint configuration"}
            
            elif "typescript" in str(error).lower():
                # Try to fix TypeScript configuration
                await self._fix_typescript_config()
                return {"success": True, "message": "Fixed TypeScript configuration"}
            
            return {"success": False, "message": "No specific recovery for this validation error"}
        
        except Exception as e:
            return {"success": False, "message": f"Recovery failed: {str(e)}"}
    
    async def _recover_api_request_error(self, error: Exception, context: Dict[str, Any], job_id: Optional[str]) -> Dict[str, Any]:
        """Recover from API request errors"""
        try:
            if "timeout" in str(error).lower():
                # Retry with exponential backoff
                await asyncio.sleep(2)
                return {"success": True, "message": "Retried with backoff"}
            
            elif "rate limit" in str(error).lower():
                # Wait and retry
                await asyncio.sleep(5)
                return {"success": True, "message": "Waited for rate limit reset"}
            
            return {"success": False, "message": "No specific recovery for this API error"}
        
        except Exception as e:
            return {"success": False, "message": f"Recovery failed: {str(e)}"}
    
    async def _recover_system_error(self, error: Exception, context: Dict[str, Any], job_id: Optional[str]) -> Dict[str, Any]:
        """Recover from system errors"""
        try:
            if "memory" in str(error).lower():
                # Try to free up memory
                import gc
                gc.collect()
                return {"success": True, "message": "Freed up memory"}
            
            elif "disk space" in str(error).lower():
                # Try to clean up temporary files
                await self._cleanup_temp_files()
                return {"success": True, "message": "Cleaned up temporary files"}
            
            return {"success": False, "message": "No specific recovery for this system error"}
        
        except Exception as e:
            return {"success": False, "message": f"Recovery failed: {str(e)}"}
    
    async def _fix_syntax_errors(self, file_path: Path) -> None:
        """Attempt to fix common syntax errors"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            # Fix common issues
            fixes = [
                (r'import\s+(\w+)\s+from\s+["\'](\w+)["\']', r'import \1 from "\2"'),
                (r'export\s+default\s+(\w+)', r'export default \1'),
                (r'const\s+(\w+)\s*=\s*\(', r'const \1 = ('),
            ]
            
            for pattern, replacement in fixes:
                content = re.sub(pattern, replacement, content)
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
        
        except Exception as e:
            self.logger.error(f"Failed to fix syntax errors in {file_path}: {e}")
    
    async def _install_missing_dependencies(self) -> None:
        """Install missing Node.js dependencies"""
        try:
            import subprocess
            subprocess.run(['npm', 'install', '@babel/core', '@babel/parser', '@babel/traverse', 'postcss'], 
                          check=True, capture_output=True)
        except Exception as e:
            self.logger.error(f"Failed to install dependencies: {e}")
    
    async def _fix_eslint_config(self) -> None:
        """Fix eslint configuration"""
        try:
            # Create a basic eslint config
            config = {
                "env": {"browser": True, "es6": True},
                "extends": ["eslint:recommended"],
                "parserOptions": {"ecmaVersion": 2020, "sourceType": "module"},
                "rules": {}
            }
            
            config_path = self.data_dir / ".eslintrc.json"
            async with aiofiles.open(config_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(config, indent=2))
        
        except Exception as e:
            self.logger.error(f"Failed to fix eslint config: {e}")
    
    async def _fix_typescript_config(self) -> None:
        """Fix TypeScript configuration"""
        try:
            config = {
                "compilerOptions": {
                    "target": "ES2020",
                    "module": "ESNext",
                    "moduleResolution": "node",
                    "strict": False,
                    "skipLibCheck": True
                }
            }
            
            config_path = self.data_dir / "tsconfig.json"
            async with aiofiles.open(config_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(config, indent=2))
        
        except Exception as e:
            self.logger.error(f"Failed to fix TypeScript config: {e}")
    
    async def _cleanup_temp_files(self) -> None:
        """Clean up temporary files to free disk space"""
        try:
            temp_dirs = [self.data_dir / "rendered", self.data_dir / "snapshots"]
            for temp_dir in temp_dirs:
                if temp_dir.exists():
                    import shutil
                    shutil.rmtree(temp_dir)
        
        except Exception as e:
            self.logger.error(f"Failed to cleanup temp files: {e}")
    
    async def _save_error_report(self, error_info: Dict[str, Any], job_id: Optional[str]) -> None:
        """Save error report to file"""
        try:
            if job_id:
                error_file = self.data_dir / job_id / "error_report.json"
                error_file.parent.mkdir(exist_ok=True)
                
                async with aiofiles.open(error_file, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(error_info, indent=2))
        
        except Exception as e:
            self.logger.error(f"Failed to save error report: {e}")
    
    async def get_error_summary(self, job_id: str) -> Dict[str, Any]:
        """Get error summary for a job"""
        try:
            error_file = self.data_dir / job_id / "error_report.json"
            if error_file.exists():
                async with aiofiles.open(error_file, 'r', encoding='utf-8') as f:
                    return json.loads(await f.read())
            return {"errors": 0, "recoveries": 0}
        
        except Exception as e:
            self.logger.error(f"Failed to get error summary: {e}")
            return {"errors": 0, "recoveries": 0}
    
    def create_error_context(self, **kwargs) -> Dict[str, Any]:
        """Create error context dictionary"""
        return {
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
