import React, { useState, useEffect, useMemo, useRef } from "react";
import { useExamStore } from "@/store/examStore";
import { useExamDraft } from "@/hooks/useExamDraft";
import QuestionRenderer from "./QuestionRenderer";
import CountdownTimer from "./CountdownTimer";
import SubmitConfirmModal from "./SubmitConfirmModal";
import ReadingSplitScreen from "./question-types/ReadingSplitScreen";
import TextAnnotationToolbar from "./TextAnnotationToolbar";
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
    original_question_number?: number;
    parent_id?: string | number | null;
    [key: string]: any;
  }>;
  examId: string | string[];
}

export const ExamPlayer: React.FC<ExamPlayerProps> = ({ exam, questions: rawQuestions, examId }) => {
  const router = useRouter();

  // Single source of truth for English/IELTS language detection
  const isEnglishExam = ["ielts", "english", "tiếng anh"].some(
    (kw) => (exam?.subject || "").toLowerCase().includes(kw)
  );

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

  const questions = useMemo(() => {
    // Helper to get effective question number for sorting
    const getEffectiveNumber = (q: any) => {
      if (q.original_question_number != null) return q.original_question_number;
      // If it's a parent block, find the minimum question number of its children
      const children = rawQuestions?.filter(c => c.parent_id === q.id) || [];
      if (children.length > 0) {
        const childNums = children.map(c => c.original_question_number).filter(n => n != null);
        if (childNums.length > 0) return Math.min(...childNums);
      }
      return 9999;
    };

    return [...(rawQuestions || [])].sort((a, b) => {
      const aNum = getEffectiveNumber(a);
      const bNum = getEffectiveNumber(b);
      if (aNum === bNum) return String(a.id).localeCompare(String(b.id));
      return aNum - bNum;
    });
  }, [rawQuestions]);

  const { forceSave, loadDraft } = useExamDraft(exam.id);
  const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
  const [activePartIndex, setActivePartIndex] = useState<number>(0);
  const [showGrid, setShowGrid] = useState(false); // Bật tắt danh sách tất cả câu hỏi
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    const init = async () => {
      const data = await loadDraft();
      let initialTime = null;
      if (data && data.remaining_time !== undefined && data.remaining_time !== null) {
        initialTime = data.remaining_time;
      }
      initializeStore(exam.duration, data?.answers || {}, initialTime);
      setIsInitialized(true);
    };
    init();
  }, [exam.id, exam.duration, initializeStore, loadDraft]);

  // Use a ref to store the latest forceSave function to avoid useEffect re-runs
  const forceSaveRef = useRef(forceSave);
  useEffect(() => {
    forceSaveRef.current = forceSave;
  }, [forceSave]);

  useEffect(() => {
    // Chèn 1 state giả vào history để chặn Back
    window.history.pushState(null, "", window.location.href);

    const handlePopState = (e: PopStateEvent) => {
      // Push lại để chặn Back thực sự
      window.history.pushState(null, "", window.location.href);
      
      if (confirm("Bạn có chắc chắn muốn thoát khỏi phòng thi? Bài làm chưa nộp sẽ chỉ được lưu nháp.")) {
        void (async () => {
          await forceSaveRef.current();
          window.location.replace("/dashboard");
        })();
      }
    };

    window.addEventListener("popstate", handlePopState);
    return () => {
      window.removeEventListener("popstate", handlePopState);
    };
  }, []);

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      forceSaveRef.current(); // Thử lưu trước khi tắt tab
      e.preventDefault();
      e.returnValue = "";
    };
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, []);

  const handleExit = async () => {
    if (confirm("Bạn có chắc chắn muốn thoát khỏi phòng thi? Bài làm chưa nộp sẽ chỉ được lưu nháp.")) {
      await forceSave();
      window.location.replace("/dashboard");
    }
  };

  const passageGroups = useMemo(() => {
    if (!questions || questions.length === 0) return [];

    const subject = exam?.subject?.toUpperCase() || "";
    const isIELTS = subject.includes("IELTS");
    
    if (!isIELTS) return [];

    // Tìm đúng 3 passage (có component_type là reading_passage)
    const passageParents = questions.filter(q => q.component_type === "reading_passage");

    // Nếu backend trả về passageParents, ta dựa vào parent_id để tạo đúng số tab đó (thường là 3)
    if (passageParents.length > 0) {
      const groups = passageParents.map((p, idx) => ({
        id: p.id,
        title: p.question_text || `Passage ${idx + 1}`,
        passageText: p.passage_ref || "",
        questions: [] as Array<{ item: any; originalIndex: number }>,
      }));

      // Bước 1: Build map từ question_id -> passage_id gốc (để resolve các câu hỏi con của block)
      const qToPassage = new Map();
      questions.forEach(q => {
        if (q.parent_id && passageParents.some(p => String(p.id) === String(q.parent_id))) {
          qToPassage.set(String(q.id), String(q.parent_id));
        }
      });
      // Lặp lần 2 để xử lý các câu cháu (thuộc block con)
      questions.forEach(q => {
        if (q.parent_id && qToPassage.has(String(q.parent_id))) {
          qToPassage.set(String(q.id), qToPassage.get(String(q.parent_id)));
        }
      });

      // Bước 2: Nhét các câu hỏi (KHÔNG phải reading_passage) vào đúng group
      questions.forEach((q, idx) => {
        if (q.component_type === "reading_passage") return; // Bỏ qua câu hỏi parent

        const resolvedPassageId = qToPassage.get(String(q.id));
        if (resolvedPassageId) {
          const group = groups.find(g => String(g.id) === resolvedPassageId);
          if (group) {
            group.questions.push({ item: q, originalIndex: idx });
          }
        } else {
          // Fallback: nếu câu hỏi bị mồ côi (không có parent_id do data cũ),
          // fallback dựa vào string matching passage_ref
          const pText = q.passage_ref?.trim() || "";
          if (pText) {
            const fallbackGroup = groups.find(g => g.passageText && g.passageText.includes(pText.substring(0, 50)));
            if (fallbackGroup) {
              fallbackGroup.questions.push({ item: q, originalIndex: idx });
              return;
            }
          }
          // Fallback cuối cùng: ném vào group cuối cùng
          if (groups.length > 0) {
            groups[groups.length - 1].questions.push({ item: q, originalIndex: idx });
          }
        }
      });

      return groups;
    }

    // Nếu không có passageParents (dữ liệu cũ không có tree structure),
    // Fallback lại logic cũ nhưng ép cứng gom nhóm tốt hơn:
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
          (extractedTitle && lastGroup.title === extractedTitle)
        ) {
          lastGroup.questions.push({ item: q, originalIndex: idx });
        } else {
          // Chỉ tạo passage mới nếu nội dung passage thực sự khác biệt
          groups.push({
            title: extractedTitle || `Passage ${groups.length + 1}`,
            passageText: cleanPassageText,
            questions: [{ item: q, originalIndex: idx }],
          });
        }
      }
    });

    return groups;
  }, [questions, exam]);

  if (!questions || questions.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-slate-500">Không có câu hỏi nào trong đề thi này.</p>
      </div>
    );
  }

  // Lọc ra các câu hỏi thực sự có thể trả lời (bỏ qua passage và block parent)
  const isParentSet = useMemo(() => {
    const isParent = new Set<string>();
    questions.forEach(q => {
      if (q.parent_id) isParent.add(String(q.parent_id));
    });
    return isParent;
  }, [questions]);

  const isBlockParent = (id: string | number) => {
    return isParentSet.has(String(id)) && questions.find(q => String(q.id) === String(id))?.component_type !== "reading_passage";
  };

  const isChildOfBlock = (id: string | number) => {
    const q = questions.find(x => String(x.id) === String(id));
    return q?.parent_id ? isBlockParent(q.parent_id) : false;
  };

  const actualQuestions = useMemo(() => {
    let displayNum = 1;
    return questions
      .map((q, idx) => ({ ...q, originalIndex: idx }))
      .filter(q => q.component_type !== "reading_passage" && !isBlockParent(q.id))
      .map(q => {
         const num = q.original_question_number || displayNum;
         if (!q.original_question_number) displayNum++;
         return { ...q, displayNumber: num };
      });
  }, [questions, isParentSet]);

  const getQuestionAnswer = (q: any) => {
    let ans = answers[String(q.id)];
    if ((ans === undefined || ans === null || ans === "") && q.parent_id) {
       if (isBlockParent(q.parent_id)) {
          const children = actualQuestions.filter(child => String(child.parent_id) === String(q.parent_id)).sort((a,b) => (a.id > b.id ? 1 : -1));
          const childIdx = children.findIndex(c => String(c.id) === String(q.id));
          if (childIdx !== -1) {
             const parentAns = answers[String(q.parent_id)];
             if (Array.isArray(parentAns)) ans = parentAns[childIdx];
          }
       }
    }
    return ans;
  };

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
    const targetQuestions = groupQuestions 
      ? actualQuestions.filter(aq => groupQuestions.some(gq => gq.item.id === aq.id || aq.parent_id === gq.item.id))
      : actualQuestions;
    return targetQuestions.filter(q => {
      const ans = getQuestionAnswer(q);
      return ans !== undefined && ans !== null && ans !== "";
    }).length;
  };

  const scrollToQuestion = (index: number) => {
    let targetIndex = index;
    const targetQ = questions[index];
    if (targetQ && targetQ.parent_id && isBlockParent(targetQ.parent_id)) {
       const parentIdx = questions.findIndex(p => String(p.id) === String(targetQ.parent_id));
       if (parentIdx !== -1) targetIndex = parentIdx;
    }

    setCurrentIndex(index);
    if (passageGroups.length > 1) {
      const partIdx = passageGroups.findIndex((g) =>
        g.questions.some((qObj) => qObj.originalIndex === index || qObj.originalIndex === targetIndex)
      );
      if (partIdx !== -1 && partIdx !== activePartIndex) {
        setActivePartIndex(partIdx);
      }
    }
    setTimeout(() => {
      const targetQId = String(questions[targetIndex].id);
      const el = document.getElementById(`question-card-${targetQId}`) || document.getElementById(`question-card-${targetIndex}`);
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

      // Transform answers: Unpack block parent arrays into child answers
      const finalAnswers = { ...answers };
      questions.forEach(q => {
        if (isBlockParent(q.id)) {
           const children = actualQuestions.filter(child => String(child.parent_id) === String(q.id)).sort((a,b) => (a.id > b.id ? 1 : -1));
           const parentAns = finalAnswers[String(q.id)];
           if (Array.isArray(parentAns)) {
              children.forEach((child, idx) => {
                 finalAnswers[String(child.id)] = parentAns[idx] || "";
              });
           }
        }
      });

      const { data } = await apiClient.post("/submissions/", {
        exam_id: exam.id,
        answers: finalAnswers,
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
            onClick={handleExit}
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
        <TextAnnotationToolbar />
        {isIELTSReadingFormat && activeGroup ? (
          // IELTS SPLIT SCREEN
          <ReadingSplitScreen
            title={activeGroup.title}
            passageText={activeGroup.passageText}
          >
            {activeGroup.questions.filter(({item}) => !isChildOfBlock(item.id)).map(({ item, originalIndex }) => {
              let qNumDisplay: string | number = originalIndex + 1;
              if (isBlockParent(item.id)) {
                  const children = actualQuestions.filter(child => String(child.parent_id) === String(item.id)).sort((a,b) => (a.id > b.id ? 1 : -1));
                  if (children.length > 0) {
                     qNumDisplay = children.length === 1 ? children[0].displayNumber : `${children[0].displayNumber} - ${children[children.length - 1].displayNumber}`;
                  }
              } else {
                  const aq = actualQuestions.find(aq => String(aq.id) === String(item.id));
                  if (aq) qNumDisplay = aq.displayNumber;
              }

              return (
                <QuestionRenderer
                  key={item.id}
                  question={item}
                  questionNumber={qNumDisplay}
                  selectedAnswer={answers[String(item.id)]}
                  onChange={(ans) => handleAnswerChange(item.id, ans)}
                  disabled={isSubmitting}
                  isStandalonePassage={true}
                  isEnglish={isEnglishExam}
                  childQuestions={isBlockParent(item.id) ? actualQuestions.filter(child => String(child.parent_id) === String(item.id)).sort((a,b) => (a.id > b.id ? 1 : -1)) : undefined}
                  childAnswers={answers}
                  onChildAnswerChange={handleAnswerChange}
                />
              );
            })}
          </ReadingSplitScreen>
        ) : (
          // STANDARD SCREEN (MATH, PHYSICS, ETC)
          <div className="h-full w-full overflow-y-auto p-4 md:p-8">
            <div className="max-w-3xl mx-auto space-y-6 pb-32">
              {questions.map((q, idx) => ({item: q, originalIndex: idx})).filter(({item}) => !isChildOfBlock(item.id) && item.component_type !== "reading_passage").map(({ item, originalIndex }) => {
                let qNumDisplay: string | number = originalIndex + 1;
                if (isBlockParent(item.id)) {
                    const children = actualQuestions.filter(child => String(child.parent_id) === String(item.id)).sort((a,b) => (a.id > b.id ? 1 : -1));
                    if (children.length > 0) {
                       qNumDisplay = children.length === 1 ? children[0].displayNumber : `${children[0].displayNumber} - ${children[children.length - 1].displayNumber}`;
                    }
                } else {
                    const aq = actualQuestions.find(aq => String(aq.id) === String(item.id));
                    if (aq) qNumDisplay = aq.displayNumber;
                }

                return (
                  <QuestionRenderer
                    key={item.id}
                    question={item}
                    questionNumber={qNumDisplay}
                    selectedAnswer={answers[String(item.id)]}
                    onChange={(ans) => handleAnswerChange(item.id, ans)}
                    disabled={isSubmitting}
                    isEnglish={isEnglishExam}
                    childQuestions={isBlockParent(item.id) ? actualQuestions.filter(child => String(child.parent_id) === String(item.id)).sort((a,b) => (a.id > b.id ? 1 : -1)) : undefined}
                    childAnswers={answers}
                    onChildAnswerChange={handleAnswerChange}
                  />
                );
              })}
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
                 {actualQuestions.map((q, qIndex) => {
                   const isAns = answers[String(q.id)] !== undefined && answers[String(q.id)] !== null && answers[String(q.id)] !== "";
                   const isFlag = flaggedQuestions[q.originalIndex];
                   return (
                     <button
                        key={q.id}
                        onClick={() => {
                          setShowGrid(false);
                          scrollToQuestion(q.originalIndex);
                        }}
                        className={`relative flex items-center justify-center h-12 w-full rounded-xl text-sm font-bold transition-all border ${
                          isAns ? "bg-brand-50 border-brand-500/50 text-brand-700 shadow-sm" : "bg-white border-slate-200 text-slate-500 hover"
                        }`}
                     >
                        {qIndex + 1}
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
          {(isIELTSReadingFormat && activeGroup ? actualQuestions.filter(aq => activeGroup.questions.some(gq => gq.item.id === aq.id)) : actualQuestions).map((q, qIndex) => {
            const qId = String(q.id);
            const isAns = answers[qId] !== undefined && answers[qId] !== null && answers[qId] !== "";
            // Trong IELTS Navigator, ta đánh dấu current dựa trên việc câu hỏi đó có thuộc block đang xem hay không
            // Nhưng hiện tại UI scroll đến item block parent, nên currentIndex có thể là index của block parent.
            // Nên so sánh currentIndex với q.originalIndex hoặc parent của nó.
            const isCurrent = currentIndex === q.originalIndex || (q.parent_id && questions[currentIndex]?.id === q.parent_id);
            
            return (
              <button
                key={qId}
                onClick={() => scrollToQuestion(q.originalIndex)}
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
                {q.displayNumber}
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
              const total = actualQuestions.filter(aq => group.questions.some(gq => gq.item.id === aq.id || aq.parent_id === gq.item.id)).length;
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
               {isEnglishExam ? "Question" : "Câu"} {
                 (() => {
                   const groupActuals = actualQuestions.filter(aq => activeGroup.questions.some(gq => gq.item.id === aq.id || aq.parent_id === gq.item.id));
                   if (groupActuals.length === 0) return "-";
                   return `${groupActuals[0].displayNumber} - ${groupActuals[groupActuals.length - 1].displayNumber}`;
                 })()
               }
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
