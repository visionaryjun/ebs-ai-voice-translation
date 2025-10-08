from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from deep_translator import GoogleTranslator
from typing import List, Dict

router = APIRouter()

# 지원 언어
SUPPORTED_LANGUAGES = {
    "ko": "Korean",
    "en": "English",
    "id": "Indonesian",
    "vi": "Vietnamese",
    "ja": "Japanese",
    "zh-CN": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)",
    "th": "Thai",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "ru": "Russian",
    "ar": "Arabic",
    "hi": "Hindi"
}

class TranslationRequest(BaseModel):
    text: str
    source_lang: str = "auto"
    target_lang: str

class SegmentTranslationRequest(BaseModel):
    segments: List[Dict]
    source_lang: str = "auto"
    target_lang: str

@router.get("/languages")
async def get_supported_languages():
    """지원 언어 목록 반환"""
    return {"languages": SUPPORTED_LANGUAGES}

@router.post("/translate")
async def translate_text(request: TranslationRequest):
    """텍스트 번역"""
    try:
        translator = GoogleTranslator(
            source=request.source_lang,
            target=request.target_lang
        )
        translated = translator.translate(request.text)

        return {
            "status": "success",
            "source_lang": request.source_lang,
            "target_lang": request.target_lang,
            "original_text": request.text,
            "translated_text": translated
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/translate-segments")
async def translate_segments(request: SegmentTranslationRequest):
    """세그먼트별 번역 (자막용)"""
    try:
        translator = GoogleTranslator(
            source=request.source_lang,
            target=request.target_lang
        )

        translated_segments = []
        for segment in request.segments:
            translated_text = translator.translate(segment["text"])
            translated_segments.append({
                "id": segment.get("id"),
                "start": segment.get("start"),
                "end": segment.get("end"),
                "original_text": segment["text"],
                "translated_text": translated_text
            })

        return {
            "status": "success",
            "source_lang": request.source_lang,
            "target_lang": request.target_lang,
            "segments": translated_segments
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-translate")
async def batch_translate(
    texts: List[str],
    source_lang: str = "auto",
    target_lang: str = "en"
):
    """여러 텍스트 일괄 번역"""
    try:
        translator = GoogleTranslator(
            source=source_lang,
            target=target_lang
        )

        translations = []
        for text in texts:
            translated = translator.translate(text)
            translations.append({
                "original": text,
                "translated": translated
            })

        return {
            "status": "success",
            "source_lang": source_lang,
            "target_lang": target_lang,
            "translations": translations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
