import React from "react";

interface MCQStandardProps {
  questionId: string | number;
  questionText: string;
  options: string[];
  selectedAnswer?: string;
  onChange: (answer: string) => void;
  disabled?: boolean;
}

export const MCQStandard: React.FC<MCQStandardProps> = ({
  questionText,
  options,
  selectedAnswer,
  onChange,
  disabled,
}) => {
  return (
    <div className="w-full">
      <h3 className="text-base md:text-lg font-semibold text-slate-100 mb-4 whitespace-pre-wrap leading-relaxed">
        {questionText}
      </h3>
      <div className="space-y-2.5">
        {options.map((option, index) => {
          const optionLetter = String.fromCharCode(65 + index);
          const isSelected = selectedAnswer === optionLetter || selectedAnswer === option;
          
          return (
            <button
              key={index}
              type="button"
              disabled={disabled}
              onClick={() => onChange(optionLetter)}
              className={`w-full flex items-center gap-3.5 px-4 py-3 rounded-xl border text-left transition-all duration-200 ${
                isSelected
                  ? "bg-brand-500/15 border-brand-500 text-slate-100 font-semibold ring-2 ring-brand-500/30 shadow-md"
                  : "bg-slate-900/60 border-slate-800/90 text-slate-200 hover:bg-slate-800/70 hover:border-slate-700"
              }`}
            >
              <span
                className={`flex items-center justify-center w-7 h-7 rounded-full border text-xs font-bold shrink-0 transition-all ${
                  isSelected
                    ? "bg-brand-600 border-brand-500 text-white shadow"
                    : "border-slate-700 bg-slate-800 text-slate-400"
                }`}
              >
                {optionLetter}
              </span>
              <span className="leading-relaxed text-sm md:text-base">{option}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
export default MCQStandard;
