import os
import zipfile
import shutil
import json
from pathlib import Path
from typing import List, Dict, Any
import aiofiles
from models.job import Fix
from utils.path_utils import get_data_dir

class FileService:
    def __init__(self):
        self.data_dir = get_data_dir()
    
    async def save_uploaded_file(self, job_id: str, file) -> None:
        """Save uploaded ZIP file and extract it"""
        job_dir = self.data_dir / job_id
        job_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        uploaded_file_path = job_dir / "uploaded.zip"
        async with aiofiles.open(uploaded_file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Extract ZIP file
        original_dir = job_dir / "original"
        original_dir.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(uploaded_file_path, 'r') as zip_ref:
            zip_ref.extractall(original_dir)
    
    def get_original_files(self, job_id: str) -> List[Path]:
        """Get all original files for analysis with comprehensive validation"""
        original_dir = self.data_dir / job_id / "original"
        files = []
        
        # Supported file extensions
        supported_extensions = ['.html', '.js', '.jsx', '.ts', '.tsx', '.css']
        
        for ext in supported_extensions:
            found_files = original_dir.rglob(f'*{ext}')
            for file_path in found_files:
                if self._validate_file_type(file_path, ext):
                    files.append(file_path)
                else:
                    print(f"Skipping invalid file: {file_path}")
        
        return files
    
    def _validate_file_type(self, file_path: Path, expected_ext: str) -> bool:
        """Validate that a file matches its expected type"""
        try:
            # Check file exists and is readable
            if not file_path.exists() or not file_path.is_file():
                return False
            
            # Check file size (max 10MB per file)
            if file_path.stat().st_size > 10 * 1024 * 1024:
                print(f"File too large: {file_path}")
                return False
            
            # Read first few bytes to check file signature
            with open(file_path, 'rb') as f:
                header = f.read(1024)
            
            # Validate based on file extension
            if expected_ext == '.html':
                return self._validate_html_file(header)
            elif expected_ext in ['.js', '.jsx']:
                return self._validate_js_file(header)
            elif expected_ext in ['.ts', '.tsx']:
                return self._validate_ts_file(header)
            elif expected_ext == '.css':
                return self._validate_css_file(header)
            
            return True
        
        except Exception as e:
            print(f"Error validating file {file_path}: {e}")
            return False
    
    def _validate_html_file(self, header: bytes) -> bool:
        """Validate HTML file content"""
        try:
            content = header.decode('utf-8', errors='ignore').lower()
            # Check for HTML tags
            return '<html' in content or '<!doctype' in content or '<div' in content or '<span' in content
        except:
            return False
    
    def _validate_js_file(self, header: bytes) -> bool:
        """Validate JavaScript file content"""
        try:
            content = header.decode('utf-8', errors='ignore')
            # Check for JavaScript patterns
            js_patterns = ['function', 'const', 'let', 'var', '=>', 'import', 'export', 'require']
            return any(pattern in content for pattern in js_patterns)
        except:
            return False
    
    def _validate_ts_file(self, header: bytes) -> bool:
        """Validate TypeScript file content"""
        try:
            content = header.decode('utf-8', errors='ignore')
            # Check for TypeScript patterns
            ts_patterns = ['interface', 'type', 'enum', 'class', 'public', 'private', 'protected']
            js_patterns = ['function', 'const', 'let', 'var', '=>', 'import', 'export']
            return any(pattern in content for pattern in ts_patterns + js_patterns)
        except:
            return False
    
    def _validate_css_file(self, header: bytes) -> bool:
        """Validate CSS file content"""
        try:
            content = header.decode('utf-8', errors='ignore')
            # Check for CSS patterns
            css_patterns = ['{', '}', ':', ';', 'color', 'font', 'margin', 'padding', 'width', 'height']
            return any(pattern in content for pattern in css_patterns)
        except:
            return False
    
    async def apply_patches(self, job_id: str, fixes: List[Fix]) -> None:
        """Apply fixes to files (legacy method)"""
        await self.apply_patches_with_line_awareness(job_id, fixes)
    
    async def apply_patches_with_line_awareness(self, job_id: str, fixes: List[Fix]) -> Dict[str, Any]:
        """Apply fixes with line-aware patching and fuzzy matching"""
        from services.patch_service import PatchService
        
        patch_service = PatchService()
        return await patch_service.apply_patches_with_line_awareness(job_id, fixes)
    
    async def create_fixed_zip(self, job_id: str) -> Path:
        """Create ZIP file with fixed code"""
        job_dir = self.data_dir / job_id
        fixed_dir = job_dir / "fixed"
        zip_path = job_dir / "fixed.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in fixed_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(fixed_dir)
                    zipf.write(file_path, arcname)
        
        return zip_path
    
    def get_fixed_zip_path(self, job_id: str) -> Path:
        """Get path to fixed ZIP file"""
        return self.data_dir / job_id / "fixed.zip"
    
    def get_report_pdf_path(self, job_id: str) -> Path:
        """Get path to PDF report"""
        return self.data_dir / job_id / "report.pdf"
    
    def get_report_json_path(self, job_id: str) -> Path:
        """Get path to JSON report metadata"""
        return self.data_dir / job_id / "report.json"
    
    def get_security_validation_path(self, job_id: str) -> Path:
        """Get path to stored security validation for a job"""
        return self.data_dir / job_id / "security_validation.json"
    
    async def save_security_validation(self, job_id: str, validation: Dict[str, Any]) -> None:
        """Store security validation result for a job (for /api/security/{job_id})"""
        path = self.get_security_validation_path(job_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(validation, indent=2, default=str))
    
    async def save_job_metadata(self, job_id: str, metadata: Dict[str, Any]) -> None:
        """Save job metadata to JSON file"""
        job_dir = self.data_dir / job_id
        metadata_path = job_dir / "metadata.json"
        
        async with aiofiles.open(metadata_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(metadata, indent=2, default=str))
