import React from "react";
import { BlockMath, InlineMath } from "react-katex";
import "katex/dist/katex.min.css";

interface LatexFormulaQuestionProps {
  questionId: string | number;
  questionText: string;
  options: string[];
  selectedAnswer?: string;
  onChange: (answer: string) => void;
  disabled?: boolean;
}

export const LatexFormulaQuestion: React.FC<LatexFormulaQuestionProps> = ({
  questionText,
  options,
  selectedAnswer,
  onChange,
  disabled,
}) => {
  // Helper to parse and render text with LaTeX blocks ($...$ or $$...$$)
  const renderTextWithLatex = (text: string) => {
    if (!text) return "";
    
    // Split by block math $$
    const blockParts = text.split(/\$\$(.*?)\$\$/g);
    
    return blockParts.map((part, blockIdx) => {
      if (blockIdx % 2 !== 0) {
        return <BlockMath key={`block-${blockIdx}`} math={part} />;
      }
      
      // Split by inline math $
      const inlineParts = part.split(/\$(.*?)\$/g);
      
      return inlineParts.map((subPart, inlineIdx) => {
        if (inlineIdx % 2 !== 0) {
          return <InlineMath key={`inline-${blockIdx}-${inlineIdx}`} math={subPart} />;
        }
        return <span key={`text-${blockIdx}-${inlineIdx}`} className="whitespace-pre-wrap">{subPart}</span>;
      });
    });
  };

  return (
    <div className="w-full">
      <div className="text-lg font-medium text-slate-100 mb-6 leading-relaxed">
        {renderTextWithLatex(questionText)}
      </div>

      {options && options.length > 0 ? (
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
                <span className="leading-relaxed text-sm md:text-base">{renderTextWithLatex(option)}</span>
              </button>
            );
          })}
        </div>
      ) : null}
    </div>
  );
};
export default LatexFormulaQuestion;
