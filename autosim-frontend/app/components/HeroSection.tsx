"use client";

import { useEffect, useRef } from "react";

const FEATURES = [
  {
    icon: "∫",
    label: "Symbolic",
    desc: "Exact solutions via SymPy",
    color: "var(--neon-purple)",
    badge: "badge-purple",
  },
  {
    icon: "ℒ",
    label: "Laplace",
    desc: "S-domain transforms",
    color: "var(--neon-blue)",
    badge: "badge-blue",
  },
  {
    icon: "⟳",
    label: "RK45 / Radau",
    desc: "Adaptive numerical ODE",
    color: "var(--neon-green)",
    badge: "badge-green",
  },
  {
    icon: "▶",
    label: "Euler Methods",
    desc: "Educational step-by-step",
    color: "var(--neon-yellow)",
    badge: "badge-yellow",
  },
  {
    icon: "🤖",
    label: "LLM Insights",
    desc: "AI-powered interpretation",
    color: "var(--neon-cyan)",
    badge: "badge-cyan",
  },
  {
    icon: "📊",
    label: "Compare All",
    desc: "Side-by-side method analysis",
    color: "var(--neon-pink)",
    badge: "badge-pink",
  },
];

export default function HeroSection() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Animated particle field
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    const particles: Array<{
      x: number; y: number; vx: number; vy: number;
      r: number; alpha: number; color: string;
    }> = [];

    const colors = ["#7c3aed", "#2563eb", "#22d3ee", "#34d399"];

    const resize = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    for (let i = 0; i < 60; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        r: Math.random() * 2 + 0.5,
        alpha: Math.random() * 0.6 + 0.2,
        color: colors[Math.floor(Math.random() * colors.length)],
      });
    }

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Connect nearby particles
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 120) {
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(99,102,241,${0.12 * (1 - dist / 120)})`;
            ctx.lineWidth = 0.6;
            ctx.stroke();
          }
        }
      }

      for (const p of particles) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = p.color + Math.round(p.alpha * 255).toString(16).padStart(2, "0");
        ctx.fill();

        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
      }

      animId = requestAnimationFrame(draw);
    };
    draw();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return (
    <section
      id="hero"
      style={{
        position: "relative",
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        overflow: "hidden",
        padding: "100px 24px 60px",
        background: "#030712",
      }}
      className="grid-bg"
    >
      {/* Particle canvas */}
      <canvas
        ref={canvasRef}
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          pointerEvents: "none",
        }}
      />

      {/* Radial gradient overlay */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse 80% 60% at 50% 50%, rgba(124,58,237,0.08) 0%, transparent 70%)",
          pointerEvents: "none",
        }}
      />

      {/* Content */}
      <div
        style={{
          position: "relative",
          zIndex: 1,
          maxWidth: 860,
          textAlign: "center",
        }}
        className="fade-in"
      >
        {/* Tag line */}
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            padding: "6px 16px",
            borderRadius: 20,
            background: "rgba(124,58,237,0.1)",
            border: "1px solid rgba(124,58,237,0.3)",
            marginBottom: 24,
          }}
        >
          <div className="pulse-dot" />
          <span
            style={{
              fontSize: "0.78rem",
              fontFamily: "var(--font-mono)",
              color: "var(--neon-purple)",
              letterSpacing: "1.5px",
              textTransform: "uppercase",
              fontWeight: 600,
            }}
          >
            Zero Hallucination ODE Solver
          </span>
        </div>

        {/* Main heading */}
        <h1
          style={{
            fontSize: "clamp(2.8rem, 6vw, 4.5rem)",
            fontWeight: 800,
            lineHeight: 1.1,
            letterSpacing: "-0.03em",
            marginBottom: 20,
          }}
        >
          <span className="gradient-text">AutoSim</span>
          <br />
          <span style={{ color: "var(--text-primary)" }}>ODE Solver</span>
        </h1>

        {/* Subtitle */}
        <p
          style={{
            fontSize: "1.1rem",
            color: "var(--text-secondary)",
            lineHeight: 1.7,
            maxWidth: 640,
            margin: "0 auto 16px",
          }}
        >
          A production-grade simulator that solves ordinary differential equations
          using{" "}
          <span className="mono-highlight">SymPy</span>,{" "}
          <span className="mono-highlight">SciPy</span>, and{" "}
          <span className="mono-highlight">NumPy</span> — every number is
          computed by a verified library, never hallucinated.
        </p>

        {/* Example equation display */}
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 10,
            padding: "10px 20px",
            borderRadius: 12,
            background: "rgba(15,23,42,0.8)",
            border: "1px solid rgba(34,211,238,0.25)",
            marginBottom: 48,
            backdropFilter: "blur(8px)",
          }}
        >
          <span style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>e.g.</span>
          <code
            style={{
              fontFamily: "var(--font-mono)",
              color: "var(--neon-cyan)",
              fontSize: "0.95rem",
              letterSpacing: "0.02em",
            }}
          >
            x&apos;&apos; + 0.2x&apos; + x = cos(t)
          </code>
        </div>

        {/* CTA buttons */}
        <div
          style={{
            display: "flex",
            gap: 12,
            justifyContent: "center",
            flexWrap: "wrap",
            marginBottom: 72,
          }}
        >
          <a
            href="#solver"
            className="btn-neon"
            style={{
              padding: "14px 32px",
              fontSize: "0.95rem",
              textDecoration: "none",
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            <span>🚀 Start Solving</span>
          </a>
          <a
            href="#about"
            style={{
              padding: "14px 32px",
              fontSize: "0.95rem",
              borderRadius: 10,
              border: "1px solid var(--border)",
              color: "var(--text-secondary)",
              textDecoration: "none",
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
              transition: "border-color 0.2s, color 0.2s",
              background: "rgba(255,255,255,0.02)",
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLElement).style.borderColor = "rgba(99,102,241,0.4)";
              (e.currentTarget as HTMLElement).style.color = "var(--text-primary)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLElement).style.borderColor = "var(--border)";
              (e.currentTarget as HTMLElement).style.color = "var(--text-secondary)";
            }}
          >
            <span>📖 Learn More</span>
          </a>
        </div>

        {/* Feature cards grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: 12,
            maxWidth: 860,
          }}
        >
          {FEATURES.map((f) => (
            <div
              key={f.label}
              className="glass-card glass-card-hover"
              style={{
                padding: "16px 18px",
                display: "flex",
                alignItems: "flex-start",
                gap: 12,
                textAlign: "left",
                cursor: "default",
                transition: "border-color 0.2s, transform 0.2s",
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLElement).style.transform = "translateY(-3px)";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLElement).style.transform = "translateY(0)";
              }}
            >
              <div
                style={{
                  fontSize: "1.5rem",
                  lineHeight: 1,
                  minWidth: 32,
                  textAlign: "center",
                }}
              >
                {f.icon}
              </div>
              <div>
                <div
                  style={{
                    fontSize: "0.85rem",
                    fontWeight: 700,
                    color: f.color,
                    marginBottom: 3,
                  }}
                >
                  {f.label}
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                  {f.desc}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Scroll cue */}
      <div
        style={{
          position: "absolute",
          bottom: 28,
          left: "50%",
          transform: "translateX(-50%)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 6,
          opacity: 0.5,
        }}
      >
        <span style={{ fontSize: "0.72rem", fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
          SCROLL
        </span>
        <div
          style={{
            width: 1.5,
            height: 32,
            background: "linear-gradient(to bottom, rgba(99,102,241,0.6), transparent)",
          }}
        />
      </div>
    </section>
  );
}
