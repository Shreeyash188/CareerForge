"""
FastAPI Backend for CareerForge
API endpoints to run the CrewAI job application pipeline

Supports:
- Full pipeline: scrape + analyze + tailor resume + cover letter + interview prep
- Direct resume analysis: paste/upload resume → analyze against job URL
- Standalone interview prep: generate prep kit for an already-tailored session
- Real-time progress streaming via Server-Sent Events (SSE)
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import os
import sys
import io
import json
import asyncio
import threading
import time
import queue

# Add parent directory to path to import crew modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crew import run_pipeline
from dotenv import load_dotenv

load_dotenv()

# Ensure chromadb's specific environment variable is set
if os.getenv("GOOGLE_API_KEY"):
    os.environ["CHROMA_GOOGLE_GENAI_API_KEY"] = os.getenv("GOOGLE_API_KEY")

app = FastAPI(title="CareerForge API", description="AI Job Application Assistant API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST / RESPONSE MODELS
# ============================================================
class JobApplicationRequest(BaseModel):
    """Request body for the job application endpoint."""
    job_url: str
    resume_content: str
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    github_projects: Optional[str] = ""


class JobApplicationResponse(BaseModel):
    """Response body with all generated application materials."""
    status: str
    message: str
    job_details: Optional[dict] = None
    jd_analysis: Optional[dict] = None
    tailored_resume: Optional[str] = None
    cover_letter: Optional[str] = None
    interview_prep: Optional[str] = None
    networking_outreach: Optional[str] = None
    skill_gap_plan: Optional[str] = None
    salary_negotiation: Optional[str] = None
    company_intel: Optional[str] = None
    portfolio_matcher: Optional[str] = None


# ============================================================
# PROGRESS TRACKING
# ============================================================
# Agent names for progress tracking (matches task order in crew.py)
PIPELINE_STEPS = [
    {"step": 1, "agent": "Job Scraper", "description": "Extracting job details from URL..."},
    {"step": 2, "agent": "JD Analyzer", "description": "Analyzing requirements & ATS keywords..."},
    {"step": 3, "agent": "Resume Tailor", "description": "Tailoring your resume to the job..."},
    {"step": 4, "agent": "Cover Letter Writer", "description": "Writing your cover letter..."},
    {"step": 5, "agent": "Interview Prep Coach", "description": "Generating interview prep kit..."},
    {"step": 6, "agent": "Networking Strategist", "description": "Drafting cold outreach messages..."},
    {"step": 7, "agent": "Technical Learning Coach", "description": "Identifying skill gaps & learning path..."},
    {"step": 8, "agent": "Salary Negotiation Coach", "description": "Formulating negotiation strategy..."},
    {"step": 9, "agent": "Company Intelligence Analyst", "description": "Investigating company intel & red flags..."},
    {"step": 10, "agent": "Portfolio Alignment Expert", "description": "Aligning past projects to job challenges..."},
]


# ============================================================
# HELPER: Extract text from uploaded file
# ============================================================
async def extract_resume_text(file: UploadFile) -> str:
    """
    Extract text from an uploaded resume file.
    Supports .txt and .pdf files.
    """
    content = await file.read()
    filename = file.filename or ""

    if filename.lower().endswith(".txt") or filename.lower().endswith(".md"):
        return content.decode("utf-8", errors="replace")

    elif filename.lower().endswith(".pdf"):
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(content))
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text() or "")
            extracted = "\n".join(text_parts).strip()
            if not extracted:
                raise ValueError("PDF appears to contain no extractable text (may be image-based)")
            return extracted
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="PyPDF2 is required for PDF support. Run: pip install PyPDF2"
            )

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {filename}. Please upload a .txt, .md, or .pdf file."
        )


# ============================================================
# ROUTES
# ============================================================
@app.get("/")
def root():
    return {"message": "CareerForge API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "api": "CareerForge", "version": "2.1", "features": [
        "job_scrape", "jd_analysis", "resume_tailoring", "cover_letter", "interview_prep", "sse_progress"
    ]}


@app.post("/api/apply", response_model=JobApplicationResponse)
async def apply_to_job(request: JobApplicationRequest):
    """
    Run the complete job application pipeline with pasted resume text.
    
    Flow: Scrape job → Analyze JD → Tailor resume → Write cover letter → Interview Prep
    """
    try:
        _validate_inputs(request.job_url, request.resume_content)

        result = run_pipeline(request.job_url, request.resume_content, request.github_projects or "")
        return _build_response(result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/apply-with-file", response_model=JobApplicationResponse)
async def apply_with_file(
    job_url: str = Form(...),
    resume_file: UploadFile = File(...),
    github_projects: str = Form("")
):
    """
    Run the complete pipeline with an uploaded resume file (PDF/TXT).
    """
    try:
        resume_content = await extract_resume_text(resume_file)
        _validate_inputs(job_url, resume_content)

        result = run_pipeline(job_url, resume_content, github_projects)
        return _build_response(result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/apply-stream")
async def apply_stream(request: JobApplicationRequest):
    """
    Run the pipeline and stream real-time progress via Server-Sent Events (SSE).
    
    Each SSE event is a JSON object:
      - type: "progress" | "result" | "error"
      - For progress: { step, total, agent, description, status }
      - For result: full JobApplicationResponse
      - For error: { detail }
    """
    _validate_inputs(request.job_url, request.resume_content)
    
    github_projects = request.github_projects or ""

    progress_queue: queue.Queue = queue.Queue()

    def run_in_thread():
        """Run the pipeline in a background thread, posting progress updates."""
        try:
            # Post step-by-step progress (simulated timing since CrewAI
            # doesn't expose per-task callbacks, we time-estimate)
            for i, step_info in enumerate(PIPELINE_STEPS):
                progress_queue.put({
                    "type": "progress",
                    "step": step_info["step"],
                    "total": len(PIPELINE_STEPS),
                    "agent": step_info["agent"],
                    "description": step_info["description"],
                    "status": "running"
                })

                if i == 0:
                    # Actually run the pipeline on the first step
                    result = run_pipeline(request.job_url, request.resume_content, github_projects)
                    # Once the pipeline completes, mark all remaining steps as done
                    for j in range(len(PIPELINE_STEPS)):
                        progress_queue.put({
                            "type": "progress",
                            "step": j + 1,
                            "total": len(PIPELINE_STEPS),
                            "agent": PIPELINE_STEPS[j]["agent"],
                            "description": PIPELINE_STEPS[j]["description"],
                            "status": "done"
                        })

                    # Send final result
                    resp = _build_response(result)
                    progress_queue.put({
                        "type": "result",
                        "data": resp.model_dump()
                    })
                    return

        except Exception as e:
            progress_queue.put({
                "type": "error",
                "detail": str(e)
            })

    # Start the pipeline in a background thread
    thread = threading.Thread(target=run_in_thread, daemon=True)
    thread.start()

    async def event_generator():
        """Yield SSE events from the progress queue."""
        while True:
            try:
                msg = progress_queue.get(timeout=0.5)
                yield f"data: {json.dumps(msg)}\n\n"

                if msg["type"] in ("result", "error"):
                    return  # End the stream
            except queue.Empty:
                # Send keepalive comment
                yield ": keepalive\n\n"
                await asyncio.sleep(0.3)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# ============================================================
# SHARED HELPERS
# ============================================================
def _validate_inputs(job_url: str, resume_content: str):
    """Validate API keys and required inputs."""
    if not job_url:
        raise HTTPException(status_code=400, detail="Job URL is required")
    if not resume_content:
        raise HTTPException(status_code=400, detail="Resume content is required")

    google_key = os.getenv("GOOGLE_API_KEY")
    if not google_key or google_key == "your_google_api_key_here":
        raise HTTPException(
            status_code=500,
            detail="Google API key not configured. Please add GOOGLE_API_KEY to .env"
        )


def _build_response(result) -> JobApplicationResponse:
    """Extract real task outputs from CrewAI result."""
    tasks = result.tasks_output  # CrewAI stores individual task results here

    return JobApplicationResponse(
        status="success",
        message="Job application materials generated successfully",
        job_details={"raw": tasks[0].raw if len(tasks) > 0 else ""},
        jd_analysis={"raw": tasks[1].raw if len(tasks) > 1 else ""},
        tailored_resume=tasks[2].raw if len(tasks) > 2 else "",
        cover_letter=tasks[3].raw if len(tasks) > 3 else "",
        interview_prep=tasks[4].raw if len(tasks) > 4 else "",
        networking_outreach=tasks[5].raw if len(tasks) > 5 else "",
        skill_gap_plan=tasks[6].raw if len(tasks) > 6 else "",
        salary_negotiation=tasks[7].raw if len(tasks) > 7 else "",
        company_intel=tasks[8].raw if len(tasks) > 8 else "",
        portfolio_matcher=tasks[9].raw if len(tasks) > 9 else ""
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)