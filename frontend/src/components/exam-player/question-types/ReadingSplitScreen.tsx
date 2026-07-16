import React from "react";

interface ReadingSplitScreenProps {
  passageText: string;
  children: React.ReactNode;
}

export const ReadingSplitScreen: React.FC<ReadingSplitScreenProps> = ({ passageText, children }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-[calc(100vh-200px)] min-h-[500px]">
      {/* Left panel: Scrollable Passage */}
      <div className="bg-slate-900/30 border border-slate-800 rounded-xl p-5 overflow-y-auto leading-relaxed text-slate-300 text-base shadow-inner">
        <h4 className="font-semibold text-slate-200 mb-3 sticky top-0 bg-slate-950/80 backdrop-blur py-2 border-b border-slate-800/50">
          Đoạn văn đọc hiểu / Reading Passage
        </h4>
        <div className="whitespace-pre-wrap pr-2 text-slate-300 font-normal leading-relaxed">{passageText}</div>
      </div>

      {/* Right panel: Scrollable Question */}
      <div className="bg-slate-900/10 border border-slate-800/50 rounded-xl p-5 overflow-y-auto flex flex-col justify-start">
        <h4 className="font-semibold text-slate-200 mb-3 pb-2 border-b border-slate-800/50">
          Câu hỏi / Question
        </h4>
        <div className="flex-grow">{children}</div>
      </div>
    </div>
  );
};
export default ReadingSplitScreen;
