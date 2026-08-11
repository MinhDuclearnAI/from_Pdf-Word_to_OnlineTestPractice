import React, { useState, useEffect, useMemo } from "react";
import { useExamStore } from "@/store/examStore";
import { useExamDraft } from "@/hooks/useExamDraft";
import QuestionRenderer from "./QuestionRenderer";
import CountdownTimer from "./CountdownTimer";
import QuestionNavigator from "./QuestionNavigator";
import SubmitConfirmModal from "./SubmitConfirmModal";
import ReadingSplitScreen from "./question-types/ReadingSplitScreen";
import Button from "../ui/Button";
import { ChevronLeft, ChevronRight, Flag, Send, LayoutList, BookOpen, Layers } from "lucide-react";
import apiClient from "@/lib/api-client";
import { useRouter } from "next/navigation";

interface ExamPlayerProps {
  exam: {
    id: number;
    title: string;
    duration: number;
    [key: string]: any;
  };
  questions: Array<{
    id: string | number;
    component_type?: string;
    question_text?: string;
    options?: string[];
    passage_ref?: string;
    part_title?: string;
    answer_placeholder?: string;
    [key: string]: any;
  }>;
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
  const [viewMode, setViewMode] = useState<"continuous" | "single">("continuous");
  const [activePartIndex, setActivePartIndex] = useState<number>(0);

  useEffect(() => {
    initializeStore(exam.duration);
  }, [exam, initializeStore]);

