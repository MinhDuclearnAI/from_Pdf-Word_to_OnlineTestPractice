import { create } from "zustand";

interface ExamState {
  answers: Record<string, any>;
  flaggedQuestions: Record<number, boolean>;
  currentIndex: number;
  timeRemaining: number;
  isSubmitting: boolean;
  initializeStore: (durationMinutes: number, initialAnswers?: Record<string, any>) => void;
  setAnswer: (questionId: string, answer: any) => void;
  toggleFlag: (questionIndex: number) => void;
  setCurrentIndex: (index: number) => void;
  setTimeRemaining: (time: number | ((prev: number) => number)) => void;
  setIsSubmitting: (isSubmitting: boolean) => void;
  resetStore: () => void;
}

export const useExamStore = create<ExamState>((set) => ({
  answers: {},
  flaggedQuestions: {},
  currentIndex: 0,
  timeRemaining: 0,
  isSubmitting: false,
  initializeStore: (durationMinutes, initialAnswers = {}) =>
    set({
      answers: initialAnswers,
      flaggedQuestions: {},
      currentIndex: 0,
      timeRemaining: durationMinutes * 60,
      isSubmitting: false,
    }),
  setAnswer: (questionId, answer) =>
    set((state) => ({
      answers: { ...state.answers, [questionId]: answer },
    })),
  toggleFlag: (questionIndex) =>
    set((state) => ({
      flaggedQuestions: {
        ...state.flaggedQuestions,
        [questionIndex]: !state.flaggedQuestions[questionIndex],
      },
    })),
  setCurrentIndex: (index) => set({ currentIndex: index }),
  setTimeRemaining: (time) =>
    set((state) => ({
      timeRemaining: typeof time === "function" ? time(state.timeRemaining) : time,
    })),
  setIsSubmitting: (isSubmitting) => set({ isSubmitting }),
  resetStore: () =>
    set({
      answers: {},
      flaggedQuestions: {},
      currentIndex: 0,
      timeRemaining: 0,
      isSubmitting: false,
    }),
}));
