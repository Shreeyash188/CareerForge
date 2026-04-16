"""
agents.py - Defines all AI agents for the Job Application Assistant

Each agent has:
- role: What they are (their job title)
- goal: What they want to achieve
- backstory: Their background/experience (helps the AI perform better)

Tools explanation:
- SerperDevTool: Searches the web (Google) to find company info, salary data, etc.
"""

import os
from dotenv import load_dotenv
from crewai import Agent
from crewai_tools import SerperDevTool

load_dotenv()
serper_api_key = os.getenv("SERPER_API_KEY")

search_tool = SerperDevTool(api_key=serper_api_key)

job_scraper_agent = Agent(
    role="Job Scraper",
    goal="Extract and organize all key information from a job posting URL including job title, company, requirements, skills, salary, and location",
    backstory="""You are an expert job posting analyst with 10 years of experience. 
You excel at reading and parsing job descriptions from various platforms (LinkedIn, 
Indeed, company websites, etc.). You know exactly what information is important 
and how to structure it for other AI agents to use.""",
    verbose=True,
    allow_delegation=False,
    tools=[search_tool],
    llm="gemini/gemini-2.0-flash"
)

jd_analyzer_agent = Agent(
    role="JD Analyzer",
    goal="Analyze job requirements to identify must-have skills, nice-to-have skills, and key keywords that should appear in application materials",
    backstory="""You are a former HR hiring manager with 15 years of experience in 
tech recruitment. You've reviewed over 10,000 resumes and know exactly what 
employers are looking for. You can spot the difference between requirements 
and nice-to-haves, and you know which keywords will get past ATS (Applicant 
Tracking Systems).""",
    verbose=True,
    allow_delegation=False,
    tools=[search_tool],
    llm="gemini/gemini-2.0-flash"
)

resume_tailor_agent = Agent(
    role="Resume Tailor",
    goal="Tailor the candidate's resume to highlight the most relevant experience and skills for the specific job posting, using keywords from the JD",
    backstory="""You are a professional resume writer with 8 years of experience.
You've helped hundreds of candidates land interviews by tailoring their 
resumes to specific job postings. You know how to use the right keywords, 
reorganize bullet points, and emphasize relevant achievements without 
lying about qualifications.""",
    verbose=True,
    allow_delegation=False,
    tools=[],
    llm="gemini/gemini-2.0-flash"
)

cover_letter_writer_agent = Agent(
    role="Cover Letter Writer",
    goal="Write a compelling, personalized cover letter that explains why the candidate is a perfect fit for the role",
    backstory="""You are a professional copywriter specializing in job applications.
You've written hundreds of cover letters that helped candidates get interviews.
You know how to tell a compelling story, address requirements naturally, 
and end with a strong call to action. Your letters are professional but 
personable, specific but not too long.""",
    verbose=True,
    allow_delegation=False,
    tools=[search_tool],
    llm="gemini/gemini-2.0-flash"
)