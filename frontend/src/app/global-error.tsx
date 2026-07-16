"use client";

import React from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  React.useEffect(() => {
    console.error("GLOBAL CRASH:", error);
  }, [error]);

  return (
    <html lang="vi">
      <body style={{ background: "#0b0f19", color: "#f1f5f9", fontFamily: "sans-serif", padding: "2rem" }}>
        <div style={{ maxWidth: "600px", margin: "4rem auto", background: "#1e293b", borderRadius: "1rem", padding: "2rem", border: "1px solid #ef4444" }}>
          <h2 style={{ color: "#f87171", marginBottom: "1rem" }}>⚠️ Lỗi hệ thống</h2>
          <p style={{ color: "#94a3b8", marginBottom: "0.5rem" }}>Thông báo lỗi:</p>
          <pre style={{ background: "#0f172a", padding: "1rem", borderRadius: "0.5rem", fontSize: "0.75rem", color: "#fca5a5", overflowX: "auto", whiteSpace: "pre-wrap", marginBottom: "1.5rem" }}>
            {error?.message}
            {"\n"}
            {error?.stack}
          </pre>
          <button
            onClick={reset}
            style={{ background: "#3b6eff", color: "white", padding: "0.5rem 1.5rem", borderRadius: "0.5rem", border: "none", cursor: "pointer", fontWeight: "600" }}
          >
            Thử lại
          </button>
          <a
            href="/login"
            style={{ marginLeft: "1rem", color: "#6b9aff", textDecoration: "underline" }}
          >
            Về trang đăng nhập
          </a>
        </div>
      </body>
    </html>
  );
}
