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
      <h3 className="text-lg font-medium text-slate-100 mb-4 whitespace-pre-wrap leading-relaxed">
        {questionText}
      </h3>
      <div className="relative">
        <textarea
          disabled={disabled}
          value={selectedAnswer}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          rows={8}
          className="w-full px-4 py-3 bg-slate-900/40 border border-slate-800 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:border-brand-500 focus:ring-brand-500/20 font-sans leading-relaxed resize-y min-h-[200px]"
        />
        <div className="absolute bottom-3 right-3 px-2 py-1 bg-slate-950/80 backdrop-blur rounded text-xs text-slate-400 border border-slate-800">
          Số từ: <span className="font-semibold text-brand-400">{wordCount}</span>
        </div>
      </div>
    </div>
  );
};
export default EssayInput;
