"use client";

import dynamic from "next/dynamic";
import type { Layout, Data, Config } from "plotly.js";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export interface InteractivePlotProps {
  data: Data[];
  layout?: Partial<Layout>;
  config?: Partial<Config>;
  height?: number;
  className?: string;
}

const BASE_LAYOUT: Partial<Layout> = {
  paper_bgcolor: "rgba(3,7,18,0)",
  plot_bgcolor: "rgba(3,7,18,0)",
  font: { family: "JetBrains Mono, monospace", color: "rgba(148,163,184,0.85)", size: 11 },
  margin: { t: 20, b: 40, l: 54, r: 16 },
  xaxis: {
    gridcolor: "rgba(99,102,241,0.1)",
    zerolinecolor: "rgba(148,163,184,0.2)",
    tickfont: { size: 10, color: "rgba(148,163,184,0.6)" },
    linecolor: "rgba(148,163,184,0.2)",
  },
  yaxis: {
    gridcolor: "rgba(99,102,241,0.1)",
    zerolinecolor: "rgba(148,163,184,0.2)",
    tickfont: { size: 10, color: "rgba(148,163,184,0.6)" },
    linecolor: "rgba(148,163,184,0.2)",
  },
  legend: {
    bgcolor: "rgba(15,23,42,0.8)",
    bordercolor: "rgba(99,102,241,0.2)",
    borderwidth: 1,
    font: { size: 11 },
  },
  hoverlabel: {
    bgcolor: "rgba(15,23,42,0.95)",
    bordercolor: "rgba(99,102,241,0.4)",
    font: { family: "JetBrains Mono, monospace", size: 11 },
  },
};

const BASE_CONFIG: Partial<Config> = {
  displaylogo: false,
  modeBarButtonsToRemove: ["select2d", "lasso2d", "autoScale2d"],
  responsive: true,
  toImageButtonOptions: { format: "png", filename: "autosim_plot", width: 1200, height: 600 },
};

export default function InteractivePlot({ data, layout, config, height = 280, className }: InteractivePlotProps) {
  const mergedLayout: Partial<Layout> = {
    ...BASE_LAYOUT,
    ...layout,
    xaxis: { ...BASE_LAYOUT.xaxis, ...layout?.xaxis },
    yaxis: { ...BASE_LAYOUT.yaxis, ...layout?.yaxis },
    legend: { ...BASE_LAYOUT.legend, ...layout?.legend },
    hoverlabel: { ...BASE_LAYOUT.hoverlabel, ...layout?.hoverlabel },
    height,
  };

  return (
    <div
      className={className}
      style={{ borderRadius: 12, background: "rgba(3,7,18,0.5)", border: "1px solid rgba(99,102,241,0.12)", overflow: "hidden" }}
    >
      <Plot
        data={data}
        layout={mergedLayout}
        config={{ ...BASE_CONFIG, ...config }}
        style={{ width: "100%", height: "100%" }}
        useResizeHandler
      />
    </div>
  );
}
