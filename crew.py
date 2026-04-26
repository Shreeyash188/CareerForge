"""
crew.py - Connects Agents and Tasks into a working CrewAI pipeline

This file:
1. Creates the Crew with all agents and tasks
2. Defines the workflow (sequential = step by step)
3. Enables memory so agents can share context
4. Shows how data flows between agents
5. Logs every application to a CSV tracker
6. Saves interview prep kit to outputs/ for offline review
"""

import os
import csv
import datetime
from crewai import Crew, Process
from agents import (
    job_scraper_agent,
    jd_analyzer_agent,
    resume_tailor_agent,
    cover_letter_writer_agent,
    interview_prep_agent,
    networker_agent,
    learning_coach_agent,
    negotiator_agent,
    intel_agent,
    portfolio_matcher_agent
)
from tasks import (
    scrape_job_task,
    analyze_jd_task,
    tailor_resume_task,
    write_cover_letter_task,
    interview_prep_task,
    network_outreach_task,
    skill_gap_task,
    salary_negotiation_task,
    company_intel_task,
    portfolio_matcher_task
)


def create_job_crew():
    """
    Create and configure the CrewAI crew for job application assistance.
    
    The crew works SEQUENTIALLY:
    1. Job Scraper extracts details from URL
    2. JD Analyzer analyzes requirements
    3. Resume Tailor adapts the resume
    4. Cover Letter Writer creates the letter
    
    Each task's output becomes input for the next task.
    """
    
    # Create the crew with all agents and tasks
    job_crew = Crew(
        agents=[
            job_scraper_agent,
            jd_analyzer_agent,
            resume_tailor_agent,
            cover_letter_writer_agent,
            interview_prep_agent,
            networker_agent,
            learning_coach_agent,
            negotiator_agent,
            intel_agent,
            portfolio_matcher_agent
        ],
        
        tasks=[
            scrape_job_task,
            analyze_jd_task,
            tailor_resume_task,
            write_cover_letter_task,
            interview_prep_task,
            network_outreach_task,
            skill_gap_task,
            salary_negotiation_task,
            company_intel_task,
            portfolio_matcher_task
        ],
        
        # Process.sequential means tasks run one after another
        # Each task waits for the previous one to complete
        process=Process.sequential,
        
        # Enable memory so agents can remember context
        # This allows agents to reference earlier work
        memory=True,
        
        # Verbose shows detailed progress
        verbose=True,
        
        # Set a reasonable timeout (in minutes)
        max_iterations=15,
        
        # Enable full-text search memory for better context recall
        embedder={
            "provider": "google-generativeai"
        }
    )
    
    return job_crew


def run_pipeline(job_url, resume_content, github_projects=""):
    """
    Run the complete job application pipeline.
    
    Args:
        job_url: URL of the job posting
        resume_content: The candidate's resume as text
        github_projects: Candidate's project list or GitHub details
        
    Returns:
        CrewOutput with results from all 5 tasks
    """
    
    # Create the crew
    crew = create_job_crew()
    
    # Kick off the workflow - this runs all tasks in sequence
    # The inputs are available to all tasks
    result = crew.kickoff(
        inputs={
            "job_url": job_url,
            "resume_content": resume_content,
            "github_projects": github_projects
        }
    )
    
    # Save the interview prep kit to a timestamped file for offline review
    _save_interview_prep(result)
    
    # Save the other new extra outputs
    _save_extra_outputs(result)
    
    # Log the application to CSV tracker
    log_application(job_url, "extracted_by_agent", "extracted_by_agent", 0)
    
    return result


def _save_interview_prep(result):
    """
    Save the interview preparation kit (task 5 output) to a markdown file
    in the outputs/ directory so the user can review it anytime offline.
    """
    try:
        tasks = result.tasks_output
        if len(tasks) < 5:
            return  # Guard: pipeline didn't run all 5 tasks

        prep_content = tasks[4].raw  # Index 4 = interview_prep_task output
        if not prep_content:
            return

        os.makedirs("outputs", exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"outputs/interview_prep_{timestamp}.md"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("# CareerForge — Interview Preparation Kit\n")
            f.write(f"_Generated: {datetime.datetime.now().strftime('%B %d, %Y at %H:%M')}_\n\n")
            f.write("---\n\n")
            f.write(prep_content)

        print(f"[CareerForge] ✅ Interview prep kit saved to: {filepath}")
    except Exception as exc:
        # Non-fatal: log but don't crash the pipeline
        print(f"[CareerForge] ⚠️ Could not save interview prep kit: {exc}")


def _save_extra_outputs(result):
    """
    Save the outputs from the 5 new tasks (networking, skills gap, etc.) to markdown files.
    """
    try:
        tasks = result.tasks_output
        if len(tasks) < 10:
            return  # Pipeline didn't run all 10 tasks

        os.makedirs("outputs", exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Mapping index to task name for saving files
        extra_tasks_map = {
            5: "networking",
            6: "skill_gap",
            7: "salary_negotiation",
            8: "company_intel",
            9: "portfolio_matcher"
        }
        
        for idx, prefix in extra_tasks_map.items():
            content = tasks[idx].raw
            if content:
                filepath = f"outputs/{prefix}_{timestamp}.md"
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"# CareerForge — {prefix.replace('_', ' ').title()}\n")
                    f.write(f"_Generated: {datetime.datetime.now().strftime('%B %d, %Y at %H:%M')}_\n\n")
                    f.write("---\n\n")
                    f.write(content)
                print(f"[CareerForge] ✅ {prefix.replace('_', ' ').title()} saved to: {filepath}")

    except Exception as exc:
        print(f"[CareerForge] ⚠️ Could not save extra outputs: {exc}")


def log_application(job_url, company, role, match_score):
    """
    Log a job application to a CSV file for tracking.
    
    Args:
        job_url: URL of the job posting
        company: Company name
        role: Job role/title
        match_score: Match score 0-100
    """
    os.makedirs("outputs", exist_ok=True)
    filepath = "outputs/applications_log.csv"
    
    # Write header only if file doesn't exist
    write_header = not os.path.exists(filepath)
    
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["timestamp", "job_url", "company", "role", "match_score", "status"])
        writer.writerow([
            datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
            job_url, company, role, match_score, "applied"
        ])


def get_crew_output():
    """
    Get the detailed output from the crew after execution.
    This includes each task's result and the final output.
    """
    crew = create_job_crew()
    return crew