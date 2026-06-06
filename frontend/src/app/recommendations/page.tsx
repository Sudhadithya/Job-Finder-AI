"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { MatchRecommendation } from "@/types";

export default function RecommendationsPage() {
  const router = useRouter();
  const [recommendations, setRecommendations] = useState<MatchRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedMatchId, setExpandedMatchId] = useState<string | null>(null);

  useEffect(() => {
    async function loadRecs() {
      try {
        const data = await api.getRecommendations();
        setRecommendations(data);
      } catch (err: any) {
        setError(err.message || "Failed to compile recommendations.");
      } finally {
        setLoading(false);
      }
    }
    loadRecs();
  }, []);

  const getScoreColor = (score: number) => {
    if (score >= 85) return "var(--success)";
    if (score >= 60) return "var(--warning)";
    return "var(--danger)";
  };

  const toggleExpand = (id: string) => {
    setExpandedMatchId(expandedMatchId === id ? null : id);
  };

  if (loading) {
    return (
      <div className="container" style={{ maxWidth: "800px" }}>
        <h2 style={{ fontSize: "24px", marginBottom: "20px" }}>Calculating Recommendations...</h2>
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div className="shimmer" style={{ width: "100%", height: "90px", borderRadius: "var(--radius-md)" }}></div>
          <div className="shimmer" style={{ width: "100%", height: "90px", borderRadius: "var(--radius-md)" }}></div>
          <div className="shimmer" style={{ width: "100%", height: "90px", borderRadius: "var(--radius-md)" }}></div>
        </div>
      </div>
    );
  }

  // Handle missing resume error specifically
  if (error && (error.includes("resume") || error.includes("No resume found"))) {
    return (
      <div className="container" style={{ maxWidth: "600px", textAlign: "center", paddingTop: "40px" }}>
        <div className="glass-panel" style={{ padding: "40px", borderTop: "4px solid var(--warning)" }}>
          <div style={{ fontSize: "48px", marginBottom: "16px" }}>⚠️</div>
          <h2 style={{ fontSize: "22px", fontWeight: 700, marginBottom: "12px" }}>Resume Not Found</h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: "32px", fontSize: "14px", lineHeight: 1.5 }}>
            To generate personalized job recommendations, you must first upload your resume. Our AI engines will analyze your skills and compare them directly to active opportunities.
          </p>
          <button
            onClick={() => router.push("/upload")}
            className="btn-primary"
            style={{ width: "100%", justifyContent: "center" }}
          >
            Upload Resume Now ➡️
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container" style={{ maxWidth: "900px" }}>
      <div style={{ marginBottom: "32px" }}>
        <h1 style={{ fontSize: "36px", fontWeight: 700, marginBottom: "8px" }}>AI Job Matches</h1>
        <p style={{ color: "var(--text-secondary)" }}>
          Evaluated against your skills, projects, and desired role categories.
        </p>
      </div>

      {error && (
        <div style={{ color: "var(--danger)", background: "rgba(255, 71, 87, 0.1)", border: "1px solid rgba(255, 71, 87, 0.2)", padding: "12px", borderRadius: "var(--radius-sm)", marginBottom: "24px", fontSize: "14px" }}>
          ⚠️ {error}
        </div>
      )}

      {recommendations.length === 0 ? (
        <div className="glass-panel" style={{ padding: "48px", textAlign: "center" }}>
          <div style={{ fontSize: "40px", marginBottom: "16px" }}>🔍</div>
          <h2 style={{ fontSize: "20px", fontWeight: 700, marginBottom: "8px" }}>No Jobs Discovered Yet</h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: "24px", fontSize: "14px" }}>
            We haven&apos;t run a scraper sweep for jobs in the last 24 hours. Let&apos;s run job discovery first!
          </p>
          <button
            onClick={() => router.push("/dashboard")}
            className="btn-primary"
          >
            Go to Discovery Scanner ➡️
          </button>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {recommendations.map((match) => {
            const scoreColor = getScoreColor(match.score);
            const isExpanded = expandedMatchId === match.id;
            
            return (
              <div
                key={match.id}
                className="glass-panel"
                style={{
                  padding: "24px",
                  cursor: "pointer",
                  transition: "var(--transition)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "16px",
                  borderColor: isExpanded ? "var(--primary)" : "var(--card-border)"
                }}
                onClick={() => toggleExpand(match.id)}
              >
                {/* Header Row */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                    {/* Score Indicator */}
                    <div
                      style={{
                        width: "60px",
                        height: "60px",
                        borderRadius: "50%",
                        border: `3px solid ${scoreColor}`,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontWeight: 700,
                        fontSize: "18px",
                        color: scoreColor,
                        background: "rgba(0,0,0,0.2)"
                      }}
                    >
                      {match.score}%
                    </div>
                    <div>
                      <h3 style={{ fontSize: "18px", fontWeight: 700, color: "#fff" }}>{match.role}</h3>
                      <p style={{ fontSize: "14px", color: "var(--text-secondary)", fontWeight: 500 }}>{match.company}</p>
                    </div>
                  </div>
                  
                  <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <a
                      href={match.job_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-secondary"
                      style={{ padding: "8px 16px", fontSize: "13px" }}
                      onClick={(e) => e.stopPropagation()} // don't toggle expand when clicking link
                    >
                      View Posting 🌐
                    </a>
                    <span style={{ fontSize: "18px", color: "var(--text-muted)", transform: isExpanded ? "rotate(180deg)" : "rotate(0deg)", transition: "var(--transition)" }}>
                      ▼
                    </span>
                  </div>
                </div>

                {/* Collapsible Details */}
                {isExpanded && (
                  <div
                    style={{
                      borderTop: "1px solid rgba(255, 255, 255, 0.08)",
                      paddingTop: "16px",
                      marginTop: "4px",
                      display: "flex",
                      flexDirection: "column",
                      gap: "16px"
                    }}
                    onClick={(e) => e.stopPropagation()} // don't toggle when interacting inside details
                  >
                    {/* AI Reasoning */}
                    <div>
                      <h4 style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>
                        AI Matching Assessment
                      </h4>
                      <p style={{ fontSize: "14px", lineHeight: 1.5, color: "var(--text-primary)" }}>
                        {match.reasoning}
                      </p>
                    </div>

                    {/* Matching Skills */}
                    {match.matching_skills.length > 0 && (
                      <div>
                        <h4 style={{ fontSize: "13px", fontWeight: 700, color: "var(--success)", textTransform: "uppercase", marginBottom: "8px" }}>
                          Matching Skills
                        </h4>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                          {match.matching_skills.map((skill, index) => (
                            <span
                              key={index}
                              style={{
                                background: "rgba(46, 213, 115, 0.15)",
                                border: "1px solid rgba(46, 213, 115, 0.3)",
                                color: "#2ed573",
                                fontSize: "12px",
                                padding: "4px 10px",
                                borderRadius: "4px",
                                fontWeight: 500
                              }}
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Missing Skills */}
                    {match.missing_skills.length > 0 && (
                      <div>
                        <h4 style={{ fontSize: "13px", fontWeight: 700, color: "var(--danger)", textTransform: "uppercase", marginBottom: "8px" }}>
                          Missing Requirements
                        </h4>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                          {match.missing_skills.map((skill, index) => (
                            <span
                              key={index}
                              style={{
                                background: "rgba(255, 71, 87, 0.15)",
                                border: "1px solid rgba(255, 71, 87, 0.3)",
                                color: "#ff4757",
                                fontSize: "12px",
                                padding: "4px 10px",
                                borderRadius: "4px",
                                fontWeight: 500
                              }}
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
