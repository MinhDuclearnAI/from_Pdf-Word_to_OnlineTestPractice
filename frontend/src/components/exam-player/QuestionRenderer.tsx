import React from "react";
import MCQStandard from "./question-types/MCQStandard";
import LatexFormulaQuestion from "./question-types/LatexFormulaQuestion";
import EssayInput from "./question-types/EssayInput";
import FillBlankInput from "./question-types/FillBlankInput";
import MatchingBlock from "./question-types/MatchingBlock";
import UnknownQuestionFallback from "./question-types/UnknownQuestionFallback";
import ReadingSplitScreen from "./question-types/ReadingSplitScreen";

interface QuestionRendererProps {
  question: {
    id: string | number;
    component_type?: string;
    question_text?: string;
    options?: string[];
    passage_ref?: string;
    part_title?: string;
    answer_placeholder?: string;
    [key: string]: any;
  };
  questionNumber?: number | string;
  selectedAnswer?: any;
  onChange: (answer: any) => void;
  disabled?: boolean;
  isStandalonePassage?: boolean; // Nếu true, không tự động bọc ReadingSplitScreen (vì container cha đã bọc)
  isEnglish?: boolean;  // Passed from ExamPlayer based on exam.subject — single source of truth
  childQuestions?: any[];
  childAnswers?: Record<string, any>;
  onChildAnswerChange?: (childId: string | number, answer: any) => void;
}

