import Link from "next/link";

export default function Home() {
  return (
    <div className="container" style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "70vh", textAlign: "center" }}>
      <div style={{ maxWidth: "800px", zIndex: 1 }}>
        {/* Badge */}
        <div style={{ display: "inline-block", background: "rgba(108, 92, 231, 0.15)", border: "1px solid rgba(108, 92, 231, 0.3)", padding: "6px 16px", borderRadius: "100px", color: "#6c5ce7", fontSize: "14px", fontWeight: 600, marginBottom: "24px" }}>
          ⚡ AI-Powered Candidate-to-Job Matching Engine
        </div>
        
        {/* Main Title */}
        <h1 style={{ fontSize: "56px", fontWeight: 800, lineHeight: 1.1, marginBottom: "20px", letterSpacing: "-1px" }}>
          Discover the jobs that fit <span style={{ background: "linear-gradient(90deg, #6c5ce7 0%, #00cec9 100%)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>your actual skills</span>
        </h1>
        
        {/* Description */}
        <p style={{ fontSize: "18px", color: "var(--text-secondary)", lineHeight: 1.6, marginBottom: "40px" }}>
          Upload your resume to parse your skills, set your desired experience category, scrape top developer sources, and see matches evaluated and ranked using Anthropic Claude.
        </p>
        
        {/* Action Buttons */}
        <div style={{ display: "flex", gap: "16px", justifyContent: "center", marginBottom: "60px" }}>
          <Link href="/upload" className="btn-primary" style={{ textDecoration: "none" }}>
            Get Started: Upload Resume 🚀
          </Link>
          <a href="#features" className="btn-secondary" style={{ textDecoration: "none" }}>
            See How it Works
          </a>
        </div>
      </div>
      
      {/* Feature Section */}
      <section id="features" style={{ width: "100%", marginTop: "40px", borderTop: "1px solid var(--card-border)", paddingTop: "60px" }}>
        <h2 style={{ fontSize: "28px", fontWeight: 700, marginBottom: "32px" }}>Engineered for Developer Hiring</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "24px", width: "100%" }}>
          {/* Card 1 */}
          <div className="glass-panel" style={{ padding: "32px", textAlign: "left" }}>
            <div style={{ fontSize: "28px", marginBottom: "16px" }}>📄</div>
            <h3 style={{ fontSize: "18px", fontWeight: 600, marginBottom: "12px" }}>One-Time Resume Parser</h3>
            <p style={{ fontSize: "14px", color: "var(--text-secondary)", lineHeight: 1.5 }}>
              Extracts text from PDF resumes using PyMuPDF and processes it via Claude once. No redundant parsing.
            </p>
          </div>
          
          {/* Card 2 */}
          <div className="glass-panel" style={{ padding: "32px", textAlign: "left" }}>
            <div style={{ fontSize: "28px", marginBottom: "16px" }}>🔍</div>
            <h3 style={{ fontSize: "18px", fontWeight: 600, marginBottom: "12px" }}>Decoupled Discovery</h3>
            <p style={{ fontSize: "14px", color: "var(--text-secondary)", lineHeight: 1.5 }}>
              Scrapes Greenhouse, Lever, YC, and Instahyre. Filters for the last 24 hours, dedupes, and stores.
            </p>
          </div>
          
          {/* Card 3 */}
          <div className="glass-panel" style={{ padding: "32px", textAlign: "left" }}>
            <div style={{ fontSize: "28px", marginBottom: "16px" }}>🎯</div>
            <h3 style={{ fontSize: "18px", fontWeight: 600, marginBottom: "12px" }}>Hybrid Match Engine</h3>
            <p style={{ fontSize: "14px", color: "var(--text-secondary)", lineHeight: 1.5 }}>
              Combines role alignment boosts (+20 / -50) with weighted Claude sub-scoring: Skills, Projects, Experience, and Education.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
