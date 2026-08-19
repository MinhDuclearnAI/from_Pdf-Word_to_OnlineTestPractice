import React from "react";
import { Plus_Jakarta_Sans, Merriweather } from "next/font/google";
import "./globals.css";
import ThemeToggle from "@/components/ThemeToggle";

const plusJakartaSans = Plus_Jakarta_Sans({ 
  subsets: ["vietnamese", "latin"],
  variable: "--font-sans",
});

const merriweather = Merriweather({
  weight: ["300", "400", "700", "900"],
  subsets: ["vietnamese", "latin"],
  variable: "--font-serif",
});

export const metadata = {
  title: "AI Exam Platform - Bóc tách đề & chấm thi bằng AI",
  description: "Hệ thống bóc tách đề kiểm tra vật lý từ PDF/Word và chấm điểm tự luận tự động bằng mô hình AI.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi" className={`${plusJakartaSans.variable} ${merriweather.variable}`}>
      <head>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.10/dist/katex.min.css" />
      </head>
      <body className="bg-slate-50 text-slate-800 min-h-screen flex flex-col transition-colors duration-300 font-sans">
        {children}
        <ThemeToggle />
      </body>
    </html>
  );
}
