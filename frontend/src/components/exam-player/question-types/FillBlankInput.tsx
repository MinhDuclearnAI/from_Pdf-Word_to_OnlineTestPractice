import React from "react";

interface FillBlankInputProps {
  questionId: string | number;
  questionText: string;
  selectedAnswer?: string | string[];
  onChange: (answer: string | string[]) => void;
  disabled?: boolean;
}

export const FillBlankInput: React.FC<FillBlankInputProps> = ({
  questionText,
  selectedAnswer = "",
  onChange,
  disabled,
}) => {
  const BLANK_REGEX = /___+|\[blank\]/g;
  const parts = questionText.split(BLANK_REGEX);
  const totalBlanks = questionText.match(BLANK_REGEX)?.length || 0;

  const answersList = Array.isArray(selectedAnswer)
    ? selectedAnswer
    : typeof selectedAnswer === "string" && selectedAnswer
    ? [selectedAnswer]
    : Array(totalBlanks).fill("");

  const handleInputChange = (index: number, val: string) => {
    const newAnswers = [...answersList];
    newAnswers[index] = val;
    
    if (totalBlanks <= 1) {
      onChange(newAnswers[0] || "");
    } else {
      onChange(newAnswers);
    }
  };

  if (totalBlanks === 0) {
    const singleAns = typeof selectedAnswer === "string" ? selectedAnswer : "";
    return (
      <div className="w-full">
        <h3 className="text-base md font-semibold text-slate-800 mb-3 whitespace-pre-wrap leading-relaxed">
          {questionText}
        </h3>
        <input
          type="text"
          disabled={disabled}
          value={singleAns}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Nhập câu trả lời điền khuyết..."
          className="w-full max-w-md px-4 py-2.5 bg-white/80 border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus focus:ring-brand-500/30 transition-all shadow-inner"
        />
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="text-base md font-semibold text-slate-800 mb-4 leading-relaxed flex flex-wrap items-center gap-y-3">
        {parts.map((part, index) => (
          <React.Fragment key={index}>
            <span className="whitespace-pre-wrap">{part}</span>
            {index < totalBlanks && (
              <input
                type="text"
                disabled={disabled}
                value={answersList[index] || ""}
                onChange={(e) => handleInputChange(index, e.target.value)}
                placeholder={`(${index + 1})`}
                className="mx-2 px-3.5 py-1.5 bg-white/90 border border-slate-300/80 rounded-lg text-brand-300 focus:outline-none focus:ring-2 focus:ring-brand-500 focus text-center font-bold text-base min-w-[110px] w-auto max-w-[220px] transition-all shadow"
              />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};
export default FillBlankInput;
