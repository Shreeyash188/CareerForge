"""
main.py - Entry point for the Job Application Assistant

Supports two modes:
    python main.py              # CLI mode (interactive)
    uvicorn main:app --reload   # API mode (FastAPI)

The program will:
1. Take a job URL and resume as input
2. Run the crew with all 4 agents sequentially
3. Output results from each agent
"""

import os
import datetime
from dotenv import load_dotenv
from crew import run_pipeline
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Load environment variables at module level (needed for both CLI and API)
load_dotenv()


# ============================================================
# FASTAPI APP
# ============================================================
app = FastAPI(
    title="CareerForge API",
    description="AI-powered job application pipeline built with CrewAI + Gemini",
    version="1.0.0"
)


class JobApplicationRequest(BaseModel):
    """Request body for the job application endpoint."""
    job_url: str
    resume_content: str
    github_projects: str = ""


class JobApplicationResponse(BaseModel):
    """Response body with all generated application materials."""
    status: str
    message: str
    job_details: dict
    jd_analysis: dict
    tailored_resume: str
    cover_letter: str
    networking_outreach: str
    skill_gap_plan: str
    salary_negotiation: str
    company_intel: str
    portfolio_matcher: str


@app.get("/")
def root():
    return {"message": "CareerForge API is running", "docs": "/docs"}


@app.post("/apply", response_model=JobApplicationResponse)
def apply_for_job(request: JobApplicationRequest):
    """
    Run the full CrewAI pipeline and return all generated materials.
    """
    try:
        result = run_pipeline(request.job_url, request.resume_content, request.github_projects)

        tasks = result.tasks_output  # CrewAI puts real output here

        return JobApplicationResponse(
            status="success",
            message="Job application materials generated successfully",
            job_details={"raw": tasks[0].raw if len(tasks) > 0 else ""},
            jd_analysis={"raw": tasks[1].raw if len(tasks) > 1 else ""},
            tailored_resume=tasks[2].raw if len(tasks) > 2 else "",
            cover_letter=tasks[3].raw if len(tasks) > 3 else "",
            networking_outreach=tasks[5].raw if len(tasks) > 5 else "",
            skill_gap_plan=tasks[6].raw if len(tasks) > 6 else "",
            salary_negotiation=tasks[7].raw if len(tasks) > 7 else "",
            company_intel=tasks[8].raw if len(tasks) > 8 else "",
            portfolio_matcher=tasks[9].raw if len(tasks) > 9 else ""
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# UTILITIES
# ============================================================
def save_output(content, filename):
    """Save content to a file in the outputs folder."""
    os.makedirs("outputs", exist_ok=True)
    filepath = os.path.join("outputs", filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(str(content))
    print(f"\nOutput saved to: {filepath}")
    return filepath


def sample_resume():
    """Return a sample resume for testing."""
    return """
JOHN DOE
Email: john.doe@email.com | Phone: (555) 123-4567 | LinkedIn: linkedin.com/in/johndoe

SUMMARY
Experienced software developer with 5 years of experience in building web applications.
Proficient in Python, JavaScript, and cloud technologies. Passionate about clean code
and user experience.

WORK EXPERIENCE
Senior Software Developer | Tech Corp | 2020 - Present
- Led development of customer-facing web application serving 100K+ users
- Implemented REST APIs using Python and Flask
- Mentored junior developers and conducted code reviews
- Reduced application load time by 40% through optimization

Software Developer | StartupXYZ | 2018 - 2020
- Built responsive web applications using React and Node.js
- Collaborated with cross-functional teams to deliver features on time
- Implemented automated testing, improving code quality

EDUCATION
Bachelor of Science in Computer Science | University of Technology | 2014 - 2018

SKILLS
Programming: Python, JavaScript, Java, SQL
Frameworks: React, Flask, Django, Node.js
Tools: Git, Docker, AWS, Jenkins
Soft Skills: Communication, Problem-solving, Teamwork
"""


# ============================================================
# CLI MODE
# ============================================================
def main():
    """Main function to run the job application pipeline in CLI mode."""

    # Check if API keys are set
    google_api_key = os.getenv("GOOGLE_API_KEY")
    serper_api_key = os.getenv("SERPER_API_KEY")

    if not google_api_key or google_api_key == "your_google_api_key_here":
        print("\n" + "="*60)
        print("ERROR: Please set your Google API key in the .env file")
        print("Get your key from: https://aistudio.google.com/app/apikey")
        print("="*60 + "\n")
        return

    if not serper_api_key or serper_api_key == "your_serper_api_key_here":
        print("\n" + "="*60)
        print("WARNING: Serper API key not set. Some features may not work.")
        print("Get your key from: https://serper.dev/api-key")
        print("="*60 + "\n")

    # ============================================================
    # INPUT: Define job URL and resume
    # ============================================================
    job_url = input("Enter the job posting URL: ") or "https://jobs.lever.co/example/123"
    resume_content = sample_resume()
    github_projects = input("Enter your GitHub projects or portfolio links (optional): ") or ""

    print("\n" + "="*60)
    print("STARTING JOB APPLICATION PIPELINE")
    print("="*60)
    print(f"\nJob URL: {job_url}")
    print(f"Resume length: {len(resume_content)} characters")
    if github_projects:
        print(f"Projects included: Yes")
    print("\nRunning crew with 9 agents and 10 tasks...")
    print("-"*60)

    # ============================================================
    # RUN: Execute the crew pipeline
    # ============================================================
    try:
        result = run_pipeline(job_url, resume_content, github_projects)

        print("\n" + "="*60)
        print("PIPELINE COMPLETE!")
        print("="*60)

        # Extract individual task outputs
        tasks = result.tasks_output
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        if len(tasks) > 2:
            save_output(tasks[2].raw, f"resume_{timestamp}.md")
        if len(tasks) > 3:
            save_output(tasks[3].raw, f"cover_letter_{timestamp}.md")

        # Also save full output
        save_output(result, "job_application_output.txt")

        # Show summary
        print("\n--- RESULTS SUMMARY ---")
        for i, task in enumerate(tasks):
            print(f"\nTask {i+1}: {task.raw[:200]}...")

    except Exception as e:
        print(f"\nError occurred: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check your .env file has valid API keys")
        print("2. Make sure the job URL is accessible")
        print("3. Try again - sometimes API calls fail temporarily")


if __name__ == "__main__":
    main()