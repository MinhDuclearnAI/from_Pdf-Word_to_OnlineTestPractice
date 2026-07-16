import React from "react";
import { useExamStore } from "@/store/examStore";

interface QuestionNavigatorProps {
  questions: Array<{ id: string | number; [key: string]: any }>;
}

export const QuestionNavigator: React.FC<QuestionNavigatorProps> = ({ questions }) => {
  const { currentIndex, setCurrentIndex, answers, flaggedQuestions } = useExamStore();

  return (
    <div className="w-full bg-slate-900/50 border border-slate-800 rounded-xl p-5">
      <h4 className="font-semibold text-slate-200 mb-4 pb-2 border-b border-slate-800/50 flex items-center justify-between">
        <span>Danh sách câu hỏi</span>
        <span className="text-xs text-slate-400 font-normal">
          Đã làm: {Object.keys(answers).filter(key => answers[key] !== undefined && answers[key] !== null && answers[key] !== "").length}/{questions.length}
        </span>
      </h4>
      
      <div className="grid grid-cols-5 gap-2 max-h-[300px] overflow-y-auto pr-1">
        {questions.map((question, index) => {
          const qId = String(question.id);
          const isCurrent = currentIndex === index;
          const isAnswered = answers[qId] !== undefined && answers[qId] !== null && answers[qId] !== "";
          const isFlagged = flaggedQuestions[index] === true;

          return (
            <button
              key={qId}
              type="button"
              onClick={() => setCurrentIndex(index)}
              className={`relative flex items-center justify-center h-10 w-full rounded-lg text-sm font-semibold transition-all duration-200 border ${
                isCurrent
                  ? "border-brand-500 text-brand-400 ring-2 ring-brand-500/20 bg-brand-500/5"
                  : isAnswered
                  ? "bg-slate-800 border-slate-700 text-slate-200 hover:bg-slate-750"
                  : "bg-slate-900/40 border-slate-800/80 text-slate-500 hover:bg-slate-900 hover:text-slate-400"
              }`}
            >
              {index + 1}
              {isFlagged && (
                <span className="absolute -top-1 -right-1 flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-orange-500"></span>
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div className="mt-5 space-y-2 border-t border-slate-800/50 pt-4 text-xs text-slate-400">
        <div className="flex items-center gap-2">
          <span className="w-3.5 h-3.5 rounded bg-brand-500/10 border border-brand-500 inline-block" />
          <span>Đang xem</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3.5 h-3.5 rounded bg-slate-800 border border-slate-700 inline-block" />
          <span>Đã trả lời</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3.5 h-3.5 rounded bg-slate-900 border border-slate-800/80 inline-block" />
          <span>Chưa làm</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="relative w-3.5 h-3.5 rounded bg-slate-900 border border-slate-800 inline-block">
            <span className="absolute top-0 right-0 h-1.5 w-1.5 rounded-full bg-orange-500" />
          </span>
          <span>Đã đánh dấu cờ</span>
        </div>
      </div>
    </div>
  );
};
export default QuestionNavigator;
