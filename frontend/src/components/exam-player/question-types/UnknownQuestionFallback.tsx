import React from "react";
import { AlertTriangle } from "lucide-react";

interface UnknownQuestionFallbackProps {
  questionType: string;
}

export const UnknownQuestionFallback: React.FC<UnknownQuestionFallbackProps> = ({ questionType }) => {
  return (
    <div className="p-6 bg-yellow-950/30 border border-yellow-800/40 rounded-xl flex flex-col items-center justify-center text-center max-w-md mx-auto">
      <AlertTriangle className="text-yellow-500 mb-3" size={36} />
      <h4 className="font-semibold text-slate-100 mb-1">Loại câu hỏi chưa được hỗ trợ</h4>
      <p className="text-sm text-slate-400">
        Hệ thống không nhận diện được loại component <span className="font-mono text-yellow-400">"{questionType}"</span> để render giao diện.
      </p>
    </div>
  );
};
export default UnknownQuestionFallback;
