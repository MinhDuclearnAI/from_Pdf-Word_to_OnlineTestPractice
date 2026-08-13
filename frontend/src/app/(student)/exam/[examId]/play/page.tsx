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
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <span className="text-slate-500">Đang chuẩn bị đề thi...</span>
      </div>
    );
  }

  if (error || !exam) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-6 text-center">
        <p className="text-red-400 mb-4 font-semibold">{error || "Không tìm thấy dữ liệu bài thi."}</p>
        <Link href="/dashboard" className="text-brand-400 hover:underline">Quay lại Dashboard</Link>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen overflow-hidden bg-white text-slate-800 flex flex-col">
      <ExamPlayer exam={exam} questions={questions} examId={examId} />
    </div>
  );
}
