from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import os
import json
import shutil
from pathlib import Path

router = APIRouter()

# 음성 데이터 저장 경로
VOICE_DATA_DIR = Path("../data/voice_models")
VOICE_DATA_DIR.mkdir(parents=True, exist_ok=True)

# 기본 학습 문장 (40개)
TRAINING_SENTENCES = [
    "안녕하세요. 반갑습니다.",
    "오늘 날씨가 정말 좋네요.",
    "이것은 인공지능 음성 학습 시스템입니다.",
    "여러분의 목소리를 학습하고 있습니다.",
    "감사합니다. 수고하셨습니다.",
    "네, 알겠습니다.",
    "아니요, 괜찮습니다.",
    "좋은 아침입니다.",
    "안녕히 가세요.",
    "다시 한번 말씀해 주시겠어요?",
    "이해가 되지 않습니다.",
    "천천히 말씀해 주세요.",
    "빠르게 진행하겠습니다.",
    "잠시만 기다려 주세요.",
    "준비가 완료되었습니다.",
    "시작하겠습니다.",
    "종료하겠습니다.",
    "확인해 주세요.",
    "저장되었습니다.",
    "삭제하시겠습니까?",
    "새로운 기능을 소개합니다.",
    "이번 주제는 무엇인가요?",
    "궁금한 점이 있으신가요?",
    "질문에 답변드리겠습니다.",
    "설명을 시작하겠습니다.",
    "중요한 내용입니다.",
    "주의 깊게 들어주세요.",
    "다음 단계로 넘어가겠습니다.",
    "이전 내용을 복습하겠습니다.",
    "오늘의 학습을 마치겠습니다.",
    "훌륭한 결과입니다.",
    "계속 진행해 주세요.",
    "잘하고 계십니다.",
    "조금만 더 노력하세요.",
    "완벽합니다.",
    "문제가 발생했습니다.",
    "해결 방법을 찾았습니다.",
    "다시 시도해 보세요.",
    "성공적으로 완료되었습니다.",
    "모든 작업이 끝났습니다."
]

@router.get("/sentences")
async def get_training_sentences():
    """학습용 문장 목록 반환"""
    return {
        "total": len(TRAINING_SENTENCES),
        "sentences": TRAINING_SENTENCES
    }

@router.post("/upload/{user_id}")
async def upload_voice_sample(
    user_id: str,
    sentence_index: int,
    file: UploadFile = File(...)
):
    """음성 샘플 업로드"""
    try:
        # 사용자별 디렉토리 생성
        user_dir = VOICE_DATA_DIR / user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        # 파일 저장
        file_path = user_dir / f"sample_{sentence_index}.wav"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "status": "success",
            "message": f"Sample {sentence_index} uploaded successfully",
            "file_path": str(file_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/progress/{user_id}")
async def get_training_progress(user_id: str):
    """학습 진행도 확인"""
    user_dir = VOICE_DATA_DIR / user_id
    if not user_dir.exists():
        return {"progress": 0, "total": len(TRAINING_SENTENCES), "completed": []}

    # 업로드된 파일 확인
    uploaded_files = list(user_dir.glob("sample_*.wav"))
    completed_indices = [
        int(f.stem.split("_")[1]) for f in uploaded_files
    ]

    return {
        "progress": len(completed_indices),
        "total": len(TRAINING_SENTENCES),
        "completed": sorted(completed_indices)
    }

@router.post("/train/{user_id}")
async def train_voice_model(user_id: str):
    """음성 모델 학습 시작"""
    try:
        user_dir = VOICE_DATA_DIR / user_id
        if not user_dir.exists():
            raise HTTPException(status_code=404, detail="No voice samples found")

        # 업로드된 파일 확인
        uploaded_files = list(user_dir.glob("sample_*.wav"))
        if len(uploaded_files) < 30:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient samples. Need at least 30, got {len(uploaded_files)}"
            )

        # TODO: 실제 TTS 모델 파인튜닝 로직
        # Coqui XTTS-v2를 사용한 음성 복제 모델 학습

        # 메타데이터 저장
        metadata = {
            "user_id": user_id,
            "samples_count": len(uploaded_files),
            "status": "trained",
            "model_path": f"../data/voice_models/{user_id}/model.pth"
        }

        with open(user_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        return {
            "status": "success",
            "message": "Voice model training completed",
            "metadata": metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/reset/{user_id}")
async def reset_training_data(user_id: str):
    """학습 데이터 초기화"""
    try:
        user_dir = VOICE_DATA_DIR / user_id
        if user_dir.exists():
            shutil.rmtree(user_dir)
        return {"status": "success", "message": "Training data reset"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
