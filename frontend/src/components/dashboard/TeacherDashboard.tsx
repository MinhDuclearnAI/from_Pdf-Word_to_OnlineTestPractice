import React, { useState } from "react";
import PremiumClassCard from "./PremiumClassCard";
import PremiumExamCard from "./PremiumExamCard";
import { Plus } from "lucide-react";

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

interface TeacherDashboardProps {
  user: any;
  displayClasses: ClassData[];
  displayExams: ExamData[];
  onOpenCreateClass: () => void;
  searchQuery?: string;
}

export default function TeacherDashboard({ user, displayClasses, displayExams, onOpenCreateClass, searchQuery = "" }: TeacherDashboardProps) {
  const [visibleExams, setVisibleExams] = useState(3);
  const [visibleClasses, setVisibleClasses] = useState(3);
  
  // Local state for pinning and deleting
  const [pinnedExams, setPinnedExams] = useState<number[]>([]);
  const [deletedExams, setDeletedExams] = useState<number[]>([]);

  const handlePin = (id: number) => {
    setPinnedExams(prev => 
      prev.includes(id) ? prev.filter(eId => eId !== id) : [...prev, id]
    );
  };

  const handleDelete = (id: number) => {
    setDeletedExams(prev => [...prev, id]);
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

  const processedClasses = displayClasses.filter(c => {
    if (!searchQuery) return true;
    const lowerQuery = searchQuery.toLowerCase();
    return c.name.toLowerCase().includes(lowerQuery) || c.subject.toLowerCase().includes(lowerQuery);
  });

  return (
    <main className="flex-grow flex flex-col w-full pb-16">
      <div className="max-w-[1200px] mx-auto w-full px-6 pt-10">
        
        {/* Welcome Banner */}
        <div className="bg-gradient-to-r from-[#0052CC] to-indigo-700 rounded-3xl p-8 flex flex-col md:flex-row justify-between items-center mb-12 shadow-lg">
          <div>
            <h2 className="text-white font-bold text-2xl mb-2">
              Chào mừng thầy/cô {user?.full_name || user?.email} đến với không gian quản lý lớp học
            </h2>
            <p className="text-indigo-100">
              Quản lý lớp học, giao bài tập và theo dõi tiến trình của học sinh dễ dàng.
            </p>
          </div>
          <div className="flex gap-4 mt-6 md:mt-0">
            <button 
              onClick={onOpenCreateClass}
              className="bg-white text-[#0052CC] hover:bg-gray-50 px-6 py-2.5 rounded-full font-semibold transition-colors text-sm shadow-sm"
            >
              + Tạo lớp học
            </button>
            <button className="bg-indigo-500 hover:bg-indigo-400 text-white px-6 py-2.5 rounded-full font-medium transition-colors text-sm border border-indigo-400 shadow-sm">
              Giao bài tập
            </button>
          </div>
        </div>

        {/* Lớp học hiện tại */}
        <div className="mb-14">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-bold text-gray-900">Danh sách lớp học</h3>
            <button 
              onClick={onOpenCreateClass}
              className="text-[#0052CC] hover:underline text-sm font-medium flex items-center"
            >
              <Plus size={16} className="mr-1"/> Tạo lớp
            </button>
          </div>
          
          {processedClasses.length === 0 ? (
            <div className="bg-[#EAF2FF] rounded-3xl p-12 text-center">
              <p className="text-gray-500 italic">
                {searchQuery ? "Không tìm thấy lớp học nào phù hợp." : "Thầy/cô chưa có lớp học nào. Hãy tạo một lớp học để bắt đầu."}
              </p>
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
          <h3 className="text-xl font-bold text-gray-900 mb-6">Đề kiểm tra & Bài tập đã giao</h3>
          {processedExams.length === 0 ? (
            <div className="py-8 text-center bg-gray-50 rounded-2xl border border-gray-100 text-gray-500 italic">
              Chưa có bài tập hay đề kiểm tra nào trong các lớp này.
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
                className="border-2 border-[#0052CC] text-[#0052CC] font-semibold px-8 py-2 rounded-full hover:bg-blue-50 transition-colors">
                hiển thị thêm
              </button>
            ) : processedExams.length > 3 ? (
              <button 
                onClick={() => setVisibleExams(3)}
                className="border-2 border-gray-300 text-gray-600 font-semibold px-8 py-2 rounded-full hover:bg-gray-50 transition-colors">
                Rút gọn
              </button>
            ) : null}
          </div>
        </div>

      </div> {/* End inner container */}
      
    </main>
  );
}
