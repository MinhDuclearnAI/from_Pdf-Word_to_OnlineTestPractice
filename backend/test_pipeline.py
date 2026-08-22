import re

def _clean_passage_paragraphs(raw_text: str) -> str:
    if not raw_text or not raw_text.strip():
        return ""
    # Bước 1: Nối các từ bị gạch nối ở cuối dòng bị ngắt (vd: wine-\nmaking -> wine-making)
    # Chỉ nối nếu chữ cái sau dấu gạch nối là chữ thường
    raw_text = re.sub(r'(\w+)-\s*\n\s*([a-z]\w*)', r'\1-\2', raw_text)
    
    # Bước 2: Tách theo các đoạn văn có khoảng trống dòng \n\n
    paragraphs = re.split(r'\n\s*\n+', raw_text)
    cleaned = []
    for p in paragraphs:
        # Trong cùng 1 đoạn văn, các dòng ngắt đơn \n (do chạm lề PDF) được nối mượt mà bằng dấu cách
        clean_p = " ".join(p.split())
        if clean_p:
            cleaned.append(clean_p)
    return "\n\n".join(cleaned)

def _is_valid_title(cand: str) -> bool:
    if not cand or len(cand) >= 80:
        return False
    cand = cand.strip()
    
    # Phải bắt đầu bằng chữ hoa (hoặc dấu ngoặc kép + chữ hoa)
    first_char_str = re.sub(r'^[\'\"“‘\s]+', '', cand)
    if not first_char_str or not first_char_str[0].isupper():
        return False
        
    # 1. Không phải là đoạn văn có nhãn A., B., C.
    if re.match(r'^[A-H]\.\s+', cand):
        return False
        
    # 2. Không kết thúc bằng dấu chấm, phẩy, chấm phẩy, hai chấm, gạch nối (chấp nhận ! hoặc ?)
    if cand.endswith(('.', ',', ';', ':', '-', '–')):
        return False
        
    # 3. Không kết thúc bằng giới từ hoặc liên từ (chứng tỏ bị ngắt dòng giữa câu)
    if re.search(r'\b(and|or|of|in|to|the|a|an|that|with|for|as|by|on|at|from|is|are|was|were)\s*$', cand, re.I):
        return False
        
    # 4. Không bắt đầu bằng các từ nối đoạn văn hoặc liên từ mở đầu
    if re.match(r'(?i)^(Although|According|When|In the|During|From|After|While|Because|However|Therefore|Moreover|Furthermore|Since|If|As a|It was|There is|They are)\b', cand):
        return False
        
    return True

def _extract_title_and_clean_passage(raw_text: str, default_title: str) -> tuple:
    if not raw_text or not raw_text.strip():
        return default_title, ""
    
    t = raw_text.strip()
    # 1. Xóa câu hướng dẫn You should spend... kể cả khi ngắt dòng ở giữa
    t = re.sub(r'(?i)^\s*You\s+should\s+spend\s+about\s+\d+\s+minut[eo]s\s+on\s+Questions?.*?(?:pages?\s+\d+.*?\n|\.\s*\n)', '\n\n', t, flags=re.DOTALL)
    # 2. Xóa các header IELTS ở đầu
    t = re.sub(r'(?i)^\s*(?:IELTS|TEST|ACADEMIC|GENERAL|PRACTICE|READING\s+TEST).*\n', '\n', t)
    
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n+', t) if p.strip()]
    if not paragraphs:
        return default_title, ""
        
    title = default_title
    cleaned_paragraphs = []
    
    for p in paragraphs:
        p_single_line = " ".join(p.split())
        # Lọc bỏ đoạn rác meta
        if re.match(r'(?i)^\s*(?:READING\s+PASSAGE\s+\d+|PASSAGE\s+\d+)(?:\s+on\s+pages?.*)?$', p_single_line):
            continue
        if re.match(r'(?i)^\s*You\s+should\s+spend\s+about', p_single_line):
            continue
        if re.match(r'(?i)^\s*(?:which\s+are\s+based\s+on\s+)?(?:Reading\s+Passage\s+\d+\s+)?(?:on\s+pages?.*)?$', p_single_line):
            continue

        # Nếu chưa tìm thấy title:
        if title == default_title:
            lines = [l.strip() for l in p.split('\n') if l.strip()]
            first_line = lines[0]
            
            # Nếu cả đoạn p là tiêu đề ngắn (ví dụ: Destination Mars)
            if len(lines) == 1 and _is_valid_title(first_line):
                title = first_line
                continue
                
            # Nếu tiêu đề dính với dòng đầu của đoạn (ví dụ: Make That Wine!\nAustralia is a nation...)
            if len(lines) > 1 and _is_valid_title(first_line):
                title = first_line
                # Giữ nguyên phần còn lại của đoạn văn
                p_remaining = '\n'.join(lines[1:])
                cleaned_paragraphs.append(p_remaining)
                continue

        cleaned_paragraphs.append(p)
        
    # CHỈ ÁP DỤNG LÀM SẠCH VÀ NỐI DÒNG CHO PHẦN THÂN BÀI ĐỌC (SAU KHI ĐÃ CẮT TITLE)
    final_body = _clean_passage_paragraphs('\n\n'.join(cleaned_paragraphs))
    return title, final_body

if __name__ == "__main__":
    for job in [74, 75, 76]:
        with open(f"/app/debug_logs/raw_text_job_{job}.txt", "r", encoding="utf-8") as f:
            t = f.read()
        print(f"=== FULL TEST JOB {job} ===")
        # P1
        p1_idx = t.find("Questions 1-")
        p1_raw = t[:p1_idx] if p1_idx != -1 else t[:1000]
        title1, body1 = _extract_title_and_clean_passage(p1_raw, "Reading Passage 1")
        print(f"P1 Title: {repr(title1)}")
        paras1 = body1.split("\n\n")
        print(f"P1 Paras Count: {len(paras1)}")
        print(f"P1 Para 1: {repr(paras1[0][:80])}")
