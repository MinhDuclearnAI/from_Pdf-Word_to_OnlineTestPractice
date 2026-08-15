import React from "react";

interface FillBlankInputProps {
  questionId: string | number;
  questionText: string;
  selectedAnswer?: string | string[];
  onChange: (answer: string | string[]) => void;
  disabled?: boolean;
  childQuestions?: any[];
  childAnswers?: Record<string, any>;
  onChildAnswerChange?: (childId: string | number, answer: any) => void;
}

export const FillBlankInput: React.FC<FillBlankInputProps> = ({
  questionText,
  selectedAnswer = "",
  onChange,
  disabled,
  childQuestions,
  childAnswers,
  onChildAnswerChange,
}) => {
  // Hỗ trợ ___ hoặc [blank] hoặc [blank_1], [blank_2]
  const BLANK_REGEX = /___+|\[blank(?:_\d+)?\]/gi;
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
    if (childQuestions && childQuestions.length > 0) {
      // Dạng hình ảnh thuần túy hoặc không có text đục lỗ, nhưng có childQuestions (từ block parent)
      return (
        <div className="w-full">
          <div className="text-base font-medium text-slate-800 mb-6 whitespace-pre-wrap leading-relaxed">
            {questionText}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {childQuestions.map((child) => {
              const cAns = childAnswers?.[String(child.id)] || "";
              const qNum = child.displayNumber || child.original_question_number || "-";
              return (
                <div key={child.id} className="flex items-center gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200">
                  <span className="font-bold text-slate-700 bg-white px-2 py-1 rounded shadow-sm border border-slate-200">{qNum}</span>
                  <input
                    type="text"
                    disabled={disabled}
                    value={cAns}
                    onChange={(e) => onChildAnswerChange && onChildAnswerChange(child.id, e.target.value)}
                    placeholder="Nhập câu trả lời..."
                    className="flex-1 px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-500/50 transition-all font-medium placeholder:font-normal placeholder:text-slate-400"
                  />
                </div>
              );
            })}
          </div>
        </div>
      );
    }

    const singleAns = typeof selectedAnswer === "string" ? selectedAnswer : "";
    return (
      <div className="w-full">
        <h3 className="text-base font-semibold text-slate-800 mb-3 whitespace-pre-wrap leading-relaxed">
          {questionText}
        </h3>
        <input
          type="text"
          disabled={disabled}
          value={singleAns}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Nhập câu trả lời điền khuyết..."
          className="w-full max-w-md px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/30 transition-all shadow-sm"
        />
      </div>
    );
  }

  return (
    <div className="w-full overflow-x-auto">
      {/* 
        Loại bỏ flex flex-wrap để giữ nguyên định dạng xuống dòng (\n) của Table và Summary.
        Sử dụng whitespace-pre-wrap để hiển thị đúng khoảng trắng và line-break.
        Các input sẽ tự động hiển thị inline cùng với text.
      */}
      <div className="text-base font-medium text-slate-800 mb-4 whitespace-pre-wrap leading-loose font-mono md:font-sans">
        {parts.map((part, index) => (
          <React.Fragment key={index}>
            <span>{part}</span>
            {index < totalBlanks && (
              <input
                type="text"
                disabled={disabled}
                value={answersList[index] || ""}
                onChange={(e) => handleInputChange(index, e.target.value)}
                placeholder={`${index + 1}`}
                className="inline-block mx-1 px-2 py-1 bg-white border border-slate-300 rounded-md text-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 text-center font-bold text-sm min-w-[80px] w-auto max-w-full transition-all shadow-sm align-middle placeholder:text-slate-300 placeholder:font-normal"
              />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};
export default FillBlankInput;
