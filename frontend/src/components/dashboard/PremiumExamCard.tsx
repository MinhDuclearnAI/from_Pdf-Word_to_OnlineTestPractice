import React, { useState, useRef, useEffect } from 'react';
import { Clock, FileText, Calendar as CalendarIcon, MoreVertical, Pin, Trash2, CheckCircle, PlayCircle } from 'lucide-react';
import Link from 'next/link';

interface ExamData {
  id: number;
  title: string;
  subject: string;
  test_type: string;
  duration: number;
  created_at?: string;
  score?: number | null;
}

interface PremiumExamCardProps {
  exam: ExamData;
  isPinned?: boolean;
  onPin?: (id: number) => void;
  onDelete?: (id: number) => void;
}

export default function PremiumExamCard({ exam, isPinned, onPin, onDelete }: PremiumExamCardProps) {
  const [showMenu, setShowMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowMenu(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const formatDateTime = (dateString?: string) => {
    if (!dateString) return 'Mới cập nhật';
    const date = new Date(dateString);
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear();
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${day}/${month}/${year} ${hours}:${minutes}`;
  };

  const uploadDate = formatDateTime(exam.created_at);

  return (
    <div className={`bg-white rounded-2xl shadow-[0_4px_20px_rgb(0,0,0,0.05)] border ${isPinned ? 'border-blue-300 ring-1 ring-blue-300' : 'border-gray-100'} hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] transition-all duration-300 relative overflow-visible flex flex-col group h-48 hover:-translate-y-1`}>
      {isPinned && (
        <div className="absolute top-0 right-0 w-8 h-8 overflow-hidden pointer-events-none rounded-tr-2xl">
          <div className="absolute top-[-10px] right-[-10px] bg-blue-500 w-16 h-16 rotate-45 transform translate-x-1/2 -translate-y-1/2 z-0"></div>
          <Pin size={12} fill="white" className="text-white absolute top-2 right-2 z-10" />
        </div>
      )}

      <div className="p-6 flex flex-col h-full cursor-pointer">
        <div className="flex items-start justify-between mb-auto">
          <div className="w-10 h-10 rounded-full bg-[#EAF2FF] flex items-center justify-center text-[#0052CC] group-hover:scale-110 transition-transform">
            <FileText size={20} strokeWidth={1.5} />
          </div>
          
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700">
              <Clock size={12} className="mr-1" /> {exam.duration} phút
            </span>
            <div className="relative" ref={menuRef}>
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  setShowMenu(!showMenu);
                }}
                className="text-gray-400 hover:text-gray-700 p-1 rounded-full hover:bg-gray-100 transition-colors"
              >
                <MoreVertical size={18} />
              </button>
              {showMenu && (
                <div className="absolute right-0 top-full mt-1 w-40 bg-white border border-gray-100 rounded-lg shadow-xl z-20 py-1" onClick={(e) => e.stopPropagation()}>
                  <button 
                    onClick={() => {
                      onPin?.(exam.id);
                      setShowMenu(false);
                    }}
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                  >
                    <Pin size={14} /> {isPinned ? 'Bỏ ghim' : 'Ghim lên đầu'}
                  </button>
                  <button 
                    onClick={() => {
                      onDelete?.(exam.id);
                      setShowMenu(false);
                    }}
                    className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                  >
                    <Trash2 size={14} /> Xóa đề thi
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
        
        <div className="mt-4 flex flex-col h-full flex-grow">
          <Link href={`/exam/${exam.id}`}>
            <h4 className="font-bold text-lg text-gray-900 line-clamp-2 leading-tight mb-3 group-hover:text-[#0052CC] transition-colors cursor-pointer">{exam.title}</h4>
          </Link>
          
          <div className="flex items-center justify-between pt-3 border-t border-gray-50 mt-auto">
            <div className="flex items-center text-xs text-gray-500">
              <CalendarIcon size={12} className="mr-1.5" />
              {uploadDate}
            </div>
            
            <div className="flex items-center gap-2">
              {exam.score !== undefined && exam.score !== null && (
                <span className="flex items-center gap-1 text-xs font-bold text-green-600 bg-green-50 px-2 py-1 rounded-md border border-green-200">
                  <CheckCircle size={12} /> {exam.score}đ
                </span>
              )}
              <Link
                href={`/exam/${exam.id}`}
                className="flex items-center gap-1 text-xs font-bold text-[#0052CC] hover:text-white hover:bg-[#0052CC] transition-colors bg-blue-50 px-3 py-1.5 rounded-lg border border-blue-100 group/btn"
              >
                <span>{exam.score !== undefined && exam.score !== null ? 'Xem lại' : 'Vào thi'}</span>
                <PlayCircle size={14} className="group-hover/btn:translate-x-0.5 transition-transform" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
