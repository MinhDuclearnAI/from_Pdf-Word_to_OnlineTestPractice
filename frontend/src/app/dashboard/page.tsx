"use client";
import React, { useEffect, useState, useRef } from "react";
import useAuth from "@/hooks/useAuth";
import apiClient from "@/lib/api-client";
import SubjectList from "@/components/dashboard/SubjectList";
import ExamCard from "@/components/dashboard/ExamCard";
import StudentDashboard from "@/components/dashboard/StudentDashboard";
import TeacherDashboard from "@/components/dashboard/TeacherDashboard";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import { LogOut, Plus, User as UserIcon, Mail, Calendar, MapPin, Briefcase, Bell, Facebook, Instagram, GraduationCap, Search } from "lucide-react";
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
  created_at?: string;
}

export default function DashboardPage() {
  const { user, logout, loading: authLoading } = useAuth();
  const router = useRouter();
  const [classes, setClasses] = useState<ClassData[]>([]);
  const [selectedClassId, setSelectedClassId] = useState<number | null>(null);
  const [exams, setExams] = useState<ExamData[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  
  const [isCreateClassModalOpen, setIsCreateClassModalOpen] = useState(false);
  const [newClassName, setNewClassName] = useState("");
  const [newClassSubject, setNewClassSubject] = useState("Toán");
  const [customSubject, setCustomSubject] = useState("");
  const [createLoading, setCreateLoading] = useState(false);

  const [classesLoading, setClassesLoading] = useState(true);
  const [examsLoading, setExamsLoading] = useState(false);
  
  const [selfPracticeExams, setSelfPracticeExams] = useState<ExamData[]>([]);
  const [selfPracticeLoading, setSelfPracticeLoading] = useState(false);

  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const profileMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (profileMenuRef.current && !profileMenuRef.current.contains(event.target as Node)) {
        setShowProfileMenu(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const fetchClasses = async () => {
    setClassesLoading(true);
    try {
      const { data } = await apiClient.get("/classes/");
      setClasses(data);
      
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

  useEffect(() => {
    const fetchSelfPractice = async (classId: number) => {
      setSelfPracticeLoading(true);
      try {
        const { data } = await apiClient.get(`/classes/${classId}/exams`);
        setSelfPracticeExams(data);
      } catch (e) {
        console.error("Failed to fetch self practice exams:", e);
      } finally {
        setSelfPracticeLoading(false);
      }
    };
    
    const spClass = classes.find(c => c.subject === "Self-Practice");
    if (spClass) {
      fetchSelfPractice(spClass.id);
    }
  }, [classes]);

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

  const handleDeleteSelfPracticeExam = async (examId: number) => {
    if (!window.confirm("Bạn có chắc chắn muốn xóa đề thi này không? Dữ liệu không thể khôi phục.")) return;
    try {
      await apiClient.delete(`/exams/${examId}`);
      setSelfPracticeExams(prev => prev.filter(exam => exam.id !== examId));
    } catch (error) {
      console.error("Lỗi khi xóa đề thi:", error);
      alert("Xóa đề thi thất bại, vui lòng thử lại!");
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center gap-3 bg-white">
        <div className="w-6 h-6 rounded-full border-2 border-[#0052CC] border-t-transparent animate-spin" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  const displayClasses = classes.filter(c => c.subject !== "Self-Practice");
  const displayExams = exams;
  const displaySelfPractice = selfPracticeExams;

  return (
    <div className="min-h-screen bg-white text-slate-800 font-sans flex flex-col">
      {/* Header */}
      <header className="w-full bg-white px-8 py-4 flex items-center justify-between border-b border-gray-200 sticky top-0 z-30">
        <div className="flex items-center">
          <Link href="/">
            <div className="border-[3px] border-purple-600 px-2 py-0.5 text-black font-black text-2xl tracking-tighter uppercase cursor-pointer">
              Steps
            </div>
          </Link>
        </div>
        <nav className="hidden md:flex items-center gap-6 lg:gap-10 font-medium text-gray-700">
          <Link href="/dashboard" className="hover:text-[#0052CC] transition-colors whitespace-nowrap">
            Danh sách lớp học
          </Link>
          <Link href="/results" className="hover:text-[#0052CC] transition-colors whitespace-nowrap">
            Kết quả học tập
          </Link>
          <Link href="/materials" className="hover:text-[#0052CC] transition-colors whitespace-nowrap">
            Tài liệu
          </Link>
        </nav>
        
        {/* Search Bar */}
        <div className="flex-1 max-w-lg mx-6 hidden md:block">
          <div className="relative w-full">
            <input 
              type="text" 
              placeholder="Tìm kiếm lớp học, đề thi..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-5 pr-14 py-2.5 border border-gray-300 rounded-full focus:outline-none focus:border-[#0052CC] focus:ring-1 focus:ring-[#0052CC] transition-all text-sm"
            />
            <button className="absolute right-0 top-0 bottom-0 px-4 bg-[#0052CC] text-white rounded-r-full hover:bg-blue-700 transition-colors flex items-center justify-center">
              <Search size={18} />
            </button>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <button className="text-gray-600 hover:text-black">
            <Bell size={22} />
          </button>
          <div className="relative" ref={profileMenuRef}>
            <button
              onClick={() => setShowProfileMenu(!showProfileMenu)}
              className="w-10 h-10 rounded-full bg-[#60A5FA] cursor-pointer hover:opacity-90 flex items-center justify-center text-white font-bold transition-opacity"
            >
              {user.full_name?.charAt(0) || user.email?.charAt(0).toUpperCase()}
            </button>
            
            {showProfileMenu && (
              <div className="absolute right-0 top-full mt-2 w-72 bg-white border border-slate-200 rounded-xl shadow-2xl z-50 overflow-hidden transform origin-top-right transition-all">
                <div className="p-4 border-b border-slate-200 bg-slate-50 flex flex-col gap-2">
                  <div>
                    <h4 className="font-bold text-slate-800 text-lg leading-tight">{user.full_name || user.email}</h4>
                    <span className="inline-block px-2 py-0.5 mt-1 text-[10px] font-bold uppercase tracking-wider text-white bg-[#0052CC] rounded-full">
                      {user.role === "teacher" ? "Giáo viên" : "Học sinh"}
                    </span>
                  </div>
                  
                  <div className="flex flex-col gap-1.5 mt-1">
                    <div className="flex items-center text-slate-600 text-sm">
                      <Mail size={14} className="mr-2 text-slate-400" />
                      {user.email}
                    </div>
                    
                    {user.date_of_birth && (
                      <div className="flex items-center text-slate-600 text-sm">
                        <Calendar size={14} className="mr-2 text-slate-400" />
                        {new Date(user.date_of_birth).toLocaleDateString('vi-VN')}
                      </div>
                    )}
                    
                    {user.school && (
                      <div className="flex items-center text-slate-600 text-sm">
                        <GraduationCap size={14} className="mr-2 text-slate-400" />
                        {user.school}
                      </div>
                    )}
                    
                    {user.workplace && (
                      <div className="flex items-center text-slate-600 text-sm">
                        <Briefcase size={14} className="mr-2 text-slate-400" />
                        {user.workplace}
                      </div>
                    )}
                  </div>
                </div>
                <div className="p-2 border-t border-gray-100">
                  <button
                    onClick={logout}
                    className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg flex items-center gap-2"
                  >
                    <LogOut size={16} /> Đăng xuất
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Router */}
      {user.role === "teacher" ? (
        <TeacherDashboard 
          user={user} 
          displayClasses={displayClasses} 
          displayExams={displayExams} 
          onOpenCreateClass={() => setIsCreateClassModalOpen(true)}
          searchQuery={searchQuery}
        />
      ) : (
        <StudentDashboard 
          user={user} 
          displayClasses={displayClasses} 
          displayExams={displayExams} 
          displaySelfPractice={displaySelfPractice}
          searchQuery={searchQuery}
        />
      )}

      {/* Footer */}
      <footer className="w-full border-t border-gray-300 bg-white">
        <div className="max-w-[1200px] mx-auto px-6 py-8 flex flex-col md:flex-row justify-between text-[13px] text-gray-700">
          <div className="leading-relaxed">
            <p>Một sản phẩm thuộc một sinh viên AI-UET VNU</p>
            <p>Trụ sở: 1194, Phường Láng, Hà Nội</p>
            <p>SĐT: 0973908835</p>
          </div>
          <div className="flex items-start gap-4 mt-6 md:mt-0">
            <span className="font-medium pt-1">Theo dõi tại:</span>
            <div className="flex gap-3">
              <div className="w-8 h-8 bg-black text-white rounded-full flex items-center justify-center">
                <span className="font-bold text-xs">t</span>
              </div>
              <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center">
                <Facebook size={18} fill="currentColor" strokeWidth={0} />
              </div>
              <div className="w-8 h-8 bg-gradient-to-tr from-yellow-400 via-pink-500 to-purple-600 text-white rounded-full flex items-center justify-center">
                <Instagram size={18} />
              </div>
            </div>
          </div>
        </div>
        <div className="text-center text-sm pb-6 text-gray-800">
          © 2026 Teeco. All rights reserved.
        </div>
      </footer>

      {/* Modals */}
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
              <label className="block text-sm font-medium text-slate-600 mb-1.5">Môn học</label>
              <select
                value={newClassSubject}
                onChange={(e) => setNewClassSubject(e.target.value)}
                className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
              >
                <option value="Toán">Toán Học</option>
                <option value="Vật Lý">Vật Lý</option>
                <option value="Hóa Học">Hóa Học</option>
                <option value="Khác">Môn khác</option>
              </select>
            </div>
            {newClassSubject === "Khác" && (
              <Input
                label="Nhập tên môn học"
                value={customSubject}
                onChange={(e) => setCustomSubject(e.target.value)}
                required
              />
            )}
            <div className="flex gap-4 justify-end mt-6">
              <Button type="button" variant="secondary" onClick={() => setIsCreateClassModalOpen(false)}>
                Hủy
              </Button>
              <Button type="submit" variant="primary">
                Tạo ngay
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
