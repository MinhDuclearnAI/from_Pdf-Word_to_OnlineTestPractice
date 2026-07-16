import React from "react";
import Link from "next/link";
import { BookOpen } from "lucide-react";

interface SubjectListProps {
  classes: Array<{
    id: number;
    name: string;
    subject: string;
    created_at?: string;
  }>;
  role: "student" | "teacher";
}

export const SubjectList: React.FC<SubjectListProps> = ({ classes, role }) => {
  // Filter out any internal self-practice containers from direct class list displays
  const publicClasses = classes.filter((c) => c.subject !== "Self-Practice");

  if (publicClasses.length === 0) {
    return (
      <div className="text-center py-8 bg-slate-900/10 border border-slate-800 rounded-xl">
        <p className="text-slate-400 text-sm">Bạn chưa có lớp học nào.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {publicClasses.map((cls) => {
        const path = role === "teacher" ? `/classes/${cls.id}` : `/dashboard?class_id=${cls.id}`;

        return (
          <Link href={path} key={cls.id} className="block">
            <div className="glass-card rounded-xl p-5 border border-slate-800 flex items-start gap-4">
              <div className="p-3 bg-brand-500/10 rounded-lg text-brand-400 shrink-0">
                <BookOpen size={22} />
              </div>
              <div className="flex-1 min-w-0">
                <h4 className="font-bold text-slate-100 truncate text-base mb-1 hover:text-brand-400 transition-colors">
                  {cls.name}
                </h4>
                <p className="text-xs text-slate-400">Môn học: {cls.subject}</p>
              </div>
            </div>
          </Link>
        );
      })}
    </div>
  );
};
export default SubjectList;
