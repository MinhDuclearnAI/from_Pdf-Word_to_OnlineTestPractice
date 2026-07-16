"use client";

import React from "react";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  React.useEffect(() => {
    console.error("Dashboard crash error:", error);
  }, [error]);

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-8 text-center">
      <div className="max-w-lg w-full bg-red-950/30 border border-red-800/50 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-red-400 mb-4">Đã xảy ra lỗi</h2>
        <pre className="text-left text-xs text-red-300 bg-slate-900 rounded-lg p-4 overflow-auto max-h-64 mb-6 whitespace-pre-wrap">
          {error?.message || "Unknown error"}
          {"\n\n"}
          {error?.stack}
        </pre>
        <button
          onClick={reset}
          className="px-6 py-2 bg-brand-500 hover:bg-brand-600 text-white font-semibold rounded-lg transition-colors"
        >
          Thử lại
        </button>
      </div>
    </div>
  );
}
