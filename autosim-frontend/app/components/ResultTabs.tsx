"use client";

import { useState, useRef, useEffect } from "react";
import type { SolveResult, SolveStep, VerificationReport, VerificationSource } from "../page";

export interface SolverCodeResult {
  parsed: {
    natural_language: string;
    order: number;
    is_linear: boolean;
    is_stiff: boolean;
    is_homogeneous: boolean;
    n_vars: number;
    forcing_function: string | null;
    nonlinear_terms: string[];
    has_pde: boolean;
  };
  solver_code: string;
  method_chosen: string;
  debug_notes: string[];
  issues_found: string[];
  is_valid: boolean;
  eval_code: string;
  full_code: string;
  refined_code: string | null;
}

interface ResultTabsProps {
  solved: boolean;
  method: string;
  equation: string;
  useLlm: boolean;
  solveResult?: SolveResult | null;
  verifReport?: VerificationReport | null;
  verifLoading?: boolean;
  codeResult?: SolverCodeResult | null;
  codeLoading?: boolean;
}


const LLM_INSIGHT = `This ODE describes a **damped harmonic oscillator** subjected to a **periodic forcing function** cos(t). 

The system exhibits **underdamped behavior** (ζ ≈ 0.1 < 1), meaning the oscillations will persist while exponentially decaying toward a steady-state driven by the forcing term. 

**Physical Analogy**: This models a spring-mass system with light friction, being continuously pushed by a cosine-wave force — like a lightly-damped pendulum driven by a periodic external push.

**Key Observations**:
- The natural frequency ω₀ = 1 rad/s is close to the forcing frequency (1 rad/s), creating near-resonance conditions
- The transient response (free oscillation) decays exponentially with time constant τ = 1/(ζω₀) = 10 seconds
- The steady-state response is a sustained oscillation in phase with the forcing function
- The system will reach steady-state approximately after t ≈ 5τ = 50 seconds`;

// ─── Verification sub-components ──────────────────────────────────────────────

function VerifSkeleton() {
  return (
    <div style={{ marginTop: 32 }}>
      <div className="neon-divider" style={{ marginBottom: 28 }} />
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
        <div style={{ width: 180, height: 22, borderRadius: 6, background: "rgba(99,102,241,0.15)", animation: "verifPulse 1.4s ease-in-out infinite" }} />
      </div>
      {[1, 2, 3].map((i) => (
        <div key={i} style={{ marginBottom: 12, padding: "16px 18px", borderRadius: 12, border: "1px solid rgba(99,102,241,0.1)", background: "rgba(15,23,42,0.5)" }}>
          <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
            <div style={{ width: 20, height: 20, borderRadius: "50%", background: "rgba(99,102,241,0.15)", animation: "verifPulse 1.4s ease-in-out infinite", animationDelay: `${i * 0.15}s` }} />
            <div style={{ width: `${120 + i * 40}px`, height: 14, borderRadius: 4, background: "rgba(99,102,241,0.12)", animation: "verifPulse 1.4s ease-in-out infinite", animationDelay: `${i * 0.15}s` }} />
          </div>
        </div>
      ))}
      <style>{`@keyframes verifPulse { 0%,100%{opacity:1} 50%{opacity:0.35} }`}</style>
    </div>
  );
}

function statusIcon(s: string) {
  if (s === "pass")  return "✅";
  if (s === "fail")  return "❌";
  if (s === "skip")  return "⏭️";
  return "⚠️";
}

function fmtNum(v: number | null | undefined): string {
  if (v == null) return "—";
  if (Math.abs(v) < 1e-3 || Math.abs(v) > 1e4) return v.toExponential(3);
  return v.toPrecision(4);
}

// Canvas overlay chart (solution blue, reference red-dashed)
function OverlayChart({ refT, refY, solveResult }: { refT: number[]; refY: number[]; solveResult?: SolveResult | null }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !refT.length) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    canvas.width = canvas.offsetWidth * window.devicePixelRatio;
    canvas.height = canvas.offsetHeight * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    const W = canvas.offsetWidth, H = canvas.offsetHeight;
    const pad = { top: 12, bottom: 28, left: 40, right: 12 };
    const pw = W - pad.left - pad.right, ph = H - pad.top - pad.bottom;
    ctx.clearRect(0, 0, W, H);
    // grid
    ctx.strokeStyle = "rgba(99,102,241,0.08)";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      ctx.beginPath(); ctx.moveTo(pad.left, pad.top + (ph / 4) * i); ctx.lineTo(pad.left + pw, pad.top + (ph / 4) * i); ctx.stroke();
    }
    const userT = solveResult?.t ?? refT;
    const userX = solveResult?.y?.[0] ?? refY;
    const allY = [...refY, ...userX];
    const tMin = refT[0], tMax = refT[refT.length - 1];
    const yMin = Math.min(...allY), yMax = Math.max(...allY);
    const yRange = yMax - yMin || 1;
    const tx = (v: number) => pad.left + ((v - tMin) / (tMax - tMin || 1)) * pw;
    const ty = (v: number) => pad.top + ph - ((v - yMin) / yRange) * ph;
    // user solution — blue
    if (userT.length > 1) {
      ctx.beginPath();
      ctx.moveTo(tx(userT[0]), ty(userX[0]));
      for (let i = 1; i < userT.length; i++) ctx.lineTo(tx(userT[i]), ty(userX[i]));
      ctx.strokeStyle = "#2563eb"; ctx.lineWidth = 2; ctx.shadowBlur = 6; ctx.shadowColor = "#2563eb"; ctx.stroke(); ctx.shadowBlur = 0;
    }
    // reference — red dashed
    ctx.setLineDash([5, 4]);
    ctx.beginPath();
    ctx.moveTo(tx(refT[0]), ty(refY[0]));
    for (let i = 1; i < refT.length; i++) ctx.lineTo(tx(refT[i]), ty(refY[i]));
    ctx.strokeStyle = "#dc2626"; ctx.lineWidth = 1.5; ctx.stroke();
    ctx.setLineDash([]);
    // labels
    ctx.fillStyle = "rgba(148,163,184,0.6)"; ctx.font = "10px JetBrains Mono, monospace"; ctx.textAlign = "center";
    ctx.fillText("t", pad.left + pw / 2, H - 4);
  }, [refT, refY, solveResult]);
  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ display: "flex", gap: 14, marginBottom: 6, fontSize: "0.7rem", fontFamily: "var(--font-mono)" }}>
        <span style={{ color: "#60a5fa" }}>── Your solution</span>
        <span style={{ color: "#f87171" }}>- - Reference</span>
      </div>
      <div style={{ borderRadius: 8, border: "1px solid rgba(99,102,241,0.15)", background: "rgba(3,7,18,0.6)", height: 130, overflow: "hidden" }}>
        <canvas ref={canvasRef} style={{ width: "100%", height: "100%" }} />
      </div>
    </div>
  );
}

