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
  questionNumber?: number;
  selectedAnswer?: any;
  onChange: (answer: any) => void;
  disabled?: boolean;
  isStandalonePassage?: boolean; // Nếu true, không tự động bọc ReadingSplitScreen (vì container cha đã bọc)
}

export const QuestionRenderer: React.FC<QuestionRendererProps> = ({
  question,
  questionNumber,
  selectedAnswer,
  onChange,
  disabled,
  isStandalonePassage = false,
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

  // If this question contains a reading passage reference AND is not inside a passage group container
  if (!isStandalonePassage && question.passage_ref && question.passage_ref.trim() !== "") {
    return (
      <ReadingSplitScreen 
        title={question.part_title || "Đoạn văn đọc hiểu / Reading Passage"} 
        passageText={question.passage_ref}
      >
        <div id={`question-card-${question.id}`} className="scroll-mt-6">
          {renderQuestionComponent()}
        </div>
      </ReadingSplitScreen>
    );
  }

  // Card render chuẩn trong danh sách cuộn liên tiếp
  return (
    <div 
      id={`question-card-${question.id}`} 
      className="bg-slate-900/65 border border-slate-800/80 rounded-2xl p-5 md:p-6 shadow-xl transition-all duration-200 hover:border-brand-500/30 scroll-mt-6"
    >
      {questionNumber !== undefined && (
        <div className="flex items-center justify-between mb-3 pb-2.5 border-b border-slate-800/60">
          <span className="text-xs font-bold text-brand-300 uppercase tracking-wider bg-brand-500/15 border border-brand-500/30 px-3 py-0.5 rounded-full shadow-sm">
            CÂU {questionNumber}
          </span>
          {question.part_title && (
            <span className="text-xs text-slate-400 font-medium">{question.part_title}</span>
          )}
        </div>
      )}
      {renderQuestionComponent()}
    </div>
  );
};
export default QuestionRenderer;
