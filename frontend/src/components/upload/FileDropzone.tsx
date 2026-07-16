import React, { useState, useRef } from "react";
import { Upload, AlertCircle } from "lucide-react";

interface FileDropzoneProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

export const FileDropzone: React.FC<FileDropzoneProps> = ({ onFileSelect, disabled }) => {
  const [isDragActive, setIsDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (disabled) return;

    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const validateAndSelectFile = (file: File) => {
    const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();
    if (ext !== ".pdf" && ext !== ".docx" && ext !== ".doc") {
      setError("Định dạng tệp không được hỗ trợ. Chỉ chấp nhận tệp PDF, DOC, DOCX.");
      return;
    }
    setError(null);
    onFileSelect(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    if (disabled) return;

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSelectFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (disabled) return;

    if (e.target.files && e.target.files[0]) {
      validateAndSelectFile(e.target.files[0]);
    }
  };

  return (
    <div className="w-full">
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={() => !disabled && fileInputRef.current?.click()}
        className={`relative flex flex-col items-center justify-center w-full h-64 border-2 border-dashed rounded-xl cursor-pointer transition-all duration-300 ${
          isDragActive
            ? "border-brand-500 bg-brand-500/10"
            : "border-slate-700 bg-slate-900/40 hover:bg-slate-900/60 hover:border-slate-600"
        } ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf,.docx,.doc"
          onChange={handleChange}
          disabled={disabled}
        />

        <div className="flex flex-col items-center justify-center pt-5 pb-6 text-center px-4">
          <div className="p-4 bg-slate-800/80 rounded-full mb-4 text-brand-400 transition-transform">
            <Upload size={28} />
          </div>
          <p className="mb-2 text-sm text-slate-200 font-medium">
            <span className="text-brand-400 font-semibold">Nhấn để tải lên</span> hoặc kéo thả tệp tin
          </p>
          <p className="text-xs text-slate-400">PDF, Word (DOCX, DOC) tối đa 10MB</p>
        </div>
      </div>

      {error && (
        <div className="mt-4 p-3 bg-red-950/40 border border-red-800/50 rounded-lg flex items-center gap-2.5 text-sm text-red-400">
          <AlertCircle size={18} className="shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};
export default FileDropzone;
