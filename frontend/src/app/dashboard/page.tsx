"use client";
import React, { useEffect, useState } from "react";
import useAuth from "@/hooks/useAuth";
import apiClient from "@/lib/api-client";
import SubjectList from "@/components/dashboard/SubjectList";
import ExamCard from "@/components/dashboard/ExamCard";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import { GraduationCap, LogOut, BookOpen, FileText, Plus, User as UserIcon } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

interface ClassData {
  id: number;
  name: string;
  subject: string;
}

interface ExamData {
  id: number;
  title: string;
  subject: string;
  test_type: string;
  duration: number;
}

export default function DashboardPage() {
  const { user, logout, loading: authLoading } = useAuth();
  const router = useRouter();
  const [classes, setClasses] = useState<ClassData[]>([]);
  const [selectedClassId, setSelectedClassId] = useState<number | null>(null);
  const [exams, setExams] = useState<ExamData[]>([]);
  
  const [isCreateClassModalOpen, setIsCreateClassModalOpen] = useState(false);
  const [newClassName, setNewClassName] = useState("");
  const [newClassSubject, setNewClassSubject] = useState("Toán");
  const [customSubject, setCustomSubject] = useState("");
  const [createLoading, setCreateLoading] = useState(false);

  const [classesLoading, setClassesLoading] = useState(true);
  const [examsLoading, setExamsLoading] = useState(false);

  const fetchClasses = async () => {
    setClassesLoading(true);
    try {
      const { data } = await apiClient.get("/classes/");
      setClasses(data);
      
      // Auto select first class for students if available
      const publicClasses = data.filter((c: any) => c.subject !== "Self-Practice");
      if (publicClasses.length > 0) {
        setSelectedClassId(publicClasses[0].id);
      }
    } catch (e) {
      console.error("Failed to fetch classes:", e);
    } finally {
      setClassesLoading(false);
    }
  };

  const fetchExams = async (classId: number) => {
    setExamsLoading(true);
    try {
      const { data } = await apiClient.get(`/classes/${classId}/exams`);
      setExams(data);
    } catch (e) {
      console.error("Failed to fetch exams:", e);
    } finally {
      setExamsLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchClasses();
    }
  }, [user]);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (selectedClassId) {
      fetchExams(selectedClassId);
    } else {
      setExams([]);
    }
  }, [selectedClassId]);

  const handleCreateClass = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateLoading(true);
    try {
      const finalSubject = newClassSubject === "Khác" ? customSubject : newClassSubject;
      await apiClient.post("/classes/", {
        name: newClassName,
        subject: finalSubject,
      });
      setIsCreateClassModalOpen(false);
      setNewClassName("");
      setCustomSubject("");
      fetchClasses();
    } catch (e) {
      console.error("Failed to create class:", e);
      alert("Lỗi khi tạo lớp học.");
    } finally {
      setCreateLoading(false);
    }
  };

  // Show loading screen while auth state is being determined
  if (authLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center gap-3">
        <div className="w-6 h-6 rounded-full border-2 border-brand-500 border-t-transparent animate-spin" />
        <span className="text-slate-400 text-sm">Đang tải hệ thống...</span>
      </div>
    );
  }

  // If auth finished loading and still no user → redirect (should be handled by middleware,
  // but this is a safety net to prevent a blank screen)
  if (!user) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center gap-4">
        <span className="text-slate-400 text-sm">Phiên đăng nhập đã hết hạn.</span>
        <a href="/login" className="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-semibold rounded-lg transition-colors">
          Đăng nhập lại
        </a>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Header */}
      <header className="border-b border-slate-900 bg-slate-900/20 backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <GraduationCap className="text-brand-500" size={32} />
            <span className="font-extrabold text-lg tracking-tight">AI Exam Platform</span>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-400">
              <UserIcon size={14} className="text-slate-400" />
              <span>{user.email}</span>
              <span className="h-1.5 w-1.5 rounded-full bg-slate-700 mx-1"></span>
              <span className="uppercase text-brand-400 font-bold">{user.role === "teacher" ? "Giáo viên" : "Học sinh"}</span>
            </div>
            <button
              onClick={logout}
              className="p-2 text-slate-400 hover:text-red-400 hover:bg-slate-900 border border-transparent hover:border-slate-800 rounded-lg transition-all duration-200"
              title="Đăng xuất"
            >
              <LogOut size={18} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-grow max-w-7xl mx-auto w-full px-6 py-8 space-y-8">
        {/* Banner Card */}
        <div className="relative glass-panel rounded-2xl border border-slate-800 p-6 md:p-8 overflow-hidden shadow-2xl">
          <div className="absolute -top-12 -right-12 w-48 h-48 rounded-full bg-brand-500/10 blur-3xl pointer-events-none" />
          <div className="relative z-10 max-w-2xl">
            <h2 className="text-2xl md:text-3xl font-extrabold text-slate-100 leading-tight mb-2">
              Xin chào, {user.email}!
            </h2>
            <p className="text-slate-400 text-sm md:text-base leading-relaxed mb-6">
              {user.role === "teacher"
                ? "Quản lý các lớp học của bạn, bóc tách đề thi vật lý PDF/Word bằng AI và theo dõi thống kê kết quả học sinh làm bài."
                : "Tham gia các lớp học của giáo viên hoặc tự upload đề thi PDF/Word lên góc tự luyện tập để hệ thống AI tạo bài thi trực tuyến."}
            </p>

            <div className="flex flex-wrap gap-4">
              {user.role === "teacher" ? (
                <>
                  <Button variant="primary" size="sm" onClick={() => setIsCreateClassModalOpen(true)}>
                    <Plus size={16} className="mr-1" /> Tạo lớp học mới
                  </Button>
                  <Link href="/exams/new">
                    <Button variant="secondary" size="sm">
                      <FileText size={16} className="mr-1" /> Tải đề thi lên lớp học
                    </Button>
                  </Link>
                </>
              ) : (
                <Link href="/practice/upload">
                  <Button variant="primary" size="sm">
                    <FileText size={16} className="mr-1" /> Upload đề tự luyện tập
                  </Button>
                </Link>
              )}
            </div>
          </div>
        </div>

        {/* Classes Section */}
        <section className="space-y-4">
          <h3 className="text-lg font-bold text-slate-200 flex items-center gap-2">
            <BookOpen size={20} className="text-brand-400" />
            Danh sách lớp học
          </h3>
          {classesLoading ? (
            <div className="text-center py-8"><span className="text-slate-500 text-sm">Đang tải danh sách...</span></div>
          ) : (
            <SubjectList classes={classes} role={user.role} />
          )}
        </section>

        {/* Exams Section (For Students) */}
        {user.role === "student" && classes.length > 0 && (
          <section className="space-y-4 border-t border-slate-900 pt-8">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <h3 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                <FileText size={20} className="text-brand-400" />
                Đề kiểm tra lớp học
              </h3>
              
              {/* Select class tabs */}
              <div className="flex gap-2 overflow-x-auto pb-1 max-w-full">
                {classes
                  .filter((c) => c.subject !== "Self-Practice")
                  .map((cls) => (
                    <button
                      key={cls.id}
                      onClick={() => setSelectedClassId(cls.id)}
                      className={`px-3 py-1.5 text-xs font-semibold rounded-lg shrink-0 border transition-all duration-200 ${
                        selectedClassId === cls.id
                          ? "bg-brand-500 border-brand-500 text-white shadow-md shadow-brand-500/10"
                          : "bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700"
                      }`}
                    >
                      {cls.name}
                    </button>
                  ))}
              </div>
            </div>

            {examsLoading ? (
              <div className="text-center py-12"><span className="text-slate-500 text-sm">Đang tải đề thi...</span></div>
            ) : exams.length === 0 ? (
              <div className="text-center py-12 bg-slate-900/10 border border-slate-800 rounded-xl">
                <p className="text-slate-500 text-sm">Chưa có bài thi nào được giao trong lớp này.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {exams.map((exam) => (
                  <ExamCard key={exam.id} exam={exam as any} role={user.role} />
                ))}
              </div>
            )}
          </section>
        )}
      </main>

      {/* Create Class Dialog (Teacher Only) */}
      {user.role === "teacher" && (
        <Modal
          isOpen={isCreateClassModalOpen}
          onClose={() => setIsCreateClassModalOpen(false)}
          title="Tạo lớp học mới"
        >
          <form onSubmit={handleCreateClass} className="space-y-4">
            <Input
              label="Tên lớp học"
              value={newClassName}
              onChange={(e) => setNewClassName(e.target.value)}
              placeholder="Ví dụ: Vật Lý Lớp 12A1"
              required
            />
            <div className="w-full">
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Môn học</label>
              <select
                value={newClassSubject}
                onChange={(e) => setNewClassSubject(e.target.value)}
                className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
              >
                <option value="Toán">Toán Học</option>
                <option value="Vật Lý">Vật Lý</option>
                <option value="Hóa Học">Hóa Học</option>
                <option value="Sinh Học">Sinh Học</option>
                <option value="Tiếng Anh">Tiếng Anh</option>
                <option value="IELTS">IELTS</option>
                <option value="HSA">Đánh giá năng lực HSA</option>
                <option value="Khác">Môn khác</option>
              </select>
            </div>
            {newClassSubject === "Khác" && (
              <Input
                label="Nhập tên môn học"
                value={customSubject}
                onChange={(e) => setCustomSubject(e.target.value)}
                placeholder="Ví dụ: Lịch sử"
                required
              />
            )}
            <div className="flex gap-4 justify-end mt-6">
              <Button type="button" variant="secondary" onClick={() => setIsCreateClassModalOpen(false)} disabled={createLoading}>
                Hủy
              </Button>
              <Button type="submit" variant="primary" disabled={createLoading}>
                {createLoading ? "Đang tạo..." : "Tạo ngay"}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
