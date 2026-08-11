import React from "react";

interface ReadingSplitScreenProps {
  title?: string;
  passageText: string;
  children: React.ReactNode;
}

export const ReadingSplitScreen: React.FC<ReadingSplitScreenProps> = ({ 
  title = "Đoạn văn đọc hiểu / Reading Passage", 
  passageText, 
  children 
}) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 min-h-[650px] h-[calc(100vh-160px)] max-h-[calc(100vh-160px)]">
      {/* Left panel: Scrollable Passage */}
      <div className="bg-slate-900/70 border border-slate-800/80 rounded-2xl p-6 overflow-y-auto leading-relaxed text-slate-100 text-base shadow-xl flex flex-col">
        <div className="sticky -top-6 -mx-6 -mt-6 px-6 py-3.5 bg-slate-900/95 backdrop-blur border-b border-slate-800/80 mb-4 z-10 flex items-center gap-2">
          <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-bold bg-brand-500/20 text-brand-300 border border-brand-500/40">
            Bài đọc
          </span>
          <h4 className="font-bold text-slate-100 text-base md:text-lg truncate">
            {title}
          </h4>
        </div>
        <div className="whitespace-pre-wrap text-slate-200 font-normal leading-relaxed tracking-wide text-justify pr-2 select-text text-[15px] md:text-base">
          {passageText}
        </div>
      </div>

      {/* Right panel: Scrollable Questions Container */}
      <div className="bg-slate-900/40 border border-slate-800/60 rounded-2xl p-6 overflow-y-auto flex flex-col space-y-5 shadow-xl">
        <div className="sticky -top-6 -mx-6 -mt-6 px-6 py-3.5 bg-slate-900/95 backdrop-blur border-b border-slate-800/80 mb-2 z-10 flex items-center justify-between">
          <h4 className="font-bold text-slate-100 text-base md:text-lg">
            Danh sách câu hỏi
          </h4>
          <span className="text-xs text-brand-400 font-medium">Cuộn xuống để làm tiếp</span>
        </div>
        <div className="flex-grow space-y-5">{children}</div>
      </div>
    </div>
  );
};
export default ReadingSplitScreen;
