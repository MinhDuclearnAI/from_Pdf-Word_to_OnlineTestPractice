"use client";
import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import apiClient from "@/lib/api-client";
import { ChevronLeft, Play, Clock, BookOpen } from "lucide-react";
import Button from "@/components/ui/Button";
import Link from "next/link";
import { SUBJECT_LABELS, TEST_TYPE_LABELS } from "@/lib/constants";

interface Exam {
  id: number;
  title: string;
  subject: string;
  test_type: string;
  duration: number;
}

export default function ExamIntroPage() {
  const { examId } = useParams();
  const router = useRouter();
  const [exam, setExam] = useState<Exam | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchExamDetails = async () => {
      try {
        const { data } = await apiClient.get(`/exams/${examId}`);
        setExam(data);
      } catch (e) {
        console.error("Failed to fetch exam details:", e);
      } finally {
        setLoading(false);
      }
    };
    if (examId) fetchExamDetails();
  }, [examId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <span className="text-slate-400">Đang tải thông tin đề thi...</span>
      </div>
    );
  }

  if (!exam) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 text-center">
        <p className="text-red-400 mb-4 font-semibold">Không tìm thấy đề thi này.</p>
        <Link href="/dashboard" className="text-brand-400 hover:underline">Quay lại Dashboard</Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between">
      {/* Header */}
      <header className="border-b border-slate-900 bg-slate-900/20 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center">
          <Link href="/dashboard" className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors">
            <ChevronLeft size={16} /> Quay lại Dashboard
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow max-w-2xl mx-auto w-full px-6 py-16 flex flex-col justify-center">
        <div className="glass-panel rounded-2xl border border-slate-800 p-8 shadow-2xl space-y-8">
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-brand-500/10 text-brand-400 border border-brand-500/20">
                {SUBJECT_LABELS[exam.subject] || exam.subject}
              </span>
              <span className="text-xs text-slate-400 font-medium">
                {TEST_TYPE_LABELS[exam.test_type] || exam.test_type}
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-100 leading-tight">
              {exam.title}
            </h1>
          </div>

          {/* Details list */}
          <div className="grid grid-cols-2 gap-4 border-y border-slate-800 py-6">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-slate-900 rounded-lg text-slate-400">
                <Clock size={20} />
              </div>
              <div>
                <p className="text-xs text-slate-500 font-medium uppercase">Thời gian</p>
                <p className="text-sm text-slate-200 font-bold mt-0.5">{exam.duration} phút</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-slate-900 rounded-lg text-slate-400">
                <BookOpen size={20} />
              </div>
              <div>
                <p className="text-xs text-slate-500 font-medium uppercase">Hình thức</p>
                <p className="text-sm text-slate-200 font-bold mt-0.5">Làm đề trực tuyến</p>
              </div>
            </div>
          </div>

          {/* Rules/Instructions */}
          <div className="space-y-3">
            <h4 className="font-bold text-slate-200 text-sm">Hướng dẫn làm bài:</h4>
            <ul className="list-disc list-inside text-xs text-slate-400 space-y-2 leading-relaxed">
              <li>Đảm bảo kết nối mạng của bạn ổn định trong suốt quá trình làm bài.</li>
              <li>Hệ thống tự động lưu nháp (Autosave) bài làm của bạn định kỳ để tránh mất dữ liệu.</li>
              <li>Bài thi sẽ tự động khóa và nộp khi hết thời gian đếm ngược.</li>
              <li>Khi đã nộp bài chính thức, bạn không thể quay lại chỉnh sửa câu trả lời.</li>
            </ul>
          </div>

          <Button
            variant="primary"
            className="w-full py-3.5 text-base font-bold shadow-lg shadow-brand-500/10 flex items-center justify-center gap-1.5"
            onClick={() => router.push(`/exam/${exam.id}/play`)}
          >
            <Play size={16} fill="currentColor" /> Bắt đầu làm bài
          </Button>
        </div>
      </main>

      <footer className="max-w-7xl mx-auto w-full px-6 py-8 border-t border-slate-900 text-center text-xs text-slate-500">
        AI Exam Platform • Chúc bạn đạt kết quả tốt nhất!
      </footer>
    </div>
  );
}
