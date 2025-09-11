import os
import re
import zipfile
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import aiofiles
from fastapi import HTTPException

# Try to import magic, fallback if not available
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

class SecurityService:
    """Comprehensive security and input validation service"""
    
    def __init__(self):
        self.data_dir = Path(os.getenv("DATA_DIR", "/app/data"))
        
        # Security limits
        self.MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
        self.MAX_FILES_IN_ZIP = 1000
        self.MAX_FILENAME_LENGTH = 255
        self.MAX_FILE_DEPTH = 10
        
        # Allowed file extensions
        self.ALLOWED_EXTENSIONS = {
            '.html', '.htm', '.js', '.jsx', '.ts', '.tsx', '.css', '.scss', '.sass'
        }
        
        # Dangerous patterns to detect
        self.DANGEROUS_PATTERNS = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'data:text/html',
            r'vbscript:',
            r'onload\s*=',
            r'onerror\s*=',
            r'eval\s*\(',
            r'Function\s*\(',
            r'setTimeout\s*\(',
            r'setInterval\s*\(',
            r'document\.write',
            r'innerHTML\s*=',
            r'outerHTML\s*=',
            r'exec\s*\(',
            r'system\s*\(',
            r'shell_exec\s*\(',
            r'passthru\s*\(',
            r'file_get_contents\s*\(',
            r'file_put_contents\s*\(',
            r'fopen\s*\(',
            r'fwrite\s*\(',
            r'include\s*\(',
            r'require\s*\(',
            r'import\s*\(',
        ]
        
        # Suspicious file signatures
        self.SUSPICIOUS_SIGNATURES = [
            b'<script',
            b'javascript:',
            b'vbscript:',
            b'data:text/html',
            b'<iframe',
            b'<object',
            b'<embed',
            b'<applet',
        ]
    
    async def validate_uploaded_file(self, file_path: Path, file_size: int) -> Dict[str, Any]:
        """Validate uploaded file for security and compliance"""
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "file_info": {}
        }
        
        try:
            # Check file size
            if file_size > self.MAX_FILE_SIZE:
                validation_result["valid"] = False
                validation_result["errors"].append(f"File size {file_size} exceeds maximum allowed size {self.MAX_FILE_SIZE}")
            
            # Check file extension
            file_ext = file_path.suffix.lower()
            if file_ext not in self.ALLOWED_EXTENSIONS:
                validation_result["valid"] = False
                validation_result["errors"].append(f"File extension {file_ext} is not allowed")
            
            # Check filename length
            if len(file_path.name) > self.MAX_FILENAME_LENGTH:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Filename too long: {len(file_path.name)} characters")
            
            # Check for suspicious characters in filename
            if not self._is_safe_filename(file_path.name):
                validation_result["valid"] = False
                validation_result["errors"].append("Filename contains suspicious characters")
            
            # Check file content
            content_validation = await self._validate_file_content(file_path)
            validation_result["warnings"].extend(content_validation["warnings"])
            validation_result["errors"].extend(content_validation["errors"])
            
            if content_validation["errors"]:
                validation_result["valid"] = False
            
            # Get file info
            validation_result["file_info"] = {
                "size": file_size,
                "extension": file_ext,
                "name": file_path.name,
                "path_depth": len(file_path.parts)
            }
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    async def validate_zip_file(self, zip_path: Path) -> Dict[str, Any]:
        """Validate ZIP file for security and compliance"""
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "file_count": 0,
            "total_size": 0,
            "files": []
        }
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                file_list = zip_file.infolist()
                validation_result["file_count"] = len(file_list)
                
                # Check file count
                if len(file_list) > self.MAX_FILES_IN_ZIP:
                    validation_result["valid"] = False
                    validation_result["errors"].append(f"Too many files in ZIP: {len(file_list)}")
                
                # Validate each file in the ZIP
                for file_info in file_list:
                    file_validation = await self._validate_zip_entry(file_info, zip_file)
                    validation_result["files"].append(file_validation)
                    validation_result["total_size"] += file_info.file_size
                    
                    if not file_validation["valid"]:
                        validation_result["valid"] = False
                        validation_result["errors"].extend(file_validation["errors"])
                    
                    validation_result["warnings"].extend(file_validation["warnings"])
                
                # Check total size
                if validation_result["total_size"] > self.MAX_FILE_SIZE:
                    validation_result["valid"] = False
                    validation_result["errors"].append(f"Total ZIP size {validation_result['total_size']} exceeds maximum")
                
                # Check for zip bombs
                if self._detect_zip_bomb(file_list):
                    validation_result["valid"] = False
                    validation_result["errors"].append("Potential ZIP bomb detected")
        
        except zipfile.BadZipFile:
            validation_result["valid"] = False
            validation_result["errors"].append("Invalid ZIP file")
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"ZIP validation error: {str(e)}")
        
        return validation_result
    
    async def _validate_zip_entry(self, file_info: zipfile.ZipInfo, zip_file: zipfile.ZipFile) -> Dict[str, Any]:
        """Validate a single entry in a ZIP file"""
        validation = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "filename": file_info.filename,
            "size": file_info.file_size,
            "compressed_size": file_info.compress_size
        }
        
        try:
            # Check filename length
            if len(file_info.filename) > self.MAX_FILENAME_LENGTH:
                validation["valid"] = False
                validation["errors"].append("Filename too long")
            
            # Check for path traversal
            if ".." in file_info.filename or file_info.filename.startswith("/"):
                validation["valid"] = False
                validation["errors"].append("Path traversal detected")
            
            # Check file depth
            depth = file_info.filename.count("/")
            if depth > self.MAX_FILE_DEPTH:
                validation["valid"] = False
                validation["errors"].append("File path too deep")
            
            # Check file extension
            file_path = Path(file_info.filename)
            if file_path.suffix.lower() not in self.ALLOWED_EXTENSIONS:
                validation["valid"] = False
                validation["errors"].append(f"File extension {file_path.suffix} not allowed")
            
            # Check for suspicious filename patterns
            if not self._is_safe_filename(file_info.filename):
                validation["valid"] = False
                validation["errors"].append("Suspicious filename pattern")
            
            # Check compression ratio (potential zip bomb)
            if file_info.file_size > 0:
                ratio = file_info.compress_size / file_info.file_size
                if ratio < 0.01:  # Less than 1% compression
                    validation["warnings"].append("Suspicious compression ratio")
            
            # Read and validate file content if it's a text file
            if file_path.suffix.lower() in {'.html', '.js', '.jsx', '.ts', '.tsx', '.css'}:
                try:
                    content = zip_file.read(file_info.filename)
                    content_validation = await self._validate_text_content(content)
                    validation["warnings"].extend(content_validation["warnings"])
                    validation["errors"].extend(content_validation["errors"])
                    
                    if content_validation["errors"]:
                        validation["valid"] = False
                
                except Exception as e:
                    validation["warnings"].append(f"Could not validate content: {str(e)}")
        
        except Exception as e:
            validation["valid"] = False
            validation["errors"].append(f"Entry validation error: {str(e)}")
        
        return validation
    
    async def _validate_file_content(self, file_path: Path) -> Dict[str, Any]:
        """Validate file content for security issues"""
        validation = {
            "warnings": [],
            "errors": []
        }
        
        try:
            # Read file content
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()
            
            # Check file type if magic is available
            if MAGIC_AVAILABLE:
                file_type = magic.from_buffer(content, mime=True)
                if not file_type.startswith('text/'):
                    validation["warnings"].append(f"Unexpected file type: {file_type}")
            
            # Validate text content
            text_validation = await self._validate_text_content(content)
            validation["warnings"].extend(text_validation["warnings"])
            validation["errors"].extend(text_validation["errors"])
        
        except Exception as e:
            validation["errors"].append(f"Content validation error: {str(e)}")
        
        return validation
    
    async def _validate_text_content(self, content: bytes) -> Dict[str, Any]:
        """Validate text content for dangerous patterns"""
        validation = {
            "warnings": [],
            "errors": []
        }
        
        try:
            # Decode content
            try:
                text_content = content.decode('utf-8')
            except UnicodeDecodeError:
                validation["errors"].append("Invalid UTF-8 encoding")
                return validation
            
            # Check for dangerous patterns
            for pattern in self.DANGEROUS_PATTERNS:
                if re.search(pattern, text_content, re.IGNORECASE | re.DOTALL):
                    validation["errors"].append(f"Dangerous pattern detected: {pattern}")
            
            # Check for suspicious signatures
            for signature in self.SUSPICIOUS_SIGNATURES:
                if signature in content:
                    validation["warnings"].append(f"Suspicious signature detected: {signature}")
            
            # Check for excessive nesting
            if self._has_excessive_nesting(text_content):
                validation["warnings"].append("Excessive nesting detected")
            
            # Check for suspicious URLs
            url_pattern = r'https?://[^\s<>"\']+'
            urls = re.findall(url_pattern, text_content)
            for url in urls:
                if self._is_suspicious_url(url):
                    validation["warnings"].append(f"Suspicious URL detected: {url}")
        
        except Exception as e:
            validation["errors"].append(f"Text validation error: {str(e)}")
        
        return validation
    
    def _is_safe_filename(self, filename: str) -> bool:
        """Check if filename is safe"""
        # Check for dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/', '\x00']
        if any(char in filename for char in dangerous_chars):
            return False
        
        # Check for reserved names (Windows)
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
        if filename.upper() in reserved_names:
            return False
        
        # Check for suspicious patterns
        suspicious_patterns = [r'\.\.', r'\.exe$', r'\.bat$', r'\.cmd$', r'\.scr$', r'\.pif$']
        for pattern in suspicious_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                return False
        
        return True
    
    def _detect_zip_bomb(self, file_list: List[zipfile.ZipInfo]) -> bool:
        """Detect potential ZIP bomb attacks"""
        total_uncompressed = sum(f.file_size for f in file_list)
        total_compressed = sum(f.compress_size for f in file_list)
        
        # Check compression ratio
        if total_uncompressed > 0:
            ratio = total_compressed / total_uncompressed
            if ratio < 0.01:  # Less than 1% compression
                return True
        
        # Check for files with suspiciously large uncompressed size
        for file_info in file_list:
            if file_info.file_size > 100 * 1024 * 1024:  # 100MB
                return True
        
        return False
    
    def _has_excessive_nesting(self, content: str) -> bool:
        """Check for excessive HTML/JSX nesting"""
        # Count opening and closing tags
        open_tags = content.count('<')
        close_tags = content.count('>')
        
        # Simple heuristic: if there are too many tags relative to content length
        if len(content) > 0:
            tag_ratio = (open_tags + close_tags) / len(content)
            if tag_ratio > 0.1:  # More than 10% tags
                return True
        
        return False
    
    def _is_suspicious_url(self, url: str) -> bool:
        """Check if URL is suspicious"""
        suspicious_domains = [
            'bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'ow.ly',
            'short.link', 'is.gd', 'v.gd', 'tiny.cc'
        ]
        
        for domain in suspicious_domains:
            if domain in url.lower():
                return True
        
        return False
    
    async def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to make it safe"""
        # Remove dangerous characters
        safe_chars = re.sub(r'[<>:"|?*\\/\x00]', '_', filename)
        
        # Remove leading/trailing dots and spaces
        safe_chars = safe_chars.strip('. ')
        
        # Ensure it's not empty
        if not safe_chars:
            safe_chars = "file"
        
        # Limit length
        if len(safe_chars) > self.MAX_FILENAME_LENGTH:
            safe_chars = safe_chars[:self.MAX_FILENAME_LENGTH]
        
        return safe_chars
    
    async def create_security_report(self, job_id: str, validation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create security report for a job"""
        total_files = len(validation_results)
        valid_files = sum(1 for r in validation_results if r.get("valid", False))
        invalid_files = total_files - valid_files
        
        total_warnings = sum(len(r.get("warnings", [])) for r in validation_results)
        total_errors = sum(len(r.get("errors", [])) for r in validation_results)
        
        return {
            "job_id": job_id,
            "total_files": total_files,
            "valid_files": valid_files,
            "invalid_files": invalid_files,
            "total_warnings": total_warnings,
            "total_errors": total_errors,
            "security_score": (valid_files / total_files * 100) if total_files > 0 else 100,
            "validation_results": validation_results
        }
