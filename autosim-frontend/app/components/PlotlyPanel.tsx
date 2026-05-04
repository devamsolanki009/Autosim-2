"use client";

import { useMemo, useState } from "react";
import type { Data } from "plotly.js";
import InteractivePlot from "./InteractivePlot";

// Mock data generator for demo visualization
function generateMockData(method: string, tEnd: number) {
  const t = Array.from({ length: 300 }, (_, i) => (i / 299) * tEnd);

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

  const x = t.map(
    (ti) =>
      A * Math.exp(-zeta * omega * ti) *
      (Math.cos(Math.sqrt(Math.max(0, 1 - zeta * zeta)) * omega * ti) +
        0.3 * Math.sin(ti * 0.7))
  );
  const dxdt = t.map((ti, i) => {
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
  solveResult?: { t: number[]; y: number[][] } | null;
}

export default function PlotlyPanel({ method, equation, tEnd, solved, solveResult }: PlotlyPanelProps) {
  const [activeView, setActiveView] = useState<"time" | "phase" | "both">("both");

  const color = METHOD_COLORS[method] ?? "#a78bfa";

  const { t, x, dxdt } = useMemo(() => {
    if (!solved) return { t: [], x: [], dxdt: [] };
    if (solveResult && solveResult.t.length > 0) {
      const tArr = solveResult.t;
      const xArr = solveResult.y[0];
      const dArr = solveResult.y.length > 1
        ? solveResult.y[1]
        : tArr.map((_, i) => i === 0 ? 0 : (xArr[i] - xArr[i - 1]) / (tArr[i] - tArr[i - 1]));
      return { t: tArr, x: xArr, dxdt: dArr };
    }
    return generateMockData(method, tEnd);
  }, [solved, method, tEnd, solveResult]);

  // Time series trace
  const timeTraces: Data[] = useMemo(() => [
    {
      x: t,
      y: x,
      type: "scatter",
      mode: "lines",
      name: "x(t)",
      line: { color, width: 2.5, shape: "spline" },
      fill: "tozeroy",
      fillcolor: color + "18",
      hovertemplate: "t = %{x:.4f}<br>x = %{y:.6f}<extra></extra>",
    },
  ], [t, x, color]);

  // Phase portrait trace
  const phaseTraces: Data[] = useMemo(() => {
    const traces: Data[] = [
      {
        x,
        y: dxdt,
        type: "scatter",
        mode: "lines",
        name: "Phase",
        line: { color, width: 2, shape: "spline" },
        hovertemplate: "x = %{x:.4f}<br>x′ = %{y:.4f}<extra></extra>",
      },
    ];
    // Arrow marker at end of trajectory
    if (x.length > 5) {
      traces.push({
        x: [x[x.length - 1]],
        y: [dxdt[dxdt.length - 1]],
        type: "scatter",
        mode: "markers",
        name: "End",
        marker: { color, size: 10, symbol: "triangle-right" },
        hoverinfo: "skip",
        showlegend: false,
      } as Data);
    }
    return traces;
  }, [x, dxdt, color]);

  return (
    <section
      id="visualization"
      style={{ padding: "0 24px 80px", maxWidth: 1400, margin: "0 auto" }}
    >
      {/* Section header */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--neon-cyan)", letterSpacing: "2px", textTransform: "uppercase" }}>
            02 — Visualization Panel
          </span>
        </div>
        <h2 style={{ fontSize: "clamp(1.6rem, 3vw, 2.2rem)", fontWeight: 700, letterSpacing: "-0.02em", marginBottom: 8 }}>
          Solution Graphs
        </h2>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem" }}>
          Interactive time-series and phase-portrait visualization of the ODE solution.
        </p>
      </div>

      <div className="glass-card" style={{ padding: "28px" }}>
        {/* Toolbar */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20, flexWrap: "wrap", gap: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 12, height: 12, borderRadius: "50%", background: color, boxShadow: `0 0 12px ${color}` }} />
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
          <div style={{ height: 320, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 16 }}>
            <div style={{ width: 64, height: 64, borderRadius: "50%", background: "rgba(99,102,241,0.08)", border: "1px solid rgba(99,102,241,0.2)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.8rem" }}>
              📊
            </div>
            <div style={{ textAlign: "center" }}>
              <p style={{ fontSize: "0.95rem", color: "var(--text-secondary)", marginBottom: 4 }}>No solution yet</p>
              <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                Configure the equation above and click{" "}
                <strong style={{ color: "var(--neon-purple)" }}>Solve ODE</strong>
              </p>
            </div>
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: activeView === "both" ? "1fr 1fr" : "1fr", gap: 20 }}>
            {(activeView === "time" || activeView === "both") && (
              <div>
                <div style={{ fontSize: "0.78rem", fontFamily: "var(--font-mono)", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: 8 }}>
                  x(t) vs. Time
                </div>
                <InteractivePlot
                  data={timeTraces}
                  layout={{
                    xaxis: { title: { text: "t", font: { size: 11 } } },
                    yaxis: { title: { text: "x(t)", font: { size: 11 } } },
                    showlegend: false,
                  }}
                  height={280}
                />
              </div>
            )}
            {(activeView === "phase" || activeView === "both") && (
              <div>
                <div style={{ fontSize: "0.78rem", fontFamily: "var(--font-mono)", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: 8 }}>
                  Phase Portrait (x vs. x&apos;)
                </div>
                <InteractivePlot
                  data={phaseTraces}
                  layout={{
                    xaxis: { title: { text: "x", font: { size: 11 } } },
                    yaxis: { title: { text: "x′", font: { size: 11 } } },
                    showlegend: false,
                  }}
                  height={280}
                />
              </div>
            )}
          </div>
        )}

        {/* Stats row */}
        {solved && (
          <div style={{ marginTop: 20, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: 12 }}>
            {[
              { label: "Method",      value: method.toUpperCase(),    color: "var(--neon-purple)" },
              { label: "Time Points", value: `${t.length}`,           color: "var(--neon-cyan)"   },
              { label: "t Range",     value: `[0, ${tEnd}]`,          color: "var(--neon-green)"  },
              { label: "State Dim",   value: "2",                     color: "var(--neon-yellow)" },
            ].map((s) => (
              <div key={s.label} className="stat-card">
                <div style={{ fontSize: "0.68rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: 4 }}>
                  {s.label}
                </div>
                <div style={{ fontSize: "1rem", fontWeight: 700, fontFamily: "var(--font-mono)", color: s.color }}>
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
