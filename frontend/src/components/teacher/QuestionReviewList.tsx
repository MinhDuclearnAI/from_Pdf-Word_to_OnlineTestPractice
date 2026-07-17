import React, { useState, useEffect } from "react";
import { Trash2, Plus, Check, Edit2 } from "lucide-react";
import Input from "../ui/Input";
import Button from "../ui/Button";
import apiClient from "@/lib/api-client";

interface Question {
  id: number;
  component_type: string;
  question_text: string;
  options: string[];
  correct_answer?: string;
  score_weight: number;
  passage_ref?: string;
}

interface QuestionReviewListProps {
  examId: number;
  initialQuestions: Question[];
  onUpdate: () => void;
}

export const QuestionReviewList: React.FC<QuestionReviewListProps> = ({ examId, initialQuestions, onUpdate }) => {
  const [questions, setQuestions] = useState<Question[]>(initialQuestions);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingData, setEditingData] = useState<Partial<Question>>({});
  const [loading, setLoading] = useState<Record<number, boolean>>({});

  useEffect(() => {
    setQuestions(initialQuestions);
  }, [initialQuestions]);

  const handleEditStart = (q: Question) => {
    setEditingId(q.id);
    setEditingData({ ...q });
  };

  const handleEditCancel = () => {
    setEditingId(null);
    setEditingData({});
  };

  const handleFieldChange = (field: keyof Question, value: any) => {
    setEditingData((prev) => ({ ...prev, [field]: value }));
  };

  const handleOptionChange = (idx: number, val: string) => {
    const opts = [...(editingData.options || [])];
    opts[idx] = val;
    handleFieldChange("options", opts);
  };

  const handleSave = async (qId: number) => {
    setLoading((prev) => ({ ...prev, [qId]: true }));
    try {
      await apiClient.patch(`/exams/${examId}/questions/${qId}`, editingData);
      setEditingId(null);
      setEditingData({});
      onUpdate();
    } catch (e) {
      console.error("Failed to save question:", e);
      alert("Lỗi khi lưu câu hỏi.");
    } finally {
      setLoading((prev) => ({ ...prev, [qId]: false }));
    }
  };

  const handleDelete = async (qId: number) => {
    if (!confirm("Bạn có chắc chắn muốn xóa câu hỏi này?")) return;
    try {
      await apiClient.delete(`/exams/${examId}/questions/${qId}`);
      onUpdate();
    } catch (e) {
      console.error("Failed to delete question:", e);
      alert("Lỗi khi xóa câu hỏi.");
    }
  };

  const handleAddQuestion = async () => {
    try {
      await apiClient.post(`/exams/${examId}/questions`, {
        exam_id: Number(examId),
        component_type: "multiple_choice",
        question_text: "Nội dung câu hỏi mới...",
        options: ["Đáp án A", "Đáp án B", "Đáp án C", "Đáp án D"],
        correct_answer: "A",
        score_weight: 1.0,
      });
      onUpdate();
    } catch (e) {
      console.error("Failed to add question:", e);
      alert("Lỗi khi thêm câu hỏi mới.");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <h3 className="text-lg font-bold text-slate-100">Danh sách câu hỏi bóc tách</h3>
        <Button variant="secondary" size="sm" onClick={handleAddQuestion} className="flex items-center gap-1">
          <Plus size={16} /> Thêm câu hỏi
        </Button>
      </div>

      {questions.length === 0 ? (
        <div className="text-center py-8 text-slate-400 text-sm">
          Chưa có câu hỏi nào. Nhấp vào "Thêm câu hỏi" để tạo.
        </div>
      ) : (
        <div className="space-y-4">
          {questions.map((q, idx) => {
            const isEditing = editingId === q.id;

            return (
              <div key={q.id} className="glass-card rounded-xl p-5 border border-slate-800 space-y-4">
                <div className="flex items-start justify-between">
                  <span className="font-bold text-brand-400 text-sm">Câu {idx + 1}</span>
                  <div className="flex items-center gap-2">
                    {isEditing ? (
                      <>
                        <Button variant="ghost" size="sm" onClick={handleEditCancel} className="text-slate-400">
                          Hủy
                        </Button>
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => handleSave(q.id)}
                          disabled={loading[q.id]}
                        >
                          <Check size={16} className="mr-1" /> Lưu
                        </Button>
                      </>
                    ) : (
                      <>
                        <button
                          type="button"
                          onClick={() => handleEditStart(q)}
                          className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded"
                        >
                          <Edit2 size={16} />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDelete(q.id)}
                          className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded"
                        >
                          <Trash2 size={16} />
                        </button>
                      </>
                    )}
                  </div>
                </div>

                {isEditing ? (
                  <div className="space-y-4">
                    <Input
                      label="Nội dung câu hỏi"
                      value={editingData.question_text || ""}
                      onChange={(e) => handleFieldChange("question_text", e.target.value)}
                    />

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-slate-300 mb-1.5">Loại Component</label>
                        <select
                          value={editingData.component_type || ""}
                          onChange={(e) => handleFieldChange("component_type", e.target.value)}
                          className="w-full px-4 py-2 bg-slate-900 border border-slate-800 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                        >
                          <option value="multiple_choice">Trắc nghiệm</option>
                          <option value="math_equation">Công thức Toán (LaTeX)</option>
                          <option value="essay">Tự luận</option>
                          <option value="fill_in_the_blank">Điền khuyết</option>
                        </select>
                      </div>

                      <Input
                        label="Điểm số câu"
                        type="number"
                        step={0.1}
                        value={editingData.score_weight || 1}
                        onChange={(e) => handleFieldChange("score_weight", Number(e.target.value))}
                      />
                    </div>

                    <Input
                      label="Nội dung Đoạn văn bài đọc (Reading Passage)"
                      value={editingData.passage_ref || ""}
                      onChange={(e) => handleFieldChange("passage_ref", e.target.value)}
                    />

                    {editingData.component_type === "multiple_choice" && (
                      <div className="space-y-2">
                        <label className="block text-sm font-medium text-slate-300">Các tùy chọn đáp án</label>
                        {(editingData.options || []).map((opt, oIdx) => (
                          <div key={oIdx} className="flex items-center gap-2">
                            <span className="font-semibold text-xs text-slate-400">{String.fromCharCode(65 + oIdx)}</span>
                            <Input value={opt} onChange={(e) => handleOptionChange(oIdx, e.target.value)} />
                          </div>
                        ))}
                      </div>
                    )}

                    <Input
                      label="Đáp án đúng"
                      value={editingData.correct_answer || ""}
                      onChange={(e) => handleFieldChange("correct_answer", e.target.value)}
                    />
                  </div>
                ) : (
                  <div className="space-y-2">
                    <p className="text-slate-200 font-medium whitespace-pre-wrap leading-relaxed">
                      {q.question_text}
                    </p>
                    
                    {q.component_type === "multiple_choice" && q.options && q.options.length > 0 && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-2">
                        {q.options.map((opt, oIdx) => (
                          <div key={oIdx} className="text-sm text-slate-400 flex gap-2">
                            <span className="font-bold text-brand-400">{String.fromCharCode(65 + oIdx)}.</span>
                            <span>{opt}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {q.correct_answer && (
                      <div className="text-sm text-slate-400 mt-2">
                        Đáp án đúng: <span className="text-green-500 font-semibold">{q.correct_answer}</span> | 
                        Trọng số: <span className="text-slate-200 font-semibold">{q.score_weight} điểm</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
export default QuestionReviewList;
