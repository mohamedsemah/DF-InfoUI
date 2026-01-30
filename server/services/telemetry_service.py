import os
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
import aiofiles
import logging
from dataclasses import dataclass, asdict

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class EventType(Enum):
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    JOB_STAGE_STARTED = "job_stage_started"
    FILE_UPLOADED = "file_uploaded"
    FILE_PROCESSED = "file_processed"
    ISSUE_DETECTED = "issue_detected"
    ISSUE_FIXED = "issue_fixed"
    VALIDATION_PASSED = "validation_passed"
    VALIDATION_FAILED = "validation_failed"
    ERROR_OCCURRED = "error_occurred"
    PERFORMANCE_METRIC = "performance_metric"
    SECURITY_VIOLATION = "security_violation"

@dataclass
class TelemetryEvent:
    """Telemetry event structure"""
    timestamp: str
    event_type: str
    level: str
    message: str
    job_id: Optional[str]
    data: Dict[str, Any]
    source: str
    duration: Optional[float] = None

class TelemetryService:
    """Comprehensive logging and telemetry service"""
    
    def __init__(self):
        from utils.path_utils import get_data_dir
        self.data_dir = get_data_dir()
        self.logs_dir = self.data_dir / "logs"
        self.telemetry_dir = self.data_dir / "telemetry"
        self.metrics_dir = self.data_dir / "metrics"
        
        # Create directories
        for dir_path in [self.logs_dir, self.telemetry_dir, self.metrics_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Event storage
        self.events = []
        self.max_events_in_memory = 1000
        
        # Performance tracking
        self.performance_metrics = {}
        
        # Error tracking
        self.error_counts = {}
        
        # Job tracking
        self.active_jobs = {}
        self.job_metrics = {}
    
    def _setup_logging(self):
        """Setup comprehensive logging configuration"""
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler for all logs
        all_logs_file = self.logs_dir / "all.log"
        file_handler = logging.FileHandler(all_logs_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
        
        # Error log file
        error_logs_file = self.logs_dir / "errors.log"
        error_handler = logging.FileHandler(error_logs_file)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)
        
        # Performance log file
        perf_logs_file = self.logs_dir / "performance.log"
        perf_handler = logging.FileHandler(perf_logs_file)
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(perf_handler)
        
        # Security log file
        security_logs_file = self.logs_dir / "security.log"
        security_handler = logging.FileHandler(security_logs_file)
        security_handler.setLevel(logging.WARNING)
        security_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(security_handler)
        
        self.logger = logging.getLogger('DF-InfoUI')
    
    async def log_event(self, 
                       event_type: EventType, 
                       message: str, 
                       level: LogLevel = LogLevel.INFO,
                       job_id: Optional[str] = None,
                       data: Optional[Dict[str, Any]] = None,
                       source: str = "system",
                       duration: Optional[float] = None):
        """Log a telemetry event"""
        
        event = TelemetryEvent(
            timestamp=datetime.now().isoformat(),
            event_type=event_type.value,
            level=level.value,
            message=message,
            job_id=job_id,
            data=data or {},
            source=source,
            duration=duration
        )
        
        # Add to memory
        self.events.append(event)
        
        # Keep only recent events in memory
        if len(self.events) > self.max_events_in_memory:
            self.events = self.events[-self.max_events_in_memory:]
        
        # Log to appropriate logger
        log_message = f"[{event_type.value}] {message}"
        if job_id:
            log_message = f"[{job_id}] {log_message}"
        
        if data:
            log_message += f" | Data: {json.dumps(data)}"
        
        if duration:
            log_message += f" | Duration: {duration:.2f}s"
        
        # Log based on level
        if level == LogLevel.DEBUG:
            self.logger.debug(log_message)
        elif level == LogLevel.INFO:
            self.logger.info(log_message)
        elif level == LogLevel.WARNING:
            self.logger.warning(log_message)
        elif level == LogLevel.ERROR:
            self.logger.error(log_message)
        elif level == LogLevel.CRITICAL:
            self.logger.critical(log_message)
        
        # Save to telemetry file
        await self._save_telemetry_event(event)
        
        # Update metrics
        await self._update_metrics(event)
    
    async def _save_telemetry_event(self, event: TelemetryEvent):
        """Save telemetry event to file"""
        try:
            # Save to daily telemetry file
            today = datetime.now().strftime('%Y%m%d')
            telemetry_file = self.telemetry_dir / f"telemetry_{today}.jsonl"
            
            event_data = asdict(event)
            event_line = json.dumps(event_data) + '\n'
            
            async with aiofiles.open(telemetry_file, 'a', encoding='utf-8') as f:
                await f.write(event_line)
        
        except Exception as e:
            self.logger.error(f"Failed to save telemetry event: {e}")
    
    async def _update_metrics(self, event: TelemetryEvent):
        """Update internal metrics based on event"""
        try:
            # Update error counts
            if event.event_type == EventType.ERROR_OCCURRED.value:
                error_key = event.data.get('error_type', 'unknown')
                self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
            
            # Update job metrics
            if event.job_id:
                if event.job_id not in self.job_metrics:
                    self.job_metrics[event.job_id] = {
                        'start_time': None,
                        'end_time': None,
                        'events': [],
                        'errors': 0,
                        'files_processed': 0,
                        'issues_detected': 0,
                        'issues_fixed': 0
                    }
                
                job_metrics = self.job_metrics[event.job_id]
                job_metrics['events'].append(event.event_type)
                
                if event.event_type == EventType.JOB_STARTED.value:
                    job_metrics['start_time'] = event.timestamp
                elif event.event_type in (EventType.JOB_COMPLETED.value, "job_completed"):
                    job_metrics['end_time'] = event.timestamp
                elif event.event_type == EventType.ERROR_OCCURRED.value:
                    job_metrics['errors'] += 1
                elif event.event_type == EventType.FILE_PROCESSED.value:
                    job_metrics['files_processed'] += 1
                elif event.event_type == EventType.ISSUE_DETECTED.value:
                    job_metrics['issues_detected'] += 1
                elif event.event_type == EventType.ISSUE_FIXED.value:
                    job_metrics['issues_fixed'] += 1
            
            # Update performance metrics
            if event.event_type == EventType.PERFORMANCE_METRIC.value:
                metric_name = event.data.get('metric_name', 'unknown')
                metric_value = event.data.get('metric_value', 0)
                
                if metric_name not in self.performance_metrics:
                    self.performance_metrics[metric_name] = []
                
                self.performance_metrics[metric_name].append({
                    'timestamp': event.timestamp,
                    'value': metric_value,
                    'job_id': event.job_id
                })
        
        except Exception as e:
            self.logger.error(f"Failed to update metrics: {e}")
    
    async def start_job_tracking(self, job_id: str, job_data: Dict[str, Any]):
        """Start tracking a job"""
        self.active_jobs[job_id] = {
            'start_time': time.time(),
            'data': job_data,
            'events': []
        }
        
        await self.log_event(
            EventType.JOB_STARTED,
            f"Job {job_id} started",
            LogLevel.INFO,
            job_id,
            job_data
        )
    
    async def end_job_tracking(self, job_id: str, success: bool, result_data: Optional[Dict[str, Any]] = None):
        """End tracking a job"""
        if job_id in self.active_jobs:
            job_info = self.active_jobs[job_id]
            duration = time.time() - job_info['start_time']
            
            event_type = EventType.JOB_COMPLETED if success else EventType.JOB_FAILED
            message = f"Job {job_id} {'completed' if success else 'failed'} in {duration:.2f}s"
            
            await self.log_event(
                event_type,
                message,
                LogLevel.INFO if success else LogLevel.ERROR,
                job_id,
                result_data,
                duration=duration
            )
            
            del self.active_jobs[job_id]
    
    async def log_file_processed(self, job_id: str, file_path: str, issues_found: int = 0):
        """Log file processing completion"""
        await self.log_event(
            EventType.FILE_PROCESSED,
            f"Processed file: {file_path}",
            LogLevel.INFO,
            job_id,
            {
                'file_path': file_path,
                'issues_found': issues_found
            }
        )
    
    async def log_issue_detected(self, job_id: str, issue_data: Dict[str, Any]):
        """Log issue detection"""
        await self.log_event(
            EventType.ISSUE_DETECTED,
            f"Issue detected: {issue_data.get('rule_id', 'unknown')}",
            LogLevel.INFO,
            job_id,
            issue_data
        )
    
    async def log_issue_fixed(self, job_id: str, fix_data: Dict[str, Any]):
        """Log issue fix"""
        await self.log_event(
            EventType.ISSUE_FIXED,
            f"Issue fixed: {fix_data.get('rule_id', 'unknown')}",
            LogLevel.INFO,
            job_id,
            fix_data
        )
    
    async def log_validation_result(self, job_id: str, validation_data: Dict[str, Any]):
        """Log validation result"""
        passed = validation_data.get('passed', False)
        event_type = EventType.VALIDATION_PASSED if passed else EventType.VALIDATION_FAILED
        
        await self.log_event(
            event_type,
            f"Validation {'passed' if passed else 'failed'}",
            LogLevel.INFO if passed else LogLevel.WARNING,
            job_id,
            validation_data
        )
    
    async def log_error(self, job_id: Optional[str], error: Exception, context: Dict[str, Any]):
        """Log an error"""
        await self.log_event(
            EventType.ERROR_OCCURRED,
            f"Error: {str(error)}",
            LogLevel.ERROR,
            job_id,
            {
                'error_type': type(error).__name__,
                'error_message': str(error),
                'context': context
            }
        )
    
    async def log_performance_metric(self, job_id: str, metric_name: str, metric_value: float, unit: str = ""):
        """Log a performance metric"""
        await self.log_event(
            EventType.PERFORMANCE_METRIC,
            f"Performance metric: {metric_name} = {metric_value}{unit}",
            LogLevel.INFO,
            job_id,
            {
                'metric_name': metric_name,
                'metric_value': metric_value,
                'unit': unit
            }
        )
    
    async def log_security_violation(self, job_id: str, violation_data: Dict[str, Any]):
        """Log a security violation"""
        await self.log_event(
            EventType.SECURITY_VIOLATION,
            f"Security violation: {violation_data.get('type', 'unknown')}",
            LogLevel.WARNING,
            job_id,
            violation_data
        )
    
    async def get_job_telemetry(self, job_id: str) -> Dict[str, Any]:
        """Get telemetry data for a specific job"""
        try:
            # Get job metrics
            job_metrics = self.job_metrics.get(job_id, {})
            
            # Get events for this job
            job_events = [event for event in self.events if event.job_id == job_id]
            
            # Get performance metrics for this job
            job_performance = {}
            for metric_name, metric_data in self.performance_metrics.items():
                job_metric_data = [m for m in metric_data if m.get('job_id') == job_id]
                if job_metric_data:
                    job_performance[metric_name] = job_metric_data
            
            return {
                'job_id': job_id,
                'metrics': job_metrics,
                'events': [asdict(event) for event in job_events],
                'performance': job_performance,
                'total_events': len(job_events)
            }
        
        except Exception as e:
            self.logger.error(f"Failed to get job telemetry: {e}")
            return {'error': str(e)}
    
    async def get_system_telemetry(self) -> Dict[str, Any]:
        """Get system-wide telemetry data"""
        try:
            # Calculate time ranges
            now = datetime.now()
            last_hour = now - timedelta(hours=1)
            last_day = now - timedelta(days=1)
            
            # Filter events by time
            recent_events = [e for e in self.events if datetime.fromisoformat(e.timestamp) > last_hour]
            daily_events = [e for e in self.events if datetime.fromisoformat(e.timestamp) > last_day]
            
            # Calculate statistics
            total_jobs = len(self.job_metrics)
            active_jobs = len(self.active_jobs)
            completed_jobs = sum(1 for j in self.job_metrics.values() if j.get('end_time'))
            failed_jobs = sum(1 for j in self.job_metrics.values() if j.get('errors', 0) > 0)
            
            # Error statistics
            error_summary = {}
            for error_type, count in self.error_counts.items():
                error_summary[error_type] = count
            
            # Performance summary
            performance_summary = {}
            for metric_name, metric_data in self.performance_metrics.items():
                if metric_data:
                    values = [m['value'] for m in metric_data]
                    performance_summary[metric_name] = {
                        'count': len(values),
                        'average': sum(values) / len(values),
                        'min': min(values),
                        'max': max(values)
                    }
            
            return {
                'timestamp': now.isoformat(),
                'jobs': {
                    'total': total_jobs,
                    'active': active_jobs,
                    'completed': completed_jobs,
                    'failed': failed_jobs
                },
                'events': {
                    'last_hour': len(recent_events),
                    'last_day': len(daily_events),
                    'total': len(self.events)
                },
                'errors': error_summary,
                'performance': performance_summary,
                'system_status': 'healthy' if failed_jobs < total_jobs * 0.1 else 'degraded'
            }
        
        except Exception as e:
            self.logger.error(f"Failed to get system telemetry: {e}")
            return {'error': str(e)}
    
    async def cleanup_old_telemetry(self, days_old: int = 30):
        """Clean up old telemetry data"""
        try:
            cutoff_time = time.time() - (days_old * 24 * 60 * 60)
            
            # Clean up telemetry files
            for telemetry_file in self.telemetry_dir.glob("telemetry_*.jsonl"):
                if telemetry_file.stat().st_mtime < cutoff_time:
                    telemetry_file.unlink()
            
            # Clean up old job metrics
            old_jobs = []
            for job_id, job_data in self.job_metrics.items():
                if job_data.get('end_time'):
                    job_end_time = datetime.fromisoformat(job_data['end_time']).timestamp()
                    if job_end_time < cutoff_time:
                        old_jobs.append(job_id)
            
            for job_id in old_jobs:
                del self.job_metrics[job_id]
            
            self.logger.info(f"Cleaned up {len(old_jobs)} old job metrics")
        
        except Exception as e:
            self.logger.error(f"Failed to cleanup old telemetry: {e}")
    
    async def export_telemetry(self, job_id: Optional[str] = None, format: str = "json") -> str:
        """Export telemetry data"""
        try:
            if job_id:
                data = await self.get_job_telemetry(job_id)
            else:
                data = await self.get_system_telemetry()
            
            if format == "json":
                return json.dumps(data, indent=2)
            else:
                return str(data)
        
        except Exception as e:
            self.logger.error(f"Failed to export telemetry: {e}")
            return json.dumps({"error": str(e)})
