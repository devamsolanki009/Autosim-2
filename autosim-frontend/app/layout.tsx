import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "AutoSim — ODE Solver Dashboard",
  description:
    "A zero-hallucination ODE solver powered by SymPy, SciPy, NumPy, and LLM-enhanced insights. Solve ordinary differential equations symbolically, numerically, and via Laplace transforms.",
  keywords: ["ODE solver", "differential equations", "SymPy", "SciPy", "numerical methods", "AutoSim"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${jetbrainsMono.variable} antialiased`}>
        {children}
      </body>
    </html>
  );
}
