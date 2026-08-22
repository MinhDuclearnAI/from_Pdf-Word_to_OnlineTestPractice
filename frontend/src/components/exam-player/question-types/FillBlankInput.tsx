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
  componentType?: string;
  options?: string[];
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
  componentType,
  options = [],
}) => {
  // Regex nhận diện các mốc đục lỗ trong đoạn văn Summary:
  // Hỗ trợ: (7)......, [7]......, 7......, 7. ......, [blank_7], [blank], ......, _____
  // Đảm bảo khớp cả cặp số + chuỗi chấm/gạch nối liền sau làm 1 token duy nhất (tránh gen đúp 2 ô trống)
  const SUMMARY_TOKEN_REGEX = /(\(\d+\)[\s\._]*|\[\d+\][\s\._]*|\b\d+[\s\.\)]*[\._]{2,}|\[blank(?:_\d+)?\]|\.{3,}|_{2,})/gi;
  
  // Regex cho các câu điền từ đơn lẻ
  const CHILD_BLANK_REGEX = /___+|\[blank(?:_\d+)?\]|\.{2,}|_{2,}/gi;

  // 1. TRƯỜNG HỢP CÓ ẢNH MINH HỌA (Diagram / Image / Table có ảnh đính kèm)
  if (imageUrl) {
    return (
      <div className="w-full space-y-6">
        <div className="flex justify-center">
          <img 
            src={imageUrl} 
            alt="Hình minh họa"
            className="w-full max-w-3xl rounded-lg shadow-sm border border-slate-200/60 object-contain"
          />
        </div>

        {childQuestions && childQuestions.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 pt-2">
            {childQuestions.map((child) => {
              const cAns = childAnswers?.[String(child.id)] || "";
              const qNum = child.displayNumber || child.original_question_number || "-";
              return (
                <div 
                  key={child.id}
                  className="flex items-center gap-3 p-3 bg-white border border-slate-200/80 rounded-xl shadow-2xs"
                >
                  <span className="font-bold text-slate-800 text-sm bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200 shadow-2xs min-w-[36px] text-center flex-shrink-0">
                    {qNum}
                  </span>
                  <input
                    type="text"
                    disabled={disabled}
                    value={cAns}
                    onChange={(e) => onChildAnswerChange && onChildAnswerChange(child.id, e.target.value)}
                    placeholder="Your answer..."
                    className="flex-1 px-3.5 py-1.5 bg-slate-50 border border-slate-300 rounded-lg text-brand-700 font-bold text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/40"
                  />
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  // 2. TRƯỜNG HỢP SUMMARY COMPLETION (Đoạn văn tóm tắt đục lỗ liên tục dạng Single Unified Object)
  // Nhận diện dứt khoát: khi componentType === "summary_completion" hoặc khi questionText có nhiều mốc đục lỗ trong cùng đoạn văn
  const isSummaryMode = 
    componentType === "summary_completion" ||
    (!imageUrl && Boolean(questionText && questionText.match(SUMMARY_TOKEN_REGEX) && (questionText.match(SUMMARY_TOKEN_REGEX)?.length || 0) >= 2 && !/^\s*\d+[\.\)]\s*[A-Z]/m.test(questionText.replace(SUMMARY_TOKEN_REGEX, ''))));

  if (isSummaryMode && questionText) {
    // Trích xuất danh sách từ vựng (List of Words A-I nếu có)
    const rawOptions: string[] = (() => {
      if (options && options.length > 0) return options;
      if (childQuestions && childQuestions.length > 0 && childQuestions[0].options && childQuestions[0].options.length > 0) {
        return childQuestions[0].options;
      }
      return [];
    })();

    // Parse options thành dạng { letter, text }
    const parsedOptions = rawOptions.map((opt) => {
      const match = opt.match(/^([A-Z])[\.\s]+(.*)$/i);
      if (match) {
        return { letter: match[1].toUpperCase(), text: match[2].trim(), full: opt };
      }
      return { letter: opt.trim().substring(0, 1).toUpperCase(), text: opt.trim(), full: opt };
    });

    // Làm sạch đoạn văn tóm tắt: Tách bỏ phần danh sách từ vựng in ở cuối text nếu có (tránh hiện lặp)
    let cleanSummaryText = questionText;
    const wordlistTailMatch = questionText.match(/\n\s*([A-Z]\s+[A-Za-z]+(?:\s+[A-Z]\s+[A-Za-z]+)+)/);
    if (wordlistTailMatch && wordlistTailMatch.index !== undefined) {
      cleanSummaryText = questionText.substring(0, wordlistTailMatch.index).trim();
    }

    const tokens = cleanSummaryText.split(SUMMARY_TOKEN_REGEX);
    let blankCounter = 0;

    return (
      <div className="w-full space-y-5">
        {/* BẢNG TỪ VỰNG DÙNG CHUNG (OPTIONS / LIST OF WORDS BOX) NẾU CÓ */}
        {parsedOptions.length > 0 && (
          <div className="bg-slate-50/95 border border-slate-200/90 rounded-2xl p-4 sm:p-5 shadow-xs">
            <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">
              Danh sách từ lựa chọn (List of Words)
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2.5">
              {parsedOptions.map((opt) => (
                <div
                  key={opt.letter}
                  className="flex items-center gap-2 p-2 bg-white rounded-xl border border-slate-200/80 shadow-2xs hover:border-brand-300 transition-colors"
                >
                  <span className="font-bold text-brand-700 text-xs bg-brand-50 border border-brand-200/80 w-6 h-6 rounded-lg flex items-center justify-center flex-shrink-0 shadow-2xs">
                    {opt.letter}
                  </span>
                  <span className="text-sm font-medium text-slate-800 truncate">
                    {opt.text}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* DUY NHẤT MỘT KHUNG OBJECT HOÀN CHỈNH CHO TOÀN BỘ ĐOẠN VĂN TÓM TẮT */}
        <div className="p-5 sm:p-7 bg-white border border-slate-200/80 rounded-2xl shadow-xs leading-loose text-base font-medium text-slate-800 whitespace-pre-wrap font-sans">
          {tokens.map((token, tIdx) => {
            const isBlank = token.match(SUMMARY_TOKEN_REGEX);

            if (isBlank) {
              const numMatch = token.match(/\d+/);
              const qNum = numMatch 
                ? parseInt(numMatch[0], 10) 
                : (childQuestions?.[blankCounter]?.original_question_number || blankCounter + 1);
              
              const childObj = childQuestions?.find(
                (c) => c.original_question_number === qNum || c.displayNumber === qNum
              ) || childQuestions?.[blankCounter];

              blankCounter++;

              const childId = childObj ? String(childObj.id) : `blank_${qNum}`;
              const currentVal = (childObj && childAnswers)
                ? (childAnswers[childId] ?? "")
                : "";

              return (
                <span key={tIdx} className="inline-flex items-center gap-1.5 mx-1.5 align-middle my-1">
                  <span className="text-xs font-black text-brand-700 bg-brand-50 px-2 py-0.5 rounded-md border border-brand-200 shadow-2xs">
                    {qNum}
                  </span>

                  {parsedOptions.length > 0 ? (
                    /* Nếu có bảng từ vựng A-I -> Render Dropdown lựa chọn */
                    <select
                      disabled={disabled}
                      value={currentVal}
                      onChange={(e) => {
                        if (childObj && onChildAnswerChange) {
                          onChildAnswerChange(childObj.id, e.target.value);
                        }
                      }}
                      className="px-2.5 py-1 bg-white border border-slate-300 rounded-lg text-brand-700 font-bold text-sm text-center focus:outline-none focus:ring-2 focus:ring-brand-500 shadow-xs cursor-pointer uppercase min-w-[75px]"
                    >
                      <option value="">--</option>
                      {parsedOptions.map((opt) => (
                        <option key={opt.letter} value={opt.letter}>
                          {opt.letter} - {opt.text}
                        </option>
                      ))}
                    </select>
                  ) : (
                    /* Nếu điền từ tự do từ bài đọc -> Render Input gõ từ */
                    <input
                      type="text"
                      disabled={disabled}
                      value={currentVal}
                      placeholder={`${qNum}`}
                      onChange={(e) => {
                        if (childObj && onChildAnswerChange) {
                          onChildAnswerChange(childObj.id, e.target.value);
                        }
                      }}
                      className="w-32 sm:w-36 px-2.5 py-1 bg-white border border-slate-300 rounded-lg text-brand-700 font-bold text-sm text-center focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 shadow-xs align-middle placeholder:text-slate-300 placeholder:font-normal"
                    />
                  )}
                </span>
              );
            }

            return <span key={tIdx}>{token}</span>;
          })}
        </div>
      </div>
    );
  }

  // 3. TRƯỜNG HỢP SENTENCE COMPLETION (Danh sách từng câu độc lập có ô điền inline thay thế dấu chấm)
  if (childQuestions && childQuestions.length > 0) {
    return (
      <div className="w-full space-y-3.5">
        {childQuestions.map((child) => {
          const cAns = childAnswers?.[String(child.id)] || "";
          const qNum = child.displayNumber || child.original_question_number || "-";
          
          // 1. Lấy text câu hỏi con
          let cText = (child.question_text || "").trim();

          // 2. Fallback: Nếu child.question_text rỗng, quét từ questionText của parent theo số câu
          if (!cText && questionText) {
            const pattern = new RegExp(`(?:^|\\n)\\s*(?:${qNum}[\\.\\s\\)]|\\(${qNum}\\))\\s*([^\\n]+)`, "i");
            const match = questionText.match(pattern);
            if (match) {
              cText = match[1].trim();
            }
          }

          // Xóa số thứ tự ở đầu câu nếu có (tránh hiện lặp: "22 22. There is...")
          cText = cText.replace(/^\s*\d+[\.\s\)]\s*/, "");
          
          // 3. Phân tách vị trí đục lỗ inline ([blank], ___, ...., ..)
          const cHasInlineBlank = CHILD_BLANK_REGEX.test(cText);
          CHILD_BLANK_REGEX.lastIndex = 0;

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
                  {cText ? (
                    <span className="text-sm sm:text-base font-medium text-slate-800 leading-relaxed">
                      {cText}
                    </span>
                  ) : (
                    <span className="text-sm font-medium text-slate-400 italic">
                      Question {qNum}
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
    );
  }

  // 4. TRƯỜNG HỢP CÂU HỎI ĐỘC LẬP (Single Blank hoặc Short-Answer)
  const singleAns = typeof selectedAnswer === "string" ? selectedAnswer : "";
  const singleParts = questionText ? questionText.split(CHILD_BLANK_REGEX) : [""];
  const singleTotalBlanks = questionText ? (questionText.match(CHILD_BLANK_REGEX)?.length || 0) : 0;

  if (singleTotalBlanks > 0) {
    return (
      <div className="w-full">
        <div className="p-4 sm:p-5 bg-white border border-slate-200/80 rounded-2xl shadow-xs leading-loose text-base font-medium text-slate-800">
          {singleParts.map((part, pIdx) => (
            <React.Fragment key={pIdx}>
              <span>{part}</span>
              {pIdx < singleTotalBlanks && (
                <input
                  type="text"
                  disabled={disabled}
                  value={singleAns}
                  onChange={(e) => onChange(e.target.value)}
                  placeholder="Your answer..."
                  className="inline-block mx-1.5 px-3 py-1 bg-white border border-slate-300 rounded-lg text-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 text-center font-bold text-sm min-w-[110px] w-auto max-w-[200px] transition-all shadow-xs align-middle"
                />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>
    );
  }

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
};

export default FillBlankInput;
