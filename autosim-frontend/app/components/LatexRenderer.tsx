"use client";

import { useEffect, useRef } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";

export default function LatexRenderer({ latex, color }: { latex: string; color?: string }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current) return;
    try {
      katex.render(latex, ref.current, {
        displayMode: true,
        throwOnError: false,
        output: "html",
      });
    } catch {
      if (ref.current) ref.current.textContent = latex;
    }
  }, [latex]);

  return (
    <div
      ref={ref}
      style={{ color: color ?? "inherit", overflowX: "auto" }}
    />
  );
}
