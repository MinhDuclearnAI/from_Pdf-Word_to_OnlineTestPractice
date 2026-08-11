"use client";
import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { Clock, PlayCircle, MoreVertical, Trash2, CheckCircle } from "lucide-react";
import { SUBJECT_LABELS, TEST_TYPE_LABELS } from "@/lib/constants";

interface ExamCardProps {
  exam: {
    id: number;
    title: string;
    subject: string;
    test_type: string;
    duration: number;
    open_at?: string;
    close_at?: string;
    score?: number;
  };
  role: "student" | "teacher";
  onDelete?: (examId: number) => void;
}

export const ExamCard: React.FC<ExamCardProps> = ({ exam, role, onDelete }) => {
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

  return (
    <div className="glass-card rounded-xl p-5 flex flex-col justify-between h-48 border border-slate-800 relative">
      <div>
        <div className="flex items-center justify-between mb-2.5">
          <div className="flex gap-2 items-center">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-brand-500/10 text-brand-400 border border-brand-500/20">
              {SUBJECT_LABELS[exam.subject] || exam.subject}
            </span>
            <span className="text-xs text-slate-400 font-medium">
              {TEST_TYPE_LABELS[exam.test_type] || exam.test_type}
            </span>
          </div>
          {onDelete && (
            <div className="relative" ref={menuRef}>
              <button
                onClick={() => setShowMenu(!showMenu)}
                className="p-1 rounded-md text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
              >
                <MoreVertical size={16} />
              </button>
              {showMenu && (
                <div className="absolute right-0 mt-1 w-36 bg-slate-900 border border-slate-700 rounded-lg shadow-xl z-10 overflow-hidden">
                  <button
                    onClick={() => {
                      setShowMenu(false);
                      onDelete(exam.id);
                    }}
                    className="w-full text-left px-3 py-2 text-sm text-red-400 hover:bg-slate-800 flex items-center gap-2 transition-colors"
                  >
                    <Trash2 size={14} /> Xóa đề thi
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
        <h3 className="text-base font-bold text-slate-100 line-clamp-2 leading-snug">
          {exam.title}
        </h3>
      </div>

      <div className="flex items-center justify-between border-t border-slate-800/60 pt-3.5">
        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <Clock size={14} />
          <span>{exam.duration} phút</span>
        </div>

        {role === "student" ? (
          <div className="flex items-center gap-3">
            {exam.score !== undefined && exam.score !== null && (
              <span className="flex items-center gap-1 text-xs font-bold text-green-400 bg-green-400/10 px-2 py-1 rounded-md border border-green-400/20">
                <CheckCircle size={12} /> {exam.score}đ
              </span>
            )}
            <Link
              href={`/exam/${exam.id}`}
              className="flex items-center gap-1 text-xs text-brand-400 hover:text-brand-300 font-bold transition-colors group"
            >
              <span>{exam.score !== undefined && exam.score !== null ? 'Xem lại' : 'Vào thi'}</span>
              <PlayCircle size={15} className="group-hover:translate-x-0.5 transition-transform" />
            </Link>
          </div>
        ) : (
          <Link
            href={`/exams/${exam.id}/edit`}
            className="text-xs text-slate-350 hover:text-brand-400 font-semibold transition-colors"
          >
            Quản lý đề
          </Link>
        )}
      </div>
    </div>
  );
};
export default ExamCard;
