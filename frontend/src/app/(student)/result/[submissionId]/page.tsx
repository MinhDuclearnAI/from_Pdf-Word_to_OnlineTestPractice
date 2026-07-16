"use client";
import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import apiClient from "@/lib/api-client";
import { ChevronLeft, CheckCircle2, XCircle, AlertCircle, Calendar, Award, RefreshCw } from "lucide-react";
import Link from "next/link";
import Button from "@/components/ui/Button";

interface Submission {
  id: number;
  exam_id: number;
  exam_title: string;
  student_id: number;
  student_email: string;
  score: number;
  status: string;
  submitted_at: string;
  answers: Record<string, any>;
  score_details?: Record<string, {
    score: number;
    max_score: number;
    is_correct: boolean;
    explanation?: string;
  }>;
}

interface Question {
  id: number;
  component_type: string;
  question_text: string;
  options: string[];
  correct_answer?: string;
  score_weight: number;
}

export default function ResultPage() {
  const { submissionId } = useParams();
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchResults = async () => {
    try {
      const { data: subData } = await apiClient.get(`/submissions/${submissionId}`);
      setSubmission(subData);

      if (subData.exam_id) {
        const { data: qData } = await apiClient.get(`/exams/${subData.exam_id}/questions`);
        setQuestions(qData);
      }
    } catch (e) {
      console.error("Failed to load results:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (submissionId) {
      fetchResults();
    }
  }, [submissionId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <span className="text-slate-400">Đang tải kết quả bài làm...</span>
      </div>
    );
  }

  if (!submission) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 text-center">
        <p className="text-red-400 mb-4 font-semibold">Không tìm thấy kết quả bài làm này.</p>
        <Link href="/dashboard" className="text-brand-400 hover:underline">Quay lại Dashboard</Link>
      </div>
    );
  }

  const isCompleted = submission.status === "completed";
  const isPending = submission.status === "pending_grading" || submission.status === "submitted";

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between">
      {/* Header */}
      <header className="border-b border-slate-900 bg-slate-900/20 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors">
            <ChevronLeft size={16} /> Quay lại Dashboard
          </Link>
          {isPending && (
            <Button variant="secondary" size="sm" onClick={fetchResults} className="flex items-center gap-1">
              <RefreshCw size={14} className="animate-spin mr-1" /> Tải lại trạng thái
            </Button>
          )}
        </div>
      </header>

      {/* Content */}
      <main className="flex-grow max-w-4xl mx-auto w-full px-6 py-10 space-y-8">
        {/* Score Summary Card */}
        <div className="glass-panel rounded-2xl border border-slate-800 p-6 md:p-8 flex flex-col md:flex-row items-center justify-between gap-6 shadow-2xl relative overflow-hidden">
          <div className="absolute -top-12 -left-12 w-40 h-40 rounded-full bg-brand-500/5 blur-3xl pointer-events-none" />
          <div className="space-y-4 text-center md:text-left">
            <h1 className="text-xl md:text-2xl font-extrabold text-slate-100 leading-tight">
              Kết quả bài thi trực tuyến
            </h1>
            <div className="flex flex-wrap items-center justify-center md:justify-start gap-4 text-sm text-slate-450">
              <span className="flex items-center gap-1.5">
                <Calendar size={15} />
                {new Date(submission.submitted_at).toLocaleString("vi-VN")}
              </span>
              <span className="h-1.5 w-1.5 rounded-full bg-slate-800"></span>
              <span>ID Bài làm: #{submission.id}</span>
            </div>
            
            {isPending && (
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-yellow-500/10 border border-yellow-500/20 rounded-full text-yellow-500 text-xs font-semibold">
                <AlertCircle size={14} /> AI đang tiến hành chấm điểm bài tự luận...
              </div>
            )}
          </div>

          <div className="flex flex-col items-center justify-center p-6 bg-slate-900/60 border border-slate-800 rounded-xl min-w-[180px]">
            <Award className="text-brand-400 mb-2" size={36} />
            {isCompleted ? (
              <>
                <span className="text-xs text-slate-550 font-bold uppercase tracking-wider mb-1">Điểm số</span>
                <span className="text-4xl font-black text-brand-400">
                  {submission.score.toFixed(1)}
                  <span className="text-lg font-medium text-slate-500">/10</span>
                </span>
              </>
            ) : (
              <>
                <span className="text-xs text-slate-550 font-bold uppercase tracking-wider mb-1">Trạng thái</span>
                <span className="text-base font-bold text-yellow-500">Đang chấm...</span>
              </>
            )}
          </div>
        </div>

        {/* Detailed Questions Review */}
        {isCompleted && questions.length > 0 && (
          <div className="space-y-6">
            <h3 className="text-lg font-bold text-slate-200">Chi tiết bài làm</h3>
            <div className="space-y-5">
              {questions.map((q, index) => {
                const qId = String(q.id);
                const studentAns = submission.answers[qId];
                const detail = submission.score_details?.[qId];
                const isCorrect = detail?.is_correct ?? false;
                const points = detail?.score ?? 0;
                const maxPoints = detail?.max_score ?? q.score_weight;

                return (
                  <div key={q.id} className="glass-card rounded-xl p-5 border border-slate-800 space-y-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-400 text-sm">Câu {index + 1}</span>
                        <span className="px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider bg-slate-900 border border-slate-800 text-slate-400">
                          {q.component_type}
                        </span>
                      </div>
                      
                      {q.component_type !== "essay" && q.component_type !== "writing" && (
                        <div className="flex items-center gap-1.5 text-xs">
                          {isCorrect ? (
                            <span className="text-green-500 font-semibold flex items-center gap-1">
                              <CheckCircle2 size={15} /> Đúng
                            </span>
                          ) : (
                            <span className="text-red-500 font-semibold flex items-center gap-1">
                              <XCircle size={15} /> Sai
                            </span>
                          )}
                          <span className="text-slate-800">|</span>
                        </div>
                      )}
                      
                      <span className="text-xs font-semibold text-slate-300">
                        {points}/{maxPoints} điểm
                      </span>
                    </div>

                    <p className="text-slate-200 font-medium whitespace-pre-wrap leading-relaxed">
                      {q.question_text}
                    </p>

                    {/* Student response review */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border-t border-slate-855 border-slate-800 pt-4 mt-2">
                      <div className="p-3 bg-slate-900/40 rounded-lg border border-slate-800">
                        <span className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Bài làm của bạn</span>
                        <span className={`text-sm font-medium ${isCorrect ? "text-green-400" : "text-slate-300"}`}>
                          {Array.isArray(studentAns)
                            ? studentAns.map((a, i) => `[${i + 1}] ${a}`).join(", ")
                            : studentAns || <span className="italic text-slate-550">Chưa làm</span>}
                        </span>
                      </div>

                      {q.correct_answer && (
                        <div className="p-3 bg-slate-900/40 rounded-lg border border-slate-800">
                          <span className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Đáp án mẫu / Đúng</span>
                          <span className="text-sm font-semibold text-green-500">
                            {q.correct_answer}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* AI Feedback (Claude reasoning) */}
                    {detail?.explanation && (
                      <div className="p-4 bg-brand-500/5 border border-brand-500/10 rounded-lg text-xs leading-relaxed text-slate-400">
                        <span className="block font-bold text-brand-400 text-xs uppercase tracking-wider mb-1">Phân tích chi tiết từ AI Claude</span>
                        <div className="whitespace-pre-wrap">{detail.explanation}</div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </main>

      <footer className="max-w-7xl mx-auto w-full px-6 py-8 border-t border-slate-900 text-center text-xs text-slate-500">
        AI Exam Platform • Trình chấm điểm & Phản hồi tự động.
      </footer>
    </div>
  );
}
