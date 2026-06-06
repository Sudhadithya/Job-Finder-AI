"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Header() {
  const pathname = usePathname();

  const links = [
    { href: "/upload", label: "1. Upload Resume" },
    { href: "/dashboard", label: "2. Profile & Discover" },
    { href: "/recommendations", label: "3. Job Matches" },
  ];

  return (
    <header className="layout-header">
      <div className="container" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Link href="/" style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ fontSize: "24px", fontWeight: 800, background: "linear-gradient(90deg, #6c5ce7 0%, #00cec9 100%)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            JobFinder AI
          </span>
        </Link>
        <nav>
          <ul style={{ display: "flex", listStyle: "none", gap: "24px", padding: 0, margin: 0 }}>
            {links.map((link) => {
              const isActive = pathname === link.href;
              return (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className={`nav-link ${isActive ? "active" : ""}`}
                    style={{
                      fontSize: "15px",
                      fontWeight: 600,
                      letterSpacing: "0.5px",
                      transition: "color 0.2s"
                    }}
                  >
                    {link.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </div>
    </header>
  );
}
