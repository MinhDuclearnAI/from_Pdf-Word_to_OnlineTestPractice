"use client";
import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import apiClient from "@/lib/api-client";
import QuestionReviewList from "@/components/teacher/QuestionReviewList";
import ExamConfigForm from "@/components/teacher/ExamConfigForm";
import Button from "@/components/ui/Button";
import { ChevronLeft, Send, Check } from "lucide-react";
import Link from "next/link";

export default function EditExamPage() {
  const { examId } = useParams();
  const router = useRouter();
  const [exam, setExam] = useState<any>(null);
  const [questions, setQuestions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [saveLoading, setSaveLoading] = useState(false);
  const [publishLoading, setPublishLoading] = useState(false);

  const fetchExamAndQuestions = async () => {
    try {
      const [examRes, questionsRes] = await Promise.all([
        apiClient.get(`/exams/${examId}`),
        apiClient.get(`/exams/${examId}/questions`),
      ]);
      setExam(examRes.data);
      setQuestions(questionsRes.data);
    } catch (e) {
      console.error("Failed to load exam data:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (examId) {
      fetchExamAndQuestions();
    }
  }, [examId]);

  const handleConfigSubmit = async (config: any) => {
    setSaveLoading(true);
    try {
      const { data } = await apiClient.patch(`/exams/${examId}/config`, config);
      setExam(data);
      alert("Đã lưu cấu hình đề thi thành công.");
    } catch (e) {
      console.error("Failed to save config:", e);
      alert("Lỗi khi lưu cấu hình đề thi.");
    } finally {
      setSaveLoading(false);
    }
  };

  const handlePublish = async () => {
    if (!confirm("Bạn có chắc chắn muốn phát hành đề thi này? Học sinh trong lớp sẽ có thể nhìn thấy và làm bài.")) return;
    setPublishLoading(true);
    try {
      await apiClient.post(`/exams/${examId}/publish`);
      alert("Đề thi đã được phát hành thành công!");
      router.push(`/classes/${exam.class_id}`);
    } catch (e) {
      console.error("Failed to publish exam:", e);
      alert("Lỗi khi phát hành đề thi.");
    } finally {
      setPublishLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <span className="text-slate-400">Đang tải thông tin đề kiểm tra...</span>
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

  const redirectPath = exam.class_id ? `/classes/${exam.class_id}` : "/dashboard";

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between">
      {/* Header */}
      <header className="border-b border-slate-900 bg-slate-900/20 backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href={redirectPath} className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors">
            <ChevronLeft size={16} /> Quay lại lớp học
          </Link>
          <div className="flex gap-3">
            <Link href={`/exams/${examId}/stats`}>
              <Button variant="secondary" size="sm">
                Xem thống kê & Điểm
              </Button>
            </Link>
            <Button
              variant="primary"
              size="sm"
              onClick={handlePublish}
              disabled={publishLoading || exam.is_published}
              className="flex items-center gap-1"
            >
              {exam.is_published ? (
                <>
                  <Check size={16} /> Đã phát hành
                </>
              ) : (
                <>
                  <Send size={16} /> Phát hành đề thi
                </>
              )}
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow max-w-7xl mx-auto w-full px-6 py-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Side: Questions list editor */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-panel rounded-2xl border border-slate-800 p-6 shadow-xl">
            <h2 className="text-xl font-black text-slate-100 mb-1">{exam.title}</h2>
            <p className="text-xs text-slate-400 uppercase font-semibold">Chỉnh sửa nội dung & đáp án</p>
          </div>

          <QuestionReviewList
            examId={exam.id}
            initialQuestions={questions}
            onUpdate={fetchExamAndQuestions}
          />
        </div>

        {/* Right Side: Config form */}
        <div className="space-y-6">
          <ExamConfigForm
            initialConfig={{
              duration: exam.duration,
              open_at: exam.open_at,
              close_at: exam.close_at,
              result_visibility: exam.result_visibility,
            }}
            onSubmit={handleConfigSubmit}
            loading={saveLoading}
          />
        </div>
      </main>

      <footer className="max-w-7xl mx-auto w-full px-6 py-8 border-t border-slate-900 text-center text-xs text-slate-500">
        AI Exam Platform • Trình biên tập nội dung đề kiểm tra.
      </footer>
    </div>
  );
}
