import re

def smart_clean_passage_paragraphs(raw_passage_body: str) -> str:
    if not raw_passage_body or not raw_passage_body.strip():
        return ""
        
    # Bước 1: Nối các từ bị gạch nối ở cuối dòng bị ngắt (vd: wine-\nmaking -> wine-making)
    # Chỉ nối nếu chữ cái sau dấu gạch nối là chữ thường
    text = re.sub(r'(\w+)-\s*\n\s*([a-z]\w*)', r'\1-\2', raw_passage_body)
    
    # Bước 2: Tách các khối theo \n\n (các đoạn văn có dòng trống ngăn cách)
    raw_blocks = [b.strip() for b in re.split(r'\n\s*\n+', text) if b.strip()]
    
    final_paragraphs = []
    
    for block in raw_blocks:
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        if not lines:
            continue
            
        current_p_lines = [lines[0]]
        
        for i in range(1, len(lines)):
            prev_line = current_p_lines[-1]
            curr_line = lines[i]
            
            # 1. Nếu curr_line là nhãn đoạn văn IELTS A., B., C., D...
            if re.match(r'^[A-H]\.\s+', curr_line):
                # Bắt buộc tách thành đoạn văn mới
                final_paragraphs.append(" ".join(current_p_lines))
                current_p_lines = [curr_line]
                continue
                
            # 2. Kiểm tra dấu kết câu của dòng trước
            prev_ends_punct = bool(re.search(r'[\.!\?][\"\'\)]?\s*$', prev_line))
            
            # 3. Xét trường hợp:
            # - Nếu dòng trước KHÔNG kết thúc bằng dấu chấm/chấm than -> chắc chắn là bị ép xuống dòng do hết chỗ -> nối bằng dấu cách
            # - Nếu dòng sau bắt đầu bằng chữ thường -> chắc chắn cùng một câu -> nối bằng dấu cách
            # - Nếu dòng trước có dấu chấm nhưng nằm trong cùng 1 khối block ban đầu -> là các câu liên tiếp trong cùng đoạn -> nối bằng dấu cách
            current_p_lines.append(curr_line)
                    
        if current_p_lines:
            final_paragraphs.append(" ".join(current_p_lines))
            
    # Chuẩn hóa khoảng trắng mượt mà bên trong mỗi đoạn
    cleaned = []
    for p in final_paragraphs:
        clean_p = " ".join(p.split())
        if clean_p:
            cleaned.append(clean_p)
            
    return "\n\n".join(cleaned)

if __name__ == "__main__":
    for job in [74, 75, 76]:
        with open(f"/app/debug_logs/raw_text_job_{job}.txt", "r", encoding="utf-8") as f:
            t = f.read()
        print(f"=== JOB {job} ===")
        cleaned = smart_clean_passage_paragraphs(t)
        paras = cleaned.split("\n\n")
        print(f"Total Paragraphs: {len(paras)}")
        print(f"Sample P1: {repr(paras[0][:60])}")
