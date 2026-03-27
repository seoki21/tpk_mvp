"""
피드백 다국어 번역 스크립트 (일회성)
question_json 내 한국어 feedback 배열을 Claude API로 번역하여
5개 언어(ko, en, ja, zh, vi) feedback_json을 생성하고 DB에 UPDATE한다.

실행:
  cd backend
  source venv/Scripts/activate
  python scripts/translate_feedback.py           # 실제 실행
  python scripts/translate_feedback.py --dry-run  # 미리보기
"""
import sys
import os
import json
import time
import io

# Windows 콘솔 인코딩 문제 해결
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# backend/ 디렉토리를 파이썬 경로에 추가하여 app 모듈 임포트 가능하게 함
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import anthropic
from app.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL
from app.database import get_connection

# --dry-run 모드 여부
DRY_RUN = "--dry-run" in sys.argv

# Anthropic 클라이언트
_client = None


def get_client():
    """Anthropic 클라이언트 싱글턴 반환"""
    global _client
    if _client is None:
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


# 번역 프롬프트 템플릿
_TRANSLATE_PROMPT = """You are a professional translator specializing in Korean language education (TOPIK).

Translate the following Korean feedback items for a TOPIK exam question into 4 languages: English (en), Japanese (ja), Chinese (zh), Vietnamese (vi).

[Korean feedback]
{feedback_ko_json}

Rules:
- Preserve the EXACT prefix format: "①:T_", "②:F_", etc. Do not translate the circled numbers or T/F markers.
- Translate ONLY the text after "T_" or "F_" in each item.
- Keep translations concise (similar length to Korean original, 20-40 characters).
- Use polite/formal register in all languages.
- Return ONLY a pure JSON object (no markdown code blocks):

{{
  "en": ["①:T_English translation...", "②:F_English translation...", ...],
  "ja": ["①:T_日本語翻訳...", "②:F_日本語翻訳...", ...],
  "zh": ["①:T_中文翻译...", "②:F_中文翻译...", ...],
  "vi": ["①:T_Bản dịch tiếng Việt...", "②:F_Bản dịch tiếng Việt...", ...]
}}"""


def fetch_target_rows():
    """feedback_json이 NULL인 문제 목록을 조회한다."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT exam_key, question_no, question_json
              FROM tb_exam_question
             WHERE del_yn = 'N'
               AND question_json IS NOT NULL
               AND feedback_json IS NULL
             ORDER BY exam_key, question_no
            """
        )
        return cursor.fetchall()
    finally:
        conn.close()


def clean_response_text(text):
    """마크다운 코드블록 제거 후 순수 텍스트 반환"""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text


def try_parse_json(text):
    """
    JSON 파싱을 시도한다. 실패 시 일반적인 오류를 수정하여 재시도한다.
    - 문자열 내 이스케이프되지 않은 따옴표 처리
    - 후행 쉼표(trailing comma) 제거
    """
    import re
    # 1차: 그대로 파싱 시도
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2차: 후행 쉼표 제거 후 재시도
    cleaned = re.sub(r',\s*([}\]])', r'\1', text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 3차: 원본 에러를 발생시킴
    return json.loads(text)


def translate_feedback(feedback_ko):
    """
    Claude API를 호출하여 한국어 피드백을 4개 언어로 번역한다.
    최대 2회 재시도 (Rate Limit 대응).

    Args:
        feedback_ko: 한국어 피드백 배열 ["①:T_...", "②:F_...", ...]

    Returns:
        번역 결과 dict {"en": [...], "ja": [...], "zh": [...], "vi": [...]}
    """
    client = get_client()
    feedback_ko_json = json.dumps(feedback_ko, ensure_ascii=False, indent=2)
    prompt = _TRANSLATE_PROMPT.format(feedback_ko_json=feedback_ko_json)

    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            response = client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )

            # 응답 텍스트 추출
            result_text = ""
            for block in response.content:
                if block.type == "text":
                    result_text += block.text

            result_text = clean_response_text(result_text)
            parsed = try_parse_json(result_text)

            # 4개 언어 키 존재 여부 검증
            for lang in ("en", "ja", "zh", "vi"):
                if lang not in parsed:
                    raise ValueError(f"'{lang}' 키가 응답에 없습니다.")
                if len(parsed[lang]) != len(feedback_ko):
                    raise ValueError(
                        f"'{lang}' 배열 길이 불일치: 원본 {len(feedback_ko)}, 번역 {len(parsed[lang])}"
                    )

            return parsed

        except anthropic.RateLimitError:
            if attempt < max_retries:
                wait = 2 ** (attempt + 1)
                print(f"    Rate limit — {wait}초 대기 후 재시도 ({attempt + 1}/{max_retries})")
                time.sleep(wait)
            else:
                raise
        except (json.JSONDecodeError, ValueError) as e:
            if attempt < max_retries:
                print(f"    JSON 파싱 실패 — 재시도 ({attempt + 1}/{max_retries}): {e}")
                time.sleep(1)
            else:
                raise


