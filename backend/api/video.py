from fastapi import APIRouter, HTTPException, Form
from pathlib import Path
import subprocess
import json
from typing import List, Dict

router = APIRouter()

OUTPUT_DIR = Path("../data/outputs")
UPLOAD_DIR = Path("../data/uploads")

@router.post("/combine")
async def combine_video_audio(
    video_path: str = Form(...),
    audio_segments: str = Form(...),  # JSON string
    output_filename: str = Form("final_output.mp4")
):
    """비디오와 오디오 세그먼트 결합"""
    try:
        segments_data = json.loads(audio_segments)

        # 모든 오디오 세그먼트 결합
        audio_files = [seg["audio_file"] for seg in segments_data]

        # concat 파일 생성
        concat_file = OUTPUT_DIR / "concat_list.txt"
        with open(concat_file, "w") as f:
            for audio_file in audio_files:
                f.write(f"file '{audio_file}'\n")

        # 오디오 파일 결합
        combined_audio = OUTPUT_DIR / "combined_audio.wav"
        concat_command = [
            "ffmpeg", "-f", "concat", "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            str(combined_audio)
        ]
        subprocess.run(concat_command, check=True)

        # 비디오와 결합된 오디오 합치기
        output_path = OUTPUT_DIR / output_filename
        combine_command = [
            "ffmpeg",
            "-i", video_path,
            "-i", str(combined_audio),
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            str(output_path)
        ]
        subprocess.run(combine_command, check=True)

        return {
            "status": "success",
            "output_file": str(output_path),
            "segments_count": len(segments_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-pipeline")
async def process_full_pipeline(
    youtube_url: str = Form(None),
    video_file: str = Form(None),
    user_id: str = Form(...),
    target_language: str = Form(...),
    output_filename: str = Form("final_output.mp4")
):
    """전체 파이프라인 실행 (STT → 번역 → TTS → 비디오 결합)"""
    try:
        from . import stt, translation, tts

        # 1. STT: 유튜브 또는 업로드 파일에서 텍스트 추출
        if youtube_url:
            stt_result = await stt.transcribe_youtube(url=youtube_url)
            video_path = f"{UPLOAD_DIR}/{stt_result['video_id']}.mp4"
        elif video_file:
            # 이미 업로드된 파일 사용
            with open(video_file, "rb") as f:
                # UploadFile 객체 생성 대신 파일 경로 직접 사용
                pass
            stt_result = {"segments": [], "language": "auto"}  # Placeholder
        else:
            raise HTTPException(status_code=400, detail="Provide either youtube_url or video_file")

        # 2. 번역: 세그먼트별 번역
        translate_request = translation.SegmentTranslationRequest(
            segments=stt_result["segments"],
            source_lang=stt_result.get("language", "auto"),
            target_lang=target_language
        )
        translation_result = await translation.translate_segments(translate_request)

        # 3. TTS: 번역된 텍스트를 학습된 음성으로 변환
        tts_result = await tts.synthesize_segments(
            segments=json.dumps(translation_result["segments"]),
            user_id=user_id,
            language=target_language
        )

        # 4. 비디오 결합
        final_result = await combine_video_audio(
            video_path=video_path,
            audio_segments=json.dumps(tts_result["segments"]),
            output_filename=output_filename
        )

        return {
            "status": "success",
            "message": "Full pipeline completed",
            "steps": {
                "stt": "completed",
                "translation": "completed",
                "tts": "completed",
                "video_combine": "completed"
            },
            "output_file": final_result["output_file"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/outputs")
async def list_outputs():
    """생성된 결과 파일 목록"""
    try:
        outputs = []
        for file_path in OUTPUT_DIR.glob("*.mp4"):
            outputs.append({
                "filename": file_path.name,
                "path": str(file_path),
                "size": file_path.stat().st_size
            })
        return {"outputs": outputs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
