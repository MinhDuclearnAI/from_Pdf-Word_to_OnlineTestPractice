import React from "react";
import { Trophy, Medal } from "lucide-react";

interface LeaderboardEntry {
  rank: number;
  student_id: number;
  student_email: string;
  exams_taken: number;
  total_score: number;
  average_score: number;
}

interface LeaderboardTableProps {
  entries: LeaderboardEntry[];
}

export const LeaderboardTable: React.FC<LeaderboardTableProps> = ({ entries }) => {
  if (entries.length === 0) {
    return (
      <div className="text-center py-8 text-slate-400 text-sm">
        Chưa có học sinh nào hoàn thành bài thi trong lớp này.
      </div>
    );
  }

  const getRankBadge = (rank: number) => {
    switch (rank) {
      case 1:
        return <Trophy className="text-yellow-500" size={20} />;
      case 2:
        return <Medal className="text-slate-300" size={20} />;
      case 3:
        return <Medal className="text-amber-600" size={20} />;
      default:
        return <span className="font-semibold text-slate-450">{rank}</span>;
    }
  };

  return (
    <div className="w-full overflow-x-auto">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-slate-800 text-xs font-semibold uppercase text-slate-400">
            <th className="py-3.5 px-4 text-center w-16">Hạng</th>
            <th className="py-3.5 px-4">Học sinh</th>
            <th className="py-3.5 px-4 text-center">Số bài đã làm</th>
            <th className="py-3.5 px-4 text-right">Tổng điểm</th>
            <th className="py-3.5 px-4 text-right">Điểm trung bình</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/50 text-sm text-slate-350">
          {entries.map((entry) => (
            <tr
              key={entry.student_id}
              className="hover:bg-slate-800/20 transition-colors"
            >
              <td className="py-4 px-4 text-center">
                <div className="flex justify-center">{getRankBadge(entry.rank)}</div>
              </td>
              <td className="py-4 px-4 font-medium text-slate-200">
                {entry.student_email}
              </td>
              <td className="py-4 px-4 text-center">{entry.exams_taken}</td>
              <td className="py-4 px-4 text-right font-semibold text-brand-400">
                {entry.total_score}
              </td>
              <td className="py-4 px-4 text-right font-medium text-slate-200">
                {entry.average_score}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
export default LeaderboardTable;
