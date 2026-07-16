"use client";
import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import apiClient from "@/lib/api-client";
import ScoreDistributionChart from "@/components/teacher/ScoreDistributionChart";
import { ChevronLeft, BarChart3, Users, Award, TrendingUp, ShieldAlert } from "lucide-react";
import Link from "next/link";

interface ExamStats {
  total_submissions: number;
  average_score: number;
  highest_score: number;
  lowest_score: number;
  score_distribution: Array<{ score: number; count: number }>;
}

interface StudentSubmission {
  id: number;
  student_id: number;
  student_email: string;
  score: number;
  status: string;
  submitted_at: string;
}

export default function ExamStatsPage() {
  const { examId } = useParams();
  const [exam, setExam] = useState<any>(null);
  const [stats, setStats] = useState<ExamStats | null>(null);
  const [submissions, setSubmissions] = useState<StudentSubmission[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadStatsData = async () => {
      try {
        const [examRes, statsRes, subRes] = await Promise.all([
          apiClient.get(`/exams/${examId}`),
          apiClient.get(`/exams/${examId}/stats`),
          apiClient.get(`/submissions/?exam_id=${examId}`),
        ]);
        setExam(examRes.data);
        setStats(statsRes.data);
        setSubmissions(subRes.data);
      } catch (e) {
        console.error("Failed to load statistics:", e);
      } finally {
        setLoading(false);
      }
    };
    if (examId) loadStatsData();
  }, [examId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <span className="text-slate-400">Đang tải báo cáo thống kê...</span>
      </div>
    );
  }

  if (!exam || !stats) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 text-center">
        <p className="text-red-400 mb-4 font-semibold">Không tìm thấy dữ liệu thống kê.</p>
        <Link href="/dashboard" className="text-brand-400 hover:underline">Quay lại Dashboard</Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between">
      {/* Header */}
      <header className="border-b border-slate-900 bg-slate-900/20 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center">
          <Link href={`/exams/${examId}/edit`} className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors">
            <ChevronLeft size={16} /> Quay lại biên tập đề
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow max-w-7xl mx-auto w-full px-6 py-8 space-y-8">
        <div>
          <h1 className="text-2xl font-black text-slate-100 mb-1">Thống Kê Báo Cáo Kết Quả</h1>
          <p className="text-xs text-slate-400 uppercase font-semibold">
            Đề kiểm tra: {exam.title} | Lớp học: {exam.class_name || `Mã #${exam.class_id}`}
          </p>
        </div>

        {/* Stats Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="glass-card rounded-xl p-5 border border-slate-800 flex items-start gap-4">
            <div className="p-3 bg-brand-500/10 rounded-lg text-brand-400 shrink-0">
              <Users size={20} />
            </div>
            <div>
              <span className="block text-xs font-bold text-slate-500 uppercase tracking-wider">Lượt nộp bài</span>
              <span className="block text-2xl font-black text-slate-200 mt-1">{stats.total_submissions}</span>
            </div>
          </div>

          <div className="glass-card rounded-xl p-5 border border-slate-800 flex items-start gap-4">
            <div className="p-3 bg-brand-500/10 rounded-lg text-brand-400 shrink-0">
              <Award size={20} />
            </div>
            <div>
              <span className="block text-xs font-bold text-slate-500 uppercase tracking-wider">Điểm trung bình</span>
              <span className="block text-2xl font-black text-brand-400 mt-1">{stats.average_score.toFixed(2)}</span>
            </div>
          </div>

          <div className="glass-card rounded-xl p-5 border border-slate-800 flex items-start gap-4">
            <div className="p-3 bg-green-500/10 rounded-lg text-green-500 shrink-0">
              <TrendingUp size={20} />
            </div>
            <div>
              <span className="block text-xs font-bold text-slate-500 uppercase tracking-wider">Điểm cao nhất</span>
              <span className="block text-2xl font-black text-green-400 mt-1">{stats.highest_score.toFixed(1)}</span>
            </div>
          </div>

          <div className="glass-card rounded-xl p-5 border border-slate-800 flex items-start gap-4">
            <div className="p-3 bg-red-500/10 rounded-lg text-red-500 shrink-0">
              <ShieldAlert size={20} />
            </div>
            <div>
              <span className="block text-xs font-bold text-slate-500 uppercase tracking-wider">Điểm thấp nhất</span>
              <span className="block text-2xl font-black text-red-400 mt-1">{stats.lowest_score.toFixed(1)}</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column: Recharts Score Distribution Graph */}
          <div className="lg:col-span-2">
            <ScoreDistributionChart data={stats.score_distribution} />
          </div>

          {/* Right Column: submissions log */}
          <div className="glass-panel rounded-xl border border-slate-800 p-5 space-y-4">
            <h3 className="font-bold text-slate-200 text-sm flex items-center gap-2 border-b border-slate-800/80 pb-3">
              <BarChart3 size={16} className="text-brand-400" /> Nhật ký bài nộp
            </h3>
            
            {submissions.length === 0 ? (
              <p className="text-slate-500 text-xs text-center py-6">Chưa có bài nộp nào.</p>
            ) : (
              <div className="divide-y divide-slate-800/40 max-h-[250px] overflow-y-auto pr-1 text-xs">
                {submissions.map((sub) => (
                  <div key={sub.id} className="py-2.5 flex items-center justify-between">
                    <div>
                      <span className="block font-medium text-slate-200 truncate max-w-[150px]" title={sub.student_email}>
                        {sub.student_email}
                      </span>
                      <span className="block text-xs text-slate-500 mt-0.5">
                        {new Date(sub.submitted_at).toLocaleDateString("vi-VN")}
                      </span>
                    </div>

                    <div className="text-right">
                      {sub.status === "completed" ? (
                        <span className="font-bold text-brand-400 text-sm">{sub.score.toFixed(1)}</span>
                      ) : (
                        <span className="text-xs font-bold text-yellow-500">Đang chấm...</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="max-w-7xl mx-auto w-full px-6 py-8 border-t border-slate-900 text-center text-xs text-slate-500">
        AI Exam Platform • Thống kê phân tích kết quả bài kiểm tra.
      </footer>
    </div>
  );
}
