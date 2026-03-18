"use client";

import { useState, useEffect } from "react";

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        zIndex: 100,
        transition: "all 0.3s",
        borderBottom: scrolled ? "1px solid rgba(99,102,241,0.15)" : "1px solid transparent",
        background: scrolled
          ? "rgba(3,7,18,0.85)"
          : "transparent",
        backdropFilter: scrolled ? "blur(20px)" : "none",
        padding: "0 24px",
      }}
    >
      <nav
        style={{
          maxWidth: 1400,
          margin: "0 auto",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          height: 64,
        }}
      >
        {/* Logo */}
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div
            style={{
              width: 34,
              height: 34,
              borderRadius: 10,
              background: "linear-gradient(135deg, #7c3aed, #2563eb)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 0 20px rgba(124,58,237,0.5)",
              fontSize: 18,
            }}
          >
            ∫
          </div>
          <span
            style={{
              fontWeight: 700,
              fontSize: "1.15rem",
              letterSpacing: "-0.02em",
            }}
            className="gradient-text"
          >
            AutoSim
          </span>
          <span
            className="badge badge-purple"
            style={{ marginLeft: 4 }}
          >
            v2.0
          </span>
        </div>

        {/* Nav links */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          {[
            { label: "Solver", href: "#solver" },
            { label: "Visualization", href: "#visualization" },
            { label: "Docs", href: "#about" },
          ].map((link) => (
            <a
              key={link.href}
              href={link.href}
              style={{
                padding: "6px 14px",
                borderRadius: 8,
                fontSize: "0.85rem",
                color: "var(--text-secondary)",
                textDecoration: "none",
                transition: "color 0.2s, background 0.2s",
              }}
              onMouseEnter={(e) => {
                (e.target as HTMLElement).style.color = "var(--text-primary)";
                (e.target as HTMLElement).style.background = "rgba(255,255,255,0.05)";
              }}
              onMouseLeave={(e) => {
                (e.target as HTMLElement).style.color = "var(--text-secondary)";
                (e.target as HTMLElement).style.background = "transparent";
              }}
            >
              {link.label}
            </a>
          ))}

          {/* Live indicator */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              padding: "6px 12px",
              borderRadius: 20,
              background: "rgba(52,211,153,0.08)",
              border: "1px solid rgba(52,211,153,0.25)",
            }}
          >
            <div className="pulse-dot" style={{ width: 7, height: 7 }} />
            <span style={{ fontSize: "0.75rem", color: "var(--neon-green)", fontWeight: 600 }}>
              LIVE
            </span>
          </div>
        </div>
      </nav>
    </header>
  );
}
