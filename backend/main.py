"""
FastAPI Backend for CareerForge
API endpoints to run the CrewAI job application pipeline

Supports:
- Full pipeline: scrape + analyze + tailor resume + cover letter
- Direct resume analysis: paste/upload resume → analyze against job URL
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import sys
import io

# Add parent directory to path to import crew modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crew import run_pipeline
from dotenv import load_dotenv

load_dotenv()

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


class JobApplicationResponse(BaseModel):
    """Response body with all generated application materials."""
    status: str
    message: str
    job_details: Optional[dict] = None
    jd_analysis: Optional[dict] = None
    tailored_resume: Optional[str] = None
    cover_letter: Optional[str] = None


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
    return {"status": "healthy", "api": "CareerForge"}


@app.post("/api/apply", response_model=JobApplicationResponse)
async def apply_to_job(request: JobApplicationRequest):
    """
    Run the complete job application pipeline with pasted resume text.
    
    Flow: Scrape job → Analyze JD → Tailor resume → Write cover letter
    """
    try:
        _validate_inputs(request.job_url, request.resume_content)

        result = run_pipeline(request.job_url, request.resume_content)
        return _build_response(result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/apply-with-file", response_model=JobApplicationResponse)
async def apply_with_file(
    job_url: str = Form(...),
    resume_file: UploadFile = File(...)
):
    """
    Run the complete pipeline with an uploaded resume file (PDF/TXT).
    """
    try:
        resume_content = await extract_resume_text(resume_file)
        _validate_inputs(job_url, resume_content)

        result = run_pipeline(job_url, resume_content)
        return _build_response(result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        cover_letter=tasks[3].raw if len(tasks) > 3 else ""
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)