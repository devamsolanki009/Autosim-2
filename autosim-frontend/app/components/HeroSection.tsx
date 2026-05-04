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

interface Particle {
  x: number;
  y: number;
  ox: number; // origin x — home position for spring return
  oy: number; // origin y
  vx: number;
  vy: number;
  r: number;
  baseR: number;
  alpha: number;
  color: string;
  hue: number;
}

export default function HeroSection() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const sectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const section = sectionRef.current;
    if (!canvas || !section) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    const particles: Particle[] = [];

    // Cursor state relative to canvas
    const mouse = { x: -9999, y: -9999, down: false };

    const COLORS: [string, number][] = [
      ["#7c3aed", 270],
      ["#2563eb", 220],
      ["#22d3ee", 188],
      ["#34d399", 160],
      ["#f472b6", 330],
    ];

    const REPEL_RADIUS = 130;   // cursor influence radius
    const REPEL_STRENGTH = 0.38; // force scalar
    const ATTRACT_RADIUS = 220; // secondary pull zone
    const ATTRACT_STRENGTH = 0.018;
    const SPRING = 0.012;       // spring back to origin
    const DAMPING = 0.88;       // velocity decay each frame
    const CONNECTION_DIST = 130;
    const BURST_PARTICLES = 8;

    const resize = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    // Seed particles spread evenly
    const COUNT = 80;
    for (let i = 0; i < COUNT; i++) {
      const ox = Math.random() * canvas.width;
      const oy = Math.random() * canvas.height;
      const [color, hue] = COLORS[Math.floor(Math.random() * COLORS.length)];
      const baseR = Math.random() * 2 + 0.8;
      particles.push({
        x: ox, y: oy, ox, oy,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.35,
        r: baseR, baseR,
        alpha: Math.random() * 0.55 + 0.25,
        color, hue,
      });
    }

    // Spawn burst on click
    const spawnBurst = (bx: number, by: number) => {
      for (let i = 0; i < BURST_PARTICLES; i++) {
        if (particles.length > 160) break;
        const angle = (i / BURST_PARTICLES) * Math.PI * 2;
        const speed = Math.random() * 3.5 + 1.5;
        const [color, hue] = COLORS[Math.floor(Math.random() * COLORS.length)];
        const baseR = Math.random() * 2.5 + 1;
        particles.push({
          x: bx, y: by, ox: bx, oy: by,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          r: baseR * 1.8, baseR,
          alpha: 0.9,
          color, hue,
        });
        // Burst particles fade out after settling — cap total so they don't pile up
        setTimeout(() => {
          const idx = particles.indexOf(particles[particles.length - (BURST_PARTICLES - i)]);
          if (idx > COUNT) particles.splice(idx, 1);
        }, 3500 + i * 200);
      }
    };

    // Convert section-relative mouse position to canvas coordinates
    const toCanvas = (clientX: number, clientY: number) => {
      const rect = canvas.getBoundingClientRect();
      return { x: clientX - rect.left, y: clientY - rect.top };
    };

    const onMouseMove = (e: MouseEvent) => {
      const pos = toCanvas(e.clientX, e.clientY);
      mouse.x = pos.x;
      mouse.y = pos.y;
    };
    const onMouseLeave = () => { mouse.x = -9999; mouse.y = -9999; };
    const onMouseDown = (e: MouseEvent) => {
      mouse.down = true;
      const pos = toCanvas(e.clientX, e.clientY);
      spawnBurst(pos.x, pos.y);
    };
    const onMouseUp = () => { mouse.down = false; };

    const onTouchMove = (e: TouchEvent) => {
      const t = e.touches[0];
      const pos = toCanvas(t.clientX, t.clientY);
      mouse.x = pos.x;
      mouse.y = pos.y;
    };
    const onTouchEnd = () => { mouse.x = -9999; mouse.y = -9999; };

    section.addEventListener("mousemove", onMouseMove);
    section.addEventListener("mouseleave", onMouseLeave);
    section.addEventListener("mousedown", onMouseDown);
    window.addEventListener("mouseup", onMouseUp);
    section.addEventListener("touchmove", onTouchMove, { passive: true });
    section.addEventListener("touchend", onTouchEnd);

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const mx = mouse.x;
      const my = mouse.y;

      // Draw cursor glow ring when cursor is active
      if (mx > 0) {
        const grd = ctx.createRadialGradient(mx, my, 0, mx, my, REPEL_RADIUS);
        grd.addColorStop(0, "rgba(124,58,237,0.07)");
        grd.addColorStop(0.5, "rgba(34,211,238,0.04)");
        grd.addColorStop(1, "rgba(0,0,0,0)");
        ctx.beginPath();
        ctx.arc(mx, my, REPEL_RADIUS, 0, Math.PI * 2);
        ctx.fillStyle = grd;
        ctx.fill();
      }

      // Update particle physics
      for (const p of particles) {
        const dx = p.x - mx;
        const dy = p.y - my;
        const distSq = dx * dx + dy * dy;
        const dist = Math.sqrt(distSq);

        if (dist < REPEL_RADIUS && dist > 0.5) {
          // Hard repulsion — push away from cursor
          const force = (REPEL_RADIUS - dist) / REPEL_RADIUS;
          const strength = REPEL_STRENGTH * force * force;
          p.vx += (dx / dist) * strength * (mouse.down ? 2.2 : 1);
          p.vy += (dy / dist) * strength * (mouse.down ? 2.2 : 1);
        } else if (dist < ATTRACT_RADIUS && dist > REPEL_RADIUS) {
          // Soft attraction just outside repel zone — creates orbit effect
          const force = (ATTRACT_RADIUS - dist) / ATTRACT_RADIUS;
          p.vx -= (dx / dist) * ATTRACT_STRENGTH * force;
          p.vy -= (dy / dist) * ATTRACT_STRENGTH * force;
        }

        // Spring return toward home origin
        p.vx += (p.ox - p.x) * SPRING;
        p.vy += (p.oy - p.y) * SPRING;

        // Dampen velocity
        p.vx *= DAMPING;
        p.vy *= DAMPING;

        p.x += p.vx;
        p.y += p.vy;

        // Soft boundary — bounce instead of hard flip to avoid edge clustering
        if (p.x < 0) { p.x = 0; p.vx = Math.abs(p.vx) * 0.7; }
        if (p.x > canvas.width) { p.x = canvas.width; p.vx = -Math.abs(p.vx) * 0.7; }
        if (p.y < 0) { p.y = 0; p.vy = Math.abs(p.vy) * 0.7; }
        if (p.y > canvas.height) { p.y = canvas.height; p.vy = -Math.abs(p.vy) * 0.7; }

        // Enlarge particles near cursor
        const proximity = Math.max(0, 1 - dist / REPEL_RADIUS);
        p.r = p.baseR + proximity * p.baseR * 1.6;
      }

      // Draw connection lines
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const pi = particles[i];
          const pj = particles[j];
          const dx = pi.x - pj.x;
          const dy = pi.y - pj.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < CONNECTION_DIST) {
            // Lines near cursor glow brighter
            const cursorBoost = Math.max(
              Math.max(0, 1 - Math.hypot(pi.x - mx, pi.y - my) / ATTRACT_RADIUS),
              Math.max(0, 1 - Math.hypot(pj.x - mx, pj.y - my) / ATTRACT_RADIUS)
            );
            const baseOpacity = 0.12 * (1 - dist / CONNECTION_DIST);
            const opacity = Math.min(0.65, baseOpacity + cursorBoost * 0.45);
            ctx.beginPath();
            ctx.moveTo(pi.x, pi.y);
            ctx.lineTo(pj.x, pj.y);
            ctx.strokeStyle = `rgba(99,102,241,${opacity})`;
            ctx.lineWidth = 0.6 + cursorBoost * 0.8;
            ctx.stroke();
          }
        }
      }

      // Draw particles
      for (const p of particles) {
        const distToCursor = Math.hypot(p.x - mx, p.y - my);
        const nearCursor = Math.max(0, 1 - distToCursor / REPEL_RADIUS);

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = p.color + Math.round(Math.min(1, p.alpha + nearCursor * 0.4) * 255).toString(16).padStart(2, "0");
        ctx.fill();

        // Glow halo for particles closest to cursor
        if (nearCursor > 0.3) {
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.r * 2.5, 0, Math.PI * 2);
          ctx.fillStyle = p.color + Math.round(nearCursor * 0.3 * 255).toString(16).padStart(2, "0");
          ctx.fill();
        }
      }

      animId = requestAnimationFrame(draw);
    };
    draw();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", resize);
      window.removeEventListener("mouseup", onMouseUp);
      section.removeEventListener("mousemove", onMouseMove);
      section.removeEventListener("mouseleave", onMouseLeave);
      section.removeEventListener("mousedown", onMouseDown);
      section.removeEventListener("touchmove", onTouchMove);
      section.removeEventListener("touchend", onTouchEnd);
    };
  }, []);

  return (
    <section
      id="hero"
      ref={sectionRef}
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
        cursor: "crosshair",
      }}
      className="grid-bg"
    >
      {/* Interactive particle canvas */}
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
