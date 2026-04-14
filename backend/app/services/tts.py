"""
TTS 생성 서비스 모듈
GPT-SoVITS API를 통해 텍스트를 음성으로 변환한다.

처리 흐름:
1. Claude API로 텍스트 분석 → 화자 판별 + 스크립트 정제 (segments JSON)
2. segments를 순서대로 GPT-SoVITS에 호출 (text: null 세그먼트는 스킵)
3. 반환된 WAV 파트를 순서대로 병합하여 단일 WAV 반환

참조 음성 고정값:
- 여자: ref_female.wav / "저, 책상을 사러 왔는데요."
- 남자: ref_male.wav  / "네, 책상은 이쪽에 있습니다."
"""
import json
import wave
import io
import httpx
from typing import Optional
import anthropic

from app.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL
from app.utils.prompt_loader import load_prompt


# ─── 참조 음성 고정 설정 ─────────────────────────────────────────
# GPT-SoVITS 서버에 업로드된 파일 경로와 참조 스크립트 (변경 불가)
SPEAKER_CONFIG: dict[str, dict] = {
    "여자": {
        "ref_audio_path": "ref_female.wav",
        "prompt_text": "저, 책상을 사러 왔는데요.",
        "prompt_lang": "ko",
    },
    "남자": {
        "ref_audio_path": "ref_male.wav",
        "prompt_text": "네, 책상은 이쪽에 있습니다.",
        "prompt_lang": "ko",
    },
}

# ─── Claude 클라이언트 싱글턴 ─────────────────────────────────────
_anthropic_client: Optional[anthropic.AsyncAnthropic] = None

# ─── 프롬프트 로드 ───────────────────────────────────────────────
_TTS_ANALYZE_PROMPT = load_prompt("tts_script_analyze")


def _get_anthropic_client() -> anthropic.AsyncAnthropic:
    """
    AsyncAnthropic 클라이언트 싱글턴을 반환한다.
    API 키가 없으면 ValueError를 발생시킨다.
    """
    global _anthropic_client
    if _anthropic_client is None:
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")
        _anthropic_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    return _anthropic_client


# ─── Claude API: 스크립트 분석 ───────────────────────────────────

async def analyze_script_with_claude(text: str) -> list[dict]:
    """
    Claude API에 텍스트를 전달하여 TTS 스크립트를 분석한다.
    화자 판별, 빈칸/지문 null 처리, ref_audio 매핑을 수행한다.

    Args:
        text: 분석할 TOPIK 문항 텍스트

    Returns:
        segments 목록 — [{ speaker, ref_audio, text | null }, ...]

    Raises:
        ValueError: API 키 미설정, JSON 파싱 실패
    """
    client = _get_anthropic_client()

    # 프롬프트의 {TEXT} 자리에 실제 텍스트 치환
    prompt = _TTS_ANALYZE_PROMPT.replace("{TEXT}", text)

    response = await client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()

    # Claude 응답 JSON 파싱
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude 응답 JSON 파싱 실패: {e}\n원문: {raw}")

    segments = result.get("segments", [])
    if not segments:
        raise ValueError("Claude가 빈 segments를 반환했습니다.")

    return segments


# ─── GPT-SoVITS 호출 ─────────────────────────────────────────────

