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
    <div className="grid grid-cols-1 lg:grid-cols-2 h-full w-full">
      {/* Left panel: Scrollable Passage */}
      <div className="bg-white overflow-y-auto leading-relaxed text-slate-800 text-base flex flex-col border-r border-slate-200">
        <div className="sticky top-0 px-6 py-4 bg-white/95 backdrop-blur border-b border-slate-100 z-10 flex items-center shadow-sm">
          <h4 className="font-bold text-brand-600 text-lg truncate">
            {title}
          </h4>
        </div>
        <div className="p-6 md:p-8 whitespace-pre-wrap font-medium leading-relaxed tracking-wide text-justify select-text text-[15px] md">
          {passageText.split(/(\*\*.*?\*\*)/g).map((part, index) => {
            if (part.startsWith('**') && part.endsWith('**')) {
              return (
                <strong key={index} className="block text-[22px] md:text-2xl font-black text-center text-slate-900 my-8 uppercase tracking-wide">
                  {part.slice(2, -2)}
                </strong>
              );
            }
            return <span key={index}>{part}</span>;
          })}
        </div>
      </div>

      {/* Right panel: Scrollable Questions Container */}
      <div className="bg-slate-50 overflow-y-auto flex flex-col relative pb-32">
        <div className="flex-grow p-6 md:p-8 space-y-6">
          {children}
        </div>
      </div>
    </div>
  );
};
export default ReadingSplitScreen;
