import { useEffect, useRef } from "react";
import apiClient from "@/lib/api-client";
import { useExamStore } from "@/store/examStore";

export const useExamDraft = (examId: number | string) => {
  const { answers, setAnswer } = useExamStore();
  const lastSavedAnswersRef = useRef<string>("");

  // Load draft from backend on init
  useEffect(() => {
    const loadDraft = async () => {
      try {
        const { data } = await apiClient.get(`/submissions/${examId}/draft`);
        if (data.answers) {
          Object.entries(data.answers).forEach(([qId, ans]) => {
            setAnswer(qId, ans);
          });
          lastSavedAnswersRef.current = JSON.stringify(data.answers);
        }
      } catch (e) {
        console.error("Failed to load draft:", e);
      }
    };
    if (examId) loadDraft();
  }, [examId, setAnswer]);

  // Debounced autosave
  useEffect(() => {
    if (Object.keys(answers).length === 0) return;

    const currentAnswersStr = JSON.stringify(answers);
    if (currentAnswersStr === lastSavedAnswersRef.current) return;

    const timer = setTimeout(async () => {
      try {
        await apiClient.put(`/submissions/${examId}/autosave`, {
          answers,
        });
        lastSavedAnswersRef.current = currentAnswersStr;
        console.log("Autosaved successfully");
      } catch (e) {
        console.error("Failed to autosave:", e);
      }
    }, 5000); // 5 seconds of inactivity

    return () => clearTimeout(timer);
  }, [answers, examId]);

  const forceSave = async () => {
    try {
      await apiClient.put(`/submissions/${examId}/autosave`, {
        answers,
      });
      lastSavedAnswersRef.current = JSON.stringify(answers);
    } catch (e) {
      console.error("Failed to force save:", e);
    }
  };

  return {
    forceSave,
  };
};
export default useExamDraft;
