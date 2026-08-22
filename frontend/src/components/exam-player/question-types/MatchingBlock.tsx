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
  // 1. Trích xuất danh sách options dùng chung (A-F)
  // Options có thể lấy từ parentQuestion.options, childQuestions[0].options, hoặc parse từ parentQuestion.question_text
  const rawOptions: string[] = (() => {
    if (parentQuestion.options && Array.isArray(parentQuestion.options) && parentQuestion.options.length > 0) {
      return parentQuestion.options;
    }
    if (childQuestions && childQuestions.length > 0 && childQuestions[0].options && Array.isArray(childQuestions[0].options)) {
      return childQuestions[0].options;
    }
    return [];
  })();

  // Parse raw options into { letter, text }
  const parsedOptions = React.useMemo(() => {
    return rawOptions.map((opt) => {
      const match = opt.match(/^([A-Z])[\.\s]+(.*)$/i);
      if (match) {
        return { letter: match[1].toUpperCase(), text: match[2].trim(), full: opt };
      }
      return { letter: opt.trim().substring(0, 1).toUpperCase(), text: opt.trim(), full: opt };
    });
  }, [rawOptions]);

  // Nếu không có mảng options nhưng có block content chứa A-F trong question_text
  const fallbackOptionsFromText = React.useMemo(() => {
    if (parsedOptions.length > 0) return parsedOptions;
    const text = parentQuestion.question_text || "";
    const lines = text.split("\n").map((l: string) => l.trim()).filter(Boolean);
    const extracted: { letter: string; text: string; full: string }[] = [];
    
    for (const line of lines) {
      const match = line.match(/^([A-Z])[\.\s]+(.*)$/);
      if (match) {
        extracted.push({ letter: match[1].toUpperCase(), text: match[2].trim(), full: line });
      }
    }
    return extracted;
  }, [parentQuestion.question_text, parsedOptions]);

  const effectiveOptions = parsedOptions.length > 0 ? parsedOptions : fallbackOptionsFromText;
  const optionLetters = effectiveOptions.map((o) => o.letter);

  return (
    <div className="w-full space-y-6">
      {/* 1. KHUNG BẢNG LỰA CHỌN A-F DÙNG CHUNG (OPTIONS BOX) */}
      {effectiveOptions.length > 0 && (
        <div className="bg-slate-50/90 border border-slate-200/90 rounded-2xl p-4 sm:p-6 shadow-xs">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">
            Danh sách lựa chọn (Options)
          </div>
          <div className="grid grid-cols-1 gap-2.5">
            {effectiveOptions.map((opt) => (
              <div
                key={opt.letter}
                className="flex items-start gap-3 p-2.5 bg-white rounded-xl border border-slate-200/70 shadow-2xs hover:border-brand-300 transition-colors"
              >
                <span className="font-black text-brand-700 text-sm bg-brand-50 border border-brand-200/70 w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 shadow-2xs">
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

              {/* Ô chọn đáp án (Select Dropdown hoặc Input) */}
              <div className="flex items-center gap-2 self-end sm:self-auto flex-shrink-0">
                <select
                  value={currentAns}
                  disabled={disabled}
                  onChange={(e) => onChildAnswerChange && onChildAnswerChange(child.id, e.target.value)}
                  className="px-3.5 py-2 bg-slate-50 border border-slate-300 hover:border-brand-500 rounded-xl text-brand-700 font-bold text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30 transition-all shadow-xs cursor-pointer min-w-[100px] text-center uppercase"
                >
                  <option value="">-- Chọn --</option>
                  {optionLetters.length > 0 ? (
                    optionLetters.map((letter) => (
                      <option key={letter} value={letter}>
                        {letter}
                      </option>
                    ))
                  ) : (
                    ["A", "B", "C", "D", "E", "F", "G", "H"].map((letter) => (
                      <option key={letter} value={letter}>
                        {letter}
                      </option>
                    ))
                  )}
                </select>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default MatchingBlock;
