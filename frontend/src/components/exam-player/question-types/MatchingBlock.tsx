import React from "react";

interface MatchingBlockProps {
  parentQuestion: any;
  childQuestions: any[];
  childAnswers?: Record<string, any>;
  onChildAnswerChange?: (childId: string | number, answer: any) => void;
  disabled?: boolean;
}

export const MatchingBlock: React.FC<MatchingBlockProps> = ({
  parentQuestion,
  childQuestions,
  childAnswers,
  onChildAnswerChange,
  disabled,
}) => {
  const isMatchingHeadings = parentQuestion.component_type === "matching_headings";

  // 1. Trích xuất danh sách options dùng chung (A-F hoặc i-ix) động 100% từ JSON
  const rawOptions: string[] = (() => {
    if (parentQuestion.options && Array.isArray(parentQuestion.options) && parentQuestion.options.length > 0) {
      return parentQuestion.options;
    }
    if (childQuestions && childQuestions.length > 0 && childQuestions[0].options && Array.isArray(childQuestions[0].options)) {
      return childQuestions[0].options;
    }
    return [];
  })();

  // Parse raw options into { letter, text, full } (Hỗ trợ cả A-Z, 1-9 và La Mã i, ii, iii...)
  const parsedOptions = React.useMemo(() => {
    return rawOptions.map((opt) => {
      const match = opt.match(/^([ivxlcdm]+|[A-Z]|\d+)[\.\s:\-]+(.*)$/i);
      if (match) {
        return { letter: match[1].trim(), text: match[2].trim(), full: opt };
      }
      return { letter: opt.trim(), text: opt.trim(), full: opt };
    });
  }, [rawOptions]);

  // Nếu không có mảng options nhưng có block content chứa A-F hoặc i-ix trong question_text
  const fallbackOptionsFromText = React.useMemo(() => {
    if (parsedOptions.length > 0 && parsedOptions.some(o => o.text !== o.letter)) return parsedOptions;
    const text = parentQuestion.question_text || "";
    const lines = text.split("\n").map((l: string) => l.trim()).filter(Boolean);
    const extracted: { letter: string; text: string; full: string }[] = [];
    
    for (const line of lines) {
      if (/^(?:List of Headings|Headings|List of Researchers|List of [A-Za-z]+)\b/i.test(line)) {
        continue;
      }
      const match = line.match(/^([ivxlcdm]+|[A-Z]|\d+)[\.\s:\-]+(.*)$/i);
      if (match) {
        extracted.push({ letter: match[1].trim(), text: match[2].trim(), full: line });
      }
    }
    return extracted;
  }, [parentQuestion.question_text, parsedOptions]);

  const effectiveOptions = (parsedOptions.length > 0 && parsedOptions.some(o => o.text !== o.letter)) 
    ? parsedOptions 
    : (fallbackOptionsFromText.length > 0 ? fallbackOptionsFromText : parsedOptions);

  const optionLetters = effectiveOptions.map((o) => o.letter);

  // Xác định xem có nên hiển thị Options Box không:
  // 1. Với matching_headings -> LUÔN HIỂN THỊ nếu có danh sách tiêu đề
  // 2. Với matching_features -> Hiển thị nếu có mô tả nội dung (A. Steven Tanksley...), Ẩn nếu chỉ là chọn đoạn văn A-F
  const isParagraphMatching = (() => {
    const parentText = (parentQuestion.question_text || "").toLowerCase();
    const parentIns = (parentQuestion.instruction || "").toLowerCase();
    return (
      !isMatchingHeadings && (
        parentText.includes("which paragraph contains") ||
        parentIns.includes("which paragraph contains") ||
        (parentIns.includes("paragraphs, a-") && !parentIns.includes("heading"))
      )
    );
  })();

  const hasMeaningfulDescriptions = effectiveOptions.some(
    (opt) => opt.text && opt.text.length > 1 && opt.text.toLowerCase() !== opt.letter.toLowerCase()
  );

  const shouldShowOptionsBox = (isMatchingHeadings && hasMeaningfulDescriptions) || (!isParagraphMatching && hasMeaningfulDescriptions);

  return (
    <div className="w-full space-y-6">
      {/* 1. KHUNG BẢNG LỰA CHỌN / TIÊU ĐỀ DÙNG CHUNG (OPTIONS BOX) */}
      {shouldShowOptionsBox && effectiveOptions.length > 0 && (
        <div className="bg-slate-50/95 border border-slate-200/90 rounded-2xl p-4 sm:p-6 shadow-xs">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">
            {isMatchingHeadings ? "List of Headings" : "Options"}
          </div>
          <div className="grid grid-cols-1 gap-2.5">
            {effectiveOptions.map((opt) => (
              <div
                key={opt.letter}
                className="flex items-start gap-3 p-3 bg-white rounded-xl border border-slate-200/80 shadow-2xs hover:border-brand-300 transition-colors"
              >
                <span className="font-bold text-brand-700 text-xs bg-brand-50 border border-brand-200/80 min-w-[28px] h-7 px-1.5 rounded-lg flex items-center justify-center flex-shrink-0 shadow-2xs">
                  {opt.letter}
                </span>
                <span className="text-sm font-medium text-slate-800 leading-relaxed pt-0.5">
                  {opt.text}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 2. DANH SÁCH CÂU HỎI CON VÀ Ô CHỌN ĐÁP ÁN */}
      <div className="space-y-3.5">
        {childQuestions.map((child) => {
          const qNum = child.displayNumber || child.original_question_number || "-";
          const currentAns = childAnswers?.[String(child.id)] || "";

          return (
            <div
              key={child.id}
              className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4 p-4 bg-white border border-slate-200/80 rounded-2xl shadow-xs hover:border-slate-300 transition-all"
            >
              {/* Vế câu hỏi với số câu bên trái */}
              <div className="flex items-start sm:items-center gap-3.5 flex-1 min-w-0">
                <span className="font-bold text-slate-800 text-sm bg-slate-100 px-3 py-1.5 rounded-xl border border-slate-200 shadow-2xs min-w-[36px] text-center flex-shrink-0 mt-0.5 sm:mt-0">
                  {qNum}
                </span>
                <p className="text-sm sm:text-base font-medium text-slate-800 leading-relaxed">
                  {child.question_text}
                </p>
              </div>

              {/* Ô chọn đáp án (Hoàn toàn Dynamic theo JSON) */}
              <div className="flex items-center gap-2 self-end sm:self-auto flex-shrink-0">
                {optionLetters.length > 0 ? (
                  <select
                    value={currentAns}
                    disabled={disabled}
                    onChange={(e) => onChildAnswerChange && onChildAnswerChange(child.id, e.target.value)}
                    className="px-3.5 py-2 bg-slate-50 border border-slate-300 hover:border-brand-500 rounded-xl text-brand-700 font-bold text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30 transition-all shadow-xs cursor-pointer min-w-[110px] text-center"
                  >
                    <option value="">-- Select --</option>
                    {optionLetters.map((letter) => (
                      <option key={letter} value={letter}>
                        {letter}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="text"
                    disabled={disabled}
                    value={currentAns}
                    onChange={(e) => onChildAnswerChange && onChildAnswerChange(child.id, e.target.value)}
                    placeholder="Your answer..."
                    className="w-full sm:max-w-[150px] px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-xl text-brand-700 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/50 transition-all font-bold text-sm text-center"
                  />
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default MatchingBlock;