def update_feedback_json(exam_key, question_no, feedback_json_str):
    """feedback_json 컬럼을 업데이트한다."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE tb_exam_question
               SET feedback_json = %s, upd_date = NOW(), upd_user = 'ai_translate'
             WHERE exam_key = %s AND question_no = %s
            """,
            (feedback_json_str, exam_key, question_no),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main():
    if DRY_RUN:
        print("=== DRY-RUN 모드 (DB 변경 없음, API 호출 없음) ===\n")

    # 대상 문제 조회
    rows = fetch_target_rows()
    total = len(rows)
    print(f"대상 문제: {total}건\n")

    if total == 0:
        print("처리할 문제가 없습니다.")
        return

    success = 0
    failed = 0
    errors = []

    for idx, row in enumerate(rows, 1):
        exam_key = row["exam_key"]
        question_no = row["question_no"]
        prefix = f"[{idx}/{total}] exam_key={exam_key}, question_no={question_no}"

        # question_json에서 feedback 추출
        try:
            q_parsed = json.loads(row["question_json"])
        except json.JSONDecodeError:
            print(f"{prefix} — SKIP: question_json 파싱 실패")
            failed += 1
            errors.append({"exam_key": exam_key, "question_no": question_no, "error": "question_json 파싱 실패"})
            continue

        feedback_ko = q_parsed.get("feedback")
        if not feedback_ko or not isinstance(feedback_ko, list):
            print(f"{prefix} — SKIP: feedback 필드 없음")
            failed += 1
            errors.append({"exam_key": exam_key, "question_no": question_no, "error": "feedback 필드 없음"})
            continue

        if DRY_RUN:
            print(f"{prefix} — ko feedback: {feedback_ko}")
            success += 1
            continue

        # Claude API 호출하여 번역
        try:
            translated = translate_feedback(feedback_ko)

            # feedback_json 조합: ko(원본) + 번역 4개 언어
            feedback_json = {
                "ko": feedback_ko,
                "en": translated["en"],
                "ja": translated["ja"],
                "zh": translated["zh"],
                "vi": translated["vi"],
            }
            feedback_json_str = json.dumps(feedback_json, ensure_ascii=False)

            # DB UPDATE
            update_feedback_json(exam_key, question_no, feedback_json_str)
            success += 1
            print(f"{prefix} — OK")

        except Exception as e:
            failed += 1
            errors.append({"exam_key": exam_key, "question_no": question_no, "error": str(e)})
            print(f"{prefix} — FAIL: {e}")

        # API 호출 간격
        time.sleep(0.5)

    # 결과 요약
    print(f"\n{'=' * 50}")
    print(f"완료 — 전체: {total}, 성공: {success}, 실패: {failed}")
    if errors:
        print("\n실패 목록:")
        for err in errors:
            print(f"  exam_key={err['exam_key']}, question_no={err['question_no']}: {err['error']}")


if __name__ == "__main__":
    main()
