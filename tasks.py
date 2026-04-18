"""
tasks.py - Defines tasks for each AI agent

Each task tells an agent:
- What to do (description)
- How to do it (instructions)
- What output to produce (expected_output)

Pipeline flow:
  Job URL -> Scraper -> JD Analyzer -> Resume Tailor -> Cover Letter Writer -> Interview Prep Coach

Key: Tasks use context=[] to pass output from prior tasks instead of
template variables like {job_details}. CrewAI injects the raw output
of all context tasks into the agent's prompt automatically.
"""

from crewai import Task
from agents import (
    job_scraper_agent,
    jd_analyzer_agent,
    resume_tailor_agent,
    cover_letter_writer_agent,
    interview_prep_agent
)


# ============================================================
# TASK 1: SCRAPE JOB DETAILS
# ============================================================
"""
This task extracts all key information from the job posting URL.
Input: job_url (provided via kickoff inputs)
Output: Structured job details (title, company, requirements, etc.)
"""
scrape_job_task = Task(
    description="""
    Extract all key information from the following job posting URL:
    {job_url}
    
    Please extract and organize:
    1. Job Title
    2. Company Name
    3. Location (remote/hybrid/onsite)
    4. Job Type (full-time/part-time/contract)
    5. Salary Range (if mentioned)
    6. Required Skills (technical and soft)
    7. Required Experience
    8. Education Requirements
    9. Key Responsibilities
    10. Company Culture (if mentioned)
    11. Application Deadline (if mentioned)
    
    Format the output as a structured summary that other agents can easily use.
    """,
    expected_output="A structured summary with all job details including title, company, location, skills, requirements, and responsibilities",
    agent=job_scraper_agent
)


# ============================================================
# TASK 2: ANALYZE JOB DESCRIPTION
# ============================================================
"""
This task analyzes the job requirements to identify what's truly important.
Input: Job details from Task 1 (via context)
Output: Priority list of skills, keywords, and match score
"""
analyze_jd_task = Task(
    description="""Analyze the job description from the scraping task and produce:
    1. Top 10 ATS keywords
    2. Must-have vs nice-to-have skills
    3. Culture tone (startup/corporate)
    4. Match score 0-100 with reasoning

    Please also identify:
    5. EXPERIENCE LEVEL required (entry/mid/senior)
    6. SOFT SKILLS that are important
    7. What the hiring manager really cares about (hidden requirements)
    
    Provide a prioritized list that will help tailor the application materials.
    """,
    expected_output="Structured analysis with keywords and match score",
    context=[scrape_job_task],
    agent=jd_analyzer_agent
)


# ============================================================
# TASK 3: TAILOR RESUME
# ============================================================
"""
This task modifies the resume to match the job requirements.
Input: Job details from Task 1 + JD analysis from Task 2 + resume_content (via kickoff inputs)
Output: Tailored resume content
"""
tailor_resume_task = Task(
    description="""Using the JD analysis and original resume: {resume_content}
    Rewrite bullet points with ATS keywords. Reorder projects by relevance.

    Please:
    1. Reorder bullet points to prioritize relevant experience
    2. Add keywords from the JD analysis that are missing
    3. Emphasize achievements that match job requirements
    4. Remove or de-emphasize irrelevant information
    5. Use similar terminology as the job posting
    6. Keep all factual information accurate (don't lie)
    
    Provide the tailored resume in markdown format that's ready to use.
    """,
    expected_output="Tailored resume in markdown",
    context=[scrape_job_task, analyze_jd_task],
    agent=resume_tailor_agent
)


# ============================================================
# TASK 4: WRITE COVER LETTER
# ============================================================
"""
This task writes a personalized cover letter.
Input: All prior task outputs (via context)
Output: Custom cover letter
"""
write_cover_letter_task = Task(
    description="""Write a 200-250 word 3-paragraph cover letter matching the company tone.

    Please write a cover letter that:
    1. Has a strong opening that grabs attention
    2. Explains why the candidate is a good fit (specific examples)
    3. Addresses key requirements naturally
    4. Shows enthusiasm for the role and company
    5. Has a clear call to action
    6. Is professional but personable (not generic)
    7. Is 3 paragraphs, 200-250 words
    8. Uses the candidate's voice/tone
    
    Output a complete, ready-to-send cover letter in markdown format.
    """,
    expected_output="Personalized cover letter in markdown",
    context=[scrape_job_task, analyze_jd_task, tailor_resume_task],
    agent=cover_letter_writer_agent
)


# ============================================================
# TASK 5: INTERVIEW PREPARATION KIT
# ============================================================
"""
This task generates a full interview preparation kit using every prior
output: job details, JD analysis, tailored resume, and cover letter.
It produces role-specific predicted questions + STAR model answers.
"""
interview_prep_task = Task(
    description="""
    Using the complete context (job details, JD analysis, tailored resume, and cover letter),
    generate a comprehensive, highly personalized interview preparation kit.

    SECTION 1 – PREDICTED INTERVIEW QUESTIONS (10 total, clearly numbered):
    - 3 Behavioral questions ("Tell me about a time when...")
      These MUST reference the specific role's requirements from the JD.
    - 3 Technical / Role-Specific questions
      These must target the top must-have skills identified in the JD analysis.
    - 2 Situational questions ("What would you do if...")
      Based on the challenges and responsibilities of the role.
    - 1 Culture-Fit question matched to the company's culture tone.
    - 1 "Why us?" question about the company/role.

    SECTION 2 – MODEL ANSWERS (one per question):
    For EACH of the 10 questions, write a complete model answer using the
    STAR method (Situation → Task → Action → Result): 
    - Situation: Set a realistic scene from the candidate's actual resume experience.
    - Task: What the candidate was responsible for.
    - Action: The specific steps the candidate took (use keywords from the JD).
    - Result: A concrete, quantified outcome where possible.
    The answer should feel like the candidate's own voice, not a generic template.
    Each answer should be 120–180 words.

    SECTION 3 – COMPANY RESEARCH TALKING POINTS:
    - Research the company (mission, recent news, products, culture) using search.
    - Provide 3-4 bullet points of compelling facts the candidate can weave into answers
      to show they've done their homework.
    - Include 1 smart question the candidate should ask the interviewer at the end.

    SECTION 4 – RAPID FIRE TIPS:
    - 5 quick, role-specific preparation tips (e.g., topics to brush up on,
      soft skills to demonstrate, common mistakes to avoid for this exact role).

    Format the entire output in clean markdown with clear section headers.
    """,
    expected_output="""A markdown-formatted interview preparation kit with:
    - 10 predicted questions (behavioral, technical, situational, culture-fit, why-us)
    - 10 STAR-method model answers personalized to the candidate's resume
    - Company research talking points and a smart closing question
    - 5 rapid-fire role-specific preparation tips""",
    context=[
        scrape_job_task,
        analyze_jd_task,
        tailor_resume_task,
        write_cover_letter_task
    ],
    agent=interview_prep_agent
)