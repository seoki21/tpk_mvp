"""
TTS 생성 API 라우터
GPT-SoVITS API를 통한 텍스트 → 음성 변환 엔드포인트를 정의한다.
화자 자동 감지(단일/복수)와 WAV 병합을 서비스 레이어에서 처리한다.
URL 접두사: /api/v1/tts
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from app.utils.auth import get_current_admin
from app.services import tts as tts_service

router = APIRouter(
    prefix="/api/v1/tts",
    tags=["TTS 생성"],
    dependencies=[Depends(get_current_admin)],
)


class TtsGenerateRequest(BaseModel):
    """TTS 생성 요청 파라미터 — GPT-SoVITS /tts 엔드포인트와 동일한 구조"""

    # 변환 대상 텍스트 (화자 접두사 포함 가능)
    text: str
    # GPT-SoVITS 서버 URL
    gpt_sovits_url: str = "http://127.0.0.1:9880"
    # 텍스트 언어
    text_lang: str = "ko"

    # GPT-SoVITS 생성 파라미터
    top_k: int = 15
    top_p: float = 1.0
    temperature: float = 1.0
    speed_factor: float = 1.0
    text_split_method: str = "cut5"
    seed: int = -1
    batch_size: int = 1
    fragment_interval: float = 0.3
    repetition_penalty: float = 1.35
    parallel_infer: bool = True
    super_sampling: bool = False

    # 출력 및 스트리밍 설정
    media_type: str = "wav"
    streaming_mode: bool = False
    overlap_length: int = 2
    min_chunk_length: int = 16


@router.post("/generate")
async def generate_tts(body: TtsGenerateRequest):
    """
    텍스트를 GPT-SoVITS API로 변환하여 WAV 오디오를 반환한다.

    - 단일 화자: 텍스트 전체를 한 번에 변환
    - 복수 화자: 남자:/여자: 접두사로 라인 분리 → 각각 변환 → WAV 병합
    - 참조 음성은 남자(ref_male.wav) / 여자(ref_female.wav) 고정 사용
    """
    params = body.model_dump(exclude={"text", "gpt_sovits_url"})

    try:
        audio_bytes = await tts_service.generate_tts(
            text=body.text,
            gpt_sovits_url=body.gpt_sovits_url,
            params=params,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS 생성 실패: {str(e)}")

    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={"Content-Disposition": "attachment; filename=tts_output.wav"},
    )
