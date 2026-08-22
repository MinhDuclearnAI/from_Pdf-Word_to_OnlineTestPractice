import sys
sys.path.insert(0, '/app')

from app.prompts.ielts_extract_prompt import IELTS_FULL_SYSTEM_PROMPT, get_ielts_full_prompt
from app.services.ai_parser import AIParserService

def test():
    parser = AIParserService()
    with open('/app/debug_logs/raw_text_job_65.txt', 'r', encoding='utf-8') as f:
        document_text = f.read()

    split_info = parser.split_ielts_document(document_text)
    prompt_input_text = f"[PASSAGE 1 QUESTIONS (Questions 1-13)]\n{split_info['p1']['questions_text']}\n\n[PASSAGE 2 QUESTIONS (Questions 14-26)]\n{split_info['p2']['questions_text']}\n\n[PASSAGE 3 QUESTIONS (Questions 27-40)]\n{split_info['p3']['questions_text']}"

    print("=== SYSTEM PROMPT ===")
    print(IELTS_FULL_SYSTEM_PROMPT)
    print("=== USER PROMPT ===")
    print(get_ielts_full_prompt(prompt_input_text))

if __name__ == '__main__':
    test()
