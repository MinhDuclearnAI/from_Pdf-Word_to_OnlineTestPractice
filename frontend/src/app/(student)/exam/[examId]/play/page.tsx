"use client";
import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import apiClient from "@/lib/api-client";
import ExamPlayer from "@/components/exam-player/ExamPlayer";
import { ChevronLeft } from "lucide-react";
import Link from "next/link";

export default function ExamPlayPage() {
  const { examId } = useParams();
  const [exam, setExam] = useState<any>(null);
  const [questions, setQuestions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadExamAndQuestions = async () => {
      try {
        const [examRes, questionsRes] = await Promise.all([
          apiClient.get(`/exams/${examId}`),
          apiClient.get(`/exams/${examId}/questions`),
        ]);
        setExam(examRes.data);
        setQuestions(questionsRes.data);
      } catch (e: any) {
        console.error("Failed to load exam data:", e);
        setError("Không thể tải dữ liệu bài thi. Vui lòng kiểm tra lại quyền truy cập hoặc kết nối.");
      } finally {
        setLoading(false);
      }
    };
    if (examId) loadExamAndQuestions();
  }, [examId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <span className="text-slate-400">Đang chuẩn bị đề thi...</span>
      </div>
    );
  }

  if (error || !exam) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 text-center">
        <p className="text-red-400 mb-4 font-semibold">{error || "Không tìm thấy dữ liệu bài thi."}</p>
        <Link href="/dashboard" className="text-brand-400 hover:underline">Quay lại Dashboard</Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Header with Exit Link */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur py-2.5 px-4 md:px-6 sticky top-0 z-30">
        <div className="max-w-[1920px] mx-auto flex items-center justify-between">
          <Link
            href={`/exam/${examId}`}
            className="flex items-center gap-1.5 text-xs font-semibold text-slate-300 hover:text-brand-400 transition-colors bg-slate-800/60 hover:bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700/50"
            onClick={(e) => {
              if (!confirm("Bạn có chắc chắn muốn thoát khỏi phòng thi? Bài làm chưa nộp sẽ chỉ được lưu nháp.")) {
                e.preventDefault();
              }
            }}
          >
            <ChevronLeft size={16} /> Thoát phòng thi
          </Link>
          <div className="text-xs text-slate-400 font-medium hidden sm:block">
            Phòng thi trực tuyến • <span className="text-brand-400 font-bold">{exam.title}</span>
          </div>
        </div>
      </header>

      {/* Main Exam Player View - Full Screen Workspace */}
      <main className="flex-grow w-full max-w-[1920px] mx-auto px-3 md:px-6 py-4 flex flex-col">
        <ExamPlayer exam={exam} questions={questions} />
      </main>
    </div>
  );
}
