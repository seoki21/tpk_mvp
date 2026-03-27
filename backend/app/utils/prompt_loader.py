"""
프롬프트 로더 유틸리티
app/prompts/ 디렉토리에서 프롬프트 텍스트 파일을 읽어 반환한다.
한 번 읽은 파일은 캐싱하여 재사용한다.
"""
import os

# 프롬프트 파일 디렉토리 경로
_PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")

# 캐시: { 파일명: 프롬프트 텍스트 }
_cache: dict[str, str] = {}


def load_prompt(name: str) -> str:
    """
    프롬프트 파일을 읽어 텍스트를 반환한다.
    캐싱되어 서버 재시작 전까지 메모리에 유지된다.

    Args:
        name: 프롬프트 파일명 (확장자 제외, 예: "feedback_generate")

    Returns:
        프롬프트 텍스트 문자열

    Raises:
        FileNotFoundError: 프롬프트 파일이 존재하지 않는 경우
    """
    if name in _cache:
        return _cache[name]

    file_path = os.path.join(_PROMPTS_DIR, f"{name}.txt")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"프롬프트 파일을 찾을 수 없습니다: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    _cache[name] = text
    return text
