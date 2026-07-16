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
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between">
      {/* Header */}
      <header className="border-b border-slate-900 bg-slate-900/20 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors">
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
          <div className="p-3 bg-brand-500/10 rounded-full text-brand-500 border border-brand-500/20 w-fit mx-auto mb-1">
            <Brain size={28} />
          </div>
          <h2 className="text-xl font-bold text-slate-100">Upload Đề Tự Luyện Tập</h2>
          <p className="text-sm text-slate-400 max-w-sm mx-auto">
            Hệ thống AI sẽ tự động phân tích đề thi và tạo một bài luyện tập trực tuyến cho bạn.
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

      <footer className="max-w-7xl mx-auto w-full px-6 py-8 border-t border-slate-900 text-center text-xs text-slate-500">
        AI bóc tách đề thi hỗ trợ file PDF gốc, PDF scan, Word (DOCX/DOC).
      </footer>
    </div>
  );
}
