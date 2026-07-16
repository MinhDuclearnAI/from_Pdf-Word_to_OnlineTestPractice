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
      <h3 className="text-lg font-medium text-slate-100 mb-4 whitespace-pre-wrap leading-relaxed">
        {questionText}
      </h3>
      <div className="space-y-3">
        {options.map((option, index) => {
          const optionLetter = String.fromCharCode(65 + index);
          // Check both literal string match and letter match (A, B, C, D)
          const isSelected = selectedAnswer === optionLetter || selectedAnswer === option;
          
          return (
            <button
              key={index}
              type="button"
              disabled={disabled}
              onClick={() => onChange(optionLetter)}
              className={`w-full flex items-center gap-3.5 px-4 py-3.5 rounded-lg border text-left transition-all duration-200 ${
                isSelected
                  ? "bg-brand-500/10 border-brand-500 text-slate-100 font-medium ring-1 ring-brand-500"
                  : "bg-slate-900/40 border-slate-800 text-slate-300 hover:bg-slate-800/40 hover:border-slate-700"
              }`}
            >
              <span
                className={`flex items-center justify-center w-6 h-6 rounded-full border text-xs font-semibold shrink-0 ${
                  isSelected
                    ? "bg-brand-500 border-brand-500 text-white"
                    : "border-slate-600 bg-slate-800 text-slate-400"
                }`}
              >
                {optionLetter}
              </span>
              <span className="leading-relaxed">{option}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
export default MCQStandard;
