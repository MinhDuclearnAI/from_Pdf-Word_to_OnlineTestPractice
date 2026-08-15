import React, { useState } from "react";
import { useExamStore } from "@/store/examStore";
import { ChevronRight, ChevronLeft, Flag } from "lucide-react";

interface QuestionNavigatorProps {
  questions: Array<{ id: string | number; [key: string]: any }>;
  onSelectQuestion?: (index: number, questionId: string) => void;
  isEnglish?: boolean;
}

export const QuestionNavigator: React.FC<QuestionNavigatorProps> = ({ questions, onSelectQuestion, isEnglish = false }) => {
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

  const labelPrefix = isEnglish ? "QUESTION" : "CÂU HỎI";
  const shortLabel = isEnglish ? "Question" : "Câu";

  if (isCollapsed) {
    return (
      <div className="bg-white/80 border border-slate-200/80 rounded-2xl p-2 shadow-2xl backdrop-blur flex flex-col items-center gap-3">
        <button
          type="button"
          onClick={() => setIsCollapsed(false)}
          className="p-2 rounded-xl bg-brand-500/20 text-brand-400 hover border border-brand-500/40 transition-colors"
          title="Mở rộng danh sách câu hỏi"
        >
          <ChevronLeft size={18} />
        </button>
        <span className="text-[10px] font-bold text-slate-600 writing-vertical rotate-180 tracking-wider">
          {labelPrefix} ({answeredCount}/{questions.length})
        </span>
      </div>
    );
  }

  return (
    <div className="w-full bg-white/70 border border-slate-200/80 rounded-2xl p-3.5 shadow-2xl backdrop-blur transition-all duration-200">
      <div className="flex items-center justify-between pb-2.5 mb-3 border-b border-slate-200/70">
        <div>
          <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wide">
            {labelPrefix}
          </h4>
          <span className="text-[11px] text-brand-400 font-semibold">
            {answeredCount}/{questions.length} đã làm
          </span>
        </div>
        <button
          type="button"
          onClick={() => setIsCollapsed(true)}
          className="p-1 rounded-lg text-slate-500 hover hover transition-colors"
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
              title={`${shortLabel} ${index + 1} - Trái: Chọn | Phải: Gắn cờ`}
              className={`relative flex items-center justify-center h-8 w-full rounded-md text-xs transition-all duration-150 border select-none ${
                isCurrent && isAnswered
                  ? "border-brand-700 text-white bg-brand-700 shadow-md ring-2 ring-brand-700/30 font-black scale-105 z-10"
                  : isCurrent
                  ? "border-brand-500 text-white bg-brand-500 shadow-md ring-2 ring-brand-500/30 font-black scale-105 z-10"
                  : isAnswered
                  ? "bg-brand-50 border-brand-200 text-brand-700 font-bold hover:bg-brand-100"
                  : "bg-white/50 border-slate-200/80 text-slate-500 font-medium hover:bg-slate-100"
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

      <div className="mt-3 space-y-1.5 border-t border-slate-200/60 pt-2.5 text-[11px] text-slate-500">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded bg-brand-500 border border-brand-500 inline-block" />
          <span>Đang chọn</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded bg-brand-50 border border-brand-200 inline-block" />
          <span>Đã trả lời</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded bg-white border border-slate-200 inline-block" />
          <span>Chưa trả lời</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="relative w-2.5 h-2.5 rounded bg-white border border-slate-200 inline-block">
            <span className="absolute top-0 right-0 h-1 w-1 rounded-full bg-orange-500" />
          </span>
          <span>🚩 Chuột phải gắn cờ</span>
        </div>
      </div>
    </div>
  );
};
export default QuestionNavigator;
