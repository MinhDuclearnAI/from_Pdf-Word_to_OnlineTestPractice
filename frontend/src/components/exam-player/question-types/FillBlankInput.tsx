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
      // Dạng câu hỏi con (Sentence Completion, Short Answer, hoặc Diagram có child questions)
      return (
        <div className="w-full space-y-4">
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

          <div className="flex flex-col gap-3.5">
            {childQuestions.map((child) => {
              const cAns = childAnswers?.[String(child.id)] || "";
              const qNum = child.displayNumber || child.original_question_number || "-";
              const cText = child.question_text || "";
              
              // Kiểm tra xem câu con có chứa đục lỗ inline ([blank], ___, ....) không
              const CHILD_BLANK_REGEX = /___+|\[blank(?:_\d+)?\]|\.{3,}/gi;
              const cHasInlineBlank = CHILD_BLANK_REGEX.test(cText);
              const cParts = cText.split(CHILD_BLANK_REGEX);
              const cTotalBlanks = cText.match(CHILD_BLANK_REGEX)?.length || 0;

              return (
                <div 
                  key={child.id} 
                  className="p-4 sm:p-5 bg-white border border-slate-200/80 rounded-2xl shadow-xs flex items-start gap-3.5 sm:gap-4 transition-all hover:border-slate-300"
                >
                  {/* Ô thứ tự câu hỏi ở bên trái */}
                  <span className="font-bold text-slate-800 text-sm bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200 shadow-2xs min-w-[36px] text-center flex-shrink-0 mt-0.5">
                    {qNum}
                  </span>

                  {cHasInlineBlank ? (
                    /* Dạng điền khuyết trực tiếp thay thế vị trí dấu chấm hoặc [blank] */
                    <div className="text-sm sm:text-base font-medium text-slate-800 leading-loose flex-1">
                      {cParts.map((part, pIdx) => (
                        <React.Fragment key={pIdx}>
                          <span>{part}</span>
                          {pIdx < cTotalBlanks && (
                            <input
                              type="text"
                              disabled={disabled}
                              value={cAns}
                              onChange={(e) => onChildAnswerChange && onChildAnswerChange(child.id, e.target.value)}
                              placeholder={`${qNum}`}
                              className="inline-block mx-1.5 px-3 py-1 bg-white border border-slate-300 rounded-lg text-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 text-center font-bold text-sm min-w-[110px] w-auto max-w-[200px] transition-all shadow-xs align-middle placeholder:text-slate-300 placeholder:font-normal"
                            />
                          )}
                        </React.Fragment>
                      ))}
                    </div>
                  ) : (
                    /* Dạng câu hỏi ngắn không có đục lỗ ở giữa */
                    <div className="flex-1 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      {cText && (
                        <span className="text-sm sm:text-base font-medium text-slate-800 leading-relaxed">
                          {cText}
                        </span>
                      )}
                      <input
                        type="text"
                        disabled={disabled}
                        value={cAns}
                        onChange={(e) => onChildAnswerChange && onChildAnswerChange(child.id, e.target.value)}
                        placeholder="Your answer..."
                        className="w-full sm:max-w-[200px] px-3.5 py-2 bg-white border border-slate-300 rounded-xl text-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-500/50 transition-all font-medium text-sm placeholder:font-normal placeholder:text-slate-400"
                      />
                    </div>
                  )}
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
          {parts.map((part, index) => {
            const childObj = childQuestions && childQuestions[index];
            const blankNum = childObj
              ? String(childObj.displayNumber || childObj.original_question_number || (index + 1))
              : `${index + 1}`;
            const currentVal = (childObj && childAnswers)
              ? (childAnswers[String(childObj.id)] ?? answersList[index] ?? "")
              : (answersList[index] || "");

            return (
              <React.Fragment key={index}>
                <span>{part}</span>
                {index < totalBlanks && (
                  <input
                    type="text"
                    disabled={disabled}
                    value={currentVal}
                    onChange={(e) => {
                      handleInputChange(index, e.target.value);
                      if (childObj && onChildAnswerChange) {
                        onChildAnswerChange(childObj.id, e.target.value);
                      }
                    }}
                    placeholder={blankNum}
                    className="inline-block mx-1 px-2 py-0.5 bg-white border border-slate-300 rounded-md text-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 text-center font-bold text-sm min-w-[60px] w-[80px] max-w-[120px] transition-all shadow-sm align-middle placeholder:text-slate-400 placeholder:font-bold"
                  />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
};
export default FillBlankInput;
