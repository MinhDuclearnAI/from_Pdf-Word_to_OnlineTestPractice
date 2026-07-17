import os
from openai import OpenAI

client = OpenAI(api_key='sk-9aba801e2437b38c5a39e3a525f198211a9b5ba80279c92fba3ee14a59bae8a2', base_url='https://api.vilao.ai/v1')

def test(p, name):
    try:
        response = client.chat.completions.create(model='gemini-2.5-flash-lite', messages=[{'role': 'user', 'content': p}])
        if hasattr(response, 'error') and response.error: print(name, 'FAILED:', response.error)
        else: print(name, 'SUCCESS')
    except Exception as e: print(name, 'EXCEPTION:', e)

test('Here is some JSON: { "questions": [] }', 'Test JSON')
test('Here is some JSON with comments: { "questions": [] } // comment', 'Test JSON with comments')
test('{"id": "q1", "type": "multiple_choice"}', 'Test JSON valid')

from app.prompts.extract_prompt import EXTRACT_USER_PROMPT_TEMPLATE
test(EXTRACT_USER_PROMPT_TEMPLATE.format(document_text='test'), 'Test Full Prompt')
