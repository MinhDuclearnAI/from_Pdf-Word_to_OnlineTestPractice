"use client";
import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import apiClient from "@/lib/api-client";
import LeaderboardTable from "@/components/dashboard/LeaderboardTable";
import ExamCard from "@/components/dashboard/ExamCard";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import { ChevronLeft, Plus, UserPlus, Users, Trophy } from "lucide-react";
import Link from "next/link";

interface Student {
  id: number;
  email: string;
}

interface Exam {
  id: number;
  title: string;
  subject: string;
  test_type: string;
  duration: number;
}

interface LeaderboardEntry {
  rank: number;
  student_id: number;
  student_email: string;
  exams_taken: number;
  total_score: number;
  average_score: number;
}

export default function ClassDetailsPage() {
  const { classId } = useParams();
  const [activeTab, setActiveTab] = useState<"exams" | "students" | "leaderboard">("exams");
  
  const [classInfo, setClassInfo] = useState<any>(null);
  const [students, setStudents] = useState<Student[]>([]);
  const [exams, setExams] = useState<Exam[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [isAddStudentOpen, setIsAddStudentOpen] = useState(false);
  const [studentEmail, setStudentEmail] = useState("");
  const [addLoading, setAddLoading] = useState(false);

  const fetchClassDetails = async () => {
    try {
      const [classRes, studentsRes, examsRes, leaderRes] = await Promise.all([
        apiClient.get(`/classes/${classId}`),
        apiClient.get(`/classes/${classId}/students`),
        apiClient.get(`/classes/${classId}/exams`),
        apiClient.get(`/classes/${classId}/leaderboard`),
      ]);
      setClassInfo(classRes.data);
      setStudents(studentsRes.data);
      setExams(examsRes.data);
      setLeaderboard(leaderRes.data);
    } catch (e) {
      console.error("Failed to load class details:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (classId) {
      fetchClassDetails();
    }
  }, [classId]);

  const handleAddStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    setAddLoading(true);
    try {
      await apiClient.post(`/classes/${classId}/students`, {
        email: studentEmail,
      });
      setIsAddStudentOpen(false);
      setStudentEmail("");
      fetchClassDetails();
    } catch (e) {
      console.error("Failed to add student:", e);
      alert("Lỗi khi thêm học sinh. Vui lòng kiểm tra lại email.");
    } finally {
      setAddLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <span className="text-slate-400">Đang tải thông tin lớp học...</span>
      </div>
    );
  }

  if (!classInfo) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 text-center">
        <p className="text-red-400 mb-4 font-semibold">Không tìm thấy lớp học này.</p>
        <Link href="/dashboard" className="text-brand-400 hover:underline">Quay lại Dashboard</Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between">
      {/* Header */}
      <header className="border-b border-slate-900 bg-slate-900/20 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors">
            <ChevronLeft size={16} /> Quay lại Dashboard
          </Link>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" onClick={() => setIsAddStudentOpen(true)}>
              <UserPlus size={16} className="mr-1" /> Thêm học sinh
            </Button>
            <Link href={`/exams/new?class_id=${classId}`}>
              <Button variant="primary" size="sm">
                <Plus size={16} className="mr-1" /> Tạo đề thi mới
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow max-w-7xl mx-auto w-full px-6 py-8 space-y-6">
        <div>
          <h1 className="text-2xl font-black text-slate-100 mb-1">{classInfo.name}</h1>
          <p className="text-xs text-slate-400 uppercase font-semibold">Môn học: {classInfo.subject}</p>
        </div>

        {/* Tab Buttons */}
        <div className="flex border-b border-slate-900 gap-6">
          <button
            onClick={() => setActiveTab("exams")}
            className={`py-3 text-sm font-semibold border-b-2 transition-colors ${
              activeTab === "exams"
                ? "border-brand-500 text-brand-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Đề kiểm tra ({exams.length})
          </button>
          <button
            onClick={() => setActiveTab("students")}
            className={`py-3 text-sm font-semibold border-b-2 transition-colors ${
              activeTab === "students"
                ? "border-brand-500 text-brand-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Học sinh ({students.length})
          </button>
          <button
            onClick={() => setActiveTab("leaderboard")}
            className={`py-3 text-sm font-semibold border-b-2 transition-colors ${
              activeTab === "leaderboard"
                ? "border-brand-500 text-brand-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Bảng xếp hạng
          </button>
        </div>

        {/* Tab content */}
        <div>
          {activeTab === "exams" && (
            <div className="space-y-4">
              {exams.length === 0 ? (
                <div className="text-center py-12 bg-slate-900/10 border border-slate-800 rounded-xl">
                  <p className="text-slate-500 text-sm">Chưa có bài thi nào được giao trong lớp này.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                  {exams.map((exam) => (
                    <ExamCard key={exam.id} exam={exam as any} role="teacher" />
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === "students" && (
            <div className="glass-panel rounded-xl border border-slate-800 p-6">
              <h3 className="font-bold text-slate-200 mb-4 flex items-center gap-2">
                <Users size={18} className="text-brand-400" /> Danh sách học sinh lớp học
              </h3>
              {students.length === 0 ? (
                <p className="text-slate-400 text-sm">Chưa có học sinh nào được thêm vào lớp học này.</p>
              ) : (
                <div className="divide-y divide-slate-800/50">
                  {students.map((st) => (
                    <div key={st.id} className="py-3 flex items-center justify-between text-sm">
                      <span className="font-medium text-slate-200">{st.email}</span>
                      <span className="text-xs text-slate-500">ID: #{st.id}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === "leaderboard" && (
            <div className="glass-panel rounded-xl border border-slate-800 p-6">
              <h3 className="font-bold text-slate-200 mb-4 flex items-center gap-2">
                <Trophy size={18} className="text-brand-400" /> Bảng điểm tổng hợp học tập
              </h3>
              <LeaderboardTable entries={leaderboard} />
            </div>
          )}
        </div>
      </main>

      {/* Add student Modal */}
      <Modal isOpen={isAddStudentOpen} onClose={() => setIsAddStudentOpen(false)} title="Thêm học sinh vào lớp">
        <form onSubmit={handleAddStudent} className="space-y-4">
          <Input
            label="Địa chỉ Email học sinh"
            type="email"
            value={studentEmail}
            onChange={(e) => setStudentEmail(e.target.value)}
            placeholder="example@student.com"
            required
          />
          <div className="flex gap-4 justify-end mt-6">
            <Button type="button" variant="secondary" onClick={() => setIsAddStudentOpen(false)} disabled={addLoading}>
              Hủy
            </Button>
            <Button type="submit" variant="primary" disabled={addLoading}>
              {addLoading ? "Đang thêm..." : "Thêm vào lớp"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
