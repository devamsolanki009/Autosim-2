"use client";

import { useState } from "react";

const EXAMPLES = [
  { label: "Damped Harmonic", eq: "x'' + 0.2*x' + x = cos(t)" },
  { label: "Simple Harmonic", eq: "x'' + x = 0" },
  { label: "Critically Damped", eq: "x'' + 2*x' + x = 0" },
  { label: "Van der Pol", eq: "x'' - (1 - x**2)*x' + x = 0" },
  { label: "Stiff System", eq: "x'' + 1000*x' + x = 0" },
  { label: "Forced Harmonic", eq: "x'' + 0.1*x' + x = sin(2*t)" },
  { label: "Underdamped", eq: "x'' + 0.5*x' + 4*x = 0" },
  { label: "Overdamped", eq: "x'' + 5*x' + 4*x = 0" },
];

const METHODS = [
  { key: "symbolic",  label: "Symbolic (SymPy)",         badge: "badge-purple", desc: "Exact closed-form" },
  { key: "laplace",   label: "Laplace Transform",         badge: "badge-blue",   desc: "S-domain exact" },
  { key: "rk45",      label: "RK45 (SciPy)",              badge: "badge-green",  desc: "Standard numerical" },
  { key: "radau",     label: "Radau — Stiff",             badge: "badge-green",  desc: "Implicit / stiff" },
  { key: "euler_fwd", label: "Forward Euler",             badge: "badge-yellow", desc: "Educational" },
  { key: "euler_imp", label: "Improved Euler (Heun's)",   badge: "badge-yellow", desc: "Better Euler" },
  { key: "compare",   label: "Compare All Methods",       badge: "badge-pink",   desc: "Side-by-side" },
];

interface SolverWorkspaceProps {
  onSolve: (params: {
    equation: string;
    x0: number;
    dx0: number;
    tStart: number;
    tEnd: number;
    method: string;
    useLlm: boolean;
    wolframKey: string;
  }) => void;
  isLoading: boolean;
}

