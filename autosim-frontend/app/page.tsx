"use client";

import { useState } from "react";
import Navbar from "./components/Navbar";
import HeroSection from "./components/HeroSection";
import SolverWorkspace from "./components/SolverWorkspace";
import PlotlyPanel from "./components/PlotlyPanel";
import ResultTabs from "./components/ResultTabs";
import type { SolverCodeResult } from "./components/ResultTabs";
import AboutSection from "./components/AboutSection";

const API_BASE = "http://localhost:8000";

interface SolveParams {
  equation: string;
  x0: number;
  dx0: number;
  tStart: number;
  tEnd: number;
  method: string;
  useLlm: boolean;
  wolframKey: string;
}

export interface SolveResult {
  t: number[];
  y: number[][];
  stats: Record<string, number>;
  method: string;
  success: boolean;
  message: string;
  classification?: Record<string, unknown>;
}

export interface VerificationSource {
  name: string;
  status: "pass" | "fail" | "skip" | "error";
  message: string;
  max_error: number | null;
  mean_error: number | null;
  confidence: number | null;
  reference_t: number[] | null;
  reference_y: number[] | null;
  details?: { 
  formula?: string;
  comparison_table?: Record<string, unknown>[];
  E0?: number;
};
}

export interface VerificationReport {
  sources: VerificationSource[];
  overall_status: "verified" | "warning" | "failed" | "partial";
  overall_confidence: number;
  summary: string;
  compute_ms: number;
}

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const [solved, setSolved] = useState(false);
  const [solveParams, setSolveParams] = useState<SolveParams>({
    equation: "x'' + 0.2*x' + x = cos(t)",
    x0: 1,
    dx0: 0,
    tStart: 0,
    tEnd: 50,
    method: "rk45",
    useLlm: false,
    wolframKey: "",
  });
  const [solveResult, setSolveResult] = useState<SolveResult | null>(null);
  const [verifReport, setVerifReport] = useState<VerificationReport | null>(null);
  const [verifLoading, setVerifLoading] = useState(false);
  const [solveError, setSolveError] = useState<string | null>(null);
  const [codeResult, setCodeResult] = useState<SolverCodeResult | null>(null);
  const [codeLoading, setCodeLoading] = useState(false);

  const handleSolve = async (params: SolveParams) => {
    setIsLoading(true);
    setSolved(false);
    setSolveResult(null);
    setVerifReport(null);
    setVerifLoading(false);
    setSolveError(null);
    setCodeResult(null);
    setCodeLoading(false);
    setSolveParams(params);

    try {
      // ── Step 1: call /solve ────────────────────────────────────────────
      const solveRes = await fetch(`${API_BASE}/solve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          equation: params.equation,
          ic: { x: params.x0, dx: params.dx0 },
          time_span: [params.tStart, params.tEnd],
          method: params.method,
          use_llm: params.useLlm,
        }),
      });

      if (!solveRes.ok) {
        const err = await solveRes.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(err.detail ?? `HTTP ${solveRes.status}`);
      }

      const result: SolveResult = await solveRes.json();
      setSolveResult(result);
      setIsLoading(false);
      setSolved(true);

      // Smooth scroll to visualization
      setTimeout(() => {
        document.getElementById("visualization")?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }, 200);

      // ── Step 2: call /verify + /generate-solver in parallel ───────────────
      setVerifLoading(true);
      setCodeLoading(true);

      // Fire both in parallel
      const verifyPromise = fetch(`${API_BASE}/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          equation: params.equation,
          ic: { x: params.x0, dx: params.dx0 },
          time_span: [params.tStart, params.tEnd],
          result: {
            t: result.t,
            y: result.y,
            method: result.method,
            stats: result.stats,
          },
          wolfram_key: params.wolframKey || null,
        }),
      });

      const codePromise = fetch(`${API_BASE}/generate-solver`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          equation: params.equation,
          ic: { x: params.x0, dx: params.dx0 },
          time_span: [params.tStart, params.tEnd],
        }),
      });

      // Handle verify
      verifyPromise
        .then((r) => r.ok ? r.json() : null)
        .then((report) => { if (report) setVerifReport(report); })
        .catch(() => {})
        .finally(() => setVerifLoading(false));

      // Handle code generation
      codePromise
        .then((r) => r.ok ? r.json() : null)
        .then((code) => { if (code) setCodeResult(code as SolverCodeResult); })
        .catch(() => {})
        .finally(() => setCodeLoading(false));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setSolveError(msg);
      setIsLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg-primary)" }}>
      <Navbar />

      <main>
        {/* Hero */}
        <HeroSection />

        {/* Main workspace area */}
        <div
          style={{
            background: "linear-gradient(to bottom, transparent, rgba(99,102,241,0.03) 50%, transparent)",
          }}
        >
          {/* Solver workspace */}
          <SolverWorkspace onSolve={handleSolve} isLoading={isLoading} />

          {/* API error banner */}
          {solveError && (
            <div
              style={{
                maxWidth: 1400,
                margin: "0 auto 24px",
                padding: "0 24px",
              }}
            >
              <div
                style={{
                  padding: "14px 18px",
                  borderRadius: 12,
                  background: "rgba(220,38,38,0.08)",
                  border: "1px solid rgba(220,38,38,0.3)",
                  color: "#fca5a5",
                  fontSize: "0.85rem",
                  fontFamily: "var(--font-mono)",
                }}
              >
                ❌ Solver error: {solveError}
                <span
                  style={{ float: "right", color: "var(--text-muted)", fontSize: "0.75rem", paddingTop: 2 }}
                >
                  Is the FastAPI server running at localhost:8000?
                </span>
              </div>
            </div>
          )}

          {/* Visualization panel */}
          <PlotlyPanel
            method={solveParams.method}
            equation={solveParams.equation}
            tEnd={solveParams.tEnd}
            solved={solved}
            solveResult={solveResult}
          />

          {/* Result tabs */}
          <ResultTabs
            solved={solved}
            method={solveParams.method}
            equation={solveParams.equation}
            useLlm={solveParams.useLlm}
            solveResult={solveResult}
            verifReport={verifReport}
            verifLoading={verifLoading}
            codeResult={codeResult}
            codeLoading={codeLoading}
          />
        </div>

        {/* About */}
        <AboutSection />
      </main>
    </div>
  );
}
