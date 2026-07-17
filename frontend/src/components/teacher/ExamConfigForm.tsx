import React, { useState } from "react";
import Input from "../ui/Input";
import Button from "../ui/Button";

interface ExamConfigFormProps {
  initialConfig: {
    duration: number;
    open_at?: string;
    close_at?: string;
    result_visibility: string;
  };
  onSubmit: (config: any) => void;
  loading?: boolean;
}

export const ExamConfigForm: React.FC<ExamConfigFormProps> = ({ initialConfig, onSubmit, loading }) => {
  const [duration, setDuration] = useState(initialConfig.duration || 60);
  const [openAt, setOpenAt] = useState(
    initialConfig.open_at ? new Date(initialConfig.open_at).toISOString().slice(0, 16) : ""
  );
  const [closeAt, setCloseAt] = useState(
    initialConfig.close_at ? new Date(initialConfig.close_at).toISOString().slice(0, 16) : ""
  );
  const [resultVisibility, setResultVisibility] = useState(initialConfig.result_visibility || "detailed");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      duration: Number(duration),
      open_at: openAt ? new Date(openAt).toISOString() : null,
      close_at: closeAt ? new Date(closeAt).toISOString() : null,
      result_visibility: resultVisibility,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5 bg-slate-900/40 p-6 border border-slate-800 rounded-xl">
      <h3 className="text-base font-bold text-slate-100 mb-2">Cấu hình bài kiểm tra</h3>
      
      <Input
        label="Thời gian làm bài (phút)"
        type="number"
        min={1}
        value={duration}
        onChange={(e) => setDuration(Number(e.target.value))}
        required
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Mở cổng đề thi"
          type="datetime-local"
          value={openAt}
          onChange={(e) => setOpenAt(e.target.value)}
        />
        <Input
          label="Đóng cổng đề thi"
          type="datetime-local"
          value={closeAt}
          onChange={(e) => setCloseAt(e.target.value)}
        />
      </div>

      <div className="w-full">
        <label className="block text-sm font-medium text-slate-300 mb-1.5">
          Quyền xem kết quả của học sinh
        </label>
        <select
          value={resultVisibility}
          onChange={(e) => setResultVisibility(e.target.value)}
          className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
        >
          <option value="detailed">Xem điểm & xem chi tiết đáp án ngay</option>
          <option value="score_only">Chỉ xem điểm, ẩn đáp án</option>
          <option value="after_close">Ẩn hoàn toàn (Giáo viên công bố sau)</option>
        </select>
      </div>

      <Button type="submit" variant="primary" className="w-full" disabled={loading}>
        {loading ? "Đang lưu cấu hình..." : "Lưu cấu hình"}
      </Button>
    </form>
  );
};
export default ExamConfigForm;
