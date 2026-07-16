"use client";
import React, { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import apiClient from "@/lib/api-client";
import FileDropzone from "@/components/upload/FileDropzone";
import AIProcessingStatus from "@/components/upload/AIProcessingStatus";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import { ChevronLeft, Brain, GraduationCap } from "lucide-react";
import Link from "next/link";

interface ClassData {
  id: number;
  name: string;
}

function NewExamContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const classIdParam = searchParams.get("class_id");

  const [classes, setClasses] = useState<ClassData[]>([]);
  const [selectedClassId, setSelectedClassId] = useState<string>(classIdParam || "");
  const [title, setTitle] = useState("");
  const [subject, setSubject] = useState("");
  const [duration, setDuration] = useState(60);
  const [testType, setTestType] = useState("exam");

  const [jobId, setJobId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchClasses = async () => {
      try {
        const { data } = await apiClient.get("/classes/");
        const publicClasses = data.filter((c: any) => c.subject !== "Self-Practice");
        setClasses(publicClasses);
        if (publicClasses.length > 0 && !selectedClassId) {
          setSelectedClassId(String(publicClasses[0].id));
        }
      } catch (e) {
        console.error("Failed to load classes:", e);
      }
    };
    fetchClasses();
  }, [selectedClassId]);

  const handleFileSelect = async (file: File) => {
    if (!selectedClassId || !title || !subject) {
      setError("Vui lòng nhập đầy đủ tiêu đề, lớp học và môn học trước khi tải tệp lên.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("class_id", selectedClassId);
      formData.append("title", title);
      formData.append("duration", String(duration));
      formData.append("test_type", testType);
      formData.append("subject", subject);

      // Call teacher upload endpoint
      const { data } = await apiClient.post("/exams/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setJobId(data.job_id);
    } catch (e: any) {
      console.error("Failed to upload exam:", e);
      setError(e.response?.data?.message || "Có lỗi xảy ra khi tạo đề thi.");
    } finally {
      setLoading(false);
    }
  };

  const redirectPath = selectedClassId ? `/classes/${selectedClassId}` : "/dashboard";

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between">
      {/* Header */}
      <header className="border-b border-slate-900 bg-slate-900/20 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href={redirectPath} className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors">
            <ChevronLeft size={16} /> Quay lại
          </Link>
          <div className="flex items-center gap-2">
            <GraduationCap className="text-brand-500" size={24} />
            <span className="font-extrabold text-sm tracking-tight">AI Exam Platform</span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-grow max-w-xl mx-auto w-full px-6 py-10 space-y-6">
        <div className="text-center space-y-2">
          <div className="p-3 bg-brand-500/10 rounded-full text-brand-500 border border-brand-500/20 w-fit mx-auto mb-1">
            <Brain size={28} />
          </div>
          <h2 className="text-xl font-bold text-slate-100">Tạo Đề Thi Mới Bằng AI</h2>
          <p className="text-sm text-slate-400 max-w-sm mx-auto">
            Nhập cấu hình đề thi, sau đó tải lên tệp PDF hoặc Word đề bài để hệ thống AI tiến hành bóc tách.
          </p>
        </div>

        {error && (
          <div className="p-4 bg-red-950/40 border border-red-800/40 rounded-xl text-sm text-red-400 text-center">
            {error}
          </div>
        )}

        {!jobId ? (
          <form className="space-y-4 bg-slate-900/40 p-6 border border-slate-800 rounded-xl">
            <Input
              label="Tiêu đề đề thi / bài kiểm tra"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Ví dụ: Kiểm tra 15 phút - Chương 1: Động Lực Học"
              required
              disabled={loading}
            />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="w-full">
                <label className="block text-sm font-medium text-slate-300 mb-1.5">Lớp học chỉ định</label>
                <select
                  value={selectedClassId}
                  onChange={(e) => setSelectedClassId(e.target.value)}
                  className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                  required
                  disabled={loading}
                >
                  <option value="" disabled>-- Chọn lớp học --</option>
                  {classes.map((cls) => (
                    <option key={cls.id} value={cls.id}>{cls.name}</option>
                  ))}
                </select>
              </div>

              <Input
                label="Thời gian làm bài (phút)"
                type="number"
                min={1}
                value={duration}
                onChange={(e) => setDuration(Number(e.target.value))}
                required
                disabled={loading}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="w-full">
                <label className="block text-sm font-medium text-slate-300 mb-1.5">Môn học</label>
                <select
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                  required
                  disabled={loading}
                >
                  <option value="" disabled>-- Chọn môn học --</option>
                  <option value="Toán Học">Toán Học</option>
                  <option value="Vật Lý">Vật Lý</option>
                  <option value="Hóa Học">Hóa Học</option>
                  <option value="Sinh Học">Sinh Học</option>
                  <option value="Ngữ Văn">Ngữ Văn</option>
                  <option value="Tiếng Anh">Tiếng Anh</option>
                  <option value="Lịch Sử">Lịch Sử</option>
                  <option value="Địa Lý">Địa Lý</option>
                  <option value="GDCD">GDCD</option>
                  <option value="Tin Học">Tin Học</option>
                </select>
              </div>

              <div className="w-full">
                <label className="block text-sm font-medium text-slate-300 mb-1.5">Dạng bài thi</label>
                <select
                  value={testType}
                  onChange={(e) => setTestType(e.target.value)}
                  className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                  disabled={loading}
                >
                  <option value="exam">Đề kiểm tra chính thức (Exam)</option>
                  <option value="homework">Bài tập về nhà (Homework)</option>
                  <option value="practice">Luyện tập thêm (Practice)</option>
                </select>
              </div>
            </div>

            <div className="border-t border-slate-800/80 pt-6">
              <label className="block text-sm font-medium text-slate-400 mb-3">Tải tệp đề kiểm tra</label>
              <FileDropzone onFileSelect={handleFileSelect} disabled={loading || !title || !selectedClassId} />
            </div>
          </form>
        ) : (
          <AIProcessingStatus
            jobId={jobId}
            onComplete={(examId) => {
              // Redirect to question review page
              router.push(`/exams/${examId}/edit`);
            }}
            onFailed={(err) => {
              setError(err);
              setJobId(null);
            }}
          />
        )}
      </main>

      <footer className="max-w-7xl mx-auto w-full px-6 py-8 border-t border-slate-900 text-center text-xs text-slate-500">
        AI Exam Platform • Trợ lý bóc tách tệp PDF/Word.
      </footer>
    </div>
  );
}

export default function NewExamPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <span className="text-slate-400">Đang tải...</span>
      </div>
    }>
      <NewExamContent />
    </Suspense>
  );
}
