"""Smoke test: _parse_claude_text_response tolerance for fence variants / truncation."""
import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
os.environ.setdefault('ANTHROPIC_API_KEY', 'mock')

from .analyzer import Analyzer

cases = [
    ("완전 펜스", "```json\n{\"a\": 1, \"b\": 2}\n```"),
    ("여는 펜스만 (닫힘 없음 = 잘림 직전)", "```json\n{\"a\": 1, \"b\": 2}"),
    ("펜스 없이 순수 JSON", "{\"a\": 1, \"b\": 2}"),
    ("앞뒤 여백 + 펜스", "  ```json\n{\"a\": 1}\n```  "),
    ("일반 ``` 펜스", "```\n{\"a\": 1}\n```"),
    ("펜스 앞 설명 텍스트", "여기 분석입니다:\n```json\n{\"a\": 1, \"b\": \"test\"}\n```"),
    ("JSON 뒤에 추가 텍스트", "{\"a\": 1}\n\n분석 끝."),
]

a = Analyzer.__new__(Analyzer)
ok = 0
fail = 0
for name, txt in cases:
    try:
        result = a._parse_claude_text_response(txt)
        print(f"  OK: {name} -> {result}")
        ok += 1
    except Exception as e:
        print(f"  FAIL: {name} -> {type(e).__name__}: {e}")
        fail += 1

# 진짜 잘림 (중간 끊김): 이건 실패해야 함
truncated = "```json\n{\"a\": 1, \"b\": \"TargetCool은 2023년 FDA/식약처"
try:
    result = a._parse_claude_text_response(truncated)
    print(f"  WARN: 진짜 잘림도 파싱됨 (예상 밖): {result}")
except Exception as e:
    print(f"  OK: 진짜 잘림은 예상대로 실패 -> {type(e).__name__}")

print(f"\n결과: {ok} OK / {fail} FAIL (잘림 케이스 제외)")
