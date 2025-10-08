from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pathlib import Path
import subprocess
import whisper
import os

router = APIRouter()

# 업로드 파일 저장 경로
UPLOAD_DIR = Path("../data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Whisper 모델 로드 (lazy loading)
whisper_model = None

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        whisper_model = whisper.load_model("base")
    return whisper_model

@router.post("/youtube")
async def transcribe_youtube(url: str = Form(...)):
    """유튜브 URL에서 음성 추출 및 텍스트 변환"""
    try:
        # 유튜브 비디오 다운로드
        video_id = url.split("v=")[-1].split("&")[0]
        output_path = UPLOAD_DIR / f"{video_id}"

        # yt-dlp로 비디오 다운로드
        yt_command = [
            "yt-dlp",
            "-f", "bestaudio",
            "-x", "--audio-format", "wav",
            "-o", f"{output_path}.%(ext)s",
            url
        ]

        subprocess.run(yt_command, check=True)

        # 음성 파일 경로
        audio_file = f"{output_path}.wav"

        # Whisper로 음성 인식
        model = get_whisper_model()
        result = model.transcribe(audio_file)

        return {
            "status": "success",
            "video_id": video_id,
            "text": result["text"],
            "segments": result["segments"],
            "language": result["language"],
            "audio_file": audio_file
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def transcribe_upload(file: UploadFile = File(...)):
    """업로드된 비디오/오디오 파일을 텍스트로 변환"""
    try:
        # 파일 저장
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # 비디오에서 오디오 추출 (필요시)
        audio_path = file_path
        if file.filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
            audio_path = UPLOAD_DIR / f"{file_path.stem}.wav"
            ffmpeg_command = [
                "ffmpeg", "-i", str(file_path),
                "-vn", "-acodec", "pcm_s16le",
                "-ar", "16000", "-ac", "1",
                str(audio_path)
            ]
            subprocess.run(ffmpeg_command, check=True)

        # Whisper로 음성 인식
        model = get_whisper_model()
        result = model.transcribe(str(audio_path))

        return {
            "status": "success",
            "filename": file.filename,
            "text": result["text"],
            "segments": result["segments"],
            "language": result["language"],
            "audio_file": str(audio_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transcribe-file")
async def transcribe_audio_file(audio_path: str = Form(...)):
    """특정 오디오 파일 경로에서 텍스트 추출"""
    try:
        if not os.path.exists(audio_path):
            raise HTTPException(status_code=404, detail="Audio file not found")

        model = get_whisper_model()
        result = model.transcribe(audio_path)

        return {
            "status": "success",
            "text": result["text"],
            "segments": result["segments"],
            "language": result["language"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
