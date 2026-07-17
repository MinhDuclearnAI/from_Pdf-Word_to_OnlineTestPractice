import React, { useEffect, useState } from "react";
import { connectToJobWS } from "@/lib/websocket-client";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";

interface AIProcessingStatusProps {
  jobId: number | string;
  onComplete: (examId: number) => void;
  onFailed: (error: string) => void;
}

export const AIProcessingStatus: React.FC<AIProcessingStatusProps> = ({ jobId, onComplete, onFailed }) => {
  const [status, setStatus] = useState<"pending" | "processing" | "done" | "failed">("pending");
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState("Đang gửi tệp tới hàng đợi xử lý...");

  const isDoneRef = React.useRef(false);

  useEffect(() => {
    const disconnect = connectToJobWS(
      jobId,
      (data) => {
        setStatus(data.status as any);
        setProgress(data.progress);
        setMessage(data.message);

        if (data.status === "done" && data.result?.exam_id) {
          isDoneRef.current = true;
          // Redirect immediately to avoid race conditions with WS disconnect
          onComplete(data.result.exam_id);
        } else if (data.status === "failed") {
          isDoneRef.current = true;
          onFailed(data.message);
        }
      },
      (err) => {
        if (!isDoneRef.current) {
          console.error("WS error:", err);
          setStatus("failed");
          setMessage("Lỗi kết nối máy chủ để cập nhật tiến trình.");
          onFailed("Lỗi kết nối máy chủ.");
        }
      }
    );

    return () => {
      disconnect();
    };
  }, [jobId, onComplete, onFailed]);

  return (
    <div className="w-full p-6 glass-panel rounded-xl border border-slate-700/50">
      <div className="flex items-center gap-4 mb-4">
        {status === "failed" ? (
          <XCircle className="text-red-500 shrink-0" size={32} />
        ) : status === "done" ? (
          <CheckCircle2 className="text-green-500 shrink-0 animate-bounce" size={32} />
        ) : (
          <Loader2 className="text-brand-400 animate-spin shrink-0" size={32} />
        )}

        <div className="flex-1">
          <h4 className="font-semibold text-slate-100 text-base">
            {status === "failed"
              ? "Xử lý tệp thất bại"
              : status === "done"
              ? "Bóc tách đề thi thành công!"
              : "Hệ thống AI đang bóc tách..."}
          </h4>
          <p className="text-sm text-slate-400 mt-0.5">{message}</p>
        </div>

        <span className="font-bold text-lg text-brand-400">{progress}%</span>
      </div>

      <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-500 ${
            status === "failed" ? "bg-red-500" : status === "done" ? "bg-green-500" : "bg-brand-500"
          }`}
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
};
export default AIProcessingStatus;
