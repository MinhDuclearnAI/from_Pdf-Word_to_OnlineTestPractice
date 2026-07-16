import React from "react";
import { Modal } from "../ui/Modal";
import { Button } from "../ui/Button";
import { AlertTriangle, CheckCircle } from "lucide-react";

interface SubmitConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: () => void;
  totalQuestions: number;
  answeredCount: number;
  loading?: boolean;
}

export const SubmitConfirmModal: React.FC<SubmitConfirmModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  totalQuestions,
  answeredCount,
  loading,
}) => {
  const unansweredCount = totalQuestions - answeredCount;
  const hasUnanswered = unansweredCount > 0;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Xác nhận nộp bài">
      <div className="text-center">
        {hasUnanswered ? (
          <div className="flex flex-col items-center mb-4">
            <div className="p-3 bg-yellow-500/10 rounded-full text-yellow-500 mb-3 border border-yellow-500/20">
              <AlertTriangle size={32} />
            </div>
            <h4 className="font-semibold text-slate-100 text-lg">Bạn vẫn muốn nộp bài?</h4>
            <p className="text-sm text-slate-400 mt-1 max-w-sm">
              Bạn vẫn còn <span className="text-yellow-500 font-semibold">{unansweredCount} câu hỏi</span> chưa hoàn thành câu trả lời.
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center mb-4">
            <div className="p-3 bg-green-500/10 rounded-full text-green-500 mb-3 border border-green-500/20">
              <CheckCircle size={32} />
            </div>
            <h4 className="font-semibold text-slate-100 text-lg">Hoàn thành bài thi</h4>
            <p className="text-sm text-slate-400 mt-1 max-w-sm">
              Tuyệt vời! Bạn đã hoàn thành toàn bộ <span className="text-green-500 font-semibold">{totalQuestions} câu hỏi</span>.
            </p>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4 mt-6">
          <Button variant="secondary" onClick={onClose} disabled={loading}>
            Tiếp tục làm bài
          </Button>
          <Button variant={hasUnanswered ? "danger" : "primary"} onClick={onSubmit} disabled={loading}>
            {loading ? "Đang nộp..." : "Nộp bài ngay"}
          </Button>
        </div>
      </div>
    </Modal>
  );
};
export default SubmitConfirmModal;
