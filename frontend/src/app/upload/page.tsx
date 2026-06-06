"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { ResumeData } from "@/types";

export default function UploadPage() {
  const router = useRouter();
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [parsedData, setParsedData] = useState<ResumeData | null>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const validateAndSetFile = (selectedFile: File) => {
    if (selectedFile.type !== "application/pdf" && !selectedFile.name.endsWith(".pdf")) {
      setError("Please select a PDF file.");
      setFile(null);
      return;
    }
    setError(null);
    setFile(selectedFile);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);

    try {
      const data = await api.uploadResume(file);
      setParsedData(data);
    } catch (err: any) {
      setError(err.message || "Something went wrong during parsing.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="container" style={{ maxWidth: "800px" }}>
      <div style={{ textAlign: "center", marginBottom: "40px" }}>
        <h1 style={{ fontSize: "36px", fontWeight: 700, marginBottom: "12px" }}>Upload Your Resume</h1>
        <p style={{ color: "var(--text-secondary)" }}>
          Upload your resume PDF. We will parse it and find matches based on your skills.
        </p>
      </div>

      {!parsedData ? (
        <div className="glass-panel" style={{ padding: "40px", textAlign: "center" }}>
          {/* Drag and Drop Zone */}
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            style={{
              border: `2px dashed ${dragActive ? "var(--primary)" : "rgba(255, 255, 255, 0.15)"}`,
              borderRadius: "var(--radius-md)",
              padding: "48px 24px",
              background: dragActive ? "rgba(108, 92, 231, 0.05)" : "rgba(255, 255, 255, 0.01)",
              cursor: "pointer",
              transition: "var(--transition)",
              position: "relative"
            }}
          >
            <input
              type="file"
              id="file-upload"
              accept=".pdf"
              style={{ display: "none" }}
              onChange={handleFileChange}
              disabled={uploading}
            />
            
            <label htmlFor="file-upload" style={{ cursor: "pointer", display: "block" }}>
              <div style={{ fontSize: "48px", marginBottom: "16px" }}>📂</div>
              {file ? (
                <div>
                  <p style={{ fontSize: "16px", fontWeight: 600, color: "var(--text-primary)" }}>{file.name}</p>
                  <p style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "4px" }}>
                    {(file.size / (1024 * 1024)).toFixed(2)} MB
                  </p>
                </div>
              ) : (
                <div>
                  <p style={{ fontSize: "16px", fontWeight: 600, color: "var(--text-primary)" }}>
                    Drag & drop your PDF resume, or <span style={{ color: "var(--primary)" }}>browse</span>
                  </p>
                  <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "8px" }}>
                    Supports PDF file format up to 10MB
                  </p>
                </div>
              )}
            </label>
          </div>

          {error && (
            <div style={{ color: "var(--danger)", background: "rgba(255, 71, 87, 0.1)", border: "1px solid rgba(255, 71, 87, 0.2)", padding: "12px", borderRadius: "var(--radius-sm)", marginTop: "20px", fontSize: "14px" }}>
              ⚠️ {error}
            </div>
          )}

          <div style={{ marginTop: "32px", display: "flex", justifyContent: "center" }}>
            <button
              onClick={handleUpload}
              disabled={!file || uploading}
              className="btn-primary"
              style={{ minWidth: "200px", justifyContent: "center" }}
            >
              {uploading ? (
                <>
                  <span className="shimmer" style={{ width: "20px", height: "20px", borderRadius: "50%", display: "inline-block" }}></span>
                  Parsing Resume...
                </>
              ) : (
                "Analyze Resume 🚀"
              )}
            </button>
          </div>
        </div>
      ) : (
        /* Extracted Profile Preview on Success */
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          <div className="glass-panel" style={{ padding: "32px", borderLeft: "4px solid var(--success)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
              <div>
                <span style={{ fontSize: "14px", fontWeight: 600, color: "var(--success)" }}>✨ PARSE COMPLETED SUCCESSFULLY</span>
                <h2 style={{ fontSize: "24px", fontWeight: 700, marginTop: "4px" }}>Extracted Candidate Profile</h2>
              </div>
              <button
                onClick={() => router.push("/dashboard")}
                className="btn-primary"
              >
                Go to Dashboard ➡️
              </button>
            </div>
            
            {/* Metrics Dashboard */}
            {parsedData.metrics && (
              <div style={{ 
                background: "rgba(255, 255, 255, 0.03)", 
                border: "1px solid rgba(255, 255, 255, 0.08)", 
                borderRadius: "var(--radius-sm)", 
                padding: "16px", 
                marginBottom: "24px",
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                gap: "16px"
              }}>
                <div style={{ textAlign: "center" }}>
                  <span style={{ fontSize: "12px", color: "var(--text-secondary)", textTransform: "uppercase" }}>Projects Extracted</span>
                  <div style={{ fontSize: "20px", fontWeight: 700, marginTop: "4px", color: parsedData.metrics.projects_extracted === parsedData.metrics.projects_detected ? "var(--success)" : "var(--warning)" }}>
                    {parsedData.metrics.projects_extracted} / {parsedData.metrics.projects_detected}
                  </div>
                </div>
                <div style={{ textAlign: "center" }}>
                  <span style={{ fontSize: "12px", color: "var(--text-secondary)", textTransform: "uppercase" }}>Experience Extracted</span>
                  <div style={{ fontSize: "20px", fontWeight: 700, marginTop: "4px", color: parsedData.metrics.experience_extracted === parsedData.metrics.experience_detected ? "var(--success)" : "var(--warning)" }}>
                    {parsedData.metrics.experience_extracted} / {parsedData.metrics.experience_detected}
                  </div>
                </div>
                <div style={{ textAlign: "center" }}>
                  <span style={{ fontSize: "12px", color: "var(--text-secondary)", textTransform: "uppercase" }}>Skills Extracted</span>
                  <div style={{ fontSize: "20px", fontWeight: 700, marginTop: "4px", color: "var(--primary)" }}>
                    {parsedData.metrics.skills_extracted}
                  </div>
                </div>
              </div>
            )}

            {/* Skills */}
            <h3 style={{ fontSize: "16px", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "12px", borderBottom: "1px solid rgba(255, 255, 255, 0.08)", paddingBottom: "6px" }}>
              Technical Skills
            </h3>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "24px" }}>
              {parsedData.skills.map((skill, index) => (
                <span
                  key={index}
                  style={{
                    background: "rgba(108, 92, 231, 0.15)",
                    border: "1px solid rgba(108, 92, 231, 0.3)",
                    padding: "6px 12px",
                    borderRadius: "100px",
                    color: "#a29bfe",
                    fontSize: "13px",
                    fontWeight: 500
                  }}
                >
                  {skill}
                </span>
              ))}
            </div>

            {/* Experience */}
            <h3 style={{ fontSize: "16px", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "16px", borderBottom: "1px solid rgba(255, 255, 255, 0.08)", paddingBottom: "6px" }}>
              Work Experience & Internships
            </h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "16px", marginBottom: "24px" }}>
              {parsedData.experience.map((exp, index) => (
                <div key={index} style={{ background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.06)", borderRadius: "var(--radius-sm)", padding: "16px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: "8px", marginBottom: "8px" }}>
                    <div>
                      <h4 style={{ fontSize: "16px", fontWeight: 700, color: "#fff" }}>{exp.role}</h4>
                      <span style={{ fontSize: "14px", color: "var(--secondary)", fontWeight: 600 }}>{exp.company}</span>
                    </div>
                    <div style={{ textAlign: "right" }}>
                      <span style={{ fontSize: "13px", color: "var(--text-secondary)" }}>{exp.start_date} - {exp.end_date}</span>
                      {exp.duration_months > 0 && (
                        <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>({exp.duration_months} m)</div>
                      )}
                    </div>
                  </div>
                  {exp.description && (
                    <p style={{ fontSize: "13.5px", color: "var(--text-secondary)", marginBottom: "12px", lineHeight: 1.5 }}>{exp.description}</p>
                  )}
                  {exp.highlights && exp.highlights.length > 0 && (
                    <ul style={{ paddingLeft: "20px", fontSize: "13px", color: "var(--text-primary)", display: "flex", flexDirection: "column", gap: "4px", margin: "0 0 12px 0", lineHeight: 1.5 }}>
                      {exp.highlights.map((hl, i) => (
                        <li key={i}>{hl}</li>
                      ))}
                    </ul>
                  )}
                  {exp.technologies && exp.technologies.length > 0 && (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                      {exp.technologies.map((tech, i) => (
                        <span key={i} style={{ background: "rgba(255, 255, 255, 0.05)", border: "1px solid rgba(255, 255, 255, 0.1)", color: "var(--text-secondary)", padding: "2px 8px", borderRadius: "4px", fontSize: "11px" }}>
                          {tech}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Projects */}
            <h3 style={{ fontSize: "16px", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "16px", borderBottom: "1px solid rgba(255, 255, 255, 0.08)", paddingBottom: "6px" }}>
              Featured Projects
            </h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "16px", marginBottom: "24px" }}>
              {parsedData.projects.map((proj, index) => (
                <div key={index} style={{ background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.06)", borderRadius: "var(--radius-sm)", padding: "16px" }}>
                  <h4 style={{ fontSize: "16px", fontWeight: 700, color: "#fff", marginBottom: "6px" }}>{proj.name}</h4>
                  {proj.description && (
                    <p style={{ fontSize: "13.5px", color: "var(--text-secondary)", marginBottom: "12px", lineHeight: 1.5 }}>{proj.description}</p>
                  )}
                  {proj.highlights && proj.highlights.length > 0 && (
                    <ul style={{ paddingLeft: "20px", fontSize: "13px", color: "var(--text-primary)", display: "flex", flexDirection: "column", gap: "4px", margin: "0 0 12px 0", lineHeight: 1.5 }}>
                      {proj.highlights.map((hl, i) => (
                        <li key={i}>{hl}</li>
                      ))}
                    </ul>
                  )}
                  {proj.technologies && proj.technologies.length > 0 && (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                      {proj.technologies.map((tech, i) => (
                        <span key={i} style={{ background: "rgba(108, 92, 231, 0.1)", border: "1px solid rgba(108, 92, 231, 0.2)", color: "#a29bfe", padding: "2px 8px", borderRadius: "4px", fontSize: "11px" }}>
                          {tech}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Education */}
            <h3 style={{ fontSize: "16px", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "12px", borderBottom: "1px solid rgba(255, 255, 255, 0.08)", paddingBottom: "6px" }}>
              Education
            </h3>
            <ul style={{ paddingLeft: "20px", color: "var(--text-primary)", fontSize: "14px", lineHeight: 1.6, display: "flex", flexDirection: "column", gap: "8px" }}>
              {parsedData.education.map((edu, index) => (
                <li key={index}>{edu}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
