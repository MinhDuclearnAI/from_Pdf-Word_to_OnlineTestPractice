export const COMPONENT_TYPE_MAP = {
  multiple_choice: "multiple_choice",
  essay: "essay",
  latex_formula: "latex_formula",
  reading_passage: "reading_passage",
  writing: "writing",
};

export const SUBJECT_LABELS: Record<string, string> = {
  "Toán": "Toán Học",
  "Vật Lý": "Vật Lý",
  "Hóa Học": "Hóa Học",
  "Sinh Học": "Sinh Học",
  "Tiếng Anh": "Tiếng Anh",
  "IELTS": "IELTS",
  "HSA": "Đánh giá năng lực HSA",
  "Khác": "Môn học khác",
};

export const TEST_TYPE_LABELS: Record<string, string> = {
  practice: "Luyện tập tự do",
  exam: "Kiểm tra chính thức",
};
