import React from "react";
import "./globals.css";
import ThemeToggle from "@/components/ThemeToggle";

export const metadata = {
  title: "AI Exam Platform - Bóc tách đề & chấm thi bằng AI",
  description: "Hệ thống bóc tách đề kiểm tra vật lý từ PDF/Word và chấm điểm tự luận tự động bằng mô hình AI.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <head>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.10/dist/katex.min.css" />
      </head>
      <body className="bg-slate-950 text-slate-100 min-h-screen flex flex-col transition-colors duration-300">
        {children}
        <ThemeToggle />
      </body>
    </html>
  );
}
