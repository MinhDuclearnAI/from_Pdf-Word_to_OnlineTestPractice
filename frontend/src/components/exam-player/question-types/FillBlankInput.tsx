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
  imageUrl?: string;
  hideChildQuestionText?: boolean;
  questionNumber?: number | string;
  labelPrefix?: string;
}

export const FillBlankInput: React.FC<FillBlankInputProps> = ({
  questionText,
  selectedAnswer = "",
  onChange,
  disabled,
  childQuestions,
  childAnswers,
  onChildAnswerChange,
  imageUrl,
  hideChildQuestionText = false,
  questionNumber,
  labelPrefix = "QUESTION",
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
          {questionText && (
            <div className="text-base font-medium text-slate-800 mb-4 whitespace-pre-wrap leading-relaxed">
              {questionText}
            </div>
          )}
          
          {imageUrl && (
            <div className="mb-6 flex justify-center">
              <img 
                src={imageUrl} 
                alt="Hình minh họa"
                className="w-full max-w-3xl rounded-lg shadow-sm border border-slate-200/60 object-contain"
              />
            </div>
          )}

          <div className="flex flex-col gap-4">
            {childQuestions.map((child) => {
              const cAns = childAnswers?.[String(child.id)] || "";
              const qNum = child.displayNumber || child.original_question_number || "-";
              return (
                <div key={child.id} className="flex items-center gap-3 bg-slate-50 px-3 py-2.5 rounded-xl border border-slate-200 flex-wrap">
                  <span className="font-bold text-slate-600 text-sm bg-white px-2 py-1 rounded-lg shadow-sm border border-slate-200 min-w-[28px] text-center flex-shrink-0">{qNum}</span>
                  {child.question_text && 
                   !hideChildQuestionText &&
                   !/^Question\s*\d+$/i.test(child.question_text) && 
                   !/^Blank\s*\d+$/i.test(child.question_text) && (
                     <span className="text-slate-700 font-medium mr-2 flex-1 min-w-[200px]">{child.question_text}</span>
                  )}
                  <input
                    type="text"
                    disabled={disabled}
                    value={cAns}
                    onChange={(e) => onChildAnswerChange && onChildAnswerChange(child.id, e.target.value)}
                    placeholder="Your answer..."
                    className="w-full max-w-[220px] px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-500/50 transition-all font-medium text-sm placeholder:font-normal placeholder:text-slate-400"
                  />
                </div>
              );
            })}
          </div>
        </div>
      );
    }

    // Trường hợp đơn: không có text đục lỗ, không có childQuestions
    // → Câu hỏi short-answer: luôn luôn phải hiện câu hỏi rồi mới đến ô trống
    const singleAns = typeof selectedAnswer === "string" ? selectedAnswer : "";
    return (
      <div className="w-full">
        {questionText && (
          <div className="flex items-start gap-3 mb-4">
            {questionNumber !== undefined && (
              <span className="text-xs font-bold text-brand-300 uppercase tracking-wider bg-brand-500/15 border border-brand-500/30 px-3 py-1 rounded-full shadow-sm shrink-0 mt-0.5">
                {labelPrefix} {questionNumber}
              </span>
            )}
            <p className="text-base font-semibold text-slate-800 whitespace-pre-wrap leading-relaxed flex-1">
              {questionText}
            </p>
          </div>
        )}
        <input
          type="text"
          disabled={disabled}
          value={singleAns}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Your answer..."
          className="w-full max-w-sm px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/30 transition-all shadow-sm text-sm"
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
      <div className="flex items-start gap-3 mb-4">
        {questionNumber !== undefined && (!childQuestions || childQuestions.length === 0) && (
          <span className="text-xs font-bold text-brand-300 uppercase tracking-wider bg-brand-500/15 border border-brand-500/30 px-3 py-1 rounded-full shadow-sm shrink-0 mt-0.5">
            {labelPrefix} {questionNumber}
          </span>
        )}
        <div className="text-base font-medium text-slate-800 whitespace-pre-wrap leading-loose font-mono md:font-sans flex-1">
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
                  className="inline-block mx-1 px-2 py-0.5 bg-white border border-slate-300 rounded-md text-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 text-center font-bold text-sm min-w-[60px] w-[80px] max-w-[120px] transition-all shadow-sm align-middle placeholder:text-slate-300 placeholder:font-normal"
                />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
};
export default FillBlankInput;
