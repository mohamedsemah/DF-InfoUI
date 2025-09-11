import os
import uuid
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

from agents.brain_agent import BrainAgent
from agents.pour_agents import POURAgents
from services.file_service import FileService
from services.validation_service import ValidationService
from services.report_service import ReportService
from models.job import Job, JobStatus

load_dotenv()

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
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload a ZIP file and start processing"""
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are allowed")
    
    job_id = str(uuid.uuid4())
    job = Job(id=job_id, status=JobStatus.UPLOADED)
    jobs[job_id] = job
    
    try:
        # Save uploaded file
        await file_service.save_uploaded_file(job_id, file)
        job.status = JobStatus.UPLOADED
        job.message = "File uploaded successfully"
        
        # Start processing in background
        background_tasks.add_task(process_job, job_id)
        
        return UploadResponse(job_id=job_id)
    except Exception as e:
        job.status = JobStatus.ERROR
        job.message = f"Upload failed: {str(e)}"
        raise HTTPException(status_code=500, detail=str(e))

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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "df-infoui-backend"}

async def process_job(job_id: str):
    """Process a job through all stages"""
    job = jobs[job_id]
    
    try:
        # Stage 1: Brain Agent - Analyze & Detect
        job.status = JobStatus.PLANNING
        job.message = "Brain Agent analyzing files and detecting accessibility issues..."
        job.progress = 20
        
        issues = await brain_agent.analyze_files(job_id)
        job.summary = {"total_issues": len(issues)}
        
        # Stage 2: Brain Agent - Coordinate Fixing Process
        job.status = JobStatus.FIXING
        job.message = "Brain Agent coordinating POUR agents to fix issues..."
        job.progress = 40
        
        # Brain Agent coordinates the entire fixing process
        coordination_results = await brain_agent.coordinate_fixing_process(job_id, issues)
        
        # Stage 3: Complete
        job.status = JobStatus.COMPLETE
        job.message = "Processing complete! All fixes applied and validated."
        job.progress = 100
        job.summary.update({
            "total_issues": coordination_results["total_issues"],
            "total_fixes": coordination_results["total_fixes"],
            "agent_reports": coordination_results["agent_reports"],
            "validation_passed": coordination_results["validation_results"].get("passed", False),
            "remaining_issues": coordination_results["validation_results"].get("remaining_issues", 0)
        })
        
    except Exception as e:
        job.status = JobStatus.ERROR
        job.message = f"Processing failed: {str(e)}"
        job.progress = 0

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
