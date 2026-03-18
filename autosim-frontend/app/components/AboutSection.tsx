"use client";

const METHODS_TABLE = [
  { method: "Symbolic (SymPy)",       type: "Exact",       best: "Linear constant-coefficient ODEs",    badge: "badge-purple" },
  { method: "Laplace Transform",      type: "Exact",       best: "Linear ODEs via s-domain",            badge: "badge-blue"   },
  { method: "RK45",                   type: "Numerical",   best: "General non-stiff problems",          badge: "badge-green"  },
  { method: "Radau",                  type: "Numerical",   best: "Stiff systems (SciPy implicit)",      badge: "badge-green"  },
  { method: "Forward Euler",          type: "Educational", best: "Understanding numerical error",       badge: "badge-yellow" },
  { method: "Improved Euler (Heun's)",type: "Educational", best: "Better accuracy than Forward Euler", badge: "badge-yellow" },
  { method: "Compare All",            type: "Special",     best: "Side-by-side method comparison",     badge: "badge-pink"   },
];

const NOTATION = [
  { input: "x''",      meaning: "Second derivative d²x/dt²" },
  { input: "x'",       meaning: "First derivative dx/dt"     },
  { input: "dx/dt",    meaning: "First derivative (alt.)"    },
  { input: "x**2",     meaning: "x squared"                  },
  { input: "sin(t)",   meaning: "Sine function"              },
  { input: "cos(t)",   meaning: "Cosine function"            },
  { input: "exp(t)",   meaning: "Exponential function"       },
];

