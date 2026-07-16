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
      className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg font-mono font-bold text-lg border transition-all duration-300 ${
        isLowTime
          ? "bg-red-500/10 border-red-500 text-red-400 animate-pulse"
          : "bg-slate-900/80 border-slate-800 text-slate-100"
      }`}
    >
      <Clock size={20} className={isLowTime ? "text-red-400" : "text-slate-400"} />
      <span>{formatTime()}</span>
    </div>
  );
};
export default CountdownTimer;
