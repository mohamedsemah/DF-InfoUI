import os
import zipfile
import shutil
import json
from pathlib import Path
from typing import List, Dict, Any
import aiofiles
from models.job import Fix

class FileService:
    def __init__(self):
        self.data_dir = Path(os.getenv("DATA_DIR", "/app/data"))
        self.data_dir.mkdir(exist_ok=True)
    
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
        """Get all original files for analysis"""
        original_dir = self.data_dir / job_id / "original"
        files = []
        
        for ext in ['*.html', '*.js', '*.jsx', '*.ts', '*.tsx', '*.css']:
            files.extend(original_dir.rglob(ext))
        
        return files
    
    async def apply_patches(self, job_id: str, fixes: List[Fix]) -> None:
        """Apply fixes to files"""
        job_dir = self.data_dir / job_id
        fixed_dir = job_dir / "fixed"
        original_dir = job_dir / "original"
        
        # Copy original files to fixed directory
        if fixed_dir.exists():
            shutil.rmtree(fixed_dir)
        shutil.copytree(original_dir, fixed_dir)
        
        # Apply each fix
        for fix in fixes:
            if not fix.applied:
                continue
                
            file_path = fixed_dir / fix.file_path
            if not file_path.exists():
                continue
            
            try:
                # Read current file content
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                
                # Apply the fix (simple string replacement for now)
                # In production, use proper diff/patch libraries
                lines = content.split('\n')
                if fix.before_code in content:
                    new_content = content.replace(fix.before_code, fix.after_code)
                    
                    async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                        await f.write(new_content)
                    
                    fix.applied = True
            except Exception as e:
                print(f"Failed to apply fix {fix.issue_id}: {e}")
    
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
    
    async def save_job_metadata(self, job_id: str, metadata: Dict[str, Any]) -> None:
        """Save job metadata to JSON file"""
        job_dir = self.data_dir / job_id
        metadata_path = job_dir / "metadata.json"
        
        async with aiofiles.open(metadata_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(metadata, indent=2, default=str))
