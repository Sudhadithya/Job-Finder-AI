"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { UserProfile, Job } from "@/types";

const CATEGORIES = [
  "SDE-1",
  "Data Scientist"
];

export default function DashboardPage() {
  const router = useRouter();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>("SDE-1");
  const [updatingCategory, setUpdatingCategory] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  
  // Jobs state
  const [jobs, setJobs] = useState<Job[]>([]);
  const [jobsLoading, setJobsLoading] = useState(true);
  const [expandedJobId, setExpandedJobId] = useState<string | null>(null);

  // Load profile and jobs on mount
  useEffect(() => {
    async function loadData() {
      try {
        const data = await api.getProfile();
        setProfile(data);
        if (data.desired_category) {
          setSelectedCategory(data.desired_category);
        }
      } catch (err: any) {
        setError(err.message || "Failed to fetch profile details.");
      } finally {
        setLoading(false);
      }
    }
    
    async function loadJobs() {
      try {
        const jobsData = await api.getJobs();
        setJobs(jobsData);
      } catch (err: any) {
        console.error("Failed to load jobs:", err);
      } finally {
        setJobsLoading(false);
      }
    }
    
    loadData();
    loadJobs();
  }, []);

  const handleUpdateCategory = async (category: string) => {
    setSelectedCategory(category);
    setUpdatingCategory(true);
    setError(null);
    try {
      const data = await api.updateCategory(category);
      setProfile(data);
    } catch (err: any) {
      setError(err.message || "Failed to update category.");
    } finally {
      setUpdatingCategory(false);
    }
  };

  const handleDiscoverJobs = async () => {
    setScanning(true);
    setScanResult(null);
    setError(null);
    try {
      const res = await api.discoverJobs();
      setScanResult(res.new_jobs_found);
      
      // Refresh jobs list after scanning
      const jobsData = await api.getJobs();
      setJobs(jobsData);
    } catch (err: any) {
      setError(err.message || "Discovery scan failed.");
    } finally {
      setScanning(false);
    }
  };

  if (loading) {
    return (
      <div className="container" style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "50vh" }}>
        <div className="shimmer" style={{ width: "100%", height: "200px", borderRadius: "var(--radius-md)" }}></div>
      </div>
    );
  }

  return (
    <div className="container" style={{ maxWidth: "900px" }}>
      <div style={{ marginBottom: "32px" }}>
        <h1 style={{ fontSize: "36px", fontWeight: 700, marginBottom: "8px" }}>Developer Dashboard</h1>
        <p style={{ color: "var(--text-secondary)" }}>
          Manage your candidate profile parameters and scan external channels.
        </p>
      </div>

      {error && (
        <div style={{ color: "var(--danger)", background: "rgba(255, 71, 87, 0.1)", border: "1px solid rgba(255, 71, 87, 0.2)", padding: "12px", borderRadius: "var(--radius-sm)", marginBottom: "24px", fontSize: "14px" }}>
          ⚠️ {error}
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(350px, 1fr))", gap: "24px" }}>
        
        {/* Left Column: Profile & Category Selector */}
        <div className="glass-panel" style={{ padding: "32px", display: "flex", flexDirection: "column", gap: "20px" }}>
          <div>
            <span style={{ fontSize: "12px", color: "var(--primary)", fontWeight: 700, textTransform: "uppercase" }}>Candidate Settings</span>
            <h2 style={{ fontSize: "20px", fontWeight: 700, marginTop: "4px" }}>Select Role Category</h2>
            <p style={{ fontSize: "13px", color: "var(--text-secondary)", marginTop: "4px" }}>
              Used to compute role alignment scoring (boosts entry levels by +20, penalizes senior roles by -50).
            </p>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            <label style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-primary)" }}>Desired Role Level</label>
            <select
              value={selectedCategory}
              onChange={(e) => handleUpdateCategory(e.target.value)}
              disabled={updatingCategory}
              style={{
                background: "rgba(0, 0, 0, 0.3)",
                border: "1px solid rgba(255, 255, 255, 0.15)",
                color: "#fff",
                padding: "12px",
                borderRadius: "var(--radius-sm)",
                fontSize: "14px",
                cursor: "pointer",
                outline: "none"
              }}
            >
              {CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          <div style={{ borderTop: "1px solid rgba(255, 255, 255, 0.08)", paddingTop: "16px", fontSize: "13px", color: "var(--text-secondary)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
              <span>Profile Email:</span>
              <span style={{ color: "var(--text-primary)", fontWeight: 600 }}>{profile?.email}</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span>Active Target:</span>
              <span style={{ color: "var(--secondary)", fontWeight: 600 }}>{profile?.desired_category || "None"}</span>
            </div>
          </div>
        </div>

        {/* Right Column: Discover Sweeper */}
        <div className="glass-panel" style={{ padding: "32px", display: "flex", flexDirection: "column", gap: "24px" }}>
          <div>
            <span style={{ fontSize: "12px", color: "var(--secondary)", fontWeight: 700, textTransform: "uppercase" }}>Job Discovery pipeline</span>
            <h2 style={{ fontSize: "20px", fontWeight: 700, marginTop: "4px" }}>Scrape Job Channels</h2>
            <p style={{ fontSize: "13px", color: "var(--text-secondary)", marginTop: "4px" }}>
              Pull postings from LinkedIn, Wellfound, YC, Greenhouse, Lever, Naukri, and Instahyre. Discards jobs older than 24 hours.
            </p>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <button
              onClick={handleDiscoverJobs}
              disabled={scanning}
              className="btn-primary"
              style={{ width: "100%", justifyContent: "center" }}
            >
              {scanning ? (
                <>
                  <span className="shimmer" style={{ width: "16px", height: "16px", borderRadius: "50%", display: "inline-block" }}></span>
                  Scanning Sources...
                </>
              ) : (
                "Scan Job Boards (Last 24h) 🔍"
              )}
            </button>

            {scanResult !== null && (
              <div style={{ background: "rgba(0, 206, 201, 0.1)", border: "1px solid rgba(0, 206, 201, 0.2)", padding: "14px", borderRadius: "var(--radius-sm)", textAlign: "center" }}>
                <p style={{ fontSize: "15px", color: "var(--secondary)", fontWeight: 700 }}>
                  🎉 Discovery scan complete!
                </p>
                <p style={{ fontSize: "13px", color: "var(--text-secondary)", marginTop: "4px" }}>
                  Found and stored <strong style={{ color: "#fff" }}>{scanResult} new jobs</strong> in the database.
                </p>
              </div>
            )}
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "auto" }}>
            <button
              onClick={() => router.push("/recommendations")}
              className="btn-secondary"
              style={{ width: "100%", justifyContent: "center", border: "1px solid var(--primary)", color: "#c7c3f3" }}
            >
              Generate Recommendations & Match 🎯
            </button>
          </div>
        </div>

      </div>

      {/* Discovered Jobs List */}
      <div className="glass-panel" style={{ marginTop: "32px", padding: "32px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px", flexWrap: "wrap", gap: "12px" }}>
          <div>
            <h2 style={{ fontSize: "22px", fontWeight: 700, color: "#fff" }}>Discovered Active Jobs</h2>
            <p style={{ fontSize: "14px", color: "var(--text-secondary)", marginTop: "4px" }}>
              Only showing SDE, technical, and data science roles (Bangalore, Hyderabad, Remote India).
            </p>
          </div>
          <span style={{ background: "var(--primary-glow)", color: "#a29bfe", border: "1px solid rgba(108, 92, 231, 0.4)", padding: "4px 12px", borderRadius: "100px", fontSize: "13px", fontWeight: 600 }}>
            {jobs.length} Jobs Total
          </span>
        </div>

        {jobsLoading ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <div className="shimmer" style={{ width: "100%", height: "80px", borderRadius: "var(--radius-sm)" }}></div>
            <div className="shimmer" style={{ width: "100%", height: "80px", borderRadius: "var(--radius-sm)" }}></div>
          </div>
        ) : jobs.length === 0 ? (
          <div style={{ padding: "40px", textAlign: "center", border: "1px dashed rgba(255,255,255,0.1)", borderRadius: "var(--radius-md)" }}>
            <div style={{ fontSize: "36px", marginBottom: "12px" }}>📂</div>
            <p style={{ color: "var(--text-secondary)", fontSize: "14px" }}>No jobs discovered yet. Click Scan Job Boards to fetch active postings.</p>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {jobs.map((job) => {
              const isExpanded = expandedJobId === job.job_id;
              return (
                <div
                  key={job.job_id}
                  style={{
                    background: "rgba(255, 255, 255, 0.02)",
                    border: isExpanded ? "1px solid var(--primary)" : "1px solid rgba(255, 255, 255, 0.08)",
                    borderRadius: "var(--radius-md)",
                    padding: "20px",
                    transition: "var(--transition)",
                    cursor: "pointer"
                  }}
                  onClick={() => setExpandedJobId(isExpanded ? null : job.job_id)}
                >
                  {/* Job Header Info */}
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "12px" }}>
                    <div>
                      <h3 style={{ fontSize: "17px", fontWeight: 700, color: "#fff" }}>{job.role}</h3>
                      <div style={{ display: "flex", gap: "12px", alignItems: "center", marginTop: "6px", flexWrap: "wrap" }}>
                        <span style={{ fontSize: "13px", color: "var(--secondary)", fontWeight: 600 }}>{job.company}</span>
                        <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>•</span>
                        <span style={{ fontSize: "13px", color: "var(--text-secondary)" }}>📍 {job.location}</span>
                        <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>•</span>
                        <span style={{ fontSize: "11px", textTransform: "uppercase", background: "rgba(255,255,255,0.05)", padding: "2px 6px", borderRadius: "4px", color: "var(--text-secondary)" }}>
                          Source: {job.source}
                        </span>
                      </div>
                    </div>
                    <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
                      <a
                        href={job.job_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-secondary"
                        style={{ padding: "6px 14px", fontSize: "12px", fontWeight: 500, borderRadius: "var(--radius-sm)" }}
                        onClick={(e) => e.stopPropagation()}
                      >
                        Apply Now 🌐
                      </a>
                      <span style={{ color: "var(--text-muted)", fontSize: "14px", transform: isExpanded ? "rotate(180deg)" : "rotate(0deg)", transition: "var(--transition)" }}>
                        ▼
                      </span>
                    </div>
                  </div>

                  {/* Requirements Dropdown Accordion Content */}
                  {isExpanded && (
                    <div
                      style={{
                        marginTop: "16px",
                        paddingTop: "16px",
                        borderTop: "1px solid rgba(255, 255, 255, 0.06)",
                        display: "flex",
                        flexDirection: "column",
                        gap: "16px"
                      }}
                      onClick={(e) => e.stopPropagation()}
                    >
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "20px" }}>
                        {/* Minimum Requirements */}
                        <div>
                          <h4 style={{ fontSize: "13px", fontWeight: 700, color: "var(--secondary)", textTransform: "uppercase", marginBottom: "8px", letterSpacing: "0.5px" }}>
                            Minimum Requirements
                          </h4>
                          <ul style={{ paddingLeft: "18px", margin: 0, display: "flex", flexDirection: "column", gap: "6px" }}>
                            {job.min_requirements && job.min_requirements.length > 0 ? (
                              job.min_requirements.map((req, i) => (
                                <li key={i} style={{ fontSize: "13.5px", color: "var(--text-primary)", lineHeight: 1.4 }}>{req}</li>
                              ))
                            ) : (
                              <li style={{ fontSize: "13.5px", color: "var(--text-secondary)", listStyleType: "none" }}>Not explicitly listed.</li>
                            )}
                          </ul>
                        </div>

                        {/* Preferred Requirements */}
                        <div>
                          <h4 style={{ fontSize: "13px", fontWeight: 700, color: "var(--primary)", textTransform: "uppercase", marginBottom: "8px", letterSpacing: "0.5px" }}>
                            Preferred / Pluses
                          </h4>
                          <ul style={{ paddingLeft: "18px", margin: 0, display: "flex", flexDirection: "column", gap: "6px" }}>
                            {job.preferred_requirements && job.preferred_requirements.length > 0 ? (
                              job.preferred_requirements.map((req, i) => (
                                <li key={i} style={{ fontSize: "13.5px", color: "var(--text-primary)", lineHeight: 1.4 }}>{req}</li>
                              ))
                            ) : (
                              <li style={{ fontSize: "13.5px", color: "var(--text-secondary)", listStyleType: "none" }}>Not explicitly listed.</li>
                            )}
                          </ul>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
