import React from "react";

interface EssayInputProps {
  questionId: string | number;
  questionText: string;
  selectedAnswer?: string;
  onChange: (answer: string) => void;
  placeholder?: string;
  disabled?: boolean;
}

export const EssayInput: React.FC<EssayInputProps> = ({
  questionText,
  selectedAnswer = "",
  onChange,
  placeholder = "Nhập câu trả lời tự luận của bạn tại đây...",
  disabled,
}) => {
  const wordCount = selectedAnswer.trim() ? selectedAnswer.trim().split(/\s+/).length : 0;

  return (
    <div className="w-full">
      <h3 className="text-base md:text-lg font-semibold text-slate-100 mb-3 whitespace-pre-wrap leading-relaxed">
        {questionText}
      </h3>
      <div className="relative">
        <textarea
          disabled={disabled}
          value={selectedAnswer}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          rows={7}
          className="w-full px-4 py-3.5 bg-slate-900/80 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:border-brand-500 focus:ring-brand-500/30 font-sans leading-relaxed resize-y min-h-[170px] transition-all shadow-inner"
        />
        <div className="absolute bottom-3 right-3 px-2.5 py-1 bg-slate-900/90 backdrop-blur rounded-lg text-xs text-slate-400 border border-slate-700/60 shadow flex items-center gap-1.5">
          <span>Số từ:</span>
          <span className="font-bold text-brand-400">{wordCount}</span>
        </div>
      </div>
    </div>
  );
};
export default EssayInput;