// Canvas energy chart
function EnergyChart({ refT, refY, e0 }: { refT: number[]; refY: number[]; e0?: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !refT.length) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    canvas.width = canvas.offsetWidth * window.devicePixelRatio;
    canvas.height = canvas.offsetHeight * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    const W = canvas.offsetWidth, H = canvas.offsetHeight;
    const pad = { top: 12, bottom: 28, left: 44, right: 12 };
    const pw = W - pad.left - pad.right, ph = H - pad.top - pad.bottom;
    ctx.clearRect(0, 0, W, H);
    ctx.strokeStyle = "rgba(99,102,241,0.08)"; ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) { ctx.beginPath(); ctx.moveTo(pad.left, pad.top + (ph / 4) * i); ctx.lineTo(pad.left + pw, pad.top + (ph / 4) * i); ctx.stroke(); }
    const tMin = refT[0], tMax = refT[refT.length - 1];
    const yMin = Math.min(...refY), yMax = Math.max(...refY);
    const yRange = yMax - yMin || 1;
    const tx = (v: number) => pad.left + ((v - tMin) / (tMax - tMin || 1)) * pw;
    const ty = (v: number) => pad.top + ph - ((v - yMin) / yRange) * ph;
    // E(t) line
    ctx.beginPath();
    ctx.moveTo(tx(refT[0]), ty(refY[0]));
    for (let i = 1; i < refT.length; i++) ctx.lineTo(tx(refT[i]), ty(refY[i]));
    ctx.strokeStyle = "#00ff88"; ctx.lineWidth = 2; ctx.shadowBlur = 6; ctx.shadowColor = "#00ff88"; ctx.stroke(); ctx.shadowBlur = 0;
    // E(0) dashed line
    if (e0 != null) {
      const e0y = ty(e0);
      ctx.setLineDash([6, 4]);
      ctx.beginPath(); ctx.moveTo(pad.left, e0y); ctx.lineTo(pad.left + pw, e0y);
      ctx.strokeStyle = "rgba(251,191,36,0.7)"; ctx.lineWidth = 1.5; ctx.stroke();
      ctx.setLineDash([]);
    }
    ctx.fillStyle = "rgba(148,163,184,0.6)"; ctx.font = "10px JetBrains Mono, monospace"; ctx.textAlign = "center";
    ctx.fillText("t", pad.left + pw / 2, H - 4);
  }, [refT, refY, e0]);
  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ display: "flex", gap: 14, marginBottom: 6, fontSize: "0.7rem", fontFamily: "var(--font-mono)" }}>
        <span style={{ color: "#00ff88" }}>── E(t)</span>
        <span style={{ color: "#fbbf24" }}>- - E(0)</span>
      </div>
      <div style={{ borderRadius: 8, border: "1px solid rgba(99,102,241,0.15)", background: "rgba(3,7,18,0.6)", height: 130, overflow: "hidden" }}>
        <canvas ref={canvasRef} style={{ width: "100%", height: "100%" }} />
      </div>
    </div>
  );
}

