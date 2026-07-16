import { useEffect } from "react";
import { useExamStore } from "@/store/examStore";

export const useCountdown = (onTimeUp: () => void) => {
  const { timeRemaining, setTimeRemaining } = useExamStore();

  useEffect(() => {
    if (timeRemaining <= 0) return;

    const timer = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          setTimeout(onTimeUp, 100);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [timeRemaining, onTimeUp, setTimeRemaining]);

  const formatTime = () => {
    const minutes = Math.floor(timeRemaining / 60);
    const seconds = timeRemaining % 60;
    return `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
  };

  return {
    timeRemaining,
    formatTime,
  };
};
export default useCountdown;
