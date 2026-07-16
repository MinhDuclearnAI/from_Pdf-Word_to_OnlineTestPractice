import React from "react";
import Link from "next/link";
import { Clock, PlayCircle } from "lucide-react";
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
  };
  role: "student" | "teacher";
}

export const ExamCard: React.FC<ExamCardProps> = ({ exam, role }) => {
  return (
    <div className="glass-card rounded-xl p-5 flex flex-col justify-between h-48 border border-slate-800">
      <div>
        <div className="flex items-center justify-between mb-2.5">
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-brand-500/10 text-brand-400 border border-brand-500/20">
            {SUBJECT_LABELS[exam.subject] || exam.subject}
          </span>
          <span className="text-xs text-slate-400 font-medium">
            {TEST_TYPE_LABELS[exam.test_type] || exam.test_type}
          </span>
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
          <Link
            href={`/exam/${exam.id}`}
            className="flex items-center gap-1 text-xs text-brand-400 hover:text-brand-300 font-bold transition-colors group"
          >
            <span>Vào thi</span>
            <PlayCircle size={15} className="group-hover:translate-x-0.5 transition-transform" />
          </Link>
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
