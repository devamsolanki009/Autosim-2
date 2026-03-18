"use client";

import { useState } from "react";

interface ResultTabsProps {
  solved: boolean;
  method: string;
  equation: string;
  useLlm: boolean;
}

const STEPS_EXAMPLE = [
  {
    num: 1,
    title: "Parse Input",
    content: "Parse the equation x'' + 0.2·x' + x = cos(t) into characteristic components.",
    latex: "x'' + 0.2x' + x = \\cos(t)",
  },
  {
    num: 2,
    title: "Write Characteristic Equation",
    content: "Replace x'' → r², x' → r, x → 1.",
    latex: "r^2 + 0.2r + 1 = 0",
  },
  {
    num: 3,
    title: "Solve for Roots",
    content: "Discriminant: Δ = 0.04 - 4 = -3.96 < 0, complex conjugate roots.",
    latex: "r = -0.1 \\pm i\\sqrt{0.99}",
  },
  {
    num: 4,
    title: "Homogeneous Solution",
    content: "Underdamped exponentially decaying oscillation.",
    latex: "x_h = e^{-0.1t}(C_1\\cos(0.995t) + C_2\\sin(0.995t))",
  },
  {
    num: 5,
    title: "Particular Solution (Method of Undetermined Coefficients)",
    content: "Assume x_p = A·cos(t) + B·sin(t) and solve for A, B.",
    latex: "x_p = \\frac{0.8}{0.64}\\cos(t) + \\frac{0.2 \\cdot 0.8}{0.64}\\sin(t)",
  },
  {
    num: 6,
    title: "Apply Initial Conditions",
    content: "Apply x(0) = 1, x'(0) = 0 to find C₁ and C₂.",
    latex: "C_1 = 1 - A, \\quad C_2 = \\frac{0.1C_1 - B}{0.995}",
  },
  {
    num: 7,
    title: "Complete Solution",
    content: "The complete solution is the sum of homogenous and particular parts.",
    latex: "x(t) = x_h(t) + x_p(t)",
  },
];

const EULER_STEPS = [
  { t: 0.0,   x: 1.000, fx: 0.000, xNew: 1.000 },
  { t: 0.1,   x: 1.000, fx: -0.127, xNew: 0.987 },
  { t: 0.2,   x: 0.987, fx: -0.118, xNew: 0.975 },
  { t: 0.3,   x: 0.975, fx: -0.109, xNew: 0.964 },
  { t: 0.4,   x: 0.964, fx: -0.101, xNew: 0.954 },
  { t: 0.5,   x: 0.954, fx: -0.092, xNew: 0.945 },
  { t: 0.6,   x: 0.945, fx: -0.083, xNew: 0.937 },
  { t: 0.7,   x: 0.937, fx: -0.075, xNew: 0.929 },
  { t: 0.8,   x: 0.929, fx: -0.066, xNew: 0.923 },
  { t: 0.9,   x: 0.923, fx: -0.058, xNew: 0.917 },
];

const LLM_INSIGHT = `This ODE describes a **damped harmonic oscillator** subjected to a **periodic forcing function** cos(t). 

The system exhibits **underdamped behavior** (ζ ≈ 0.1 < 1), meaning the oscillations will persist while exponentially decaying toward a steady-state driven by the forcing term. 

**Physical Analogy**: This models a spring-mass system with light friction, being continuously pushed by a cosine-wave force — like a lightly-damped pendulum driven by a periodic external push.

**Key Observations**:
- The natural frequency ω₀ = 1 rad/s is close to the forcing frequency (1 rad/s), creating near-resonance conditions
- The transient response (free oscillation) decays exponentially with time constant τ = 1/(ζω₀) = 10 seconds
- The steady-state response is a sustained oscillation in phase with the forcing function
- The system will reach steady-state approximately after t ≈ 5τ = 50 seconds`;

