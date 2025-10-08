from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pathlib import Path
import subprocess
import whisper
import os
import re
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# 업로드 파일 저장 경로 (절대 경로 사용)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Whisper 모델 로드 (lazy loading)
whisper_model = None

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        logger.info("Loading Whisper model...")
        whisper_model = whisper.load_model("base")
        logger.info("Whisper model loaded successfully")
    return whisper_model

def extract_video_id(url: str) -> str:
    """유튜브 URL에서 video ID 추출"""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'^([0-9A-Za-z_-]{11})$'
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    raise ValueError(f"Could not extract video ID from URL: {url}")

@router.post("/youtube")
async def transcribe_youtube(url: str = Form(...)):
    """유튜브 URL에서 음성 추출 및 텍스트 변환"""
    try:
        logger.info(f"Processing YouTube URL: {url}")

        # 유튜브 비디오 ID 추출
        video_id = extract_video_id(url)
        logger.info(f"Extracted video ID: {video_id}")

        output_template = str(UPLOAD_DIR / f"{video_id}.%(ext)s")

        # yt-dlp로 오디오 다운로드 (YouTube 차단 회피 옵션 추가)
        yt_command = [
            "yt-dlp",
            "-f", "bestaudio/best",
            "--extract-audio",
            "--audio-format", "wav",
            "--audio-quality", "0",
            "-o", output_template,
            "--no-playlist",
            # YouTube 차단 회피 옵션
            "--cookies-from-browser", "chrome",  # Chrome 브라우저 쿠키 사용
            "--user-agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "--extractor-args", "youtube:player_client=web,mweb",
            "--no-check-certificates",
            url
        ]

        logger.info(f"Running yt-dlp command: {' '.join(yt_command)}")
        result = subprocess.run(
            yt_command,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            logger.error(f"yt-dlp error: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"YouTube download failed: {result.stderr}"
            )

        logger.info("YouTube download completed")

        # 생성된 오디오 파일 찾기
        audio_file = UPLOAD_DIR / f"{video_id}.wav"

        if not audio_file.exists():
            logger.error(f"Audio file not found: {audio_file}")
            raise HTTPException(
                status_code=500,
                detail=f"Audio file was not created: {audio_file}"
            )

        logger.info(f"Audio file found: {audio_file}")

        # Whisper로 음성 인식
        logger.info("Starting transcription...")
        model = get_whisper_model()
        transcription_result = model.transcribe(str(audio_file))

        logger.info("Transcription completed")

        return {
            "status": "success",
            "video_id": video_id,
            "text": transcription_result["text"],
            "segments": transcription_result["segments"],
            "language": transcription_result["language"],
            "audio_file": str(audio_file)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in transcribe_youtube: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/upload")
async def transcribe_upload(file: UploadFile = File(...)):
    """업로드된 비디오/오디오 파일을 텍스트로 변환"""
    try:
        logger.info(f"Uploading file: {file.filename}")

        # 파일 저장
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        logger.info(f"File saved to: {file_path}")

        # 비디오에서 오디오 추출 (필요시)
        audio_path = file_path
        if file.filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
            audio_path = UPLOAD_DIR / f"{file_path.stem}.wav"
            logger.info(f"Extracting audio to: {audio_path}")

            ffmpeg_command = [
                "ffmpeg", "-y", "-i", str(file_path),
                "-vn", "-acodec", "pcm_s16le",
                "-ar", "16000", "-ac", "1",
                str(audio_path)
            ]
            result = subprocess.run(
                ffmpeg_command,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Audio extraction failed: {result.stderr}"
                )

            logger.info("Audio extraction completed")

        # Whisper로 음성 인식
        logger.info("Starting transcription...")
        model = get_whisper_model()
        transcription_result = model.transcribe(str(audio_path))

        logger.info("Transcription completed")

        return {
            "status": "success",
            "filename": file.filename,
            "text": transcription_result["text"],
            "segments": transcription_result["segments"],
            "language": transcription_result["language"],
            "audio_file": str(audio_path)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in transcribe_upload: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

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
