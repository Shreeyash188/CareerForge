"use client";

import { useState, useRef, useCallback } from "react";

interface JobResult {
  status: string;
  message: string;
  job_details?: { raw: string };
  jd_analysis?: { raw: string };
  tailored_resume?: string;
  cover_letter?: string;
  interview_prep?: string;
}

interface ProgressStep {
  step: number;
  total: number;
  agent: string;
  description: string;
  status: "pending" | "running" | "done";
}

type ResumeInputMode = "paste" | "upload";
type ResultTab = "analysis" | "resume" | "cover" | "interview";

export default function Home() {
  const [jobUrl, setJobUrl] = useState("");
  const [resumeContent, setResumeContent] = useState("");
  const [resumeMode, setResumeMode] = useState<ResumeInputMode>("paste");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<JobResult | null>(null);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState<ResultTab>("analysis");
  const [progressSteps, setProgressSteps] = useState<ProgressStep[]>([
    { step: 1, total: 5, agent: "Job Scraper", description: "Extracting job details...", status: "pending" },
    { step: 2, total: 5, agent: "JD Analyzer", description: "Analyzing requirements...", status: "pending" },
    { step: 3, total: 5, agent: "Resume Tailor", description: "Tailoring your resume...", status: "pending" },
    { step: 4, total: 5, agent: "Cover Letter Writer", description: "Writing cover letter...", status: "pending" },
    { step: 5, total: 5, agent: "Interview Prep Coach", description: "Generating interview kit...", status: "pending" },
  ]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── Download helper ────────────────────────────────────────
  const downloadFile = (content: string, filename: string) => {
    const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const downloadAll = () => {
    if (!result) return;
    if (result.job_details?.raw) downloadFile(result.job_details.raw, "job_details.md");
    if (result.jd_analysis?.raw) downloadFile(result.jd_analysis.raw, "jd_analysis.md");
    if (result.tailored_resume) downloadFile(result.tailored_resume, "tailored_resume.md");
    if (result.cover_letter) downloadFile(result.cover_letter, "cover_letter.md");
    if (result.interview_prep) downloadFile(result.interview_prep, "interview_prep.md");
  };

  // ── File handling ──────────────────────────────────────────
  const handleFileSelect = (file: File) => {
    const allowed = [".pdf", ".txt", ".md"];
    const ext = file.name.toLowerCase().slice(file.name.lastIndexOf("."));
    if (!allowed.includes(ext)) {
      setError("Please upload a .pdf, .txt, or .md file");
      return;
    }
    setUploadedFile(file);
    setError("");

    // If it's a text file, also read it into the textarea for preview
    if (ext === ".txt" || ext === ".md") {
      const reader = new FileReader();
      reader.onload = (e) => {
        setResumeContent(e.target?.result as string);
      };
      reader.readAsText(file);
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const removeFile = () => {
    setUploadedFile(null);
    setResumeContent("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  // ── Submit ─────────────────────────────────────────────────
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    setResult(null);

    try {
      let response: Response;

      if (resumeMode === "upload" && uploadedFile) {
        // Use multipart form upload
        const formData = new FormData();
        formData.append("job_url", jobUrl);
        formData.append("resume_file", uploadedFile);

        response = await fetch("http://localhost:8000/api/apply-with-file", {
          method: "POST",
          body: formData,
        });
      } else {
        // Use JSON body with pasted text
        response = await fetch("http://localhost:8000/api/apply", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            job_url: jobUrl,
            resume_content: resumeContent,
          }),
        });
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to submit application");
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  const resetForm = () => {
    setJobUrl("");
    setResumeContent("");
    setUploadedFile(null);
    setResult(null);
    setError("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const isSubmitDisabled =
    isLoading ||
    !jobUrl ||
    (resumeMode === "paste" && !resumeContent) ||
    (resumeMode === "upload" && !uploadedFile);

  // ── Helpers ────────────────────────────────────────────────
  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  };

  // ── Render ─────────────────────────────────────────────────
  return (
    <div className="min-h-screen py-12 px-4 font-sans relative overflow-hidden">
      <div className="max-w-4xl mx-auto relative z-10">
        {/* Header */}
        <div className="text-center mb-12 animate-fade-in">
          <div className="inline-flex items-center justify-center p-2 mb-4 rounded-2xl bg-white/5 border border-white/10 shadow-xl backdrop-blur-md">
            <svg className="w-8 h-8 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
          </div>
          <h1 className="text-5xl md:text-6xl font-bold font-outfit gradient-text mb-4 tracking-tight">
            CareerForge
          </h1>
          <p className="text-lg md:text-xl text-indigo-200/70 font-light">
            AI-Powered Job Application Assistant
          </p>
        </div>

        {!result ? (
          /* ─── INPUT FORM ─────────────────────────────────── */
          <form onSubmit={handleSubmit} className="glass rounded-2xl p-8">
            <div className="space-y-6">
              {/* Job URL */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Job Posting URL
                </label>
                <input
                  id="job-url-input"
                  type="url"
                  value={jobUrl}
                  onChange={(e) => setJobUrl(e.target.value)}
                  placeholder="https://jobs.lever.co/company/123"
                  required
                  className="w-full px-4 py-3 rounded-lg input-field"
                />
              </div>

              {/* ── Resume Input Section ────────────────────── */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <label className="block text-sm font-medium text-gray-300">
                    Your Resume
                  </label>

                  {/* Mode Toggle */}
                  <div className="mode-toggle">
                    <button
                      type="button"
                      className={`mode-toggle-btn ${
                        resumeMode === "paste" ? "active" : ""
                      }`}
                      onClick={() => setResumeMode("paste")}
                    >
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                      </svg>
                      Paste Text
                    </button>
                    <button
                      type="button"
                      className={`mode-toggle-btn ${
                        resumeMode === "upload" ? "active" : ""
                      }`}
                      onClick={() => setResumeMode("upload")}
                    >
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                        />
                      </svg>
                      Upload File
                    </button>
                  </div>
                </div>

                {/* Paste Mode */}
                {resumeMode === "paste" && (
                  <div className="animate-fade-in">
                    <textarea
                      id="resume-textarea"
                      value={resumeContent}
                      onChange={(e) => setResumeContent(e.target.value)}
                      placeholder={`Paste your resume content here...\n\nExample:\nJOHN DOE\nSoftware Developer | john@email.com\n\nEXPERIENCE\nSenior Developer at TechCorp (2020–Present)\n- Led development of customer-facing web app...\n\nSKILLS\nPython, JavaScript, React, Node.js, AWS...`}
                      required={resumeMode === "paste"}
                      rows={12}
                      className="w-full px-4 py-3 rounded-lg input-field resize-none font-mono text-sm"
                    />
                    <div className="flex justify-between mt-2 text-xs text-gray-500">
                      <span>
                        {resumeContent.length > 0
                          ? `${resumeContent.length} characters`
                          : "Paste your full resume text"}
                      </span>
                      <span>Supports plain text & markdown</span>
                    </div>
                  </div>
                )}

                {/* Upload Mode */}
                {resumeMode === "upload" && (
                  <div className="animate-fade-in">
                    {!uploadedFile ? (
                      <div
                        className={`drop-zone ${isDragging ? "dragging" : ""}`}
                        onDrop={handleDrop}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onClick={() => fileInputRef.current?.click()}
                      >
                        <input
                          ref={fileInputRef}
                          type="file"
                          accept=".pdf,.txt,.md"
                          className="hidden"
                          onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (file) handleFileSelect(file);
                          }}
                        />
                        <div className="drop-zone-icon">
                          <svg
                            className="w-10 h-10"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={1.5}
                              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                            />
                          </svg>
                        </div>
                        <p className="text-gray-300 font-medium mb-1">
                          Drop your resume here or{" "}
                          <span className="text-indigo-400 underline">
                            browse files
                          </span>
                        </p>
                        <p className="text-xs text-gray-500">
                          Supports PDF, TXT, and Markdown files
                        </p>
                      </div>
                    ) : (
                      <div className="file-preview">
                        <div className="flex items-center gap-3">
                          <div className="file-icon">
                            {uploadedFile.name.endsWith(".pdf") ? (
                              <svg
                                className="w-6 h-6 text-red-400"
                                fill="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zM6 20V4h7v5h5v11H6z" />
                              </svg>
                            ) : (
                              <svg
                                className="w-6 h-6 text-blue-400"
                                fill="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zM6 20V4h7v5h5v11H6z" />
                              </svg>
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-white truncate">
                              {uploadedFile.name}
                            </p>
                            <p className="text-xs text-gray-500">
                              {formatFileSize(uploadedFile.size)}
                            </p>
                          </div>
                          <button
                            type="button"
                            onClick={removeFile}
                            className="p-1.5 rounded-lg hover:bg-white/10 transition-colors text-gray-400 hover:text-red-400"
                          >
                            <svg
                              className="w-5 h-5"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M6 18L18 6M6 6l12 12"
                              />
                            </svg>
                          </button>
                        </div>
                        <div className="mt-3 flex items-center gap-2 text-xs text-green-400">
                          <svg
                            className="w-4 h-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M5 13l4 4L19 7"
                            />
                          </svg>
                          Ready to analyze
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Submit Button */}
              <button
                id="submit-button"
                type="submit"
                disabled={isSubmitDisabled}
                className={`w-full py-4 rounded-lg btn-primary font-semibold text-lg ${
                  isLoading ? "loading" : ""
                }`}
              >
                {isLoading ? (
                  <span className="flex items-center justify-center gap-3">
                    <svg
                      className="animate-spin h-5 w-5"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="none"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                      />
                    </svg>
                    Analyzing & Generating Materials...
                  </span>
                ) : (
                  "🚀 Generate Application Materials"
                )}
              </button>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mt-6 p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300">
                <div className="flex items-center gap-2">
                  <svg
                    className="w-5 h-5 flex-shrink-0"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                      clipRule="evenodd"
                    />
                  </svg>
                  {error}
                </div>
              </div>
            )}
          </form>
        ) : (
          /* ─── RESULTS VIEW ───────────────────────────────── */
          <div className="space-y-8 animate-fade-in">
            {/* Success header */}
            <div className="glass rounded-2xl p-8 text-center relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500"></div>
              <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-green-500/10 border border-green-500/20 flex items-center justify-center shadow-[0_0_30px_rgba(34,197,94,0.2)]">
                <svg
                  className="w-10 h-10 text-green-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <h2 className="text-2xl font-bold font-outfit text-white mb-3">
                Application Materials Generated!
              </h2>
              <p className="text-indigo-200/70 mb-6">{result.message}</p>
              <button
                onClick={resetForm}
                className="px-6 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all font-medium text-sm text-white flex items-center gap-2 mx-auto"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
                Start Over
              </button>
            </div>

            {/* Tabs */}
            <div className="glass rounded-3xl p-6 md:p-8">
              <div className="tabs-container mb-8">
                <button
                  id="tab-analysis"
                  onClick={() => setActiveTab("analysis")}
                  className={`tab-button ${
                    activeTab === "analysis" ? "active" : ""
                  }`}
                >
                  <svg
                    className="w-4 h-4 inline mr-1.5 -mt-0.5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                    />
                  </svg>
                  JD Analysis
                </button>
                <button
                  id="tab-resume"
                  onClick={() => setActiveTab("resume")}
                  className={`tab-button ${
                    activeTab === "resume" ? "active" : ""
                  }`}
                >
                  <svg
                    className="w-4 h-4 inline mr-1.5 -mt-0.5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                  Tailored Resume
                </button>
                <button
                  id="tab-cover"
                  onClick={() => setActiveTab("cover")}
                  className={`tab-button ${
                    activeTab === "cover" ? "active" : ""
                  }`}
                >
                  <svg
                    className="w-4 h-4 inline mr-1.5 -mt-0.5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                    />
                  </svg>
                  Cover Letter
                </button>
              </div>

              {/* Tab Content */}
              <div className="scroll-content">
                {activeTab === "analysis" && (
                  <div className="space-y-4 animate-fade-in">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold text-white">
                        Job Description Analysis
                      </h3>
                      <span className="text-xs px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                        ATS Keywords &amp; Match Score
                      </span>
                    </div>
                    <div className="result-card rounded-lg p-4">
                      <h4 className="text-sm font-medium text-gray-400 mb-2">
                        Scraped Job Details
                      </h4>
                      <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono">
                        {result.job_details?.raw || "No job details available"}
                      </pre>
                    </div>
                    <div className="result-card rounded-lg p-4">
                      <h4 className="text-sm font-medium text-gray-400 mb-2">
                        Analysis &amp; Keywords
                      </h4>
                      <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono">
                        {result.jd_analysis?.raw || "No analysis available"}
                      </pre>
                    </div>
                  </div>
                )}

                {activeTab === "resume" && (
                  <div className="space-y-4 animate-fade-in">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold text-white">
                        Tailored Resume
                      </h3>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(
                            result.tailored_resume || ""
                          );
                        }}
                        className="text-xs px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 transition-colors text-gray-300"
                      >
                        📋 Copy
                      </button>
                    </div>
                    <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono result-card rounded-lg p-4">
                      {result.tailored_resume ||
                        "Resume will be generated..."}
                    </pre>
                  </div>
                )}

                {activeTab === "cover" && (
                  <div className="space-y-4 animate-fade-in">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold text-white">
                        Cover Letter
                      </h3>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(
                            result.cover_letter || ""
                          );
                        }}
                        className="text-xs px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 transition-colors text-gray-300"
                      >
                        📋 Copy
                      </button>
                    </div>
                    <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono result-card rounded-lg p-4">
                      {result.cover_letter ||
                        "Cover letter will be generated..."}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="text-center mt-12 mb-6 text-indigo-200/40 text-sm font-medium flex items-center justify-center gap-2">
          <span>Powered by</span>
          <span className="text-indigo-400/80">CrewAI</span>
          <span>&amp;</span>
          <span className="text-purple-400/80">Gemini</span>
        </div>
      </div>
    </div>
  );
}