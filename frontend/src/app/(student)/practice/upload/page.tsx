"use client";
import React, { useState } from "react";
import { useRouter } from "next/navigation";
import FileDropzone from "@/components/upload/FileDropzone";
import AIProcessingStatus from "@/components/upload/AIProcessingStatus";
import apiClient from "@/lib/api-client";
import { ChevronLeft, Brain, GraduationCap } from "lucide-react";
import Link from "next/link";

export default function PracticeUploadPage() {
  const router = useRouter();
  const [jobId, setJobId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = async (file: File) => {
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);

      // Call student quick upload endpoint
      const { data } = await apiClient.post("/practice/upload-quick", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setJobId(data.job_id);
    } catch (e: any) {
      console.error("Failed to upload file:", e);
      setError(e.response?.data?.message || "Có lỗi xảy ra khi tải đề lên hệ thống.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col justify-between">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white/20 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-1.5 text-xs text-slate-500 hover transition-colors">
            <ChevronLeft size={16} /> Quay lại Dashboard
          </Link>
          <div className="flex items-center gap-2">
            <GraduationCap className="text-brand-500" size={24} />
            <span className="font-extrabold text-sm tracking-tight">AI Exam Platform</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow max-w-xl mx-auto w-full px-6 py-12 flex flex-col justify-center space-y-6">
        <div className="text-center space-y-2 mb-4">
          <div className="p-3.5 bg-brand-500/15 rounded-2xl text-brand-400 border border-brand-500/30 w-fit mx-auto mb-2 shadow-lg">
            <Brain size={32} />
          </div>
          <h2 className="text-2xl font-black text-slate-800">Upload Đề Tự Luyện Tập</h2>
          <p className="text-sm text-slate-500 max-w-md mx-auto leading-relaxed">
            Hệ thống AI sẽ tự động bóc tách đề thi (PDF/Word) và thiết lập bài luyện tập trực tuyến 1 trang liền mạch cho bạn.
          </p>
        </div>

        {error && (
          <div className="p-4 bg-red-950/40 border border-red-800/40 rounded-xl text-sm text-red-400 text-center">
            {error}
          </div>
        )}

        {!jobId ? (
          <FileDropzone onFileSelect={handleFileSelect} disabled={loading} />
        ) : (
          <AIProcessingStatus
            jobId={jobId}
            onComplete={(examId) => {
              // Redirect directly to play screen
              router.push(`/exam/${examId}`);
            }}
            onFailed={(err) => {
              setError(err);
              setJobId(null);
            }}
          />
        )}
      </main>

      <footer className="max-w-7xl mx-auto w-full px-6 py-8 border-t border-slate-200 text-center text-xs text-slate-500">
        AI bóc tách đề thi hỗ trợ file PDF gốc, PDF scan, Word (DOCX/DOC).
      </footer>
    </div>
  );
}
