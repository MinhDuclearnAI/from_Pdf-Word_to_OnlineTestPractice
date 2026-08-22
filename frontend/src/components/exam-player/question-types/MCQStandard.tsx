import React from "react";

interface MCQStandardProps {
  questionId: string | number;
  questionText: string;
  options: string[];
  selectedAnswer?: string;
  onChange: (answer: string) => void;
  disabled?: boolean;
  questionNumber?: number | string;
  labelPrefix?: string;
}

export const MCQStandard: React.FC<MCQStandardProps> = ({
  questionText,
  options,
  selectedAnswer,
  onChange,
  disabled,
  questionNumber,
  labelPrefix = "QUESTION",
}) => {
  // Hàm chuẩn hóa text đáp án: Bỏ tiền tố A., B., C. và viết hoa chữ cái đầu câu
  const cleanOptionText = (text: string) => {
    if (!text) return "";
    let cleaned = text.trim();
    
    // Nếu là TRUE / FALSE / NOT GIVEN / YES / NO thì giữ nguyên
    if (/^(true|false|not given|yes|no)$/i.test(cleaned)) {
      return cleaned.toUpperCase();
    }

    // Loại bỏ tiền tố như "A.", "A)", "A -", "A:", "(A)", "A "
    cleaned = cleaned.replace(/^\(?[A-Za-z0-9]\)?[\.\s:\-]+/i, "").trim();
    if (cleaned.length > 0) {
      cleaned = cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
    }
    return cleaned;
  };

  return (
    <div className="w-full">
      <div className="flex items-start gap-3 mb-4">
        {questionNumber !== undefined && (
          <span className="text-xs font-bold text-brand-300 uppercase tracking-wider bg-brand-500/15 border border-brand-500/30 px-3 py-1 rounded-full shadow-sm shrink-0 mt-0.5">
            {labelPrefix} {questionNumber}
          </span>
        )}
        <h3 className="text-base font-semibold text-slate-800 whitespace-pre-wrap leading-relaxed flex-1">
          {questionText}
        </h3>
      </div>
      <div className="space-y-2.5">
        {options.map((option, index) => {
          const optionLetter = String.fromCharCode(65 + index);
          const isSelected = selectedAnswer === optionLetter || selectedAnswer === option;
          const displayOptionText = cleanOptionText(option);
          
          return (
            <button
              key={index}
              type="button"
              disabled={disabled}
              onClick={() => onChange(optionLetter)}
              className={`w-full flex items-center gap-3.5 px-4 py-3 rounded-xl border text-left transition-all duration-200 ${
                isSelected
                  ? "bg-brand-500/15 border-brand-500 text-slate-800 font-semibold ring-2 ring-brand-500/30 shadow-md"
                  : "bg-white/60 border-slate-200/90 text-slate-700 hover:bg-slate-50/80 hover:border-slate-300"
              }`}
            >
              <span
                className={`flex items-center justify-center w-7 h-7 rounded-full border text-xs font-bold shrink-0 transition-all ${
                  isSelected
                    ? "bg-brand-600 border-brand-500 text-white shadow"
                    : "border-slate-300 bg-slate-100 text-slate-500"
                }`}
              >
                {optionLetter}
              </span>
              <span className="leading-relaxed text-sm md:text-base text-slate-800 font-medium flex-1">
                {displayOptionText}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
export default MCQStandard;
