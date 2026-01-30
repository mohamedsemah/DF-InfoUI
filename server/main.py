import os
import uuid
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import aiofiles
from dotenv import load_dotenv

from agents.brain_agent import BrainAgent
from agents.pour_agents import POURAgents
from services.file_service import FileService, MAX_FILES_COUNT
from services.validation_service import ValidationService
from services.report_service import ReportService
from services.security_service import SecurityService
from services.performance_service import PerformanceService
from services.telemetry_service import TelemetryService, EventType
from services.error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
from models.job import Job, JobStatus

load_dotenv('.env')

app = FastAPI(title="DF-InfoUI", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
file_service = FileService()
brain_agent = BrainAgent()
pour_agents = POURAgents()
validation_service = ValidationService()
report_service = ReportService()
security_service = SecurityService()
performance_service = PerformanceService()
telemetry_service = TelemetryService()
error_handler = ErrorHandler()

# In-memory job storage (in production, use Redis or database)
jobs: Dict[str, Job] = {}

class UploadResponse(BaseModel):
    job_id: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: int
    message: str
    summary: Optional[Dict[str, Any]] = None

@app.post("/api/upload", response_model=UploadResponse)
async def upload_file(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    """Upload a ZIP file (single) or multiple UI/source files and start processing."""
    job_id = str(uuid.uuid4())
    if not files:
        raise HTTPException(status_code=400, detail="No files provided. Upload a ZIP or one or more supported files.")
    # Single ZIP: use existing flow
    if len(files) == 1 and files[0].filename and files[0].filename.lower().endswith(".zip"):
        file = files[0]
        try:
            await telemetry_service.start_job_tracking(job_id, {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": file.size
            })
            file_path = await file_service.save_uploaded_file(job_id, file)
            security_validation = await security_service.validate_zip_file(file_path)
            await file_service.save_security_validation(job_id, security_validation)
            if not security_validation["valid"]:
                await error_handler.handle_error(
                    ValueError("Security validation failed"),
                    error_handler.create_error_context(
                        filename=file.filename,
                        validation_errors=security_validation["errors"]
                    ),
                    ErrorCategory.SECURITY_VIOLATION,
                    ErrorSeverity.HIGH,
                    job_id
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Security validation failed: {', '.join(security_validation['errors'])}"
                )
            job = Job(id=job_id, status=JobStatus.UPLOADED)
            jobs[job_id] = job
            job.message = "File uploaded and validated successfully"
            await telemetry_service.log_event(
                EventType.FILE_UPLOADED,
                f"File {file.filename} uploaded successfully",
                job_id=job_id,
                data={"filename": file.filename, "size": file.size}
            )
            background_tasks.add_task(process_job, job_id)
            return UploadResponse(job_id=job_id)
        except HTTPException:
            raise
        except Exception as e:
            import traceback
            print(f"DEBUG: Upload exception: {traceback.format_exc()}")
            await error_handler.handle_error(
                e,
                error_handler.create_error_context(filename=file.filename),
                ErrorCategory.FILE_PROCESSING,
                ErrorSeverity.HIGH,
                job_id
            )
            await telemetry_service.end_job_tracking(job_id, False, {"error": str(e)})
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    # Multiple files or single non-ZIP: save into original/ and process
    filenames = [f.filename or "" for f in files]
    try:
        await telemetry_service.start_job_tracking(job_id, {"filenames": filenames, "count": len(files)})
        if len(files) > MAX_FILES_COUNT:
            raise HTTPException(status_code=400, detail=f"Too many files. Maximum {MAX_FILES_COUNT} files per upload.")
        await file_service.save_uploaded_files(job_id, files)
        job = Job(id=job_id, status=JobStatus.UPLOADED)
        jobs[job_id] = job
        job.message = f"{len(files)} file(s) uploaded successfully"
        await telemetry_service.log_event(EventType.FILE_UPLOADED, f"{len(files)} files uploaded", job_id=job_id, data={"count": len(files), "filenames": filenames})
        background_tasks.add_task(process_job, job_id)
        return UploadResponse(job_id=job_id)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        print(f"DEBUG: Multi-file upload exception: {traceback.format_exc()}")
        await error_handler.handle_error(e, error_handler.create_error_context(filenames=filenames), ErrorCategory.FILE_PROCESSING, ErrorSeverity.HIGH, job_id)
        await telemetry_service.end_job_tracking(job_id, False, {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get job status and progress"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    return JobStatusResponse(
        job_id=job_id,
        status=job.status,
        progress=job.progress,
        message=job.message,
        summary=job.summary
    )

@app.get("/api/download/{job_id}/fixed.zip")
async def download_fixed_zip(job_id: str):
    """Download the fixed ZIP file"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job.status != JobStatus.COMPLETE:
        raise HTTPException(status_code=400, detail="Job not complete")
    
    zip_path = file_service.get_fixed_zip_path(job_id)
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Fixed ZIP not found")
    
    return FileResponse(
        path=str(zip_path),
        filename=f"fixed_{job_id}.zip",
        media_type="application/zip"
    )

@app.get("/api/download/{job_id}/report.pdf")
async def download_report_pdf(job_id: str):
    """Download the PDF report"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job.status != JobStatus.COMPLETE:
        raise HTTPException(status_code=400, detail="Job not complete")
    
    pdf_path = file_service.get_report_pdf_path(job_id)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF report not found")
    
    return FileResponse(
        path=str(pdf_path),
        filename=f"report_{job_id}.pdf",
        media_type="application/pdf"
    )

@app.get("/api/report/{job_id}")
async def get_job_report(job_id: str):
    """Get detailed job report data for frontend"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job.status != JobStatus.COMPLETE:
        raise HTTPException(status_code=400, detail="Job not complete")
    
    # Load report data from file
    report_path = file_service.get_report_json_path(job_id)
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report data not found")
    
    try:
        async with aiofiles.open(report_path, 'r', encoding='utf-8') as f:
            report_data = json.loads(await f.read())
        return report_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load report data: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "df-infoui-backend"}

@app.get("/api/telemetry/{job_id}")
async def get_job_telemetry(job_id: str):
    """Get telemetry data for a specific job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    telemetry_data = await telemetry_service.get_job_telemetry(job_id)
    return telemetry_data

@app.get("/api/telemetry")
async def get_system_telemetry():
    """Get system-wide telemetry data"""
    telemetry_data = await telemetry_service.get_system_telemetry()
    return telemetry_data

@app.get("/api/performance/{job_id}")
async def get_job_performance(job_id: str):
    """Get performance metrics for a specific job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    performance_data = await performance_service.get_performance_summary(job_id)
    return performance_data

@app.get("/api/security/{job_id}")
async def get_job_security_report(job_id: str):
    """Get security report for a specific job (from ZIP validation at upload)"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    path = file_service.get_security_validation_path(job_id)
    if not path.exists():
        return {"job_id": job_id, "message": "No security validation data for this job (upload predates this feature)."}
    
    try:
        async with aiofiles.open(path, 'r', encoding='utf-8') as f:
            data = json.loads(await f.read())
        report = await security_service.create_security_report(
            job_id,
            data.get("files", [])
        )
        report["validation"] = data
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load security report: {str(e)}")

async def process_job(job_id: str):
    """Process a job through all stages with performance monitoring and telemetry"""
    job = jobs[job_id]
    
    try:
        # Monitor overall job performance
        result = await performance_service.monitor_performance(
            "job_processing",
            _process_job_internal,
            job_id
        )
        
        # Update job with results
        job.status = JobStatus.COMPLETE
        job.message = "Processing complete! All fixes applied and validated."
        job.progress = 100
        job.summary = result.get("summary", {})
        
        # End job tracking
        await telemetry_service.end_job_tracking(job_id, True, result)
        
    except Exception as e:
        # Handle error with error handler
        await error_handler.handle_error(
            e,
            error_handler.create_error_context(job_id=job_id),
            ErrorCategory.SYSTEM,
            ErrorSeverity.HIGH,
            job_id
        )
        
        job.status = JobStatus.ERROR
        job.message = f"Processing failed: {str(e)}"
        job.progress = 0
        
        # End job tracking with failure
        await telemetry_service.end_job_tracking(job_id, False, {"error": str(e)})

async def _process_job_internal(job_id: str):
    """Internal job processing function for performance monitoring"""
    job = jobs[job_id]
    
    # Stage 1: Brain Agent - Analyze & Detect
    job.status = JobStatus.PLANNING
    job.message = "Brain Agent analyzing files and detecting accessibility issues..."
    job.progress = 20
    
    await telemetry_service.log_event(
        EventType.JOB_STAGE_STARTED,
        "Starting file analysis and issue detection",
        job_id=job_id,
        data={"stage": "analysis"}
    )
    
    issues = await brain_agent.analyze_files(job_id)
    job.summary = {"total_issues": len(issues)}
    
    await telemetry_service.log_file_processed(job_id, "analysis_complete", len(issues))
    
    # Stage 2: Brain Agent - Coordinate Fixing Process
    job.status = JobStatus.FIXING
    job.message = "Brain Agent coordinating POUR agents to fix issues..."
    job.progress = 40
    
    await telemetry_service.log_event(
        EventType.JOB_STAGE_STARTED,
        "Starting issue fixing coordination",
        job_id=job_id,
        data={"stage": "fixing", "issues_count": len(issues)}
    )
    
    # Brain Agent coordinates the entire fixing process
    coordination_results = await brain_agent.coordinate_fixing_process(job_id, issues)
    
    # Stage 3: Validation
    job.status = JobStatus.VALIDATING
    job.message = "Validating fixes with ESLint, axe-core, and TypeScript compilation..."
    job.progress = 80
    
    await telemetry_service.log_event(
        EventType.JOB_STAGE_STARTED,
        "Starting validation process",
        job_id=job_id,
        data={"stage": "validation"}
    )
    
    # Stage 4: Complete
    job.status = JobStatus.COMPLETE
    job.message = "Processing complete! All fixes applied and validated."
    job.progress = 100
    
    summary = {
        "total_issues": coordination_results["total_issues"],
        "total_fixes": coordination_results["total_fixes"],
        "agent_reports": coordination_results["agent_reports"],
        "validation_passed": coordination_results["validation_results"].get("passed", False),
        "remaining_issues": coordination_results["validation_results"].get("remaining_issues", 0)
    }
    
    job.summary.update(summary)
    
    # Log completion
    await telemetry_service.log_event(
        EventType.JOB_COMPLETED,
        "Job processing completed successfully",
        job_id=job_id,
        data=summary
    )
    
    return {"summary": summary}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
