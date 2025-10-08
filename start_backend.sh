#!/bin/bash

echo "🚀 EBS AI Backend 시작..."

# 백엔드 디렉토리로 이동
cd backend

# Python 가상환경 확인 및 생성
if [ ! -d "venv" ]; then
    echo "📦 Python 가상환경 생성 중..."
    python3 -m venv venv
fi

# 가상환경 활성화
echo "🔧 가상환경 활성화..."
source venv/bin/activate

# 의존성 설치
echo "📥 의존성 설치 중..."
pip install -r requirements.txt

# 필요한 디렉토리 생성
mkdir -p ../data/voice_models
mkdir -p ../data/uploads
mkdir -p ../data/outputs

# Coqui TTS 사용 약관 자동 동의
export COQUI_TOS_AGREED=1

# FastAPI 서버 시작
echo "✅ 서버 시작 (http://localhost:8000)"
uvicorn main:app --reload --reload-dir . --reload-exclude 'venv/*' --host 0.0.0.0 --port 8000
