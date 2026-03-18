"use client";

import { useState } from "react";
import Navbar from "./components/Navbar";
import HeroSection from "./components/HeroSection";
import SolverWorkspace from "./components/SolverWorkspace";
import PlotlyPanel from "./components/PlotlyPanel";
import ResultTabs from "./components/ResultTabs";
import AboutSection from "./components/AboutSection";

interface SolveParams {
  equation: string;
  x0: number;
  dx0: number;
  tStart: number;
  tEnd: number;
  method: string;
  useLlm: boolean;
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
  });

  const handleSolve = async (params: SolveParams) => {
    setIsLoading(true);
    setSolved(false);
    setSolveParams(params);

    // Simulate API call delay (replace with real API call to Python backend)
    await new Promise((resolve) => setTimeout(resolve, 1200));

    setIsLoading(false);
    setSolved(true);

    // Smooth scroll to visualization
    setTimeout(() => {
      document.getElementById("visualization")?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }, 200);
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

          {/* Visualization panel */}
          <PlotlyPanel
            method={solveParams.method}
            equation={solveParams.equation}
            tEnd={solveParams.tEnd}
            solved={solved}
          />

          {/* Result tabs */}
          <ResultTabs
            solved={solved}
            method={solveParams.method}
            equation={solveParams.equation}
            useLlm={solveParams.useLlm}
          />
        </div>

        {/* About */}
        <AboutSection />
      </main>
    </div>
  );
}