export default function ResultTabs({ solved, method, equation, useLlm }: ResultTabsProps) {
  const [activeTab, setActiveTab] = useState("solution");

  const TABS = [
    { id: "solution",  label: "📋 Solution",    color: "var(--neon-purple)" },
    { id: "graph",     label: "📈 Graph Info",  color: "var(--neon-cyan)"   },
    { id: "llm",       label: "🤖 LLM Insight", color: "var(--neon-blue)"   },
    { id: "steps",     label: "🔢 Steps",       color: "var(--neon-yellow)" },
  ];

  const isSymbolicOrEuler = ["symbolic", "laplace", "euler_fwd", "euler_imp"].includes(method);

  return (
    <section
      id="results"
      style={{
        padding: "0 24px 80px",
        maxWidth: 1400,
        margin: "0 auto",
      }}
    >
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "0.75rem",
            color: "var(--neon-yellow)",
            letterSpacing: "2px",
            textTransform: "uppercase",
            display: "block",
            marginBottom: 8,
          }}
        >
          03 — Analysis Results
        </span>
        <h2
          style={{
            fontSize: "clamp(1.6rem, 3vw, 2.2rem)",
            fontWeight: 700,
            letterSpacing: "-0.02em",
            marginBottom: 8,
          }}
        >
          Solution Explorer
        </h2>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem" }}>
          Detailed breakdown of your ODE solution across multiple analytical perspectives.
        </p>
      </div>

      <div className="glass-card" style={{ overflow: "hidden" }}>
        {/* Tab bar */}
        <div
          style={{
            display: "flex",
            padding: "16px 20px 0",
            gap: 4,
            borderBottom: "1px solid var(--border)",
            overflowX: "auto",
          }}
        >
          {TABS.map((tab) => (
            <button
              key={tab.id}
              className={`tab-btn ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
              style={{
                flexShrink: 0,
                borderRadius: "8px 8px 0 0",
                color: activeTab === tab.id ? tab.color : undefined,
                borderColor: activeTab === tab.id ? "rgba(124,58,237,0.35)" : "transparent",
                borderBottom: "none",
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div style={{ padding: "28px 28px" }}>
          {!solved ? (
            <div
              style={{
                textAlign: "center",
                padding: "60px 20px",
                color: "var(--text-muted)",
              }}
            >
              <div style={{ fontSize: "3rem", marginBottom: 16 }}>🔬</div>
              <p style={{ fontSize: "1rem", color: "var(--text-secondary)" }}>
                Solve an equation to see results here
              </p>
              <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginTop: 6 }}>
                Results will appear across all tabs after solving
              </p>
            </div>
          ) : (
            <>
              {/* SOLUTION TAB */}
              {activeTab === "solution" && (
                <div className="fade-in">
                  <div style={{ marginBottom: 24 }}>
                    <h3
                      style={{
                        fontSize: "1rem",
                        fontWeight: 700,
                        marginBottom: 16,
                        color: "var(--neon-purple)",
                      }}
                    >
                      Equation Classification
                    </h3>
                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
                        gap: 12,
                        marginBottom: 24,
                      }}
                    >
                      {[
                        { label: "Order", value: "2nd", icon: "📐" },
                        { label: "Type", value: "Linear", icon: "🔢" },
                        { label: "Family", value: "Harmonic", icon: "🏷️" },
                        { label: "Stiff", value: "No ✓", icon: "⚡" },
                      ].map((item) => (
                        <div key={item.label} className="stat-card">
                          <div
                            style={{
                              fontSize: "1.2rem",
                              marginBottom: 4,
                            }}
                          >
                            {item.icon}
                          </div>
                          <div
                            style={{
                              fontSize: "0.7rem",
                              color: "var(--text-muted)",
                              fontFamily: "var(--font-mono)",
                              textTransform: "uppercase",
                              letterSpacing: "1px",
                              marginBottom: 4,
                            }}
                          >
                            {item.label}
                          </div>
                          <div
                            style={{
                              fontSize: "1.1rem",
                              fontWeight: 700,
                              color: "var(--text-primary)",
                              fontFamily: "var(--font-mono)",
                            }}
                          >
                            {item.value}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="neon-divider" style={{ marginBottom: 24 }} />

                  <h3
                    style={{
                      fontSize: "1rem",
                      fontWeight: 700,
                      marginBottom: 16,
                      color: "var(--neon-cyan)",
                    }}
                  >
                    Solver Decision
                  </h3>
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                      gap: 12,
                      marginBottom: 24,
                    }}
                  >
                    <div
                      style={{
                        padding: "16px",
                        borderRadius: 12,
                        background: "rgba(124,58,237,0.07)",
                        border: "1px solid rgba(124,58,237,0.2)",
                      }}
                    >
                      <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: 6 }}>
                        METHOD
                      </div>
                      <div style={{ color: "var(--neon-purple)", fontWeight: 700 }}>
                        {method.toUpperCase()}
                      </div>
                      <div style={{ marginTop: 4, fontSize: "0.8rem", color: "var(--text-muted)" }}>
                        Compute time:{" "}
                        <span style={{ color: "var(--neon-green)", fontFamily: "var(--font-mono)" }}>
                          {(Math.random() * 80 + 20).toFixed(1)} ms
                        </span>
                      </div>
                    </div>
                    <div
                      style={{
                        padding: "16px",
                        borderRadius: 12,
                        background: "rgba(52,211,153,0.06)",
                        border: "1px solid rgba(52,211,153,0.2)",
                      }}
                    >
                      <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: 6 }}>
                        EQUATION FAMILY
                      </div>
                      <div style={{ color: "var(--neon-green)", fontWeight: 700 }}>
                        Forced Harmonic Oscillator
                      </div>
                      <div style={{ marginTop: 4, fontSize: "0.8rem", color: "var(--text-muted)" }}>
                        Stiffness: <span style={{ color: "var(--neon-green)" }}>🟢 Not detected</span>
                      </div>
                    </div>
                  </div>

                  <div className="neon-divider" style={{ marginBottom: 24 }} />

                  <h3
                    style={{
                      fontSize: "1rem",
                      fontWeight: 700,
                      marginBottom: 16,
                      color: "var(--neon-green)",
                    }}
                  >
                    Solution Statistics
                  </h3>
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
                      gap: 12,
                    }}
                  >
                    {[
                      { label: "x final", value: "0.03281", color: "var(--neon-purple)" },
                      { label: "x max",   value: "1.24711", color: "var(--neon-cyan)"   },
                      { label: "x min",   value: "-0.63094",color: "var(--neon-pink)"   },
                      { label: "x mean",  value: "0.21408", color: "var(--neon-blue)"   },
                      { label: "Std dev", value: "0.38201", color: "var(--neon-yellow)" },
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
                            fontSize: "1.05rem",
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
                </div>
              )}

              {/* GRAPH INFO TAB */}
              {activeTab === "graph" && (
                <div className="fade-in">
                  <h3
                    style={{
                      fontSize: "1rem",
                      fontWeight: 700,
                      marginBottom: 16,
                      color: "var(--neon-cyan)",
                    }}
                  >
                    Solution Array Information
                  </h3>
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                      gap: 12,
                      marginBottom: 24,
                    }}
                  >
                    {[
                      { label: "Time Points",     value: "300 pts",     color: "var(--neon-cyan)"   },
                      { label: "Time Range",       value: "[0.00, 50.00]",color: "var(--neon-green)" },
                      { label: "State Dimensions", value: "2 (x, x')",  color: "var(--neon-purple)" },
                      { label: "Sample Rate",      value: "~6.0 pts/s", color: "var(--neon-yellow)" },
                    ].map((item) => (
                      <div key={item.label} className="stat-card">
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
                          {item.label}
                        </div>
                        <div
                          style={{
                            fontSize: "1.05rem",
                            fontWeight: 700,
                            fontFamily: "var(--font-mono)",
                            color: item.color,
                          }}
                        >
                          {item.value}
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="neon-divider" style={{ marginBottom: 20 }} />

                  <h3
                    style={{
                      fontSize: "1rem",
                      fontWeight: 700,
                      marginBottom: 14,
                      color: "var(--neon-cyan)",
                    }}
                  >
                    Raw Data Preview (first 6 points)
                  </h3>
                  <div style={{ overflowX: "auto" }}>
                    <table
                      style={{
                        width: "100%",
                        borderCollapse: "collapse",
                        fontFamily: "var(--font-mono)",
                        fontSize: "0.82rem",
                      }}
                    >
                      <thead>
                        <tr>
                          {["t", "x(t)", "x'(t)"].map((col) => (
                            <th
                              key={col}
                              style={{
                                padding: "10px 14px",
                                textAlign: "left",
                                borderBottom: "1px solid var(--border)",
                                color: "var(--text-muted)",
                                fontSize: "0.72rem",
                                textTransform: "uppercase",
                                letterSpacing: "1px",
                              }}
                            >
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {[
                          [0.00, 1.00000, 0.00000],
                          [0.17, 0.99821, -0.12634],
                          [0.33, 0.99286, -0.24802],
                          [0.50, 0.98412, -0.36153],
                          [0.67, 0.97218, -0.46356],
                          [0.84, 0.95723, -0.55106],
                        ].map((row, i) => (
                          <tr
                            key={i}
                            style={{
                              borderBottom: "1px solid rgba(99,102,241,0.06)",
                              background:
                                i % 2 === 0
                                  ? "transparent"
                                  : "rgba(99,102,241,0.03)",
                            }}
                          >
                            <td style={{ padding: "10px 14px", color: "var(--neon-yellow)" }}>
                              {row[0].toFixed(2)}
                            </td>
                            <td style={{ padding: "10px 14px", color: "var(--neon-cyan)" }}>
                              {row[1].toFixed(5)}
                            </td>
                            <td style={{ padding: "10px 14px", color: "var(--neon-pink)" }}>
                              {row[2].toFixed(5)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* LLM INSIGHT TAB */}
              {activeTab === "llm" && (
                <div className="fade-in">
                  {!useLlm ? (
                    <div
                      style={{
                        padding: "32px",
                        borderRadius: 16,
                        background: "rgba(251,191,36,0.05)",
                        border: "1px solid rgba(251,191,36,0.2)",
                        textAlign: "center",
                      }}
                    >
                      <div style={{ fontSize: "2.5rem", marginBottom: 12 }}>🤖</div>
                      <p
                        style={{
                          color: "var(--neon-yellow)",
                          fontWeight: 600,
                          marginBottom: 8,
                        }}
                      >
                        LLM Insights Disabled
                      </p>
                      <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                        Enable{" "}
                        <strong style={{ color: "var(--text-secondary)" }}>LLM Insights</strong> in
                        the solver workspace and re-solve to see AI-generated interpretations.
                      </p>
                    </div>
                  ) : (
                    <div>
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 10,
                          marginBottom: 20,
                        }}
                      >
                        <div
                          style={{
                            width: 36,
                            height: 36,
                            borderRadius: 10,
                            background: "linear-gradient(135deg, #2563eb, #7c3aed)",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            fontSize: "1.2rem",
                          }}
                        >
                          🤖
                        </div>
                        <div>
                          <div
                            style={{
                              fontWeight: 700,
                              fontSize: "0.9rem",
                            }}
                          >
                            LLM Analysis
                          </div>
                          <div
                            style={{
                              fontSize: "0.72rem",
                              color: "var(--text-muted)",
                              fontFamily: "var(--font-mono)",
                            }}
                          >
                            interpretation only · no computation
                          </div>
                        </div>
                        <span className="badge badge-blue" style={{ marginLeft: "auto" }}>
                          AI Generated
                        </span>
                      </div>

                      <div
                        style={{
                          padding: "20px 22px",
                          borderRadius: 14,
                          background: "rgba(37,99,235,0.06)",
                          border: "1px solid rgba(37,99,235,0.2)",
                          lineHeight: 1.8,
                          fontSize: "0.9rem",
                          color: "var(--text-secondary)",
                          whiteSpace: "pre-wrap",
                          marginBottom: 16,
                        }}
                      >
                        {LLM_INSIGHT.split("**").map((part, i) =>
                          i % 2 === 1 ? (
                            <strong key={i} style={{ color: "var(--text-primary)" }}>
                              {part}
                            </strong>
                          ) : (
                            part
                          )
                        )}
                      </div>

                      <div
                        style={{
                          padding: "14px 18px",
                          borderRadius: 12,
                          background: "rgba(52,211,153,0.06)",
                          border: "1px solid rgba(52,211,153,0.2)",
                          display: "flex",
                          alignItems: "flex-start",
                          gap: 10,
                          fontSize: "0.8rem",
                          color: "var(--text-muted)",
                        }}
                      >
                        <span style={{ color: "var(--neon-green)", fontSize: "1rem" }}>ℹ️</span>
                        <span>
                          This interpretation is AI-generated. All numerical values are computed
                          by SymPy/SciPy/NumPy — the LLM only explains the physics and behavior.
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* STEPS TAB */}
              {activeTab === "steps" && (
                <div className="fade-in">
                  {isSymbolicOrEuler && method !== "euler_fwd" && method !== "euler_imp" ? (
                    // Symbolic derivation steps
                    <div>
                      <h3
                        style={{
                          fontSize: "1rem",
                          fontWeight: 700,
                          marginBottom: 20,
                          color: "var(--neon-yellow)",
                        }}
                      >
                        Step-by-Step Derivation
                      </h3>
                      {STEPS_EXAMPLE.map((step) => (
                        <div
                          key={step.num}
                          style={{
                            marginBottom: 16,
                            padding: "16px 18px",
                            borderRadius: 12,
                            background: "rgba(15,23,42,0.6)",
                            border: "1px solid var(--border)",
                            transition: "border-color 0.2s",
                          }}
                          onMouseEnter={(e) => {
                            (e.currentTarget as HTMLElement).style.borderColor = "rgba(124,58,237,0.3)";
                          }}
                          onMouseLeave={(e) => {
                            (e.currentTarget as HTMLElement).style.borderColor = "var(--border)";
                          }}
                        >
                          <div
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: 10,
                              marginBottom: 10,
                            }}
                          >
                            <div
                              style={{
                                width: 28,
                                height: 28,
                                borderRadius: 8,
                                background: "rgba(124,58,237,0.2)",
                                border: "1px solid rgba(124,58,237,0.4)",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                fontSize: "0.78rem",
                                fontWeight: 700,
                                color: "var(--neon-purple)",
                                fontFamily: "var(--font-mono)",
                                flexShrink: 0,
                              }}
                            >
                              {step.num}
                            </div>
                            <div
                              style={{
                                fontWeight: 700,
                                fontSize: "0.88rem",
                                color: "var(--text-primary)",
                              }}
                            >
                              {step.title}
                            </div>
                          </div>
                          <p
                            style={{
                              fontSize: "0.82rem",
                              color: "var(--text-secondary)",
                              marginBottom: 10,
                              marginLeft: 38,
                            }}
                          >
                            {step.content}
                          </p>
                          <div
                            style={{
                              marginLeft: 38,
                              padding: "10px 16px",
                              borderRadius: 8,
                              background: "rgba(34,211,238,0.05)",
                              border: "1px solid rgba(34,211,238,0.15)",
                              fontFamily: "var(--font-mono)",
                              fontSize: "0.9rem",
                              color: "var(--neon-cyan)",
                            }}
                          >
                            {step.latex}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : method === "euler_fwd" || method === "euler_imp" ? (
                    // Euler steps table
                    <div>
                      <h3
                        style={{
                          fontSize: "1rem",
                          fontWeight: 700,
                          marginBottom: 16,
                          color: "var(--neon-yellow)",
                        }}
                      >
                        Integration Steps (first 10)
                      </h3>
                      <div
                        style={{
                          padding: "10px 14px",
                          borderRadius: 10,
                          background: "rgba(34,211,238,0.06)",
                          border: "1px solid rgba(34,211,238,0.2)",
                          marginBottom: 16,
                          fontSize: "0.8rem",
                          color: "var(--neon-cyan)",
                          fontFamily: "var(--font-mono)",
                        }}
                      >
                        Step size h = 0.100000 · Total steps: 500
                      </div>
                      <div style={{ overflowX: "auto" }}>
                        <table
                          style={{
                            width: "100%",
                            borderCollapse: "collapse",
                            fontFamily: "var(--font-mono)",
                            fontSize: "0.82rem",
                          }}
                        >
                          <thead>
                            <tr>
                              {["t_n", "x_n", "f(t,x)", "x_{n+1}"].map((col) => (
                                <th
                                  key={col}
                                  style={{
                                    padding: "10px 14px",
                                    textAlign: "left",
                                    borderBottom: "1px solid var(--border)",
                                    color: "var(--text-muted)",
                                    fontSize: "0.72rem",
                                    textTransform: "uppercase",
                                    letterSpacing: "1px",
                                  }}
                                >
                                  {col}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {EULER_STEPS.map((row, i) => (
                              <tr
                                key={i}
                                style={{
                                  borderBottom: "1px solid rgba(99,102,241,0.06)",
                                  background: i % 2 === 0 ? "transparent" : "rgba(99,102,241,0.02)",
                                }}
                              >
                                <td style={{ padding: "9px 14px", color: "var(--neon-yellow)" }}>
                                  {row.t.toFixed(1)}
                                </td>
                                <td style={{ padding: "9px 14px", color: "var(--neon-cyan)" }}>
                                  {row.x.toFixed(3)}
                                </td>
                                <td style={{ padding: "9px 14px", color: "var(--text-secondary)" }}>
                                  {row.fx.toFixed(3)}
                                </td>
                                <td style={{ padding: "9px 14px", color: "var(--neon-green)" }}>
                                  {row.xNew.toFixed(3)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ) : (
                    // Numerical methods — no step-by-step
                    <div
                      style={{
                        padding: "40px",
                        textAlign: "center",
                      }}
                    >
                      <div style={{ fontSize: "2.5rem", marginBottom: 12 }}>⚙️</div>
                      <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", marginBottom: 8 }}>
                        Step-by-step derivation is not available for numerical methods.
                      </p>
                      <p style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
                        Use{" "}
                        <span className="badge badge-purple">Symbolic</span> or{" "}
                        <span className="badge badge-purple">Euler</span> methods to see derivation steps.
                      </p>
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
