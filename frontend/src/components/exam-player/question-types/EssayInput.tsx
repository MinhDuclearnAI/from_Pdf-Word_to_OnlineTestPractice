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
      <h3 className="text-base md font-semibold text-slate-800 mb-3 whitespace-pre-wrap leading-relaxed">
        {questionText}
      </h3>
      <div className="relative">
        <textarea
          disabled={disabled}
          value={selectedAnswer}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          rows={7}
          className="w-full px-4 py-3.5 bg-white/80 border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus focus:ring-brand-500/30 font-sans leading-relaxed resize-y min-h-[170px] transition-all shadow-inner"
        />
        <div className="absolute bottom-3 right-3 px-2.5 py-1 bg-white/90 backdrop-blur rounded-lg text-xs text-slate-500 border border-slate-300/60 shadow flex items-center gap-1.5">
          <span>Số từ:</span>
          <span className="font-bold text-brand-400">{wordCount}</span>
        </div>
      </div>
    </div>
  );
};
export default EssayInput;
