from fastapi import APIRouter, HTTPException, Form
from pydantic import BaseModel
from pathlib import Path
import torch
from TTS.api import TTS
import os
import json

router = APIRouter()

# 생성된 오디오 저장 경로
OUTPUT_DIR = Path("../data/outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

VOICE_MODEL_DIR = Path("../data/voice_models")

# TTS 모델 (lazy loading)
tts_model = None

def get_tts_model():
    global tts_model
    if tts_model is None:
        # Coqui XTTS-v2 모델 사용 (다국어 + 음성 복제 지원)
        tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        if torch.cuda.is_available():
            tts_model = tts_model.to("cuda")
    return tts_model

class TTSRequest(BaseModel):
    text: str
    user_id: str
    language: str = "ko"
    output_filename: str = "output.wav"

@router.post("/synthesize")
async def synthesize_speech(
    text: str = Form(...),
    user_id: str = Form(...),
    language: str = Form("ko"),
    output_filename: str = Form("output.wav")
):
    """학습된 음성으로 텍스트를 음성으로 변환"""
    try:
        # 사용자 음성 모델 확인
        user_voice_dir = VOICE_MODEL_DIR / user_id
        if not user_voice_dir.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Voice model not found for user {user_id}"
            )

        # 메타데이터 확인
        metadata_path = user_voice_dir / "metadata.json"
        if not metadata_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Voice model not trained yet"
            )

        # 참조 음성 파일 (첫 번째 샘플 사용)
        reference_audio = list(user_voice_dir.glob("sample_*.wav"))[0]

        # TTS 모델 로드
        model = get_tts_model()

        # 출력 파일 경로
        output_path = OUTPUT_DIR / output_filename

        # 음성 합성 (음성 복제)
        model.tts_to_file(
            text=text,
            file_path=str(output_path),
            speaker_wav=str(reference_audio),
            language=language
        )

        return {
            "status": "success",
            "output_file": str(output_path),
            "text": text,
            "language": language
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/synthesize-segments")
async def synthesize_segments(
    segments: str = Form(...),  # JSON string
    user_id: str = Form(...),
    language: str = Form("ko")
):
    """세그먼트별로 음성 합성 (자막 타이밍 맞춤)"""
    try:
        import json
        segments_data = json.loads(segments)

        # 사용자 음성 모델 확인
        user_voice_dir = VOICE_MODEL_DIR / user_id
        if not user_voice_dir.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Voice model not found for user {user_id}"
            )

        reference_audio = list(user_voice_dir.glob("sample_*.wav"))[0]
        model = get_tts_model()

        synthesized_segments = []
        for i, segment in enumerate(segments_data):
            output_filename = f"segment_{i}_{segment.get('id', i)}.wav"
            output_path = OUTPUT_DIR / output_filename

            model.tts_to_file(
                text=segment["translated_text"],
                file_path=str(output_path),
                speaker_wav=str(reference_audio),
                language=language
            )

            synthesized_segments.append({
                "id": segment.get("id"),
                "start": segment.get("start"),
                "end": segment.get("end"),
                "text": segment["translated_text"],
                "audio_file": str(output_path)
            })

        return {
            "status": "success",
            "segments": synthesized_segments,
            "language": language
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/voices")
async def list_available_voices():
    """학습된 음성 모델 목록"""
    try:
        voices = []
        for user_dir in VOICE_MODEL_DIR.iterdir():
            if user_dir.is_dir():
                metadata_path = user_dir / "metadata.json"
                if metadata_path.exists():
                    with open(metadata_path, "r") as f:
                        metadata = json.load(f)
                        voices.append({
                            "user_id": user_dir.name,
                            "status": metadata.get("status"),
                            "samples_count": metadata.get("samples_count")
                        })
        return {"voices": voices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
