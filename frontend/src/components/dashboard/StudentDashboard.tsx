import React, { useState } from "react";
import Link from "next/link";
import PremiumClassCard from "./PremiumClassCard";
import PremiumExamCard from "./PremiumExamCard";
import apiClient from "@/lib/api-client";

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
  score?: number | null;
}

interface StudentDashboardProps {
  user: any;
  displayClasses: ClassData[];
  displayExams: ExamData[];
  displaySelfPractice: ExamData[];
  searchQuery?: string;
}

export default function StudentDashboard({ user, displayClasses, displayExams, displaySelfPractice, searchQuery = "" }: StudentDashboardProps) {
  const [visibleExams, setVisibleExams] = useState(3);
  const [visibleSelfPractice, setVisibleSelfPractice] = useState(3);
  const [visibleClasses, setVisibleClasses] = useState(3);
  
  // Local state for pinning and deleting
  const [pinnedExams, setPinnedExams] = useState<number[]>([]);
  const [deletedExams, setDeletedExams] = useState<number[]>([]);

  const handlePin = (id: number) => {
    setPinnedExams(prev => 
      prev.includes(id) ? prev.filter(eId => eId !== id) : [...prev, id]
    );
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm("Bạn có chắc chắn muốn xóa đề thi này không? Dữ liệu không thể khôi phục.")) return;
    try {
      await apiClient.delete(`/exams/${id}`);
      setDeletedExams(prev => [...prev, id]);
    } catch (error) {
      console.error("Lỗi khi xóa đề thi:", error);
      alert("Xóa đề thi thất bại, vui lòng thử lại!");
    }
  };

  const filterExamsBySearch = (exams: ExamData[]) => {
    if (!searchQuery) return exams;
    const lowerQuery = searchQuery.toLowerCase();
    return exams.filter(e => 
      e.title.toLowerCase().includes(lowerQuery) || 
      e.subject.toLowerCase().includes(lowerQuery)
    );
  };

  const processExams = (exams: ExamData[]) => {
    return filterExamsBySearch([...exams])
      .filter(e => !deletedExams.includes(e.id))
      .sort((a, b) => {
        const isAPinned = pinnedExams.includes(a.id);
        const isBPinned = pinnedExams.includes(b.id);
        if (isAPinned && !isBPinned) return -1;
        if (!isAPinned && isBPinned) return 1;
        
        const dateA = a.created_at ? new Date(a.created_at).getTime() : 0;
        const dateB = b.created_at ? new Date(b.created_at).getTime() : 0;
        return dateB - dateA;
      });
  };

  const processedExams = processExams(displayExams);
  const processedSelfPractice = processExams(displaySelfPractice);

  const processedClasses = displayClasses.filter(c => {
    if (!searchQuery) return true;
    const lowerQuery = searchQuery.toLowerCase();
    return c.name.toLowerCase().includes(lowerQuery) || c.subject.toLowerCase().includes(lowerQuery);
  });

  return (
    <main className="flex-grow flex flex-col w-full pb-16">
      <div className="max-w-[1200px] mx-auto w-full px-6 pt-10">
        
        {/* Welcome Banner */}
        <div className="bg-[#0052CC] rounded-3xl p-8 flex flex-col md:flex-row justify-between items-center mb-12 shadow-md">
          <div>
            <h2 className="text-white font-bold text-2xl mb-2">
              {user?.full_name || user?.email}, chào mừng bạn quay lại quá trình luyện đề
            </h2>
            <p className="text-blue-100">
              Tải file lên để học tập, làm bài trên máy tính
            </p>
          </div>
          <div className="flex gap-4 mt-6 md:mt-0">
            <Link href="/practice/upload">
              <button className="bg-[#1D70F5] hover:bg-blue-600 text-white px-6 py-2.5 rounded-full font-medium transition-colors text-sm">
                Tải đề lên
              </button>
            </Link>
            <button className="bg-[#1D70F5] hover:bg-blue-600 text-white px-6 py-2.5 rounded-full font-medium transition-colors text-sm">
              Tiếp tục học tập
            </button>
          </div>
        </div>

        {/* Lớp học hiện tại */}
        <div className="mb-14">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-bold text-gray-900">Lớp học hiện tại</h3>
          </div>
          
          {processedClasses.length === 0 ? (
            <div className="bg-[#EAF2FF] rounded-3xl p-12 text-center">
              <p className="text-gray-500 italic">Hiện tại chưa có lớp học nào.</p>
            </div>
          ) : (
            <div className="bg-[#EAF2FF] rounded-3xl p-8">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {processedClasses.slice(0, visibleClasses).map((cls) => (
                  <PremiumClassCard key={cls.id} cls={cls} />
                ))}
              </div>
            </div>
          )}
          <div className="flex justify-center mt-6">
            {visibleClasses < processedClasses.length ? (
              <button 
                onClick={() => setVisibleClasses(prev => prev + 3)}
                className="border-2 border-[#0052CC] text-[#0052CC] font-semibold px-8 py-2 rounded-full hover:bg-blue-50 transition-colors">
                hiển thị thêm
              </button>
            ) : processedClasses.length > 3 ? (
              <button 
                onClick={() => setVisibleClasses(3)}
                className="border-2 border-gray-300 text-gray-600 font-semibold px-8 py-2 rounded-full hover:bg-gray-50 transition-colors">
                Rút gọn
              </button>
            ) : null}
          </div>
        </div>

        {/* Bài tập - Đề kiểm tra của lớp */}
        <div className="mb-14">
          <h3 className="text-xl font-bold text-gray-900 mb-6">Bài tập - Đề kiểm tra của lớp</h3>
          {processedExams.length === 0 ? (
            <div className="py-8 text-center bg-gray-50 rounded-2xl border border-gray-100 text-gray-500 italic">
              Bạn chưa có bài tập hay đề kiểm tra nào.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {processedExams.slice(0, visibleExams).map((exam) => (
                <PremiumExamCard 
                  key={exam.id} 
                  exam={exam} 
                  isPinned={pinnedExams.includes(exam.id)}
                  onPin={handlePin}
                  onDelete={handleDelete}
                />
              ))}
            </div>
          )}
          <div className="flex justify-center mt-8">
            {visibleExams < processedExams.length ? (
              <button 
                onClick={() => setVisibleExams(prev => prev + 3)}
                className="border-2 border-[#0052CC] text-[#0052CC] font-semibold px-8 py-2 rounded-full hover:bg-blue-50 transition-colors bg-white">
                Hiển thị thêm
              </button>
            ) : processedExams.length > 3 ? (
              <button 
                onClick={() => setVisibleExams(3)}
                className="border-2 border-gray-300 text-gray-600 font-semibold px-8 py-2 rounded-full hover:bg-gray-50 transition-colors bg-white">
                Rút gọn
              </button>
            ) : null}
          </div>
        </div>

      </div> {/* End inner container */}
      
      {/* Đề tự luyện - Full width banner section */}
      <div className="w-full mt-8">
        <div className="bg-[#0052CC] w-full py-4 px-6 md:px-12">
          <div className="max-w-[1200px] mx-auto flex flex-col md:flex-row justify-between items-center">
            <h3 className="text-white font-bold text-xl">Đề tự luyện</h3>
            <div className="flex gap-4 mt-4 md:mt-0">
              <Link href="/practice/upload">
                <button className="bg-[#1D70F5] hover:bg-blue-600 text-white px-5 py-2 rounded-full text-sm font-medium transition-colors">
                  Tải đề lên
                </button>
              </Link>
              <button className="bg-[#1D70F5] hover:bg-blue-600 text-white px-5 py-2 rounded-full text-sm font-medium transition-colors">
                Kết quả gần đây
              </button>
            </div>
          </div>
        </div>
        
        <div className="max-w-[1200px] mx-auto w-full px-6 pt-10 pb-4">
          {processedSelfPractice.length === 0 ? (
            <div className="py-12 text-center text-gray-500 italic">
              Bạn chưa có đề tự luyện nào.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {processedSelfPractice.slice(0, visibleSelfPractice).map((exam) => (
                <PremiumExamCard 
                  key={exam.id} 
                  exam={exam} 
                  isPinned={pinnedExams.includes(exam.id)}
                  onPin={handlePin}
                  onDelete={handleDelete}
                />
              ))}
            </div>
          )}
          <div className="flex justify-center mt-10">
            {visibleSelfPractice < processedSelfPractice.length ? (
              <button 
                onClick={() => setVisibleSelfPractice(prev => prev + 3)}
                className="border-2 border-[#0052CC] text-[#0052CC] font-semibold px-8 py-2 rounded-full hover:bg-blue-50 transition-colors bg-white">
                Hiển thị thêm
              </button>
            ) : processedSelfPractice.length > 3 ? (
              <button 
                onClick={() => setVisibleSelfPractice(3)}
                className="border-2 border-gray-300 text-gray-600 font-semibold px-8 py-2 rounded-full hover:bg-gray-50 transition-colors bg-white">
                Rút gọn
              </button>
            ) : null}
          </div>
        </div>
      </div>
    </main>
  );
}
