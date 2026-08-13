import React from "react";
import useCountdown from "@/hooks/useCountdown";
import { Clock } from "lucide-react";

interface CountdownTimerProps {
  onTimeUp: () => void;
}

export const CountdownTimer: React.FC<CountdownTimerProps> = ({ onTimeUp }) => {
  const { timeRemaining, formatTime } = useCountdown(onTimeUp);
  const isLowTime = timeRemaining <= 300; // Less than 5 minutes

  return (
    <div
      className={`inline-flex items-center gap-2 px-3 md:px-4 py-1.5 md:py-2 rounded-lg font-mono font-bold text-sm md border transition-all duration-300 ${
        isLowTime
          ? "bg-red-50 border-red-200 text-red-600 animate-pulse"
          : "bg-white border-slate-200 text-slate-700"
      }`}
    >
      <Clock size={20} className={isLowTime ? "text-red-500" : "text-slate-500"} />
      <span>{formatTime()}</span>
    </div>
  );
};
export default CountdownTimer;
