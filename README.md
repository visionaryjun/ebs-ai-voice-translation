# EBS AI 음성학습 및 번역 시스템

## 기능
1. **AI 음성학습** - 사용자 음성 녹음 및 AI 학습 (40-50개 문장)
2. **STT** - 유튜브 URL/영상 업로드 → 다국어 텍스트 변환
3. **번역** - 인도네시아어, 베트남어 등 다국어 지원
4. **TTS** - 학습된 음성으로 번역된 텍스트 음성 변환
5. **영상 출력** - 원본 영상에 학습된 음성 오버레이

## 기술 스택
- **Backend**: FastAPI, Python 3.9+
- **Frontend**: React
- **AI/ML**:
  - Whisper (STT)
  - GoogleTranslate/LibreTranslate (번역)
  - Coqui XTTS-v2 (음성 복제 및 TTS)
  - yt-dlp (유튜브 다운로드)

## 설치 방법

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm start
```

## 사용 방법
1. AI 음성학습 페이지에서 40-50개 문장 녹음
2. STT 페이지에서 유튜브 URL 입력 또는 영상 업로드
3. 원하는 번역 언어 선택
4. 학습된 음성으로 변환된 영상 확인
