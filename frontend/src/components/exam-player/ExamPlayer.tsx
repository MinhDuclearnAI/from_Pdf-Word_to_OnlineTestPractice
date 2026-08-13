import React, { useState, useEffect, useMemo } from "react";
import { useExamStore } from "@/store/examStore";
import { useExamDraft } from "@/hooks/useExamDraft";
import QuestionRenderer from "./QuestionRenderer";
import CountdownTimer from "./CountdownTimer";
import SubmitConfirmModal from "./SubmitConfirmModal";
import ReadingSplitScreen from "./question-types/ReadingSplitScreen";
import Button from "../ui/Button";
import { ChevronLeft, ChevronRight, Flag, LayoutGrid, X, FileText } from "lucide-react";
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
  examId: string | string[];
}

export const ExamPlayer: React.FC<ExamPlayerProps> = ({ exam, questions, examId }) => {
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
  const [activePartIndex, setActivePartIndex] = useState<number>(0);
  const [showGrid, setShowGrid] = useState(false); // Bật tắt danh sách tất cả câu hỏi

  useEffect(() => {
    initializeStore(exam.duration);
  }, [exam, initializeStore]);

  const passageGroups = useMemo(() => {
    if (!questions || questions.length === 0) return [];

    // Chỉ kích hoạt chế độ Split Screen nếu có passage_ref thực sự dài (>= 40 ký tự) 
    // hoặc môn học là IELTS và có chia phần. Tránh việc AI nhận nhầm tiêu đề thành passage.
    const isIELTS = exam?.subject?.toUpperCase() === "IELTS";
    const hasValidPassage = questions.some((q) => {
      const pText = q.passage_ref?.trim() || "";
      const isJustTitle = pText.startsWith("[") && pText.endsWith("]") && pText.length < 40;
      return pText.length > 40 && !isJustTitle;
    });

    // Nếu không phải IELTS và không có bài đọc nào đủ dài, thì hiển thị chế độ 1 cột (Standard)
    if (!hasValidPassage && !isIELTS) return [];

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
        extractedTitle = `Passage ${groups.length + 1}`;
      }

      if (groups.length === 0) {
        groups.push({
          title: extractedTitle || "Questions",
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
            title: extractedTitle || `Passage ${groups.length + 1}`,
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
      <div className="h-full flex items-center justify-center">
        <p className="text-slate-500">Không có câu hỏi nào trong đề thi này.</p>
      </div>
    );
  }

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      scrollToQuestion(currentIndex + 1);
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      scrollToQuestion(currentIndex - 1);
    }
  };

  const handleAnswerChange = (questionId: string | number, ans: any) => {
    setAnswer(String(questionId), ans);
  };

  const calculateAnsweredCount = (groupQuestions?: Array<{item: any}>) => {
    const targetQuestions = groupQuestions ? groupQuestions.map(g => g.item) : questions;
    return targetQuestions.filter(q => {
      const ans = answers[String(q.id)];
      return ans !== undefined && ans !== null && ans !== "";
    }).length;
  };

  const scrollToQuestion = (index: number) => {
    setCurrentIndex(index);
    if (passageGroups.length > 1) {
      const partIdx = passageGroups.findIndex((g) =>
        g.questions.some((qObj) => qObj.originalIndex === index)
      );
      if (partIdx !== -1 && partIdx !== activePartIndex) {
        setActivePartIndex(partIdx);
      }
    }
    setTimeout(() => {
      const targetQId = String(questions[index].id);
      const el = document.getElementById(`question-card-${targetQId}`) || document.getElementById(`question-card-${index}`);
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
  const activeGroup = isIELTSReadingFormat ? passageGroups[activePartIndex] : null;

  return (
    <div className="flex flex-col h-full w-full bg-slate-100 font-sans relative">
      {/* 1. HEADER COPIED FROM DOL IELTS (CLEAN) */}
      <header className="flex-shrink-0 h-16 px-4 md:px-6 bg-white border-b border-slate-200 flex items-center justify-between z-30 shadow-sm">
        <div className="flex items-center gap-4 md:gap-6">
          <button 
            onClick={() => {
              if (confirm("Bạn có chắc chắn muốn thoát khỏi phòng thi? Bài làm chưa nộp sẽ chỉ được lưu nháp.")) {
                router.push("/dashboard");
              }
            }}
            className="p-2 rounded-xl border border-slate-200 text-slate-500 hover transition-colors"
            title="Thoát"
          >
            <X size={20} />
          </button>
          
          <div className="flex items-center gap-1 md:gap-2">
            <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-white font-bold">
              AI
            </div>
            <div className="font-black text-xl tracking-tight hidden sm:block text-slate-800">
              Exam<span className="text-brand-600">Platform</span>
            </div>
          </div>
          
          <div className="border-l border-slate-200 pl-4 md:pl-6">
            <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider mb-0.5">
              Làm bài
            </p>
            <h1 className="text-sm md font-bold text-slate-800 truncate max-w-[200px] sm:max-w-md lg:max-w-xl">
              {exam.title}
            </h1>
          </div>
        </div>

        <div className="flex items-center">
          <CountdownTimer onTimeUp={handleSubmit} />
        </div>
      </header>

      {/* 2. MAIN WORKSPACE */}
      <main className="flex-1 overflow-hidden relative">
        {isIELTSReadingFormat && activeGroup ? (
          // IELTS SPLIT SCREEN
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
        ) : (
          // STANDARD SCREEN (MATH, PHYSICS, ETC)
          <div className="h-full w-full overflow-y-auto p-4 md:p-8">
            <div className="max-w-3xl mx-auto space-y-6 pb-32">
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
          </div>
        )}

        {/* Màn che mờ và Grid Modal (Danh sách tất cả câu hỏi) */}
        {showGrid && (
          <div className="absolute inset-0 z-40 bg-white/95 backdrop-blur-sm overflow-y-auto p-8 flex flex-col items-center">
             <div className="w-full max-w-4xl">
               <div className="flex items-center justify-between mb-8 border-b border-slate-200 pb-4">
                 <h2 className="text-2xl font-bold text-slate-800">Tổng quan bài làm</h2>
                 <button onClick={() => setShowGrid(false)} className="p-2 rounded-full hover"><X size={24}/></button>
               </div>
               
               <div className="grid grid-cols-5 sm:grid-cols-8 md:grid-cols-10 lg:grid-cols-12 gap-3">
                 {questions.map((q, idx) => {
                   const isAns = answers[String(q.id)] !== undefined && answers[String(q.id)] !== null && answers[String(q.id)] !== "";
                   const isFlag = flaggedQuestions[idx];
                   return (
                     <button
                        key={q.id}
                        onClick={() => {
                          setShowGrid(false);
                          scrollToQuestion(idx);
                        }}
                        className={`relative flex items-center justify-center h-12 w-full rounded-xl text-sm font-bold transition-all border ${
                          isAns ? "bg-brand-50 border-brand-500/50 text-brand-700 shadow-sm" : "bg-white border-slate-200 text-slate-500 hover"
                        }`}
                     >
                        {idx + 1}
                        {isFlag && <span className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-orange-500 shadow-sm border-2 border-white" />}
                     </button>
                   )
                 })}
               </div>
             </div>
          </div>
        )}
      </main>

      {/* 3. HORIZONTAL NAVIGATOR FOR ALL EXAMS */}
      {!showGrid && (
        <div className="w-full bg-slate-50 border-t border-slate-200 px-4 py-2 flex items-center justify-center gap-1.5 sm:gap-2 overflow-x-auto shadow-inner z-20">
          {(isIELTSReadingFormat && activeGroup ? activeGroup.questions : questions.map((item, idx) => ({ item, originalIndex: idx }))).map(({ item, originalIndex }) => {
            const qId = String(item.id);
            const isAns = answers[qId] !== undefined && answers[qId] !== null && answers[qId] !== "";
            const isCurrent = currentIndex === originalIndex;
            return (
              <button
                key={qId}
                onClick={() => scrollToQuestion(originalIndex)}
                className={`flex items-center justify-center min-w-[36px] h-9 rounded-lg text-sm transition-all border flex-shrink-0 ${
                  isCurrent && isAns
                    ? "bg-brand-700 text-white border-brand-700 font-bold shadow-md transform scale-110 z-10"
                    : isCurrent
                    ? "bg-brand-500 text-white border-brand-500 font-bold shadow-md transform scale-110 z-10"
                    : isAns
                    ? "bg-brand-50 border-brand-200 text-brand-700 font-bold hover:bg-brand-100"
                    : "bg-white border-slate-200 text-slate-500 font-medium hover:bg-slate-100"
                }`}
              >
                {originalIndex + 1}
              </button>
            );
          })}
        </div>
      )}

      {/* 4. FOOTER (Fixed Bottom) */}
      <footer className="flex-shrink-0 h-16 w-full bg-white border-t border-slate-200 flex items-center justify-between px-4 md:px-6 z-30 shadow-[0_-4px_10px_rgba(0,0,0,0.05)][0_-4px_10px_rgba(0,0,0,0.2)]">
        
        {/* Left: Grid overview toggle */}
        <div className="flex items-center">
          <button 
            onClick={() => setShowGrid(!showGrid)}
            className="flex items-center gap-2 p-2 rounded-xl text-slate-500 hover border border-transparent hover transition-all font-medium text-sm"
          >
            <LayoutGrid size={20} />
            <span className="hidden sm:inline">Tổng quan</span>
          </button>
        </div>

        {/* Center: Passage Tabs (Only for IELTS) */}
        {isIELTSReadingFormat && (
          <div className="flex items-center gap-1 sm:gap-2">
            {passageGroups.map((group, pIdx) => {
              const isActive = activePartIndex === pIdx;
              const answered = calculateAnsweredCount(group.questions);
              const total = group.questions.length;
              return (
                <button
                  key={pIdx}
                  onClick={() => setActivePartIndex(pIdx)}
                  className={`flex flex-col sm:flex-row sm:items-center gap-0 sm:gap-2 px-3 py-1.5 sm:px-4 sm:py-2 rounded-xl text-sm font-bold transition-all border ${
                    isActive
                      ? "bg-brand-50 border-brand-500/30 text-brand-700 shadow-sm"
                      : "bg-transparent border-transparent text-slate-500 hover"
                  }`}
                >
                  <span className="truncate max-w-[80px] sm:max-w-[120px]">{group.title}</span>
                  <span className={`text-[10px] sm font-medium px-1.5 py-0.5 rounded-full ${isActive ? 'bg-brand-100' : 'bg-slate-100'} text-slate-600`}>
                    {answered}/{total}
                  </span>
                </button>
              )
            })}
          </div>
        )}

        {/* Right: Navigation & Submit */}
        <div className="flex items-center gap-2 md:gap-3">
           {isIELTSReadingFormat && activeGroup ? (
             <div className="hidden sm:flex items-center text-sm font-semibold text-slate-500 mr-2">
               Câu {activeGroup.questions[0].originalIndex + 1} - {activeGroup.questions[activeGroup.questions.length - 1].originalIndex + 1}
             </div>
           ) : null}
           
           <button
             onClick={handlePrev}
             disabled={currentIndex === 0}
             className="w-10 h-10 flex items-center justify-center rounded-xl border border-slate-200 text-slate-600 hover disabled:opacity-50 disabled:cursor-not-allowed transition-all"
           >
             <ChevronLeft size={20} />
           </button>
           <button
             onClick={handleNext}
             disabled={currentIndex === questions.length - 1}
             className="w-10 h-10 flex items-center justify-center rounded-xl border border-slate-200 text-slate-600 hover disabled:opacity-50 disabled:cursor-not-allowed transition-all"
           >
             <ChevronRight size={20} />
           </button>

           <div className="w-px h-8 bg-slate-200 mx-1 md:mx-2"></div>

           <Button variant="primary" onClick={() => setIsSubmitModalOpen(true)} disabled={isSubmitting} className="font-bold shadow-md h-10 px-4 md:px-6">
             Nộp bài
           </Button>
        </div>
      </footer>

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
