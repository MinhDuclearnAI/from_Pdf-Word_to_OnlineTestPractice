import React, { useState } from "react";
import { useExamStore } from "@/store/examStore";
import { ChevronRight, ChevronLeft, Flag } from "lucide-react";

interface QuestionNavigatorProps {
  questions: Array<{ id: string | number; [key: string]: any }>;
  onSelectQuestion?: (index: number, questionId: string) => void;
}

export const QuestionNavigator: React.FC<QuestionNavigatorProps> = ({ questions, onSelectQuestion }) => {
  const { currentIndex, setCurrentIndex, answers, flaggedQuestions, toggleFlag } = useExamStore();
  const [isCollapsed, setIsCollapsed] = useState(false);

  const answeredCount = Object.keys(answers).filter(
    (key) => answers[key] !== undefined && answers[key] !== null && answers[key] !== ""
  ).length;

  const handleSelect = (index: number, qId: string) => {
    setCurrentIndex(index);
    if (onSelectQuestion) {
      onSelectQuestion(index, qId);
    } else {
      const el = document.getElementById(`question-card-${qId}`) || document.getElementById(`question-card-${index}`);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }
  };

  const handleContextMenu = (e: React.MouseEvent, index: number) => {
    e.preventDefault();
    toggleFlag(index);
  };

  if (isCollapsed) {
    return (
      <div className="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-2 shadow-2xl backdrop-blur flex flex-col items-center gap-3">
        <button
          type="button"
          onClick={() => setIsCollapsed(false)}
          className="p-2 rounded-xl bg-brand-500/20 text-brand-400 hover:bg-brand-500/30 border border-brand-500/40 transition-colors"
          title="Mở rộng danh sách câu hỏi"
        >
          <ChevronLeft size={18} />
        </button>
        <span className="text-[10px] font-bold text-slate-300 writing-vertical rotate-180 tracking-wider">
          CÂU HỎI ({answeredCount}/{questions.length})
        </span>
      </div>
    );
  }

  return (
    <div className="w-full bg-slate-900/70 border border-slate-800/80 rounded-2xl p-3.5 shadow-2xl backdrop-blur transition-all duration-200">
      <div className="flex items-center justify-between pb-2.5 mb-3 border-b border-slate-800/70">
        <div>
          <h4 className="font-bold text-slate-100 text-xs uppercase tracking-wide">
            Câu hỏi
          </h4>
          <span className="text-[11px] text-brand-400 font-semibold">
            {answeredCount}/{questions.length} đã làm
          </span>
        </div>
        <button
          type="button"
          onClick={() => setIsCollapsed(true)}
          className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          title="Thu gọn thanh câu hỏi"
        >
          <ChevronRight size={16} />
        </button>
      </div>
      
      {/* 6-Column Compact Grid */}
      <div className="grid grid-cols-6 gap-1.5 max-h-[380px] overflow-y-auto pr-1">
        {questions.map((question, index) => {
          const qId = String(question.id);
          const isCurrent = currentIndex === index;
          const isAnswered = answers[qId] !== undefined && answers[qId] !== null && answers[qId] !== "";
          const isFlagged = flaggedQuestions[index] === true;

          return (
            <button
              key={qId}
              type="button"
              onClick={() => handleSelect(index, qId)}
              onContextMenu={(e) => handleContextMenu(e, index)}
              title={`Câu ${index + 1} - Trái: Chọn | Phải: Gắn cờ`}
              className={`relative flex items-center justify-center h-8 w-full rounded-md text-xs font-bold transition-all duration-150 border select-none ${
                isCurrent
                  ? "border-brand-500 text-white bg-brand-600 shadow-md ring-2 ring-brand-500/30 font-black scale-105 z-10"
                  : isAnswered
                  ? "bg-slate-800 border-slate-700/80 text-brand-300 hover:bg-slate-750"
                  : "bg-slate-900/50 border-slate-800/80 text-slate-400 hover:bg-slate-850 hover:text-slate-200"
              }`}
            >
              {index + 1}
              {isFlagged && (
                <span className="absolute -top-1 -right-1 flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-orange-500 shadow"></span>
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div className="mt-3 space-y-1.5 border-t border-slate-800/60 pt-2.5 text-[11px] text-slate-400">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded bg-brand-600 border border-brand-500 inline-block" />
          <span>Đang xem</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded bg-slate-800 border border-slate-700 inline-block" />
          <span>Đã trả lời</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded bg-slate-900 border border-slate-800 inline-block" />
          <span>Chưa làm</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="relative w-2.5 h-2.5 rounded bg-slate-900 border border-slate-800 inline-block">
            <span className="absolute top-0 right-0 h-1 w-1 rounded-full bg-orange-500" />
          </span>
          <span>🚩 Chuột phải gắn cờ</span>
        </div>
      </div>
    </div>
  );
};
export default QuestionNavigator;
