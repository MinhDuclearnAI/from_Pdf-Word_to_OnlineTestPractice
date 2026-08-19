import { useEffect, useRef, useCallback } from "react";
import apiClient from "@/lib/api-client";
import { useExamStore } from "@/store/examStore";

export const useExamDraft = (examId: number | string) => {
  const { answers, setAnswer, timeRemaining } = useExamStore();
  const lastSavedAnswersRef = useRef<string>("");

  // Không tự động fetch draft trong useEffect ở đây nữa.
  // Component cha (ExamPlayer) sẽ chủ động gọi loadDraft() để đồng bộ timeRemaining.

  // Debounced autosave
  useEffect(() => {
    if (Object.keys(answers).length === 0) return;

    const currentAnswersStr = JSON.stringify(answers);
    if (currentAnswersStr === lastSavedAnswersRef.current) return;

    const timer = setTimeout(async () => {
      try {
        await apiClient.put(`/submissions/${examId}/autosave`, {
          answers,
          remaining_time: useExamStore.getState().timeRemaining,
        });
        lastSavedAnswersRef.current = currentAnswersStr;
        console.log("Autosaved successfully");
      } catch (e) {
        console.error("Failed to autosave:", e);
      }
    }, 5000); // 5 seconds of inactivity

    return () => clearTimeout(timer);
  }, [answers, examId]);

  const forceSave = useCallback(async () => {
    try {
      await apiClient.put(`/submissions/${examId}/autosave`, {
        answers: useExamStore.getState().answers,
        remaining_time: useExamStore.getState().timeRemaining,
      });
      lastSavedAnswersRef.current = JSON.stringify(useExamStore.getState().answers);
    } catch (e) {
      console.error("Failed to force save:", e);
    }
  }, [examId]);

  const loadDraft = useCallback(async () => {
    if (!examId) return null;
    try {
      const { data } = await apiClient.get(`/submissions/${examId}/draft`);
      if (data.answers) {
        Object.entries(data.answers).forEach(([qId, ans]) => {
          setAnswer(qId, ans);
        });
        lastSavedAnswersRef.current = JSON.stringify(data.answers);
      }
      return data;
    } catch (e) {
      console.error("Failed to load draft:", e);
      return null;
    }
  }, [examId, setAnswer]);

  return {
    forceSave,
    loadDraft,
  };
};
export default useExamDraft;
