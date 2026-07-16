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
    component_type: string;
    question_text: string;
    options?: string[];
    passage_ref?: string;
    answer_placeholder?: string;
  };
  selectedAnswer?: any;
  onChange: (answer: any) => void;
  disabled?: boolean;
}

export const QuestionRenderer: React.FC<QuestionRendererProps> = ({
  question,
  selectedAnswer,
  onChange,
  disabled,
}) => {
  const renderQuestionComponent = () => {
    switch (question.component_type) {
      case "multiple_choice":
        return (
          <MCQStandard
            questionId={question.id}
            questionText={question.question_text}
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
            questionText={question.question_text}
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
            questionText={question.question_text}
            selectedAnswer={selectedAnswer}
            onChange={onChange}
            placeholder={question.answer_placeholder}
            disabled={disabled}
          />
        );
      case "fill_in_the_blank":
      case "fill_blank":
        return (
          <FillBlankInput
            questionId={question.id}
            questionText={question.question_text}
            selectedAnswer={selectedAnswer}
            onChange={onChange}
            disabled={disabled}
          />
        );
      default:
        return <UnknownQuestionFallback questionType={question.component_type} />;
    }
  };

  // If this question contains a reading passage reference, wrap it in a Split Screen
  if (question.passage_ref && question.passage_ref.trim() !== "") {
    return (
      <ReadingSplitScreen passageText={question.passage_ref}>
        {renderQuestionComponent()}
      </ReadingSplitScreen>
    );
  }

  // Otherwise, render full screen in a nice container card
  return (
    <div className="bg-slate-900/30 border border-slate-800 rounded-xl p-6 md:p-8">
      {renderQuestionComponent()}
    </div>
  );
};
export default QuestionRenderer;