  // Phân tích và nhóm câu hỏi theo Phần / Bài đọc (Passage Groups) nếu có
  const passageGroups = useMemo(() => {
    if (!questions || questions.length === 0) return [];

    const hasAnyPassage = questions.some(
      (q) => q.passage_ref && q.passage_ref.trim().length > 0
    );

    if (!hasAnyPassage) return [];

    // Nhóm các câu hỏi có chung passage_ref hoặc part_title
    const groups: Array<{
      title: string;
      passageText: string;
      questions: Array<{ item: any; originalIndex: number }>;
    }> = [];

    questions.forEach((q, idx) => {
      const pText = q.passage_ref?.trim() || "";
      let extractedTitle = q.part_title?.trim() || "";
      let cleanPassageText = pText;

      const titleMatch = pText.match(/^\[(.*?)\](?:\n\n|\n)?([\s\S]*)$/);
      if (titleMatch) {
        extractedTitle = titleMatch[1].trim();
        cleanPassageText = titleMatch[2].trim() || titleMatch[1].trim();
      }

      if (!extractedTitle && cleanPassageText) {
        extractedTitle = `Bài đọc ${groups.length + 1}`;
      }

      if (groups.length === 0) {
        groups.push({
          title: extractedTitle || "Câu hỏi",
          passageText: cleanPassageText,
          questions: [{ item: q, originalIndex: idx }],
        });
      } else {
        const lastGroup = groups[groups.length - 1];
        if (
          (cleanPassageText && lastGroup.passageText === cleanPassageText) ||
          (!cleanPassageText && lastGroup.passageText && lastGroup.questions.length < 15) ||
          (extractedTitle && lastGroup.title === extractedTitle)
        ) {
          lastGroup.questions.push({ item: q, originalIndex: idx });
        } else {
          groups.push({
            title: extractedTitle || `Bài đọc ${groups.length + 1}`,
            passageText: cleanPassageText,
            questions: [{ item: q, originalIndex: idx }],
          });
        }
      }
    });

    return groups;
  }, [questions]);

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
      const nextIdx = currentIndex + 1;
      setCurrentIndex(nextIdx);
      scrollToQuestion(nextIdx, String(questions[nextIdx].id));
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      const prevIdx = currentIndex - 1;
      setCurrentIndex(prevIdx);
      scrollToQuestion(prevIdx, String(questions[prevIdx].id));
    }
  };

  const handleAnswerChange = (questionId: string | number, ans: any) => {
    setAnswer(String(questionId), ans);
  };

  const calculateAnsweredCount = () => {
    return Object.keys(answers).filter(
      (key) => answers[key] !== undefined && answers[key] !== null && answers[key] !== ""
    ).length;
  };

  const scrollToQuestion = (index: number, targetQId: string) => {
    setCurrentIndex(index);
    // Nếu đang ở bài đọc IELTS theo Part, tự động chuyển Tab sang Part chứa câu hỏi đó
    if (passageGroups.length > 1) {
      const partIdx = passageGroups.findIndex((g) =>
        g.questions.some((qObj) => qObj.originalIndex === index)
      );
      if (partIdx !== -1 && partIdx !== activePartIndex) {
        setActivePartIndex(partIdx);
      }
    }

    setTimeout(() => {
      const el =
        document.getElementById(`question-card-${targetQId}`) ||
        document.getElementById(`question-card-${index}`);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }, 50);
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setIsSubmitModalOpen(false);
    try {
      await forceSave();
      const { data } = await apiClient.post("/submissions/", {
        exam_id: exam.id,
        answers,
      });
      router.push(`/result/${data.id}`);
    } catch (e) {
      console.error("Failed to submit exam:", e);
      alert("Đã xảy ra lỗi khi nộp bài. Vui lòng thử lại.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const isIELTSReadingFormat = passageGroups.length > 0;
  const isSingleQuestionMode = exam.display_mode === "single";

  return (
    <div className="w-full flex flex-col lg:flex-row gap-5 items-start">
      {/* Main Player Workspace */}
      <div className="flex-grow w-full flex flex-col justify-between min-h-[650px]">
        {/* Exam Header */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4 bg-slate-900/70 p-4 md:p-5 border border-slate-800/80 rounded-2xl shadow-xl backdrop-blur">
          <div>
            <h2 className="text-xl md:text-2xl font-bold text-slate-100">{exam.title}</h2>
            <div className="flex items-center gap-3 mt-1.5 text-xs text-slate-400">
              <span>
                Tổng số: <strong className="text-slate-200">{questions.length} câu</strong>
              </span>
              <span>•</span>
              <span>
                Đã làm: <strong className="text-brand-400">{calculateAnsweredCount()}</strong>/{questions.length}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <CountdownTimer onTimeUp={handleSubmit} />
          </div>
        </div>

        {/* IELTS / Multi-Part Passage Tab Bar (Nếu đề có chia Part/Passage) */}
        {isIELTSReadingFormat && passageGroups.length > 1 && (
          <div className="flex items-center gap-2 mb-4 overflow-x-auto pb-1">
            {passageGroups.map((group, pIdx) => {
              const startQ = group.questions[0].originalIndex + 1;
              const endQ = group.questions[group.questions.length - 1].originalIndex + 1;
              const isActive = activePartIndex === pIdx;

              return (
                <button
                  key={pIdx}
                  type="button"
                  onClick={() => setActivePartIndex(pIdx)}
                  className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all border shrink-0 ${
                    isActive
                      ? "bg-brand-500/20 border-brand-500 text-brand-300 ring-2 ring-brand-500/25 shadow-md"
                      : "bg-slate-900/40 border-slate-800 text-slate-400 hover:bg-slate-850 hover:text-slate-200"
                  }`}
                >
                  <BookOpen size={16} />
                  <span>{group.title}</span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800/80 text-slate-400 border border-slate-700/60">
                    Câu {startQ} - {endQ}
                  </span>
                </button>
              );
            })}
          </div>
        )}

        {/* Question Area */}
        <div className="flex-grow mb-6">
          {/* Chế độ 1: IELTS / Đọc hiểu chia 2 cột */}
          {isIELTSReadingFormat && !isSingleQuestionMode ? (
            (() => {
              const activeGroup = passageGroups[activePartIndex] || passageGroups[0];
              return (
                <ReadingSplitScreen
                  title={activeGroup.title}
                  passageText={activeGroup.passageText}
                >
                  {activeGroup.questions.map(({ item, originalIndex }) => (
                    <QuestionRenderer
                      key={item.id}
                      question={item}
                      questionNumber={originalIndex + 1}
                      selectedAnswer={answers[String(item.id)]}
                      onChange={(ans) => handleAnswerChange(item.id, ans)}
                      disabled={isSubmitting}
                      isStandalonePassage={true}
                    />
                  ))}
                </ReadingSplitScreen>
              );
            })()
          ) : !isSingleQuestionMode ? (
            /* Chế độ 2: Đề tiêu chuẩn (Toán, Lý, Hóa...) cuộn liền mạch từ trên xuống */
            <div className="space-y-5">
              {questions.map((q, idx) => (
                <QuestionRenderer
                  key={q.id}
                  question={q}
                  questionNumber={idx + 1}
                  selectedAnswer={answers[String(q.id)]}
                  onChange={(ans) => handleAnswerChange(q.id, ans)}
                  disabled={isSubmitting}
                />
              ))}
            </div>
          ) : (
            /* Chế độ 3: Xem từng câu một (Nếu Giáo viên cấu hình) */
            <QuestionRenderer
              question={currentQuestion as any}
              questionNumber={currentIndex + 1}
              selectedAnswer={answers[qId]}
              onChange={(ans) => handleAnswerChange(qId, ans)}
              disabled={isSubmitting}
            />
          )}
        </div>

        {/* Bottom Nav Controller */}
        <div className="sticky bottom-4 z-20 flex items-center justify-between bg-slate-900/90 backdrop-blur-md p-3.5 md:p-4 border border-slate-800/80 rounded-2xl shadow-2xl">
          <div className="flex items-center gap-2.5">
            <Button
              variant="secondary"
              size="sm"
              onClick={handlePrev}
              disabled={currentIndex === 0 || isSubmitting}
            >
              <ChevronLeft size={18} className="mr-1" /> Câu trước
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleNext}
              disabled={currentIndex === questions.length - 1 || isSubmitting}
            >
              Câu sau <ChevronRight size={18} className="ml-1" />
            </Button>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => toggleFlag(currentIndex)}
              className={flaggedQuestions[currentIndex] ? "text-orange-400 hover:text-orange-300" : "text-slate-400"}
              disabled={isSubmitting}
              title="Đánh dấu cờ (Hoặc chuột phải ở danh sách câu hỏi)"
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

      {/* Right pane: Navigator and Status Panel (Slim & Sticky) */}
      <div className="w-full lg:w-60 shrink-0 sticky top-16">
        <QuestionNavigator questions={questions} onSelectQuestion={scrollToQuestion} />
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