export default function SolverWorkspace({ onSolve, isLoading }: SolverWorkspaceProps) {
  const [equation, setEquation] = useState("x'' + 0.2*x' + x = cos(t)");
  const [x0, setX0] = useState(1.0);
  const [dx0, setDx0] = useState(0.0);
  const [tStart, setTStart] = useState(0);
  const [tEnd, setTEnd] = useState(50);
  const [method, setMethod] = useState("rk45");
  const [useLlm, setUseLlm] = useState(false);
  const [showExamples, setShowExamples] = useState(false);
  const [wolframKey, setWolframKey] = useState("");
  const [showWolframTip, setShowWolframTip] = useState(false);

  const selectedMethod = METHODS.find((m) => m.key === method) ?? METHODS[2];

  const handleSolve = () => {
    onSolve({ equation, x0, dx0, tStart, tEnd, method, useLlm, wolframKey });
  };

  return (
    <section
      id="solver"
      style={{
        padding: "80px 24px",
        maxWidth: 1400,
        margin: "0 auto",
      }}
    >
      {/* Section header */}
      <div style={{ marginBottom: 36 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "0.75rem",
              color: "var(--neon-purple)",
              letterSpacing: "2px",
              textTransform: "uppercase",
            }}
          >
            01 — Solver Workspace
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
          Configure Your ODE
        </h2>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem" }}>
          Input your differential equation, set initial conditions, and choose a solving method.
        </p>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 360px",
          gap: 24,
          alignItems: "start",
        }}
      >
        {/* Main input panel */}
        <div className="glass-card" style={{ padding: "28px 28px" }}>
          {/* Equation input */}
          <div style={{ marginBottom: 24 }}>
            <label
              style={{
                display: "block",
                fontSize: "0.8rem",
                fontFamily: "var(--font-mono)",
                color: "var(--text-muted)",
                letterSpacing: "1px",
                textTransform: "uppercase",
                marginBottom: 10,
              }}
            >
              Differential Equation
            </label>
            <textarea
              className="neon-input"
              value={equation}
              onChange={(e) => setEquation(e.target.value)}
              rows={3}
              placeholder="e.g. x'' + 0.2*x' + x = cos(t)"
              style={{
                width: "100%",
                padding: "14px 16px",
                fontSize: "1.05rem",
                resize: "none",
                lineHeight: 1.6,
              }}
            />
            <div
              style={{
                marginTop: 8,
                display: "flex",
                gap: 8,
                flexWrap: "wrap",
              }}
            >
              {[
                { sym: "x''", tip: "2nd derivative" },
                { sym: "x'", tip: "1st derivative" },
                { sym: "sin(t)", tip: "sine forcing" },
                { sym: "cos(t)", tip: "cosine forcing" },
                { sym: "exp(t)", tip: "exponential" },
              ].map((s) => (
                <button
                  key={s.sym}
                  title={s.tip}
                  onClick={() => setEquation((eq) => eq + s.sym)}
                  style={{
                    padding: "3px 10px",
                    borderRadius: 6,
                    background: "rgba(34,211,238,0.07)",
                    border: "1px solid rgba(34,211,238,0.2)",
                    color: "var(--neon-cyan)",
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.78rem",
                    cursor: "pointer",
                    transition: "background 0.15s",
                  }}
                  onMouseEnter={(e) =>
                    ((e.target as HTMLElement).style.background = "rgba(34,211,238,0.14)")
                  }
                  onMouseLeave={(e) =>
                    ((e.target as HTMLElement).style.background = "rgba(34,211,238,0.07)")
                  }
                >
                  {s.sym}
                </button>
              ))}
            </div>
          </div>

          {/* Examples toggle */}
          <div style={{ marginBottom: 24 }}>
            <button
              onClick={() => setShowExamples((v) => !v)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                padding: "8px 14px",
                borderRadius: 8,
                background: "rgba(124,58,237,0.08)",
                border: "1px solid rgba(124,58,237,0.2)",
                color: "var(--neon-purple)",
                fontSize: "0.82rem",
                cursor: "pointer",
                transition: "background 0.15s",
              }}
            >
              📚 {showExamples ? "Hide" : "Show"} Example Equations
              <span style={{ marginLeft: 4 }}>{showExamples ? "▲" : "▼"}</span>
            </button>

            {showExamples && (
              <div
                style={{
                  marginTop: 12,
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
                  gap: 8,
                }}
              >
                {EXAMPLES.map((ex) => (
                  <button
                    key={ex.label}
                    onClick={() => {
                      setEquation(ex.eq);
                      setShowExamples(false);
                    }}
                    style={{
                      padding: "10px 14px",
                      borderRadius: 10,
                      background: "rgba(15,23,42,0.6)",
                      border: "1px solid var(--border)",
                      color: "var(--text-secondary)",
                      fontSize: "0.8rem",
                      cursor: "pointer",
                      textAlign: "left",
                      transition: "all 0.15s",
                    }}
                    onMouseEnter={(e) => {
                      (e.currentTarget as HTMLElement).style.borderColor = "rgba(124,58,237,0.4)";
                      (e.currentTarget as HTMLElement).style.color = "var(--text-primary)";
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLElement).style.borderColor = "var(--border)";
                      (e.currentTarget as HTMLElement).style.color = "var(--text-secondary)";
                    }}
                  >
                    <div style={{ fontWeight: 600, marginBottom: 3, color: "var(--neon-purple)", fontSize: "0.78rem" }}>
                      {ex.label}
                    </div>
                    <div
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: "0.72rem",
                        color: "var(--text-muted)",
                      }}
                    >
                      {ex.eq}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Initial conditions + time range */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr 1fr 1fr",
              gap: 16,
              marginBottom: 24,
            }}
          >
            {[
              { label: "x(0)", value: x0, setter: setX0, color: "var(--neon-cyan)" },
              { label: "x'(0)", value: dx0, setter: setDx0, color: "var(--neon-cyan)" },
              { label: "t start", value: tStart, setter: setTStart, color: "var(--neon-green)" },
              { label: "t end", value: tEnd, setter: setTEnd, color: "var(--neon-green)" },
            ].map((field) => (
              <div key={field.label}>
                <label
                  style={{
                    display: "block",
                    fontSize: "0.72rem",
                    fontFamily: "var(--font-mono)",
                    color: "var(--text-muted)",
                    letterSpacing: "1px",
                    textTransform: "uppercase",
                    marginBottom: 6,
                    textAlign: "center",
                  }}
                >
                  {field.label}
                </label>
                <input
                  type="number"
                  className="neon-number"
                  value={field.value}
                  onChange={(e) => field.setter(parseFloat(e.target.value) || 0)}
                  step={0.1}
                  style={{ color: field.color }}
                />
              </div>
            ))}
          </div>

          {/* Method selector */}
          <div style={{ marginBottom: 24 }}>
            <label
              style={{
                display: "block",
                fontSize: "0.72rem",
                fontFamily: "var(--font-mono)",
                color: "var(--text-muted)",
                letterSpacing: "1px",
                textTransform: "uppercase",
                marginBottom: 10,
              }}
            >
              Solving Method
            </label>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
                gap: 8,
              }}
            >
              {METHODS.map((m) => (
                <button
                  key={m.key}
                  onClick={() => setMethod(m.key)}
                  style={{
                    padding: "10px 14px",
                    borderRadius: 10,
                    border: `1px solid ${method === m.key ? "rgba(124,58,237,0.5)" : "var(--border)"}`,
                    background:
                      method === m.key
                        ? "rgba(124,58,237,0.12)"
                        : "rgba(15,23,42,0.5)",
                    cursor: "pointer",
                    textAlign: "left",
                    transition: "all 0.15s",
                    display: "flex",
                    flexDirection: "column",
                    gap: 3,
                  }}
                >
                  <span
                    style={{
                      fontSize: "0.82rem",
                      fontWeight: 600,
                      color:
                        method === m.key ? "var(--neon-purple)" : "var(--text-secondary)",
                    }}
                  >
                    {m.label}
                  </span>
                  <span
                    style={{
                      fontSize: "0.7rem",
                      color: "var(--text-muted)",
                      fontFamily: "var(--font-mono)",
                    }}
                  >
                    {m.desc}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right panel: settings + solve */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Selected method card */}
          <div
            className="glass-card"
            style={{
              padding: "20px 22px",
              borderColor: "rgba(124,58,237,0.3)",
            }}
          >
            <div
              style={{
                fontSize: "0.72rem",
                fontFamily: "var(--font-mono)",
                color: "var(--text-muted)",
                letterSpacing: "1px",
                textTransform: "uppercase",
                marginBottom: 10,
              }}
            >
              Selected Method
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
              <div
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: "50%",
                  background: "var(--neon-purple)",
                  boxShadow: "0 0 10px var(--neon-purple)",
                }}
              />
              <span
                style={{
                  fontWeight: 700,
                  color: "var(--text-primary)",
                  fontSize: "0.95rem",
                }}
              >
                {selectedMethod.label}
              </span>
            </div>
            <span className={`badge ${selectedMethod.badge}`}>{selectedMethod.desc}</span>
          </div>

          {/* LLM Insights toggle */}
          <div
            className="glass-card"
            style={{ padding: "20px 22px" }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: 10,
              }}
            >
              <div>
                <div
                  style={{
                    fontWeight: 600,
                    fontSize: "0.9rem",
                    marginBottom: 3,
                  }}
                >
                  🤖 LLM Insights
                </div>
                <div style={{ fontSize: "0.74rem", color: "var(--text-muted)" }}>
                  AI interpretation of results
                </div>
              </div>
              {/* Toggle */}
              <div
                className={`toggle-bg ${useLlm ? "on" : ""}`}
                onClick={() => setUseLlm((v) => !v)}
                style={{
                  width: 44,
                  height: 24,
                  display: "flex",
                  alignItems: "center",
                  padding: "3px",
                }}
              >
                <div className="toggle-knob" />
              </div>
            </div>
            {useLlm && (
              <div
                style={{
                  padding: "8px 12px",
                  borderRadius: 8,
                  background: "rgba(34,211,238,0.07)",
                  border: "1px solid rgba(34,211,238,0.2)",
                  fontSize: "0.74rem",
                  color: "var(--neon-cyan)",
                }}
              >
                LLM will provide natural language explanations and physical interpretations.
              </div>
            )}
          </div>

          {/* WolframAlpha key */}
          <div className="glass-card" style={{ padding: "20px 22px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
              <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>🔍 WolframAlpha Key</div>
              <div
                style={{
                  position: "relative",
                  display: "inline-flex",
                  alignItems: "center",
                  cursor: "pointer",
                }}
                onMouseEnter={() => setShowWolframTip(true)}
                onMouseLeave={() => setShowWolframTip(false)}
              >
                <span
                  style={{
                    width: 16,
                    height: 16,
                    borderRadius: "50%",
                    background: "rgba(251,191,36,0.15)",
                    border: "1px solid rgba(251,191,36,0.4)",
                    color: "var(--neon-yellow)",
                    fontSize: "0.65rem",
                    fontWeight: 700,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontFamily: "var(--font-mono)",
                  }}
                >
                  ?
                </span>
                {showWolframTip && (
                  <div
                    style={{
                      position: "absolute",
                      bottom: "calc(100% + 8px)",
                      left: "50%",
                      transform: "translateX(-50%)",
                      width: 240,
                      padding: "10px 12px",
                      borderRadius: 10,
                      background: "rgba(15,23,42,0.97)",
                      border: "1px solid rgba(251,191,36,0.35)",
                      fontSize: "0.72rem",
                      color: "var(--text-secondary)",
                      lineHeight: 1.5,
                      zIndex: 50,
                      pointerEvents: "none",
                    }}
                  >
                    Optional — free key from{" "}
                    <span style={{ color: "var(--neon-yellow)", fontFamily: "var(--font-mono)" }}>
                      developer.wolframalpha.com
                    </span>
                    . Enables independent WolframAlpha cross-check.
                  </div>
                )}
              </div>
            </div>
            <input
              id="wolfram-key-input"
              type="password"
              className="neon-input"
              value={wolframKey}
              onChange={(e) => setWolframKey(e.target.value)}
              placeholder="App ID (optional)"
              style={{
                width: "100%",
                padding: "10px 14px",
                fontSize: "0.82rem",
                letterSpacing: wolframKey ? "0.12em" : "normal",
              }}
            />
            {wolframKey && (
              <div
                style={{
                  marginTop: 8,
                  padding: "6px 10px",
                  borderRadius: 6,
                  background: "rgba(52,211,153,0.08)",
                  border: "1px solid rgba(52,211,153,0.25)",
                  fontSize: "0.72rem",
                  color: "var(--neon-green)",
                }}
              >
                ✓ WolframAlpha check enabled
              </div>
            )}
          </div>

          {/* Zero hallucination note */}
          <div
            style={{
              padding: "14px 16px",
              borderRadius: 12,
              background: "rgba(52,211,153,0.06)",
              border: "1px solid rgba(52,211,153,0.2)",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                marginBottom: 6,
              }}
            >
              <span style={{ fontSize: "0.9rem" }}>🔒</span>
              <span
                style={{
                  fontSize: "0.8rem",
                  fontWeight: 700,
                  color: "var(--neon-green)",
                }}
              >
                Zero Hallucination
              </span>
            </div>
            <p
              style={{
                fontSize: "0.74rem",
                color: "var(--text-muted)",
                lineHeight: 1.5,
                margin: 0,
              }}
            >
              All mathematics: SymPy · SciPy · NumPy
              <br />
              LLM = interpretation only, never computes
            </p>
          </div>

          {/* Solve button */}
          <button
            className="btn-neon"
            onClick={handleSolve}
            disabled={isLoading}
            style={{
              width: "100%",
              padding: "18px",
              fontSize: "1rem",
              opacity: isLoading ? 0.7 : 1,
              cursor: isLoading ? "not-allowed" : "pointer",
            }}
          >
            <span
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 8,
              }}
            >
              {isLoading ? (
                <>
                  <span
                    style={{
                      display: "inline-block",
                      width: 16,
                      height: 16,
                      border: "2px solid rgba(255,255,255,0.3)",
                      borderTop: "2px solid white",
                      borderRadius: "50%",
                      animation: "spin 0.8s linear infinite",
                    }}
                  />
                  Solving…
                </>
              ) : (
                <>🚀 Solve ODE</>
              )}
            </span>
          </button>
        </div>
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </section>
  );
}
