"use client";
import React, { useState } from "react";
import { useRouter } from "next/navigation";
import FileDropzone from "@/components/upload/FileDropzone";
import AIProcessingStatus from "@/components/upload/AIProcessingStatus";
import apiClient from "@/lib/api-client";
import { ChevronLeft, Brain, GraduationCap, Clock } from "lucide-react";
import Link from "next/link";

const SUBJECT_OPTIONS = [
  { value: "IELTS", label: "IELTS Reading / Listening" },
  { value: "Toán Học", label: "Toán Học" },
  { value: "Vật Lý", label: "Vật Lý" },
  { value: "Hóa Học", label: "Hóa Học" },
  { value: "Sinh Học", label: "Sinh Học" },
  { value: "Tiếng Anh", label: "Tiếng Anh (THPT Quốc Gia)" },
  { value: "Lịch Sử", label: "Lịch Sử" },
  { value: "Địa Lý", label: "Địa Lý" },
  { value: "GDCD", label: "Giáo Dục Công Dân (GDCD)" },
  { value: "HSA", label: "Đánh Giá Năng Lực (HSA)" },
];

export default function PracticeUploadPage() {
  const router = useRouter();
  const [subject, setSubject] = useState("");
  const [duration, setDuration] = useState<string>("");
  const [jobId, setJobId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = async (file: File) => {
    if (!subject) {
      setError("Vui lòng chọn môn học / loại đề trước khi tải file lên.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("subject", subject);
      if (duration && parseInt(duration) > 0) {
        formData.append("duration", duration);
      }
      const { data } = await apiClient.post("/practice/upload-quick", formData);
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
          <div className="space-y-4">
            {/* Subject + Duration card */}
            <div className="bg-white p-5 border border-slate-200 rounded-2xl shadow-sm space-y-4">
              {/* Subject select */}
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  Môn học / Loại đề <span className="text-red-400">*</span>
                </label>
                <select
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-400 transition-all text-sm"
                  disabled={loading}
                >
                  <option value="" disabled>-- Chọn môn học --</option>
                  {SUBJECT_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              {/* Duration */}
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                  <span className="flex items-center gap-1.5">
                    <Clock size={14} className="text-slate-400" />
                    Thời gian làm bài (phút)
                    <span className="text-xs font-normal text-slate-400">— để trống để AI tự phân tích</span>
                  </span>
                </label>
                <div className="relative">
                  <input
                    type="number"
                    min={5}
                    max={300}
                    value={duration}
                    onChange={(e) => setDuration(e.target.value)}
                    placeholder="Ví dụ: 60"
                    disabled={loading}
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-400 transition-all text-sm pr-16"
                  />
                  <span className="absolute right-4 top-1/2 -translate-y-1/2 text-xs text-slate-400 font-medium pointer-events-none">phút</span>
                </div>
              </div>
            </div>

            {/* File dropzone */}
            <div className={!subject ? "opacity-50 pointer-events-none" : ""}>
              <FileDropzone onFileSelect={handleFileSelect} disabled={loading || !subject} />
            </div>
          </div>
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

      <footer className="max-w-7xl mx-auto w-full px-6 py-6 border-t border-slate-200 text-center text-xs text-slate-400">
        AI bóc tách đề thi hỗ trợ PDF gốc, PDF scan, Word (DOCX/DOC). Dữ liệu của bạn được bảo mật.
      </footer>
    </div>
  );
}
