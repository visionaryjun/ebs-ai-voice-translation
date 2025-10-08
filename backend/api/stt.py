from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pathlib import Path
import subprocess
import whisper
import os
import re
import logging
import glob

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

        video_output = str(UPLOAD_DIR / f"{video_id}.mp4")
        audio_output = str(UPLOAD_DIR / f"{video_id}.wav")

        # Step 1: yt-dlp로 비디오 다운로드
        yt_command = [
            "yt-dlp",
            "-f", "best[height<=720]",  # 720p 이하로 제한 (빠른 다운로드)
            "-o", video_output,
            "--no-playlist",
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "--extractor-args", "youtube:player_client=android",
            url
        ]

        logger.info(f"Downloading video: {' '.join(yt_command)}")
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

        logger.info("Video download completed")

        # 다운로드된 파일 확인
        if not os.path.exists(video_output):
            # glob으로 실제 파일 찾기
            possible_files = glob.glob(str(UPLOAD_DIR / f"{video_id}.*"))
            logger.info(f"Looking for files: {possible_files}")

            if not possible_files:
                raise HTTPException(
                    status_code=500,
                    detail=f"Video file not found after download"
                )

            video_output = possible_files[0]
            logger.info(f"Found video file: {video_output}")

        # Step 2: FFmpeg로 오디오 추출 및 WAV 변환
        logger.info("Extracting audio with FFmpeg...")
        ffmpeg_command = [
            "ffmpeg", "-y",
            "-i", video_output,
            "-vn",  # 비디오 제거
            "-acodec", "pcm_s16le",  # WAV 코덱
            "-ar", "16000",  # 16kHz 샘플레이트 (Whisper 최적)
            "-ac", "1",  # 모노
            audio_output
        ]

        logger.info(f"Running FFmpeg: {' '.join(ffmpeg_command)}")
        ffmpeg_result = subprocess.run(
            ffmpeg_command,
            capture_output=True,
            text=True,
            check=False
        )

        if ffmpeg_result.returncode != 0:
            logger.error(f"FFmpeg error: {ffmpeg_result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"Audio extraction failed: {ffmpeg_result.stderr}"
            )

        logger.info("Audio extraction completed")

        # 오디오 파일 확인
        if not os.path.exists(audio_output):
            raise HTTPException(
                status_code=500,
                detail=f"Audio file was not created: {audio_output}"
            )

        logger.info(f"Audio file ready: {audio_output}")

        # Whisper로 음성 인식
        logger.info("Starting transcription...")
        model = get_whisper_model()
        transcription_result = model.transcribe(audio_output)

        logger.info("Transcription completed")

        return {
            "status": "success",
            "video_id": video_id,
            "text": transcription_result["text"],
            "segments": transcription_result["segments"],
            "language": transcription_result["language"],
            "audio_file": audio_output
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