export default function AboutSection() {
  return (
    <section
      id="about"
      style={{
        padding: "0 24px 100px",
        maxWidth: 1400,
        margin: "0 auto",
      }}
    >
      {/* Divider */}
      <div className="neon-divider" style={{ marginBottom: 80 }} />

      {/* Header */}
      <div style={{ marginBottom: 48, textAlign: "center" }}>
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "0.75rem",
            color: "var(--neon-pink)",
            letterSpacing: "2px",
            textTransform: "uppercase",
            display: "block",
            marginBottom: 12,
          }}
        >
          04 — About AutoSim
        </span>
        <h2
          style={{
            fontSize: "clamp(1.8rem, 3vw, 2.6rem)",
            fontWeight: 800,
            letterSpacing: "-0.03em",
            marginBottom: 12,
          }}
        >
          Built for <span className="gradient-text">Precision</span>
        </h2>
        <p
          style={{
            color: "var(--text-secondary)",
            fontSize: "1rem",
            maxWidth: 560,
            margin: "0 auto",
            lineHeight: 1.7,
          }}
        >
          A production-grade ODE solver where every number is computed by a
          verified library — SymPy, SciPy, NumPy — never by an AI model.
        </p>
      </div>

      {/* Architecture card */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 24,
          marginBottom: 32,
        }}
      >
        <div className="glass-card" style={{ padding: "28px" }}>
          <h3
            style={{
              fontSize: "1rem",
              fontWeight: 700,
              marginBottom: 16,
              color: "var(--neon-purple)",
            }}
          >
            🏗 System Architecture
          </h3>
          <div
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "0.82rem",
              lineHeight: 2.0,
              color: "var(--text-secondary)",
            }}
          >
            {[
              { step: "User Input",    arrow: "↓", color: "var(--neon-cyan)"   },
              { step: "Parser",        arrow: "↓", color: "var(--neon-blue)"   },
              { step: "Router",        arrow: "↓", color: "var(--neon-purple)" },
              { step: "Solver",        arrow: "↓", color: "var(--neon-green)"  },
              { step: "Visualisation", arrow: "↓", color: "var(--neon-yellow)" },
              { step: "LLM Explanation", arrow: "",color: "var(--neon-pink)"   },
            ].map((item, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div
                  style={{
                    width: 4,
                    height: 16,
                    borderRadius: 2,
                    background: item.color,
                    boxShadow: `0 0 8px ${item.color}`,
                    flexShrink: 0,
                  }}
                />
                <span style={{ color: item.color }}>{item.step}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="glass-card" style={{ padding: "28px" }}>
          <h3
            style={{
              fontSize: "1rem",
              fontWeight: 700,
              marginBottom: 16,
              color: "var(--neon-green)",
            }}
          >
            🔒 Zero Hallucination Stack
          </h3>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 12,
            }}
          >
            {[
              { lib: "SymPy",       role: "Symbolic mathematics",   color: "var(--neon-purple)" },
              { lib: "SciPy",       role: "Numerical integration",  color: "var(--neon-blue)"   },
              { lib: "NumPy",       role: "Array operations",       color: "var(--neon-green)"  },
              { lib: "LLM (Gemini)", role: "Interpretation only",   color: "var(--neon-cyan)"   },
            ].map((item) => (
              <div
                key={item.lib}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  padding: "10px 14px",
                  borderRadius: 10,
                  background: "rgba(15,23,42,0.5)",
                  border: "1px solid var(--border)",
                }}
              >
                <div
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    background: item.color,
                    boxShadow: `0 0 8px ${item.color}`,
                    flexShrink: 0,
                  }}
                />
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.85rem",
                    color: item.color,
                    fontWeight: 600,
                    minWidth: 100,
                  }}
                >
                  {item.lib}
                </span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  {item.role}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Methods table */}
      <div className="glass-card" style={{ padding: "28px", marginBottom: 24 }}>
        <h3
          style={{
            fontSize: "1rem",
            fontWeight: 700,
            marginBottom: 20,
            color: "var(--neon-cyan)",
          }}
        >
          ⚗️ Available Solving Methods
        </h3>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
            <thead>
              <tr>
                {["Method", "Type", "Best For"].map((col) => (
                  <th
                    key={col}
                    style={{
                      padding: "10px 16px",
                      textAlign: "left",
                      borderBottom: "1px solid var(--border)",
                      color: "var(--text-muted)",
                      fontSize: "0.72rem",
                      fontFamily: "var(--font-mono)",
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
              {METHODS_TABLE.map((row, i) => (
                <tr
                  key={i}
                  style={{
                    borderBottom: "1px solid rgba(99,102,241,0.06)",
                    background: i % 2 === 0 ? "transparent" : "rgba(99,102,241,0.02)",
                    transition: "background 0.15s",
                  }}
                  onMouseEnter={(e) =>
                    ((e.currentTarget as HTMLElement).style.background = "rgba(124,58,237,0.06)")
                  }
                  onMouseLeave={(e) =>
                    ((e.currentTarget as HTMLElement).style.background = i % 2 === 0 ? "transparent" : "rgba(99,102,241,0.02)")
                  }
                >
                  <td style={{ padding: "12px 16px", fontWeight: 600, color: "var(--text-primary)" }}>
                    {row.method}
                  </td>
                  <td style={{ padding: "12px 16px" }}>
                    <span className={`badge ${row.badge}`}>{row.type}</span>
                  </td>
                  <td style={{ padding: "12px 16px", color: "var(--text-secondary)", fontSize: "0.82rem" }}>
                    {row.best}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Supported notation */}
      <div className="glass-card" style={{ padding: "28px" }}>
        <h3
          style={{
            fontSize: "1rem",
            fontWeight: 700,
            marginBottom: 20,
            color: "var(--neon-yellow)",
          }}
        >
          ✏️ Supported Equation Notation
        </h3>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
            gap: 10,
          }}
        >
          {NOTATION.map((item) => (
            <div
              key={item.input}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 14,
                padding: "10px 14px",
                borderRadius: 10,
                background: "rgba(15,23,42,0.5)",
                border: "1px solid var(--border)",
              }}
            >
              <code
                style={{
                  fontFamily: "var(--font-mono)",
                  background: "rgba(34,211,238,0.08)",
                  border: "1px solid rgba(34,211,238,0.2)",
                  borderRadius: 6,
                  padding: "3px 10px",
                  color: "var(--neon-cyan)",
                  fontSize: "0.85rem",
                  minWidth: 80,
                  textAlign: "center",
                }}
              >
                {item.input}
              </code>
              <span style={{ fontSize: "0.82rem", color: "var(--text-secondary)" }}>
                {item.meaning}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div
        style={{
          marginTop: 60,
          textAlign: "center",
        }}
      >
        <div className="neon-divider" style={{ marginBottom: 32 }} />
        <p style={{ color: "var(--text-muted)", fontSize: "0.8rem", fontFamily: "var(--font-mono)" }}>
          Built with{" "}
          {["Python", "Next.js", "Tailwind CSS", "SymPy", "SciPy", "NumPy"].map((t, i) => (
            <span key={t}>
              <span style={{ color: "var(--neon-purple)" }}>{t}</span>
              {i < 5 ? " · " : ""}
            </span>
          ))}
        </p>
        <p style={{ color: "var(--text-muted)", fontSize: "0.72rem", marginTop: 8 }}>
          AutoSim © 2025 — Zero Hallucination ODE Solver
        </p>
      </div>
    </section>
  );
}
