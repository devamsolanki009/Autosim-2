"use client";

import { useEffect, useRef, useState } from "react";

// Mock data generator for demo visualization
function generateMockData(method: string, tEnd: number) {
  const t = Array.from({ length: 300 }, (_, i) => (i / 299) * tEnd);

  let x: number[];
  let dxdt: number[];

  const methodSeed: Record<string, [number, number, number]> = {
    symbolic:  [1, 0.1, 1],
    laplace:   [1, 0.1, 1],
    rk45:      [1, 0.1, 1.01],
    radau:     [1, 0.1, 0.99],
    euler_fwd: [1, 0.12, 1],
    euler_imp: [1, 0.11, 1],
    compare:   [1, 0.1, 1],
  };

  const [A, zeta, omega] = methodSeed[method] ?? [1, 0.1, 1];

  x = t.map(
    (ti) =>
      A * Math.exp(-zeta * omega * ti) *
      (Math.cos(Math.sqrt(Math.max(0, 1 - zeta * zeta)) * omega * ti) +
        0.3 * Math.sin(ti * 0.7))
  );
  dxdt = t.map((ti, i) => {
    if (i === 0) return 0;
    return (x[i] - x[i - 1]) / (t[i] - t[i - 1]);
  });

  return { t, x, dxdt };
}

const METHOD_COLORS: Record<string, string> = {
  symbolic:  "#a78bfa",
  laplace:   "#60a5fa",
  rk45:      "#34d399",
  radau:     "#fbbf24",
  euler_fwd: "#f87171",
  euler_imp: "#f472b6",
  compare:   "#22d3ee",
};

interface PlotlyPanelProps {
  method: string;
  equation: string;
  tEnd: number;
  solved: boolean;
}