function SourceCard({ src, solveResult }: { src: VerificationSource; solveResult?: SolveResult | null }) {
  const [expanded, setExpanded] = useState(src.status === "fail");
  const icon = statusIcon(src.status);
  const isEnergy = src.name.toLowerCase().includes("energy");

  const borderColor = src.status === "pass" ? "rgba(52,211,153,0.25)"
    : src.status === "fail" ? "rgba(220,38,38,0.3)"
    : src.status === "skip" ? "rgba(99,102,241,0.15)"
    : "rgba(251,191,36,0.25)";

  const bgColor = src.status === "pass" ? "rgba(52,211,153,0.04)"
    : src.status === "fail" ? "rgba(220,38,38,0.05)"
    : "rgba(15,23,42,0.5)";

  const metrics: { label: string; value: string; color: string }[] = [
    {
      label: "Result",
      value: src.status === "pass" ? "PASS" : src.status === "fail" ? "FAIL" : src.status.toUpperCase(),
      color: src.status === "pass" ? "var(--neon-green)" : src.status === "fail" ? "#f87171" : "var(--text-muted)",
    },
    { label: "Max Error",  value: fmtNum(src.max_error),                                                   color: "var(--neon-cyan)"   },
    { label: "Confidence", value: src.confidence != null ? `${src.confidence.toFixed(1)}%` : "—",          color: "var(--neon-purple)" },
  ];

  return (
    <div style={{ marginBottom: 10, borderRadius: 12, border: `1px solid ${borderColor}`, background: bgColor, overflow: "hidden" }}>
      <button
        onClick={() => setExpanded((v) => !v)}
        style={{ width: "100%", display: "flex", alignItems: "center", gap: 10, padding: "13px 16px", background: "transparent", border: "none", cursor: "pointer", textAlign: "left" }}
      >
        <span style={{ fontSize: "1rem", flexShrink: 0 }}>{icon}</span>
        <span style={{ fontWeight: 600, fontSize: "0.88rem", color: "var(--text-primary)", flex: 1 }}>{src.name}</span>
        <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)", marginRight: 4 }}>
          {src.status.toUpperCase()}
        </span>
        <span style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>{expanded ? "▲" : "▼"}</span>
      </button>

      {expanded && (
        <div style={{ padding: "0 16px 16px" }}>
          {/* Message */}
          <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginBottom: 14, lineHeight: 1.6, fontFamily: "var(--font-mono)" }}>
            {src.message}
          </p>

          {/* 3-column metrics — inlined to avoid IIFE ReactNode inference issue */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, marginBottom: 14 }}>
            {metrics.map((m) => (
              <div key={m.label} style={{ padding: "10px 12px", borderRadius: 8, background: "rgba(15,23,42,0.7)", border: "1px solid rgba(99,102,241,0.12)", textAlign: "center" }}>
                <div style={{ fontSize: "0.62rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: 4 }}>{m.label}</div>
                <div style={{ fontSize: "0.9rem", fontWeight: 700, fontFamily: "var(--font-mono)", color: m.color }}>{m.value}</div>
              </div>
            ))}
          </div>

          {/* Formula */}
          {src.details?.formula && (
            <div style={{ marginBottom: 12, padding: "10px 14px", borderRadius: 8, background: "rgba(34,211,238,0.05)", border: "1px solid rgba(34,211,238,0.15)", fontFamily: "var(--font-mono)", fontSize: "0.82rem", color: "var(--neon-cyan)", overflowX: "auto", whiteSpace: "nowrap" }}>
              {String(src.details.formula)}
            </div>
          )}

          {/* Comparison table */}
          {src.details?.comparison_table && Array.isArray(src.details.comparison_table) && (
            <div style={{ overflowX: "auto", marginBottom: 12 }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: "var(--font-mono)", fontSize: "0.75rem" }}>
                <thead>
                  <tr>
                    {Object.keys((src.details.comparison_table as Record<string, unknown>[])[0] ?? {}).map((k) => (
                      <th key={k} style={{ padding: "6px 10px", textAlign: "left", borderBottom: "1px solid var(--border)", color: "var(--text-muted)", textTransform: "uppercase", fontSize: "0.65rem", letterSpacing: "1px" }}>{k}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(src.details.comparison_table as Record<string, unknown>[]).map((row, i) => (
                    <tr key={i} style={{ borderBottom: "1px solid rgba(99,102,241,0.06)", background: i % 2 === 0 ? "transparent" : "rgba(99,102,241,0.03)" }}>
                      {Object.entries(row).map(([k, v]) => (
                        <td key={k} style={{ padding: "6px 10px", color: typeof v === "number" ? "var(--neon-cyan)" : "var(--text-secondary)" }}>
                          {typeof v === "number" ? v.toExponential(3) : String(v)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Chart */}
          {src.reference_t && src.reference_y && (
            isEnergy
              ? <EnergyChart refT={src.reference_t} refY={src.reference_y} e0={src.details?.E0 as number | undefined} />
              : <OverlayChart refT={src.reference_t} refY={src.reference_y} solveResult={solveResult} />
          )}
        </div>
      )}
    </div>
  );
}

const VERDICT_STYLES: Record<string, { bg: string; color: string; icon: string; label: string }> = {
  verified: { bg: "#D1FAE5", color: "#065F46", icon: "✅", label: "VERIFIED" },
  warning:  { bg: "#FEF3C7", color: "#92400E", icon: "⚠️", label: "WARNING"  },
  failed:   { bg: "#FEE2E2", color: "#991B1B", icon: "❌", label: "FAILED"   },
  partial:  { bg: "#DBEAFE", color: "#1E40AF", icon: "ℹ️", label: "PARTIAL"  },
};

function VerificationSection({ report, loading, solveResult }: { report: VerificationReport | null | undefined; loading: boolean; solveResult?: SolveResult | null }) {
  if (!loading && !report) return null;

  return (
    <div style={{ marginTop: 32 }}>
      <div className="neon-divider" style={{ marginBottom: 28 }} />
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
        <span style={{ fontSize: "1rem" }}>🔬</span>
        <h3 style={{ fontSize: "1rem", fontWeight: 700, color: "#0088ff", margin: 0 }}>Solution Verification</h3>
        <span style={{ fontSize: "0.72rem", fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>6 independent checks</span>
      </div>

      {loading && <VerifSkeleton />}

      {!loading && report && (() => {
        const vs = VERDICT_STYLES[report.overall_status] ?? VERDICT_STYLES.partial;
        return (
          <>
            {/* Verdict Banner */}
            <div style={{ padding: "16px 20px", borderRadius: 14, background: vs.bg, marginBottom: 20, display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap" }}>
              <span style={{ fontSize: "1.5rem" }}>{vs.icon}</span>
              <div>
                <div style={{ fontWeight: 800, fontSize: "1rem", color: vs.color, fontFamily: "var(--font-mono)", letterSpacing: "1px" }}>{vs.label}</div>
                <div style={{ fontSize: "0.78rem", color: vs.color, opacity: 0.8, marginTop: 2 }}>{report.summary}</div>
              </div>
              <div style={{ marginLeft: "auto", textAlign: "right" }}>
                <div style={{ fontSize: "1.4rem", fontWeight: 800, fontFamily: "var(--font-mono)", color: vs.color }}>
                  {report.overall_confidence.toFixed(1)}%
                </div>
                <div style={{ fontSize: "0.7rem", color: vs.color, opacity: 0.7, fontFamily: "var(--font-mono)" }}>
                  confidence · {report.compute_ms.toFixed(0)} ms
                </div>
              </div>
            </div>

            {/* Per-source cards */}
            <div>
              {report.sources.map((src) => (
                <SourceCard key={src.name} src={src} solveResult={solveResult} />
              ))}
            </div>
          </>
        );
      })()}
    </div>
  );
}

// ─── Main component ────────────────────────────────────────────────────────────

export default function ResultTabs({ solved, method, equation, useLlm, solveResult, verifReport, verifLoading, codeResult, codeLoading }: ResultTabsProps) {
  const [activeTab, setActiveTab] = useState("solution");
  const [copied, setCopied] = useState(false);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const TABS = [
    { id: "solution", label: "📋 Solution",    color: "var(--neon-purple)" },
    { id: "graph",    label: "📈 Graph Info",  color: "var(--neon-cyan)"   },
    { id: "code",     label: "⚙️ Code",        color: "var(--neon-green)"  },
    { id: "llm",      label: "🤖 LLM Insight", color: "var(--neon-blue)"   },
    { id: "steps",    label: "🔢 Steps",       color: "var(--neon-yellow)" },
  ];

  // Derive stats from real solve result if available
  const stats = solveResult?.stats;
  const classification = solveResult?.classification as Record<string, unknown> | undefined;

  return (
    <section id="results" style={{ padding: "0 24px 80px", maxWidth: 1400, margin: "0 auto" }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--neon-yellow)", letterSpacing: "2px", textTransform: "uppercase", display: "block", marginBottom: 8 }}>
          03 — Analysis Results
        </span>
        <h2 style={{ fontSize: "clamp(1.6rem, 3vw, 2.2rem)", fontWeight: 700, letterSpacing: "-0.02em", marginBottom: 8 }}>
          Solution Explorer
        </h2>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem" }}>
          Detailed breakdown of your ODE solution across multiple analytical perspectives.
        </p>
      </div>

      <div className="glass-card" style={{ overflow: "hidden" }}>
        {/* Tab bar */}
        <div style={{ display: "flex", padding: "16px 20px 0", gap: 4, borderBottom: "1px solid var(--border)", overflowX: "auto" }}>
          {TABS.map((tab) => (
            <button
              key={tab.id}
              className={`tab-btn ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
              style={{ flexShrink: 0, borderRadius: "8px 8px 0 0", color: activeTab === tab.id ? tab.color : undefined, borderTopColor: activeTab === tab.id ? "rgba(124,58,237,0.35)" : "transparent", borderLeftColor: activeTab === tab.id ? "rgba(124,58,237,0.35)" : "transparent", borderRightColor: activeTab === tab.id ? "rgba(124,58,237,0.35)" : "transparent", borderBottomColor: "transparent", borderStyle: "solid" }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div style={{ padding: "28px 28px" }}>
          {!solved ? (
            <div style={{ textAlign: "center", padding: "60px 20px", color: "var(--text-muted)" }}>
              <div style={{ fontSize: "3rem", marginBottom: 16 }}>🔬</div>
              <p style={{ fontSize: "1rem", color: "var(--text-secondary)" }}>Solve an equation to see results here</p>
              <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginTop: 6 }}>Results will appear across all tabs after solving</p>
            </div>
          ) : (
            <>
              {/* SOLUTION TAB */}
              {activeTab === "solution" && (
                <div className="fade-in">
                  <div style={{ marginBottom: 24 }}>
                    <h3 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: 16, color: "var(--neon-purple)" }}>Equation Classification</h3>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12, marginBottom: 24 }}>
                      {[
                        { label: "Order",  value: classification?.order ? `${classification.order}${classification.order === 1 ? "st" : "nd"}` : "2nd", icon: "📐" },
                        { label: "Type",   value: classification?.linear === false ? "Nonlinear" : "Linear", icon: "🔢" },
                        { label: "Family", value: String(classification?.family ?? "Harmonic"), icon: "🏷️" },
                        { label: "Stiff",  value: classification?.stiff ? "Yes ⚠️" : "No ✓", icon: "⚡" },
                      ].map((item) => (
                        <div key={item.label} className="stat-card">
                          <div style={{ fontSize: "1.2rem", marginBottom: 4 }}>{item.icon}</div>
                          <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: 4 }}>{item.label}</div>
                          <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-primary)", fontFamily: "var(--font-mono)" }}>{item.value}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="neon-divider" style={{ marginBottom: 24 }} />

                  <h3 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: 16, color: "var(--neon-cyan)" }}>Solver Decision</h3>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 12, marginBottom: 24 }}>
                    <div style={{ padding: "16px", borderRadius: 12, background: "rgba(124,58,237,0.07)", border: "1px solid rgba(124,58,237,0.2)" }}>
                      <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: 6 }}>METHOD</div>
                      <div style={{ color: "var(--neon-purple)", fontWeight: 700 }}>{method.toUpperCase()}</div>
                      <div style={{ marginTop: 4, fontSize: "0.8rem", color: "var(--text-muted)" }}>
                        Compute time: <span style={{ color: "var(--neon-green)", fontFamily: "var(--font-mono)" }}>
                          {stats?.compute_ms != null ? `${stats.compute_ms.toFixed(1)} ms` : "—"}
                        </span>
                      </div>
                    </div>
                    <div style={{ padding: "16px", borderRadius: 12, background: "rgba(52,211,153,0.06)", border: "1px solid rgba(52,211,153,0.2)" }}>
                      <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: 6 }}>EQUATION FAMILY</div>
                      <div style={{ color: "var(--neon-green)", fontWeight: 700 }}>{String(classification?.family ?? "Harmonic Oscillator")}</div>
                      <div style={{ marginTop: 4, fontSize: "0.8rem", color: "var(--text-muted)" }}>
                        Stiffness: <span style={{ color: "var(--neon-green)" }}>{classification?.stiff ? "🔴 Detected" : "🟢 Not detected"}</span>
                      </div>
                    </div>
                  </div>

                  <div className="neon-divider" style={{ marginBottom: 24 }} />

                  <h3 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: 16, color: "var(--neon-green)" }}>Solution Statistics</h3>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 12 }}>
                    {[
                      { label: "x final", key: "x_final", color: "var(--neon-purple)" },
                      { label: "x max",   key: "x_max",   color: "var(--neon-cyan)"   },
                      { label: "x min",   key: "x_min",   color: "var(--neon-pink)"   },
                      { label: "x mean",  key: "x_mean",  color: "var(--neon-blue)"   },
                      { label: "Std dev", key: "x_std",   color: "var(--neon-yellow)" },
                    ].map((s) => (
                      <div key={s.label} className="stat-card">
                        <div style={{ fontSize: "0.68rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: 4 }}>{s.label}</div>
                        <div style={{ fontSize: "1.05rem", fontWeight: 700, fontFamily: "var(--font-mono)", color: s.color }}>
                          {stats?.[s.key] != null ? Number(stats[s.key]).toFixed(5) : "—"}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* VERIFICATION SECTION */}
                  <VerificationSection report={verifReport} loading={!!verifLoading} solveResult={solveResult} />
                </div>
              )}

              {/* GRAPH INFO TAB */}
              {activeTab === "graph" && (
                <div className="fade-in">
                  <h3 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: 16, color: "var(--neon-cyan)" }}>Solution Array Information</h3>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12, marginBottom: 24 }}>
                    {[
                      { label: "Time Points",     value: stats?.n_points ? `${stats.n_points} pts` : "300 pts",     color: "var(--neon-cyan)"   },
                      { label: "Time Range",       value: stats ? `[${stats.t_start?.toFixed(2) ?? "0.00"}, ${stats.t_end?.toFixed(2) ?? "50.00"}]` : "[0.00, 50.00]", color: "var(--neon-green)" },
                      { label: "State Dimensions", value: stats?.n_states ? `${stats.n_states} (x, x′)` : "2 (x, x′)", color: "var(--neon-purple)" },
                      { label: "Sample Rate",      value: stats?.n_points && stats?.t_end && stats?.t_start ? `~${(stats.n_points / (stats.t_end - stats.t_start)).toFixed(1)} pts/s` : "~6.0 pts/s", color: "var(--neon-yellow)" },
                    ].map((item) => (
                      <div key={item.label} className="stat-card">
                        <div style={{ fontSize: "0.68rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: 4 }}>{item.label}</div>
                        <div style={{ fontSize: "1.05rem", fontWeight: 700, fontFamily: "var(--font-mono)", color: item.color }}>{item.value}</div>
                      </div>
                    ))}
                  </div>

                  <div className="neon-divider" style={{ marginBottom: 20 }} />

                  <h3 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: 14, color: "var(--neon-cyan)" }}>Raw Data Preview (first 6 points)</h3>
                  <div style={{ overflowX: "auto" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: "var(--font-mono)", fontSize: "0.82rem" }}>
                      <thead>
                        <tr>
                          {["t", "x(t)", "x′(t)"].map((col) => (
                            <th key={col} style={{ padding: "10px 14px", textAlign: "left", borderBottom: "1px solid var(--border)", color: "var(--text-muted)", fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "1px" }}>{col}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {(solveResult
                          ? solveResult.t.slice(0, 6).map((t, i) => [t, solveResult.y[0][i], solveResult.y[1]?.[i] ?? 0])
                          : [[0.00, 1.00000, 0.00000],[0.17, 0.99821, -0.12634],[0.33, 0.99286, -0.24802],[0.50, 0.98412, -0.36153],[0.67, 0.97218, -0.46356],[0.84, 0.95723, -0.55106]]
                        ).map((row, i) => (
                          <tr key={i} style={{ borderBottom: "1px solid rgba(99,102,241,0.06)", background: i % 2 === 0 ? "transparent" : "rgba(99,102,241,0.03)" }}>
                            <td style={{ padding: "10px 14px", color: "var(--neon-yellow)" }}>{Number(row[0]).toFixed(2)}</td>
                            <td style={{ padding: "10px 14px", color: "var(--neon-cyan)" }}>{Number(row[1]).toFixed(5)}</td>
                            <td style={{ padding: "10px 14px", color: "var(--neon-pink)" }}>{Number(row[2]).toFixed(5)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* CODE TAB */}
              {activeTab === "code" && (
                <div className="fade-in">
                  {/* Pipeline step badges */}
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 20 }}>
                    {[
                      { num: "01", label: "Parse & Restate",    color: "var(--neon-purple)" },
                      { num: "02", label: "Generate Code",      color: "var(--neon-cyan)"   },
                      { num: "03", label: "Self-Debug",         color: "var(--neon-green)"  },
                      { num: "04", label: "Eval Block",         color: "var(--neon-yellow)" },
                      { num: "05", label: "Refinement Loop",    color: "var(--neon-pink)"   },
                    ].map((step) => (
                      <div key={step.num} style={{ display: "flex", alignItems: "center", gap: 6, padding: "5px 12px", borderRadius: 20, background: "rgba(15,23,42,0.8)", border: `1px solid ${step.color}33`, fontSize: "0.72rem", fontFamily: "var(--font-mono)" }}>
                        <span style={{ color: step.color, fontWeight: 700 }}>STEP {step.num}</span>
                        <span style={{ color: "var(--text-muted)" }}>{step.label}</span>
                      </div>
                    ))}
                  </div>

                  {codeLoading && (
                    <div style={{ padding: "40px", textAlign: "center" }}>
                      <div style={{ display: "inline-block", width: 32, height: 32, border: "3px solid rgba(52,211,153,0.2)", borderTop: "3px solid var(--neon-green)", borderRadius: "50%", animation: "spin 0.8s linear infinite", marginBottom: 16 }} />
                      <p style={{ color: "var(--text-secondary)" }}>Running 5-step solver engine pipeline…</p>
                    </div>
                  )}

                  {!codeLoading && !codeResult && (
                    <div style={{ padding: "40px", textAlign: "center" }}>
                      <div style={{ fontSize: "2.5rem", marginBottom: 12 }}>⚙️</div>
                      <p style={{ color: "var(--text-secondary)" }}>Solve an equation to generate the solver code.</p>
                    </div>
                  )}

                  {!codeLoading && codeResult && (
                    <>
                      {/* Step 1 — Problem restatement */}
                      <div style={{ marginBottom: 20, padding: "16px 18px", borderRadius: 12, background: "rgba(124,58,237,0.06)", border: "1px solid rgba(124,58,237,0.2)" }}>
                        <div style={{ fontSize: "0.72rem", fontFamily: "var(--font-mono)", color: "var(--neon-purple)", letterSpacing: "2px", textTransform: "uppercase", marginBottom: 10 }}>STEP 01 — Problem Restatement</div>
                        <pre style={{ margin: 0, fontSize: "0.82rem", color: "var(--text-secondary)", fontFamily: "var(--font-mono)", whiteSpace: "pre-wrap", lineHeight: 1.7 }}>{codeResult.parsed.natural_language}</pre>
                        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 12 }}>
                          {[
                            { label: `Order ${codeResult.parsed.order}`, color: "badge-purple" },
                            { label: codeResult.parsed.is_linear ? "Linear" : "Nonlinear", color: "badge-cyan" },
                            { label: codeResult.parsed.is_stiff ? "⚠ Stiff" : "Non-stiff", color: codeResult.parsed.is_stiff ? "badge-yellow" : "badge-green" },
                            { label: codeResult.parsed.is_homogeneous ? "Homogeneous" : "Non-homogeneous", color: "badge-blue" },
                            { label: `Method: ${codeResult.method_chosen}`, color: "badge-green" },
                          ].map((b) => (
                            <span key={b.label} className={`badge ${b.color}`}>{b.label}</span>
                          ))}
                        </div>
                      </div>

                      {/* PDE warning */}
                      {codeResult.parsed.has_pde && (
                        <div style={{ marginBottom: 20, padding: "14px 18px", borderRadius: 12, background: "rgba(220,38,38,0.06)", border: "1px solid rgba(220,38,38,0.3)", color: "#fca5a5", fontSize: "0.85rem" }}>
                          ❌ <strong>PDE detected.</strong> AutoSim Phase-1 only supports ODEs. PDE support is coming in a future phase.
                        </div>
                      )}

                      {/* Step 3 — Debug notes */}
                      <div style={{ marginBottom: 20, padding: "14px 18px", borderRadius: 12, background: codeResult.is_valid ? "rgba(52,211,153,0.05)" : "rgba(220,38,38,0.05)", border: `1px solid ${codeResult.is_valid ? "rgba(52,211,153,0.2)" : "rgba(220,38,38,0.25)"}` }}>
                        <div style={{ fontSize: "0.72rem", fontFamily: "var(--font-mono)", color: codeResult.is_valid ? "var(--neon-green)" : "#f87171", letterSpacing: "2px", textTransform: "uppercase", marginBottom: 8 }}>STEP 03 — Self-Debug {codeResult.is_valid ? "✅ PASSED" : "❌ ISSUES FOUND"}</div>
                        {codeResult.debug_notes.map((note, i) => (
                          <div key={i} style={{ fontSize: "0.78rem", color: "var(--text-secondary)", fontFamily: "var(--font-mono)", marginBottom: 3 }}>{note}</div>
                        ))}
                        {codeResult.issues_found.map((issue, i) => (
                          <div key={i} style={{ fontSize: "0.78rem", color: "#f87171", fontFamily: "var(--font-mono)", marginBottom: 3 }}>⚠ {issue}</div>
                        ))}
                      </div>

                      {/* Step 2+4 — Full generated code */}
                      <div style={{ position: "relative" }}>
                        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
                          <div style={{ fontSize: "0.72rem", fontFamily: "var(--font-mono)", color: "var(--neon-cyan)", letterSpacing: "2px", textTransform: "uppercase" }}>STEPS 02 + 04 — Generated Python Code</div>
                          <button
                            onClick={() => handleCopy(codeResult.full_code)}
                            style={{ padding: "6px 14px", borderRadius: 8, background: copied ? "rgba(52,211,153,0.15)" : "rgba(34,211,238,0.08)", border: `1px solid ${copied ? "rgba(52,211,153,0.4)" : "rgba(34,211,238,0.2)"}`, color: copied ? "var(--neon-green)" : "var(--neon-cyan)", fontSize: "0.75rem", fontFamily: "var(--font-mono)", cursor: "pointer", transition: "all 0.2s" }}
                          >
                            {copied ? "✓ Copied!" : "📋 Copy code"}
                          </button>
                        </div>
                        <div style={{ borderRadius: 12, background: "#0a0f1e", border: "1px solid rgba(34,211,238,0.15)", overflow: "hidden" }}>
                          <div style={{ padding: "10px 16px", background: "rgba(34,211,238,0.05)", borderBottom: "1px solid rgba(34,211,238,0.1)", display: "flex", gap: 6 }}>
                            <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#ef4444" }} />
                            <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#f59e0b" }} />
                            <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#22c55e" }} />
                            <span style={{ marginLeft: 8, fontSize: "0.7rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>autosim_solver.py</span>
                          </div>
                          <pre style={{ margin: 0, padding: "20px", fontSize: "0.78rem", lineHeight: 1.65, color: "#e2e8f0", fontFamily: "var(--font-mono)", overflowX: "auto", maxHeight: 520, overflowY: "auto", whiteSpace: "pre" }}>
                            <code>{codeResult.full_code}</code>
                          </pre>
                        </div>
                      </div>

                      {/* Step 5 — Refinement hint */}
                      <div style={{ marginTop: 20, padding: "14px 18px", borderRadius: 12, background: "rgba(244,114,182,0.05)", border: "1px solid rgba(244,114,182,0.2)" }}>
                        <div style={{ fontSize: "0.72rem", fontFamily: "var(--font-mono)", color: "var(--neon-pink)", letterSpacing: "2px", textTransform: "uppercase", marginBottom: 6 }}>STEP 05 — Refinement Loop</div>
                        <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", lineHeight: 1.6, margin: 0 }}>
                          If you run this code and encounter issues, AutoSim will refine it automatically:<br />
                          <span style={{ color: "var(--neon-pink)", fontFamily: "var(--font-mono)" }}>oscillation → Radau</span> · <span style={{ color: "var(--neon-yellow)", fontFamily: "var(--font-mono)" }}>high error → tighter tolerances</span> · <span style={{ color: "var(--neon-green)", fontFamily: "var(--font-mono)" }}>slow → LSODA + fewer points</span>
                        </p>
                      </div>
                    </>
                  )}
                </div>
              )}

              {/* LLM INSIGHT TAB */}
              {activeTab === "llm" && (
                <div className="fade-in">
                  {!useLlm ? (
                    <div style={{ padding: "32px", borderRadius: 16, background: "rgba(251,191,36,0.05)", border: "1px solid rgba(251,191,36,0.2)", textAlign: "center" }}>
                      <div style={{ fontSize: "2.5rem", marginBottom: 12 }}>🤖</div>
                      <p style={{ color: "var(--neon-yellow)", fontWeight: 600, marginBottom: 8 }}>LLM Insights Disabled</p>
                      <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                        Enable <strong style={{ color: "var(--text-secondary)" }}>LLM Insights</strong> in the solver workspace and re-solve to see AI-generated interpretations.
                      </p>
                    </div>
                  ) : (
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
                        <div style={{ width: 36, height: 36, borderRadius: 10, background: "linear-gradient(135deg, #2563eb, #7c3aed)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.2rem" }}>🤖</div>
                        <div>
                          <div style={{ fontWeight: 700, fontSize: "0.9rem" }}>LLM Analysis</div>
                          <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>interpretation only · no computation</div>
                        </div>
                        <span className="badge badge-blue" style={{ marginLeft: "auto" }}>AI Generated</span>
                      </div>
                      <div style={{ padding: "20px 22px", borderRadius: 14, background: "rgba(37,99,235,0.06)", border: "1px solid rgba(37,99,235,0.2)", lineHeight: 1.8, fontSize: "0.9rem", color: "var(--text-secondary)", whiteSpace: "pre-wrap", marginBottom: 16 }}>
                        {LLM_INSIGHT.split("**").map((part, i) =>
                          i % 2 === 1 ? <strong key={i} style={{ color: "var(--text-primary)" }}>{part}</strong> : part
                        )}
                      </div>
                      <div style={{ padding: "14px 18px", borderRadius: 12, background: "rgba(52,211,153,0.06)", border: "1px solid rgba(52,211,153,0.2)", display: "flex", alignItems: "flex-start", gap: 10, fontSize: "0.8rem", color: "var(--text-muted)" }}>
                        <span style={{ color: "var(--neon-green)", fontSize: "1rem" }}>ℹ️</span>
                        <span>This interpretation is AI-generated. All numerical values are computed by SymPy/SciPy/NumPy — the LLM only explains the physics and behavior.</span>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* STEPS TAB */}
              {activeTab === "steps" && (
                <div className="fade-in">
                  {(method === "symbolic" || method === "laplace") ? (
                    // ── Symbolic / Laplace: real derivation steps from backend ──
                    <div>
                      <h3 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: 20, color: "var(--neon-yellow)" }}>
                        {method === "laplace" ? "Laplace Transform Derivation" : "Step-by-Step Symbolic Derivation"}
                      </h3>
                      {(solveResult?.steps ?? []).length === 0 ? (
                        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>No derivation steps returned by the solver.</p>
                      ) : (
                        (solveResult!.steps as SolveStep[]).map((step) => (
                          <div key={step.step_number} style={{ marginBottom: 16, padding: "16px 18px", borderRadius: 12, background: "rgba(15,23,42,0.6)", border: "1px solid var(--border)", transition: "border-color 0.2s" }}
                            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "rgba(124,58,237,0.3)"; }}
                            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "var(--border)"; }}
                          >
                            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
                              <div style={{ width: 28, height: 28, borderRadius: 8, background: "rgba(124,58,237,0.2)", border: "1px solid rgba(124,58,237,0.4)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.78rem", fontWeight: 700, color: "var(--neon-purple)", fontFamily: "var(--font-mono)", flexShrink: 0 }}>
                                {step.step_number}
                              </div>
                              <div style={{ fontWeight: 700, fontSize: "0.88rem", color: "var(--text-primary)" }}>{step.title}</div>
                            </div>
                            {step.equation && (
                              <pre style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginBottom: 10, marginLeft: 38, fontFamily: "var(--font-mono)", whiteSpace: "pre-wrap", margin: "0 0 10px 38px", lineHeight: 1.6 }}>{step.equation}</pre>
                            )}
                            {step.latex && (
                              <div style={{ marginLeft: 38, padding: "10px 16px", borderRadius: 8, background: "rgba(34,211,238,0.05)", border: "1px solid rgba(34,211,238,0.15)", fontFamily: "var(--font-mono)", fontSize: "0.85rem", color: "var(--neon-cyan)", overflowX: "auto", whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                                {step.latex}
                              </div>
                            )}
                          </div>
                        ))
                      )}
                    </div>
                  ) : (method === "euler_fwd" || method === "euler_imp") ? (
                    // ── Euler: real steps_table from backend ──
                    (() => {
                      const eulerSteps = (solveResult?.steps ?? []) as SolveStep[];
                      const isImproved = method === "euler_imp";
                      const cols = isImproved
                        ? ["t_n", "x_n", "k1", "k2", "x_{n+1}"]
                        : ["t_n", "x_n", "f(t,y)", "x_{n+1}"];
                      const h = eulerSteps.length > 1
                        ? ((eulerSteps[1].t_n ?? 0) - (eulerSteps[0].t_n ?? 0)).toFixed(6)
                        : "—";
                      return (
                        <div>
                          <h3 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: 16, color: "var(--neon-yellow)" }}>
                            {isImproved ? "Improved Euler (Heun's Method) — Integration Steps (first 10)" : "Forward Euler — Integration Steps (first 10)"}
                          </h3>
                          <div style={{ padding: "10px 14px", borderRadius: 10, background: "rgba(34,211,238,0.06)", border: "1px solid rgba(34,211,238,0.2)", marginBottom: 16, fontSize: "0.8rem", color: "var(--neon-cyan)", fontFamily: "var(--font-mono)" }}>
                            Step size h = {h}
                          </div>
                          {eulerSteps.length === 0 ? (
                            <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>No integration steps returned.</p>
                          ) : (
                            <div style={{ overflowX: "auto" }}>
                              <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: "var(--font-mono)", fontSize: "0.82rem" }}>
                                <thead>
                                  <tr>
                                    {cols.map((col) => (
                                      <th key={col} style={{ padding: "10px 14px", textAlign: "left", borderBottom: "1px solid var(--border)", color: "var(--text-muted)", fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "1px" }}>{col}</th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody>
                                  {eulerSteps.map((row, i) => (
                                    <tr key={i} style={{ borderBottom: "1px solid rgba(99,102,241,0.06)", background: i % 2 === 0 ? "transparent" : "rgba(99,102,241,0.02)" }}>
                                      <td style={{ padding: "9px 14px", color: "var(--neon-yellow)" }}>{(row.t_n ?? 0).toFixed(4)}</td>
                                      <td style={{ padding: "9px 14px", color: "var(--neon-cyan)" }}>{(row.x_n ?? 0).toFixed(6)}</td>
                                      {isImproved ? (
                                        <>
                                          <td style={{ padding: "9px 14px", color: "var(--text-secondary)" }}>{(row.k1 ?? 0).toFixed(6)}</td>
                                          <td style={{ padding: "9px 14px", color: "var(--text-secondary)" }}>{(row.k2 ?? 0).toFixed(6)}</td>
                                        </>
                                      ) : (
                                        <td style={{ padding: "9px 14px", color: "var(--text-secondary)" }}>{(row["f(t,y)"] ?? 0).toFixed(6)}</td>
                                      )}
                                      <td style={{ padding: "9px 14px", color: "var(--neon-green)" }}>{(row["x_{n+1}"] ?? 0).toFixed(6)}</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          )}
                        </div>
                      );
                    })()
                  ) : (
                    // ── Numerical (RK45 / Radau / Compare): solver breakdown from backend ──
                    <div>
                      <h3 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: 20, color: "var(--neon-yellow)" }}>
                        {method === "compare"
                          ? "Method Comparison — RK45 vs Radau"
                          : `Numerical Solver Breakdown (${method.toUpperCase()})`}
                      </h3>
                      {(solveResult?.steps ?? []).length === 0 ? (
                        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>No breakdown returned by the solver.</p>
                      ) : (
                        (solveResult!.steps as SolveStep[]).map((step) => (
                          <div key={step.step_number} style={{ marginBottom: 16, padding: "16px 18px", borderRadius: 12, background: "rgba(15,23,42,0.6)", border: "1px solid var(--border)", transition: "border-color 0.2s" }}
                            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "rgba(52,211,153,0.3)"; }}
                            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "var(--border)"; }}
                          >
                            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
                              <div style={{ width: 28, height: 28, borderRadius: 8, background: "rgba(52,211,153,0.15)", border: "1px solid rgba(52,211,153,0.4)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.78rem", fontWeight: 700, color: "var(--neon-green)", fontFamily: "var(--font-mono)", flexShrink: 0 }}>
                                {step.step_number}
                              </div>
                              <div style={{ fontWeight: 700, fontSize: "0.88rem", color: "var(--text-primary)" }}>{step.title}</div>
                            </div>
                            {step.equation && (
                              <pre style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginBottom: 10, marginLeft: 38, fontFamily: "var(--font-mono)", whiteSpace: "pre-wrap", margin: "0 0 10px 38px", lineHeight: 1.6 }}>{step.equation}</pre>
                            )}
                            {step.latex && (
                              <div style={{ marginLeft: 38, padding: "10px 16px", borderRadius: 8, background: "rgba(52,211,153,0.04)", border: "1px solid rgba(52,211,153,0.15)", fontFamily: "var(--font-mono)", fontSize: "0.85rem", color: "var(--neon-green)", overflowX: "auto", whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                                {step.latex}
                              </div>
                            )}
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </section>
  );
}