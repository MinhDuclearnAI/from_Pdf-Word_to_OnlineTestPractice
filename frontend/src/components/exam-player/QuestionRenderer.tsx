import React from "react";
import MCQStandard from "./question-types/MCQStandard";
import LatexFormulaQuestion from "./question-types/LatexFormulaQuestion";
import EssayInput from "./question-types/EssayInput";
import FillBlankInput from "./question-types/FillBlankInput";
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
  childQuestions,
  childAnswers,
  onChildAnswerChange,
}) => {
  const renderQuestionComponent = () => {
    const qText = question.question_text || "";
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
          />
        );
      default:
        return <UnknownQuestionFallback questionType={question.component_type || "unknown"} />;
    }
  };

  // Đối với các môn thường, nếu có passage_ref bị thừa (ví dụ "[Multiple Choice]"), ta sẽ bỏ qua không in ra Split Screen nữa.
  // Các passage_ref hợp lệ và dài đã được ExamPlayer gom nhóm và tự bọc SplitScreen.
  // Vì vậy QuestionRenderer chỉ tập trung render duy nhất câu hỏi.


  // Card render chuẩn trong danh sách cuộn liên tiếp
  return (
    <div 
      id={`question-card-${question.id}`} 
      className="bg-white border border-slate-200/80 rounded-2xl p-5 md:p-6 shadow-sm transition-all duration-200 scroll-mt-6"
    >
      {questionNumber !== undefined && (
        <div className="flex items-center justify-between mb-3 pb-2.5 border-b border-slate-200/60">
          <span className="text-xs font-bold text-brand-300 uppercase tracking-wider bg-brand-500/15 border border-brand-500/30 px-3 py-0.5 rounded-full shadow-sm">
            CÂU {questionNumber}
          </span>
          {question.part_title && (
            <span className="text-xs text-slate-500 font-medium">{question.part_title}</span>
          )}
        </div>
      )}
      
      {/* Hiển thị Hình ảnh / Biểu đồ (nếu có) */}
      {question.image_url && (
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
          {/* Render Parent Instruction/Content */}
          {question.component_type !== "table_completion" && question.component_type !== "summary_completion" && question.component_type !== "diagram_label_completion" && question.component_type !== "sentence_completion" && (
             <div className="text-base font-medium text-slate-800 mb-4 whitespace-pre-wrap leading-relaxed">
               {question.question_text}
             </div>
          )}

          {/* Render Children or Grouped Input */}
          {(question.component_type === "table_completion" || question.component_type === "summary_completion" || question.component_type === "diagram_label_completion" || question.component_type === "sentence_completion") ? (
             <FillBlankInput
               questionId={question.id}
               questionText={question.question_text || ""}
               selectedAnswer={selectedAnswer}
               onChange={onChange}
               disabled={disabled}
               childQuestions={childQuestions}
               childAnswers={childAnswers}
               onChildAnswerChange={onChildAnswerChange}
             />
          ) : (
             <div className="space-y-4 pt-4 border-t border-slate-100">
               {childQuestions.map((child) => (
                 <QuestionRenderer
                   key={child.id}
                   question={child}
                   questionNumber={child.displayNumber || child.original_question_number}
                   selectedAnswer={childAnswers?.[String(child.id)]}
                   onChange={(ans) => onChildAnswerChange && onChildAnswerChange(child.id, ans)}
                   disabled={disabled}
                 />
               ))}
             </div>
          )}
        </div>
      ) : (
        renderQuestionComponent()
      )}
    </div>
  );
};
export default QuestionRenderer;
