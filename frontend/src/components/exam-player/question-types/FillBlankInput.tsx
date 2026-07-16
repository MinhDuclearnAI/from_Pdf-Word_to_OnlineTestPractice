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
        <h3 className="text-lg font-medium text-slate-100 mb-4 whitespace-pre-wrap leading-relaxed">
          {questionText}
        </h3>
        <input
          type="text"
          disabled={disabled}
          value={singleAns}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Nhập câu trả lời điền khuyết..."
          className="w-full max-w-md px-4 py-2.5 bg-slate-900/60 border border-slate-855 border-slate-800 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:border-brand-500 focus:ring-brand-500/20"
        />
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="text-lg font-medium text-slate-100 mb-6 leading-relaxed flex flex-wrap items-center gap-y-3">
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
                className="mx-2 px-3 py-1 bg-slate-900 border border-slate-700 rounded-md text-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 text-center font-semibold text-base min-w-[100px] w-auto max-w-[200px]"
              />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};
export default FillBlankInput;