export default function PlotlyPanel({ method, equation, tEnd, solved }: PlotlyPanelProps) {
  const timeCanvasRef = useRef<HTMLCanvasElement>(null);
  const phaseCanvasRef = useRef<HTMLCanvasElement>(null);
  const [activeView, setActiveView] = useState<"time" | "phase" | "both">("both");

  useEffect(() => {
    if (!solved) return;

    const { t, x, dxdt } = generateMockData(method, tEnd);
    const color = METHOD_COLORS[method] ?? "#a78bfa";

    // Draw time series
    const drawTimeSeries = () => {
      const canvas = timeCanvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      canvas.width = canvas.offsetWidth * window.devicePixelRatio;
      canvas.height = canvas.offsetHeight * window.devicePixelRatio;
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

      const W = canvas.offsetWidth;
      const H = canvas.offsetHeight;
      const pad = { top: 20, bottom: 40, left: 50, right: 20 };
      const pw = W - pad.left - pad.right;
      const ph = H - pad.top - pad.bottom;

      // Background
      ctx.fillStyle = "rgba(3,7,18,0.0)";
      ctx.fillRect(0, 0, W, H);

      // Grid lines
      ctx.strokeStyle = "rgba(99,102,241,0.08)";
      ctx.lineWidth = 1;
      for (let i = 0; i <= 8; i++) {
        const gx = pad.left + (pw / 8) * i;
        ctx.beginPath();
        ctx.moveTo(gx, pad.top);
        ctx.lineTo(gx, pad.top + ph);
        ctx.stroke();
      }
      for (let i = 0; i <= 5; i++) {
        const gy = pad.top + (ph / 5) * i;
        ctx.beginPath();
        ctx.moveTo(pad.left, gy);
        ctx.lineTo(pad.left + pw, gy);
        ctx.stroke();
      }

      // Axes
      ctx.strokeStyle = "rgba(148,163,184,0.3)";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(pad.left, pad.top);
      ctx.lineTo(pad.left, pad.top + ph);
      ctx.lineTo(pad.left + pw, pad.top + ph);
      ctx.stroke();

      const xMin = Math.min(...t);
      const xMax = Math.max(...t);
      const yMin = Math.min(...x);
      const yMax = Math.max(...x);
      const yRange = yMax - yMin || 1;

      const toCanvasX = (v: number) => pad.left + ((v - xMin) / (xMax - xMin)) * pw;
      const toCanvasY = (v: number) => pad.top + ph - ((v - yMin) / yRange) * ph;

      // Zero line
      if (yMin < 0 && yMax > 0) {
        ctx.strokeStyle = "rgba(148,163,184,0.15)";
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 4]);
        const zy = toCanvasY(0);
        ctx.beginPath();
        ctx.moveTo(pad.left, zy);
        ctx.lineTo(pad.left + pw, zy);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      // Glow effect under curve
      const gradient = ctx.createLinearGradient(0, pad.top, 0, pad.top + ph);
      gradient.addColorStop(0, color + "33");
      gradient.addColorStop(1, color + "00");
      ctx.beginPath();
      ctx.moveTo(toCanvasX(t[0]), pad.top + ph);
      for (let i = 0; i < t.length; i++) {
        ctx.lineTo(toCanvasX(t[i]), toCanvasY(x[i]));
      }
      ctx.lineTo(toCanvasX(t[t.length - 1]), pad.top + ph);
      ctx.closePath();
      ctx.fillStyle = gradient;
      ctx.fill();

      // Main curve
      ctx.beginPath();
      ctx.moveTo(toCanvasX(t[0]), toCanvasY(x[0]));
      for (let i = 1; i < t.length; i++) {
        ctx.lineTo(toCanvasX(t[i]), toCanvasY(x[i]));
      }
      ctx.strokeStyle = color;
      ctx.lineWidth = 2.5;
      ctx.shadowBlur = 12;
      ctx.shadowColor = color;
      ctx.stroke();
      ctx.shadowBlur = 0;

      // Axis labels
      ctx.fillStyle = "rgba(148,163,184,0.7)";
      ctx.font = "11px JetBrains Mono, monospace";
      ctx.textAlign = "center";
      ctx.fillText("t", pad.left + pw / 2, H - 6);
      ctx.save();
      ctx.translate(12, pad.top + ph / 2);
      ctx.rotate(-Math.PI / 2);
      ctx.fillText("x(t)", 0, 0);
      ctx.restore();

      // X-axis ticks
      for (let i = 0; i <= 5; i++) {
        const tv = xMin + (i / 5) * (xMax - xMin);
        ctx.fillText(tv.toFixed(0), toCanvasX(tv), pad.top + ph + 16);
      }
    };

    // Draw phase portrait
    const drawPhasePortrait = () => {
      const canvas = phaseCanvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      canvas.width = canvas.offsetWidth * window.devicePixelRatio;
      canvas.height = canvas.offsetHeight * window.devicePixelRatio;
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

      const W = canvas.offsetWidth;
      const H = canvas.offsetHeight;
      const pad = { top: 20, bottom: 40, left: 50, right: 20 };
      const pw = W - pad.left - pad.right;
      const ph = H - pad.top - pad.bottom;

      ctx.fillStyle = "rgba(3,7,18,0.0)";
      ctx.fillRect(0, 0, W, H);

      // Grid
      ctx.strokeStyle = "rgba(99,102,241,0.08)";
      ctx.lineWidth = 1;
      for (let i = 0; i <= 6; i++) {
        ctx.beginPath();
        ctx.moveTo(pad.left + (pw / 6) * i, pad.top);
        ctx.lineTo(pad.left + (pw / 6) * i, pad.top + ph);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(pad.left, pad.top + (ph / 6) * i);
        ctx.lineTo(pad.left + pw, pad.top + (ph / 6) * i);
        ctx.stroke();
      }

      // Axes
      ctx.strokeStyle = "rgba(148,163,184,0.3)";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(pad.left, pad.top);
      ctx.lineTo(pad.left, pad.top + ph);
      ctx.lineTo(pad.left + pw, pad.top + ph);
      ctx.stroke();

      const xArr = x;
      const yArr = dxdt;
      const xMin = Math.min(...xArr);
      const xMax = Math.max(...xArr);
      const yMin = Math.min(...yArr);
      const yMax = Math.max(...yArr);

      const toX = (v: number) => pad.left + ((v - xMin) / (xMax - xMin || 1)) * pw;
      const toY = (v: number) => pad.top + ph - ((v - yMin) / (yMax - yMin || 1)) * ph;

      // Gradient path
      ctx.beginPath();
      ctx.moveTo(toX(xArr[0]), toY(yArr[0]));
      for (let i = 1; i < xArr.length; i++) {
        ctx.lineTo(toX(xArr[i]), toY(yArr[i]));
      }
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.shadowBlur = 10;
      ctx.shadowColor = color;
      ctx.stroke();
      ctx.shadowBlur = 0;

      // Arrow at tail
      const li = xArr.length - 1;
      const lx = toX(xArr[li]);
      const ly = toY(yArr[li]);
      const px2 = toX(xArr[li - 5]);
      const py2 = toY(yArr[li - 5]);
      const angle = Math.atan2(ly - py2, lx - px2);
      ctx.save();
      ctx.translate(lx, ly);
      ctx.rotate(angle);
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.lineTo(-9, -4);
      ctx.lineTo(-9, 4);
      ctx.closePath();
      ctx.fill();
      ctx.restore();

      // Labels
      ctx.fillStyle = "rgba(148,163,184,0.7)";
      ctx.font = "11px JetBrains Mono, monospace";
      ctx.textAlign = "center";
      ctx.fillText("x", pad.left + pw / 2, H - 6);
      ctx.save();
      ctx.translate(12, pad.top + ph / 2);
      ctx.rotate(-Math.PI / 2);
      ctx.fillText("x'", 0, 0);
      ctx.restore();
    };

    drawTimeSeries();
    drawPhasePortrait();
  }, [solved, method, tEnd]);

  const color = METHOD_COLORS[method] ?? "#a78bfa";

  return (
    <section
      id="visualization"
      style={{
        padding: "0 24px 80px",
        maxWidth: 1400,
        margin: "0 auto",
      }}
    >
      {/* Section header */}
      <div style={{ marginBottom: 28 }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            marginBottom: 8,
          }}
        >
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "0.75rem",
              color: "var(--neon-cyan)",
              letterSpacing: "2px",
              textTransform: "uppercase",
            }}
          >
            02 — Visualization Panel
          </span>
        </div>
        <h2
          style={{
            fontSize: "clamp(1.6rem, 3vw, 2.2rem)",
            fontWeight: 700,
            letterSpacing: "-0.02em",
            marginBottom: 8,
          }}
        >
          Solution Graphs
        </h2>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem" }}>
          Interactive time-series and phase-portrait visualization of the ODE solution.
        </p>
      </div>

      <div className="glass-card" style={{ padding: "28px" }}>
        {/* Toolbar */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: 20,
            flexWrap: "wrap",
            gap: 12,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: "50%",
                background: color,
                boxShadow: `0 0 12px ${color}`,
              }}
            />
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.85rem", color: "var(--text-secondary)" }}>
              {solved ? equation : "No solution yet"}
            </span>
          </div>
          <div style={{ display: "flex", gap: 6 }}>
            {(["time", "phase", "both"] as const).map((v) => (
              <button
                key={v}
                className={`tab-btn ${activeView === v ? "active" : ""}`}
                onClick={() => setActiveView(v)}
                style={{ fontSize: "0.78rem", padding: "6px 14px" }}
              >
                {v === "time" ? "x(t) Series" : v === "phase" ? "Phase Portrait" : "Both"}
              </button>
            ))}
          </div>
        </div>

        {!solved ? (
          <div
            style={{
              height: 320,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: 16,
            }}
          >
            {/* Idle placeholder */}
            <div
              style={{
                width: 64,
                height: 64,
                borderRadius: "50%",
                background: "rgba(99,102,241,0.08)",
                border: "1px solid rgba(99,102,241,0.2)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "1.8rem",
              }}
            >
              📊
            </div>
            <div style={{ textAlign: "center" }}>
              <p style={{ fontSize: "0.95rem", color: "var(--text-secondary)", marginBottom: 4 }}>
                No solution yet
              </p>
              <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                Configure the equation above and click{" "}
                <strong style={{ color: "var(--neon-purple)" }}>Solve ODE</strong>
              </p>
            </div>
          </div>
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                activeView === "both"
                  ? "1fr 1fr"
                  : "1fr",
              gap: 20,
            }}
          >
            {(activeView === "time" || activeView === "both") && (
              <div>
                <div
                  style={{
                    fontSize: "0.78rem",
                    fontFamily: "var(--font-mono)",
                    color: "var(--text-muted)",
                    textTransform: "uppercase",
                    letterSpacing: "1px",
                    marginBottom: 8,
                  }}
                >
                  x(t) vs. Time
                </div>
                <div
                  style={{
                    borderRadius: 12,
                    background: "rgba(3,7,18,0.5)",
                    border: "1px solid rgba(99,102,241,0.12)",
                    overflow: "hidden",
                    height: 280,
                  }}
                >
                  <canvas
                    ref={timeCanvasRef}
                    style={{ width: "100%", height: "100%" }}
                  />
                </div>
              </div>
            )}
            {(activeView === "phase" || activeView === "both") && (
              <div>
                <div
                  style={{
                    fontSize: "0.78rem",
                    fontFamily: "var(--font-mono)",
                    color: "var(--text-muted)",
                    textTransform: "uppercase",
                    letterSpacing: "1px",
                    marginBottom: 8,
                  }}
                >
                  Phase Portrait (x vs. x&apos;)
                </div>
                <div
                  style={{
                    borderRadius: 12,
                    background: "rgba(3,7,18,0.5)",
                    border: "1px solid rgba(99,102,241,0.12)",
                    overflow: "hidden",
                    height: 280,
                  }}
                >
                  <canvas
                    ref={phaseCanvasRef}
                    style={{ width: "100%", height: "100%" }}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Stats row */}
        {solved && (
          <div
            style={{
              marginTop: 20,
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
              gap: 12,
            }}
          >
            {[
              { label: "Method", value: method.toUpperCase(), color: "var(--neon-purple)" },
              { label: "Time Points", value: "300", color: "var(--neon-cyan)" },
              { label: "t Range", value: `[0, ${tEnd}]`, color: "var(--neon-green)" },
              { label: "State Dim", value: "2", color: "var(--neon-yellow)" },
            ].map((s) => (
              <div key={s.label} className="stat-card">
                <div
                  style={{
                    fontSize: "0.68rem",
                    color: "var(--text-muted)",
                    fontFamily: "var(--font-mono)",
                    textTransform: "uppercase",
                    letterSpacing: "1px",
                    marginBottom: 4,
                  }}
                >
                  {s.label}
                </div>
                <div
                  style={{
                    fontSize: "1rem",
                    fontWeight: 700,
                    fontFamily: "var(--font-mono)",
                    color: s.color,
                  }}
                >
                  {s.value}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