async def _call_gpt_sovits(
    gpt_sovits_url: str,
    text: str,
    ref_audio: str,
    params: dict,
) -> bytes:
    """
    GPT-SoVITS /tts 엔드포인트를 호출하여 WAV 바이트를 반환한다.
    ref_audio ("남자" | "여자")로 SPEAKER_CONFIG에서 참조 음성을 조회한다.

    Args:
        gpt_sovits_url: GPT-SoVITS API 서버 URL
        text: 변환할 텍스트
        ref_audio: "남자" 또는 "여자"
        params: 생성 파라미터 dict

    Returns:
        WAV 오디오 바이트
    """
    # ref_audio가 SPEAKER_CONFIG에 없으면 여자로 폴백
    speaker_cfg = SPEAKER_CONFIG.get(ref_audio, SPEAKER_CONFIG["여자"])

    request_body = {
        "text": text,
        "text_lang": params.get("text_lang", "ko"),
        "ref_audio_path": speaker_cfg["ref_audio_path"],
        "prompt_text": speaker_cfg["prompt_text"],
        "prompt_lang": speaker_cfg["prompt_lang"],
        "top_k": params.get("top_k", 15),
        "top_p": params.get("top_p", 1.0),
        "temperature": params.get("temperature", 1.0),
        "speed_factor": params.get("speed_factor", 1.0),
        "text_split_method": params.get("text_split_method", "cut5"),
        "seed": params.get("seed", -1),
        "batch_size": params.get("batch_size", 1),
        "fragment_interval": params.get("fragment_interval", 0.3),
        "repetition_penalty": params.get("repetition_penalty", 1.35),
        "parallel_infer": params.get("parallel_infer", True),
        "super_sampling": params.get("super_sampling", False),
        # 병합을 위해 항상 WAV로 수신
        "media_type": "wav",
        "streaming_mode": params.get("streaming_mode", False),
    }

    # 스트리밍 모드 전용 파라미터
    if params.get("streaming_mode"):
        request_body["overlap_length"] = params.get("overlap_length", 2)
        request_body["min_chunk_length"] = params.get("min_chunk_length", 16)

    url = gpt_sovits_url.rstrip("/") + "/tts"

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, json=request_body)
        response.raise_for_status()
        return response.content


# ─── WAV 병합 ────────────────────────────────────────────────────

def merge_wav_bytes(wav_bytes_list: list[bytes]) -> bytes:
    """
    여러 WAV 바이트를 하나의 WAV 파일로 순서대로 병합한다.
    Python 표준 라이브러리 wave 모듈 사용 (외부 의존성 없음).
    모든 WAV가 동일한 샘플레이트/채널/비트깊이여야 한다.

    Args:
        wav_bytes_list: 순서대로 병합할 WAV 바이트 목록

    Returns:
        병합된 WAV 바이트
    """
    output = io.BytesIO()
    params = None
    all_frames: list[bytes] = []

    for wav_bytes in wav_bytes_list:
        buf = io.BytesIO(wav_bytes)
        with wave.open(buf, "rb") as w:
            if params is None:
                params = w.getparams()
            all_frames.append(w.readframes(w.getnframes()))

    with wave.open(output, "wb") as out_wav:
        out_wav.setparams(params)
        for frames in all_frames:
            out_wav.writeframes(frames)

    return output.getvalue()


# ─── 메인 진입점 ──────────────────────────────────────────────────

async def generate_tts(
    text: str,
    gpt_sovits_url: str,
    params: dict,
) -> bytes:
    """
    텍스트를 TTS로 변환하여 WAV 바이트를 반환한다.

    처리 흐름:
    1. Claude API로 텍스트 분석 → segments (화자/ref_audio/정제텍스트)
    2. text가 null인 세그먼트는 스킵
    3. 유효한 세그먼트를 순서대로 GPT-SoVITS 호출
    4. 결과 WAV 파트를 병합하여 반환

    Args:
        text: 변환할 텍스트 (화자 접두사 포함 가능)
        gpt_sovits_url: GPT-SoVITS API 서버 URL
        params: 생성 파라미터 dict

    Returns:
        병합된 WAV 오디오 바이트
    """
    # Step 1: Claude API로 스크립트 분석
    segments = await analyze_script_with_claude(text)

    # Step 2: null 세그먼트 필터링 후 GPT-SoVITS 순차 호출
    wav_parts: list[bytes] = []
    for seg in segments:
        seg_text = seg.get("text")
        if not seg_text or not seg_text.strip():
            # 빈칸/지문/null 세그먼트 스킵
            continue

        ref_audio = seg.get("ref_audio", "여자")
        wav = await _call_gpt_sovits(
            gpt_sovits_url=gpt_sovits_url,
            text=seg_text,
            ref_audio=ref_audio,
            params=params,
        )
        wav_parts.append(wav)

    if not wav_parts:
        raise ValueError("TTS 생성 가능한 텍스트가 없습니다. (전체 빈칸 또는 지문으로만 구성)")

    # Step 3: WAV 파트가 1개면 병합 불필요, 2개 이상이면 병합
    if len(wav_parts) == 1:
        return wav_parts[0]

    return merge_wav_bytes(wav_parts)
