import React, { useState, useEffect } from "react";
import { useExamStore } from "@/store/examStore";
import { useExamDraft } from "@/hooks/useExamDraft";
import QuestionRenderer from "./QuestionRenderer";
import CountdownTimer from "./CountdownTimer";
import QuestionNavigator from "./QuestionNavigator";
import SubmitConfirmModal from "./SubmitConfirmModal";
import Button from "../ui/Button";
import { ChevronLeft, ChevronRight, Flag, Send } from "lucide-react";
import apiClient from "@/lib/api-client";
import { useRouter } from "next/navigation";

interface ExamPlayerProps {
  exam: {
    id: number;
    title: string;
    duration: number;
    [key: string]: any;
  };
  questions: Array<{ id: string | number; [key: string]: any }>;
}

export const ExamPlayer: React.FC<ExamPlayerProps> = ({ exam, questions }) => {
  const router = useRouter();
  const {
    answers,
    setAnswer,
    flaggedQuestions,
    toggleFlag,
    currentIndex,
    setCurrentIndex,
    initializeStore,
    isSubmitting,
    setIsSubmitting,
  } = useExamStore();

  const { forceSave } = useExamDraft(exam.id);
  const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);

  useEffect(() => {
    initializeStore(exam.duration);
  }, [exam, initializeStore]);

  if (!questions || questions.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-400">Không có câu hỏi nào trong đề thi này.</p>
      </div>
    );
  }

  const currentQuestion = questions[currentIndex];
  const qId = String(currentQuestion.id);

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const handleAnswerChange = (ans: any) => {
    setAnswer(qId, ans);
  };

  const calculateAnsweredCount = () => {
    return Object.keys(answers).filter(
      (key) => answers[key] !== undefined && answers[key] !== null && answers[key] !== ""
    ).length;
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setIsSubmitModalOpen(false);
    try {
      // Force draft save
      await forceSave();

      // Submit exam officially
      const { data } = await apiClient.post("/submissions/", {
        exam_id: exam.id,
        answers,
      });

      // Redirect to submission result view
      router.push(`/result/${data.id}`);
    } catch (e) {
      console.error("Failed to submit exam:", e);
      alert("Đã xảy ra lỗi khi nộp bài. Vui lòng thử lại.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full flex flex-col lg:flex-row gap-6">
      {/* Left pane: Main Player Workspace */}
      <div className="flex-grow flex flex-col justify-between min-h-[500px]">
        {/* Exam Header */}
        <div className="flex items-center justify-between mb-4 bg-slate-900/40 p-4 border border-slate-800 rounded-xl">
          <div>
            <h2 className="text-xl font-bold text-slate-100">{exam.title}</h2>
            <p className="text-xs text-slate-400 mt-1">
              Câu hỏi <span className="font-semibold text-slate-200">{currentIndex + 1}</span> trên{" "}
              <span className="font-semibold text-slate-200">{questions.length}</span>
            </p>
          </div>
          <CountdownTimer onTimeUp={handleSubmit} />
        </div>

        {/* Question Area */}
        <div className="flex-grow mb-6">
          <QuestionRenderer
            question={currentQuestion as any}
            selectedAnswer={answers[qId]}
            onChange={handleAnswerChange}
            disabled={isSubmitting}
          />
        </div>

        {/* Bottom Nav Controller */}
        <div className="flex items-center justify-between bg-slate-900/20 p-4 border border-slate-800/80 rounded-xl">
          <div className="flex items-center gap-3">
            <Button
              variant="secondary"
              size="sm"
              onClick={handlePrev}
              disabled={currentIndex === 0 || isSubmitting}
            >
              <ChevronLeft size={18} className="mr-1" /> Trước
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleNext}
              disabled={currentIndex === questions.length - 1 || isSubmitting}
            >
              Sau <ChevronRight size={18} className="ml-1" />
            </Button>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => toggleFlag(currentIndex)}
              className={flaggedQuestions[currentIndex] ? "text-orange-400 hover:text-orange-300" : "text-slate-400"}
              disabled={isSubmitting}
            >
              <Flag size={18} className="mr-1" />
              {flaggedQuestions[currentIndex] ? "Bỏ cờ" : "Đánh dấu cờ"}
            </Button>
            <Button variant="primary" size="sm" onClick={() => setIsSubmitModalOpen(true)} disabled={isSubmitting}>
              <Send size={16} className="mr-1" /> Nộp bài
            </Button>
          </div>
        </div>
      </div>

      {/* Right pane: Navigator and Status Panel */}
      <div className="w-full lg:w-72 shrink-0">
        <QuestionNavigator questions={questions} />
      </div>

      {/* Submit Confirm Dialog */}
      <SubmitConfirmModal
        isOpen={isSubmitModalOpen}
        onClose={() => setIsSubmitModalOpen(false)}
        onSubmit={handleSubmit}
        totalQuestions={questions.length}
        answeredCount={calculateAnsweredCount()}
        loading={isSubmitting}
      />
    </div>
  );
};
export default ExamPlayer;
