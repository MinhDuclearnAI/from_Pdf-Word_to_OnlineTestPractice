import React, { useState, useEffect, useRef } from "react";
import { Highlighter, StickyNote, Trash2, X, Check } from "lucide-react";

interface AnnotationToolbarProps {
  containerRef?: React.RefObject<HTMLElement>;
}

export const TextAnnotationToolbar: React.FC<AnnotationToolbarProps> = ({ containerRef }) => {
  const [toolbarPos, setToolbarPos] = useState<{ top: number; left: number } | null>(null);
  const [selectedRange, setSelectedRange] = useState<Range | null>(null);
  const [activeMark, setActiveMark] = useState<HTMLElement | null>(null);
  
  // Note dialog state
  const [isNoteOpen, setIsNoteOpen] = useState(false);
  const [noteText, setNoteText] = useState("");
  const [activeColor, setActiveColor] = useState<"yellow" | "green" | "pink">("yellow");

  const toolbarRef = useRef<HTMLDivElement>(null);

  const colors = {
    yellow: "bg-yellow-200 hover:bg-yellow-300 text-slate-900",
    green: "bg-emerald-200 hover:bg-emerald-300 text-slate-900",
    pink: "bg-pink-200 hover:bg-pink-300 text-slate-900",
  };

  // Lắng nghe sự kiện mouseup và selection
  useEffect(() => {
    const handleMouseUp = (e: MouseEvent) => {
      // Nếu click bên trong toolbar hoặc modal note thì bỏ qua
      if (toolbarRef.current && toolbarRef.current.contains(e.target as Node)) {
        return;
      }

      // 1. Kiểm tra xem có click vào một Highlight đã có sẵn không
      const target = e.target as HTMLElement;
      const clickedMark = target.closest("mark[data-ielts-highlight='true']") as HTMLElement;
      
      if (clickedMark) {
        const rect = clickedMark.getBoundingClientRect();
        setActiveMark(clickedMark);
        setSelectedRange(null);
        setNoteText(clickedMark.getAttribute("data-note") || "");
        setToolbarPos({
          top: rect.top - 50 + window.scrollY,
          left: rect.left + rect.width / 2,
        });
        setIsNoteOpen(false);
        return;
      }

      // 2. Kiểm tra text selection mới
      const selection = window.getSelection();
      if (!selection || selection.isCollapsed) {
        if (!isNoteOpen) {
          setToolbarPos(null);
          setSelectedRange(null);
          setActiveMark(null);
        }
        return;
      }

      const text = selection.toString().trim();
      if (text.length === 0) {
        if (!isNoteOpen) {
          setToolbarPos(null);
          setSelectedRange(null);
          setActiveMark(null);
        }
        return;
      }

      // Kiểm tra vùng bôi đen có nằm trong container bài thi hay không (nếu có truyền ref)
      if (containerRef?.current) {
        const anchorNode = selection.anchorNode;
        if (anchorNode && !containerRef.current.contains(anchorNode)) {
          return;
        }
      }

      const range = selection.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      
      if (rect.width > 0 && rect.height > 0) {
        setSelectedRange(range.cloneRange());
        setActiveMark(null);
        setNoteText("");
        setToolbarPos({
          top: rect.top - 50 + window.scrollY,
          left: rect.left + rect.width / 2,
        });
        setIsNoteOpen(false);
      }
    };

    document.addEventListener("mouseup", handleMouseUp);
    return () => {
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [containerRef, isNoteOpen]);

  // Thực hiện Highlight text
  const applyHighlight = (color: "yellow" | "green" | "pink", note?: string) => {
    if (!selectedRange) return;

    try {
      const mark = document.createElement("mark");
      mark.setAttribute("data-ielts-highlight", "true");
      mark.className = `${colors[color]} rounded px-1 py-0.5 cursor-pointer transition-colors select-text inline`;
      
      if (note && note.trim()) {
        mark.setAttribute("data-note", note.trim());
      }

      // Bọc nội dung đã chọn vào thẻ mark
      const contents = selectedRange.extractContents();
      mark.appendChild(contents);

      if (note && note.trim()) {
        const noteBadge = document.createElement("span");
        noteBadge.className = "inline-flex items-center justify-center ml-1 px-1.5 py-0.2 bg-amber-500 text-white rounded-full text-[10px] font-bold shadow-sm align-middle select-none";
        noteBadge.innerText = "📝";
        noteBadge.title = `Ghi chú: ${note.trim()}`;
        mark.appendChild(noteBadge);
      }

      selectedRange.insertNode(mark);
      
      // Xóa vùng chọn
      window.getSelection()?.removeAllRanges();
      setToolbarPos(null);
      setSelectedRange(null);
      setIsNoteOpen(false);
      setNoteText("");
    } catch (err) {
      console.warn("Could not wrap range across complex DOM elements:", err);
    }
  };

  // Cập nhật hoặc lưu note cho mark đã có
  const saveNoteForActiveMark = () => {
    if (activeMark) {
      if (noteText.trim()) {
        activeMark.setAttribute("data-note", noteText.trim());
        // Kiểm tra xem đã có badge icon chưa
        let badge = activeMark.querySelector("span");
        if (!badge) {
          badge = document.createElement("span");
          badge.className = "inline-flex items-center justify-center ml-1 px-1.5 py-0.2 bg-amber-500 text-white rounded-full text-[10px] font-bold shadow-sm align-middle select-none";
          badge.innerText = "📝";
          activeMark.appendChild(badge);
        }
        badge.title = `Ghi chú: ${noteText.trim()}`;
      } else {
        activeMark.removeAttribute("data-note");
        const badge = activeMark.querySelector("span");
        if (badge) badge.remove();
      }
      setIsNoteOpen(false);
      setToolbarPos(null);
      setActiveMark(null);
    } else if (selectedRange) {
      applyHighlight(activeColor, noteText);
    }
  };

  // Xóa Highlight
  const removeHighlight = () => {
    if (activeMark && activeMark.parentNode) {
      // Xóa note badge trước nếu có
      const badge = activeMark.querySelector("span");
      if (badge) badge.remove();

      while (activeMark.firstChild) {
        activeMark.parentNode.insertBefore(activeMark.firstChild, activeMark);
      }
      activeMark.parentNode.removeChild(activeMark);
      setToolbarPos(null);
      setActiveMark(null);
      setIsNoteOpen(false);
    }
  };

  if (!toolbarPos) return null;

  return (
    <div
      ref={toolbarRef}
      style={{
        top: `${toolbarPos.top}px`,
        left: `${toolbarPos.left}px`,
        transform: "translateX(-50%)",
      }}
      className="fixed z-50 animate-in fade-in zoom-in-95 duration-150"
    >
      {!isNoteOpen ? (
        <div className="bg-slate-900 text-white px-3 py-1.5 rounded-xl shadow-2xl flex items-center gap-2 border border-slate-700/80 backdrop-blur">
          {/* Nhóm nút chọn màu Highlight */}
          <div className="flex items-center gap-1.5 pr-2 border-r border-slate-700">
            <button
              onClick={() => {
                if (activeMark) {
                  activeMark.className = `${colors.yellow} rounded px-1 py-0.5 cursor-pointer transition-colors select-text inline`;
                  setToolbarPos(null);
                } else {
                  applyHighlight("yellow");
                }
              }}
              title="Highlight Vàng"
              className="w-5 h-5 rounded-full bg-yellow-300 hover:scale-110 transition-transform shadow-sm flex items-center justify-center"
            />
            <button
              onClick={() => {
                if (activeMark) {
                  activeMark.className = `${colors.green} rounded px-1 py-0.5 cursor-pointer transition-colors select-text inline`;
                  setToolbarPos(null);
                } else {
                  applyHighlight("green");
                }
              }}
              title="Highlight Xanh"
              className="w-5 h-5 rounded-full bg-emerald-400 hover:scale-110 transition-transform shadow-sm flex items-center justify-center"
            />
            <button
              onClick={() => {
                if (activeMark) {
                  activeMark.className = `${colors.pink} rounded px-1 py-0.5 cursor-pointer transition-colors select-text inline`;
                  setToolbarPos(null);
                } else {
                  applyHighlight("pink");
                }
              }}
              title="Highlight Hồng"
              className="w-5 h-5 rounded-full bg-pink-400 hover:scale-110 transition-transform shadow-sm flex items-center justify-center"
            />
          </div>

          {/* Nút Ghi chú */}
          <button
            onClick={() => setIsNoteOpen(true)}
            className="flex items-center gap-1 text-xs font-semibold px-2 py-1 bg-slate-800 hover:bg-slate-700 rounded-lg text-amber-300 hover:text-amber-200 transition-colors"
          >
            <StickyNote size={13} />
            {activeMark?.getAttribute("data-note") ? "Xem/Sửa Note" : "Ghi chú"}
          </button>

          {/* Nút Xóa (khi click vào highlight có sẵn) */}
          {activeMark && (
            <button
              onClick={removeHighlight}
              title="Xóa Highlight này"
              className="p-1 hover:bg-red-500/20 text-red-400 hover:text-red-300 rounded-lg transition-colors ml-0.5"
            >
              <Trash2 size={14} />
            </button>
          )}

          {/* Nút Đóng */}
          <button
            onClick={() => {
              setToolbarPos(null);
              setActiveMark(null);
              window.getSelection()?.removeAllRanges();
            }}
            className="text-slate-400 hover:text-white p-0.5"
          >
            <X size={13} />
          </button>
        </div>
      ) : (
        /* Hộp thoại Nhập / Chỉnh sửa Ghi chú */
        <div className="bg-white text-slate-800 p-3 rounded-xl shadow-2xl border border-slate-200 w-72 flex flex-col gap-2 animate-in fade-in duration-150">
          <div className="flex items-center justify-between border-b border-slate-100 pb-1.5">
            <span className="text-xs font-bold text-slate-700 flex items-center gap-1">
              <StickyNote size={13} className="text-amber-500" /> Ghi chú bài thi
            </span>
            <button onClick={() => setIsNoteOpen(false)} className="text-slate-400 hover:text-slate-600">
              <X size={14} />
            </button>
          </div>
          <textarea
            autoFocus
            rows={3}
            value={noteText}
            onChange={(e) => setNoteText(e.target.value)}
            placeholder="Nhập ghi chú hoặc từ khóa tại đây..."
            className="w-full text-xs p-2 bg-amber-50/50 border border-amber-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-400 text-slate-800 placeholder-slate-400 resize-none font-sans"
          />
          <div className="flex items-center justify-between pt-1">
            {activeMark && (
              <button
                onClick={removeHighlight}
                className="text-xs text-red-600 hover:text-red-700 font-medium flex items-center gap-1"
              >
                <Trash2 size={12} /> Xóa
              </button>
            )}
            <div className="flex gap-1.5 ml-auto">
              <button
                onClick={() => setIsNoteOpen(false)}
                className="px-2.5 py-1 text-xs text-slate-500 hover:bg-slate-100 rounded-md font-medium"
              >
                Hủy
              </button>
              <button
                onClick={saveNoteForActiveMark}
                className="px-3 py-1 text-xs bg-amber-500 hover:bg-amber-600 text-white rounded-md font-bold shadow-sm flex items-center gap-1"
              >
                <Check size={12} /> Lưu
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TextAnnotationToolbar;
