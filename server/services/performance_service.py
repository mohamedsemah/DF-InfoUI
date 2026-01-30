import os
import asyncio
import time
import json
import psutil
import gc
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import aiofiles
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring"""
    start_time: float
    end_time: float
    duration: float
    memory_usage: float
    cpu_usage: float
    files_processed: int
    operations_completed: int
    errors: int

class PerformanceService:
    """Service for performance optimization and monitoring"""
    
    def __init__(self):
        from utils.path_utils import get_data_dir
        self.data_dir = get_data_dir()
        self.metrics_dir = self.data_dir / "metrics"
        self.metrics_dir.mkdir(exist_ok=True)
        
        # Performance limits
        self.MAX_MEMORY_USAGE = 80  # 80% of available memory
        self.MAX_CPU_USAGE = 90     # 90% of available CPU
        self.MAX_CONCURRENT_FILES = 10
        self.CHUNK_SIZE = 8192      # 8KB chunks for file processing
        
        # Thread/Process pools
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self.process_pool = ProcessPoolExecutor(max_workers=2)
        
        # Performance monitoring
        self.active_operations = {}
        self.performance_history = []
    
    async def monitor_performance(self, operation_name: str, operation_func: Callable, *args, **kwargs) -> Any:
        """Monitor performance of an operation"""
        operation_id = f"{operation_name}_{int(time.time())}"
        
        # Start monitoring
        start_time = time.time()
        start_memory = psutil.virtual_memory().percent
        start_cpu = psutil.cpu_percent()
        
        self.active_operations[operation_id] = {
            "name": operation_name,
            "start_time": start_time,
            "start_memory": start_memory,
            "start_cpu": start_cpu
        }
        
        try:
            # Execute operation
            result = await operation_func(*args, **kwargs)
            
            # End monitoring
            end_time = time.time()
            end_memory = psutil.virtual_memory().percent
            end_cpu = psutil.cpu_percent()
            
            # Calculate metrics
            metrics = PerformanceMetrics(
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                memory_usage=end_memory - start_memory,
                cpu_usage=end_cpu - start_cpu,
                files_processed=getattr(result, 'files_processed', 0),
                operations_completed=getattr(result, 'operations_completed', 1),
                errors=getattr(result, 'errors', 0)
            )
            
            # Store metrics
            await self._store_metrics(operation_id, metrics)
            
            return result
        
        except Exception as e:
            # Record error
            end_time = time.time()
            metrics = PerformanceMetrics(
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                memory_usage=psutil.virtual_memory().percent - start_memory,
                cpu_usage=psutil.cpu_percent() - start_cpu,
                files_processed=0,
                operations_completed=0,
                errors=1
            )
            
            await self._store_metrics(operation_id, metrics)
            raise
        
        finally:
            # Cleanup
            if operation_id in self.active_operations:
                del self.active_operations[operation_id]
    
    async def optimize_file_processing(self, files: List[Path], process_func: Callable) -> List[Any]:
        """Optimize file processing with chunking and parallel processing"""
        if not files:
            return []
        
        # Check system resources
        if not await self._check_system_resources():
            await self._cleanup_resources()
        
        # Process files in chunks
        results = []
        chunk_size = min(self.MAX_CONCURRENT_FILES, len(files))
        
        for i in range(0, len(files), chunk_size):
            chunk = files[i:i + chunk_size]
            
            # Process chunk in parallel
            chunk_results = await self._process_chunk_parallel(chunk, process_func)
            results.extend(chunk_results)
            
            # Yield control to prevent blocking
            await asyncio.sleep(0.01)
        
        return results
    
    async def _process_chunk_parallel(self, files: List[Path], process_func: Callable) -> List[Any]:
        """Process a chunk of files in parallel"""
        tasks = []
        
        for file_path in files:
            task = asyncio.create_task(
                self._process_single_file(file_path, process_func)
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for result in results:
            if not isinstance(result, Exception):
                valid_results.append(result)
        
        return valid_results
    
    async def _process_single_file(self, file_path: Path, process_func: Callable) -> Any:
        """Process a single file with error handling"""
        try:
            return await process_func(file_path)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return None
    
    async def _check_system_resources(self) -> bool:
        """Check if system has enough resources"""
        memory_usage = psutil.virtual_memory().percent
        cpu_usage = psutil.cpu_percent()
        
        if memory_usage > self.MAX_MEMORY_USAGE:
            print(f"High memory usage: {memory_usage}%")
            return False
        
        if cpu_usage > self.MAX_CPU_USAGE:
            print(f"High CPU usage: {cpu_usage}%")
            return False
        
        return True
    
    async def _cleanup_resources(self):
        """Clean up system resources"""
        # Force garbage collection
        gc.collect()
        
        # Clear caches if available
        try:
            import sys
            if hasattr(sys, 'getsizeof'):
                # Clear any large objects
                pass
        except:
            pass
    
    async def optimize_memory_usage(self, job_id: str) -> Dict[str, Any]:
        """Optimize memory usage for a job"""
        job_dir = self.data_dir / job_id
        
        optimization_result = {
            "memory_before": psutil.virtual_memory().percent,
            "files_cleaned": 0,
            "memory_after": 0,
            "optimization_applied": []
        }
        
        try:
            # Clean up temporary files
            temp_dirs = ["rendered", "snapshots", "temp"]
            for temp_dir in temp_dirs:
                temp_path = job_dir / temp_dir
                if temp_path.exists():
                    await self._cleanup_directory(temp_path)
                    optimization_result["files_cleaned"] += 1
                    optimization_result["optimization_applied"].append(f"Cleaned {temp_dir}")
            
            # Force garbage collection
            gc.collect()
            
            # Check memory after cleanup
            optimization_result["memory_after"] = psutil.virtual_memory().percent
            
        except Exception as e:
            print(f"Memory optimization error: {e}")
        
        return optimization_result
    
    async def _cleanup_directory(self, directory: Path):
        """Clean up a directory"""
        try:
            import shutil
            if directory.exists():
                shutil.rmtree(directory)
        except Exception as e:
            print(f"Error cleaning directory {directory}: {e}")
    
    async def optimize_ast_analysis(self, files: List[Path]) -> List[Dict[str, Any]]:
        """Optimize AST analysis for multiple files"""
        # Group files by type for batch processing
        file_groups = {
            'js': [],
            'ts': [],
            'jsx': [],
            'tsx': [],
            'css': []
        }
        
        for file_path in files:
            ext = file_path.suffix.lower()
            if ext in file_groups:
                file_groups[ext].append(file_path)
        
        results = []
        
        # Process each group in parallel
        tasks = []
        for file_type, type_files in file_groups.items():
            if type_files:
                task = asyncio.create_task(
                    self._analyze_file_group(file_type, type_files)
                )
                tasks.append(task)
        
        # Wait for all groups to complete
        group_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results
        for result in group_results:
            if isinstance(result, list):
                results.extend(result)
        
        return results
    
    async def _analyze_file_group(self, file_type: str, files: List[Path]) -> List[Dict[str, Any]]:
        """Analyze a group of files of the same type"""
        from services.ast_service import ASTService
        
        ast_service = ASTService()
        results = []
        
        # Process files in smaller chunks to avoid memory issues
        chunk_size = min(5, len(files))
        
        for i in range(0, len(files), chunk_size):
            chunk = files[i:i + chunk_size]
            
            # Analyze chunk
            chunk_results = await ast_service.analyze_files_ast_batch(chunk)
            results.extend(chunk_results)
            
            # Yield control
            await asyncio.sleep(0.01)
        
        return results
    
    async def optimize_validation(self, files: List[Path]) -> List[Dict[str, Any]]:
        """Optimize validation for multiple files"""
        # Group files by validation type
        validation_groups = {
            'html': [],
            'js': [],
            'ts': [],
            'css': []
        }
        
        for file_path in files:
            ext = file_path.suffix.lower()
            if ext == '.html':
                validation_groups['html'].append(file_path)
            elif ext in ['.js', '.jsx']:
                validation_groups['js'].append(file_path)
            elif ext in ['.ts', '.tsx']:
                validation_groups['ts'].append(file_path)
            elif ext == '.css':
                validation_groups['css'].append(file_path)
        
        results = []
        
        # Process each group in parallel
        tasks = []
        for validation_type, type_files in validation_groups.items():
            if type_files:
                task = asyncio.create_task(
                    self._validate_file_group(validation_type, type_files)
                )
                tasks.append(task)
        
        # Wait for all groups to complete
        group_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results
        for result in group_results:
            if isinstance(result, list):
                results.extend(result)
        
        return results
    
    async def _validate_file_group(self, validation_type: str, files: List[Path]) -> List[Dict[str, Any]]:
        """Validate a group of files of the same type"""
        from services.validation_service import ValidationService
        
        validation_service = ValidationService()
        results = []
        
        # Process files in smaller chunks
        chunk_size = min(5, len(files))
        
        for i in range(0, len(files), chunk_size):
            chunk = files[i:i + chunk_size]
            
            # Validate chunk
            chunk_results = await validation_service.validate_files_batch(chunk)
            results.extend(chunk_results)
            
            # Yield control
            await asyncio.sleep(0.01)
        
        return results
    
    async def _store_metrics(self, operation_id: str, metrics: PerformanceMetrics):
        """Store performance metrics"""
        try:
            metrics_file = self.metrics_dir / f"{operation_id}.json"
            metrics_data = {
                "operation_id": operation_id,
                "timestamp": datetime.now().isoformat(),
                "duration": metrics.duration,
                "memory_usage": metrics.memory_usage,
                "cpu_usage": metrics.cpu_usage,
                "files_processed": metrics.files_processed,
                "operations_completed": metrics.operations_completed,
                "errors": metrics.errors
            }
            
            async with aiofiles.open(metrics_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(metrics_data, indent=2))
            
            # Store in memory for quick access
            self.performance_history.append(metrics_data)
            
            # Keep only last 100 metrics in memory
            if len(self.performance_history) > 100:
                self.performance_history = self.performance_history[-100:]
        
        except Exception as e:
            print(f"Error storing metrics: {e}")
    
    async def get_performance_summary(self, job_id: str) -> Dict[str, Any]:
        """Get performance summary for a job"""
        try:
            # Find metrics files for this job
            metrics_files = list(self.metrics_dir.glob(f"*{job_id}*"))
            
            if not metrics_files:
                return {"message": "No performance data available"}
            
            # Load metrics
            all_metrics = []
            for metrics_file in metrics_files:
                async with aiofiles.open(metrics_file, 'r', encoding='utf-8') as f:
                    metrics_data = json.loads(await f.read())
                    all_metrics.append(metrics_data)
            
            # Calculate summary
            total_duration = sum(m["duration"] for m in all_metrics)
            total_files = sum(m["files_processed"] for m in all_metrics)
            total_operations = sum(m["operations_completed"] for m in all_metrics)
            total_errors = sum(m["errors"] for m in all_metrics)
            
            avg_memory = sum(m["memory_usage"] for m in all_metrics) / len(all_metrics)
            avg_cpu = sum(m["cpu_usage"] for m in all_metrics) / len(all_metrics)
            
            return {
                "job_id": job_id,
                "total_duration": total_duration,
                "total_files_processed": total_files,
                "total_operations": total_operations,
                "total_errors": total_errors,
                "average_memory_usage": avg_memory,
                "average_cpu_usage": avg_cpu,
                "operations_count": len(all_metrics),
                "performance_score": self._calculate_performance_score(all_metrics)
            }
        
        except Exception as e:
            return {"error": f"Failed to get performance summary: {e}"}
    
    def _calculate_performance_score(self, metrics: List[Dict[str, Any]]) -> float:
        """Calculate performance score (0-100)"""
        if not metrics:
            return 0.0
        
        # Base score
        score = 100.0
        
        # Penalize for errors
        error_rate = sum(m["errors"] for m in metrics) / sum(m["operations_completed"] for m in metrics)
        score -= error_rate * 50
        
        # Penalize for high memory usage
        avg_memory = sum(m["memory_usage"] for m in metrics) / len(metrics)
        if avg_memory > 50:
            score -= (avg_memory - 50) * 0.5
        
        # Penalize for high CPU usage
        avg_cpu = sum(m["cpu_usage"] for m in metrics) / len(metrics)
        if avg_cpu > 50:
            score -= (avg_cpu - 50) * 0.5
        
        return max(0.0, min(100.0, score))
    
    async def cleanup_old_metrics(self, days_old: int = 7):
        """Clean up old performance metrics"""
        try:
            cutoff_time = time.time() - (days_old * 24 * 60 * 60)
            
            for metrics_file in self.metrics_dir.glob("*.json"):
                if metrics_file.stat().st_mtime < cutoff_time:
                    metrics_file.unlink()
        
        except Exception as e:
            print(f"Error cleaning up old metrics: {e}")
    
    def __del__(self):
        """Cleanup when service is destroyed"""
        try:
            self.thread_pool.shutdown(wait=False)
            self.process_pool.shutdown(wait=False)
        except:
            pass