export const QuestionRenderer: React.FC<QuestionRendererProps> = ({
  question,
  questionNumber,
  selectedAnswer,
  onChange,
  disabled,
  isStandalonePassage = false,
  isEnglish = false,
  childQuestions,
  childAnswers,
  onChildAnswerChange,
}) => {
  const rawQText = question.question_text || "";
  let instructionText = rawQText;
  let contentText = "";

  if (
    question.component_type &&
    ["table_completion", "summary_completion", "diagram_label_completion", "sentence_completion", "matching_features"].includes(
      question.component_type
    )
  ) {
    const parts = rawQText.split(/\n\n+/);
    if (parts.length > 1) {
      instructionText = parts[0];
      contentText = parts.slice(1).join("\n\n");
      // Xóa rác [blank] nếu content chỉ toàn là [blank]
      if (/^(\[blank(?:_\d+)?\]|\s)+$/i.test(contentText)) {
        contentText = "";
      }
    } else {
      instructionText = parts[0];
    }
  }

  // Dọn dẹp triệt để rác [blank_X] khỏi instructionText để Red Badge luôn sạch
  instructionText = instructionText.replace(/\[blank(?:_\d+)?\]/gi, '').trim();

  const renderQuestionComponent = () => {
    const qText = rawQText;
    switch (question.component_type) {
      case "multiple_choice":
      case "true_false_not_given":
      case "multiple_choice_ielts":
        return (
          <MCQStandard
            questionId={question.id}
            questionText={qText}
            options={question.options || []}
            selectedAnswer={selectedAnswer}
            onChange={onChange}
            disabled={disabled}
            questionNumber={questionNumber}
            labelPrefix={labelPrefix}
          />
        );
      case "math_equation":
      case "latex_formula":
        return (
          <LatexFormulaQuestion
            questionId={question.id}
            questionText={qText}
            options={question.options || []}
            selectedAnswer={selectedAnswer}
            onChange={onChange}
            disabled={disabled}
            questionNumber={questionNumber}
            labelPrefix={labelPrefix}
          />
        );
      case "essay":
      case "writing":
        return (
          <EssayInput
            questionId={question.id}
            questionText={qText}
            selectedAnswer={selectedAnswer}
            onChange={onChange}
            placeholder={question.answer_placeholder}
            disabled={disabled}
            questionNumber={questionNumber}
            labelPrefix={labelPrefix}
          />
        );
      case "fill_in_the_blank":
      case "fill_blank":
      case "sentence_completion":
      case "summary_completion":
      case "table_completion":
      case "diagram_label_completion":
      case "matching_headings":
      case "matching_features":
        return (
          <FillBlankInput
            questionId={question.id}
            questionText={qText}
            selectedAnswer={selectedAnswer}
            onChange={onChange}
            disabled={disabled}
            questionNumber={questionNumber}
            labelPrefix={labelPrefix}
          />
        );
      default:
        return <UnknownQuestionFallback questionType={question.component_type || "unknown"} />;
    }
  };

  // Đối với các môn thường, nếu có passage_ref bị thừa (ví dụ "[Multiple Choice]"), ta sẽ bỏ qua không in ra Split Screen nữa.
  // Các passage_ref hợp lệ và dài đã được ExamPlayer gom nhóm và tự bọc SplitScreen.
  // Vì vậy QuestionRenderer chỉ tập trung render duy nhất câu hỏi.


  // Label prefix: determined by isEnglish prop (set by ExamPlayer from exam.subject)
  const labelPrefix = isEnglish ? "QUESTION" : "CÂU";


  // Card render chuẩn trong danh sách cuộn liên tiếp
  return (
    <div 
      id={`question-card-${question.id}`} 
      className="bg-white border border-slate-200/80 rounded-2xl p-5 md:p-6 shadow-sm transition-all duration-200 scroll-mt-6"
    >
      {question.part_title && (!childQuestions || childQuestions.length === 0) && (
        <div className="flex items-center justify-end mb-2">
          <span className="text-xs text-slate-400 font-medium">{question.part_title}</span>
        </div>
      )}
      
      {/* Hiển thị Hình ảnh / Biểu đồ (nếu không phải là group question, vì group question sẽ pass xuống component con để render tối ưu) */}
      {question.image_url && (!childQuestions || childQuestions.length === 0) && (
        <div className="mb-6 flex justify-center">
          <img 
            src={question.image_url} 
            alt={`Hình minh họa cho câu ${questionNumber || ''}`}
            className="w-full max-w-3xl rounded-lg shadow-sm border border-slate-200/60 object-contain"
          />
        </div>
      )}

      {childQuestions && childQuestions.length > 0 ? (
        <div className="mt-2">
          {/* MỚI: Render Red IELTS Badge cho Instruction */}
          <div className="bg-[#e22f2f] text-white p-3 md:px-5 md:py-3.5 rounded-xl mb-6 shadow-sm flex flex-col md:flex-row md:items-center gap-2 md:gap-4 leading-relaxed">
            <span className="font-bold text-[15px] whitespace-nowrap">{labelPrefix} {questionNumber}</span>
            <span className="font-medium text-white/95 text-[15px]">{instructionText}</span>
          </div>

          {/* MỚI: Xác định xem có nên ẩn text của câu hỏi con hay không */}
          {(() => {
            const insLower = instructionText.toLowerCase();
            const compType = question.component_type || "";
            
            // Nếu block parent CÓ ẢNH → child text luôn là hallucination → ẩn đi
            // Ngoại trừ instruction rõ ràng yêu cầu trả lời câu hỏi
            const hasImage = !!question.image_url;
            const isExplicitShow = insLower.includes("answer the question") 
                                 || insLower.includes("answer the following")
                                 || insLower.includes("complete the sentence");
            
            const hideChildQuestionText = hasImage && !isExplicitShow;

            return (
              <>
                {/* Render Children or Grouped Input */}
                {["matching_features", "matching_headings", "matching_sentence_endings"].includes(compType) ? (
                   <MatchingBlock
                     parentQuestion={question}
                     childQuestions={childQuestions}
                     childAnswers={childAnswers}
                     onChildAnswerChange={onChildAnswerChange}
                     disabled={disabled}
                   />
                ) : (["table_completion", "summary_completion", "diagram_label_completion", "sentence_completion"].includes(compType) || hasImage) ? (
                   <FillBlankInput
                     questionId={question.id}
                     questionText={contentText} // Truyền nội dung thật xuống thay vì pass rỗng
                     selectedAnswer={selectedAnswer}
                     onChange={onChange}
                     disabled={disabled}
                     childQuestions={childQuestions}
                     childAnswers={childAnswers}
                     onChildAnswerChange={onChildAnswerChange}
                     imageUrl={question.image_url}
                     hideChildQuestionText={hideChildQuestionText}
                   />
                ) : (
             <div className="space-y-4 pt-4 border-t border-slate-100">
               {question.image_url && (
                 <div className="mb-6 flex justify-center">
                   <img 
                     src={question.image_url} 
                     alt="Hình minh họa"
                     className="w-full max-w-3xl rounded-lg shadow-sm border border-slate-200/60 object-contain"
                   />
                 </div>
               )}
               {childQuestions.map((child) => (
                 <QuestionRenderer
                   key={child.id}
                   question={child}
                   questionNumber={child.displayNumber || child.original_question_number}
                   selectedAnswer={childAnswers?.[String(child.id)]}
                   onChange={(ans) => onChildAnswerChange && onChildAnswerChange(child.id, ans)}
                   disabled={disabled}
                   isEnglish={isEnglish}
                 />
               ))}
             </div>
          )}
          </>
        );
      })()}
        </div>
      ) : (
        renderQuestionComponent()
      )}
    </div>
  );
};
export default QuestionRenderer;
