# 설치 및 실행 가이드

## 📋 시스템 요구사항

- **Python**: 3.9 이상
- **Node.js**: 16.x 이상
- **FFmpeg**: 비디오/오디오 처리를 위해 필요
- **최소 RAM**: 8GB (권장: 16GB)
- **디스크 공간**: 최소 10GB

## 🔧 사전 설치

### 1. FFmpeg 설치

#### macOS
```bash
brew install ffmpeg
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install ffmpeg
```

#### Windows
[FFmpeg 공식 사이트](https://ffmpeg.org/download.html)에서 다운로드 후 PATH 설정

### 2. Python 가상환경 도구
```bash
python3 -m pip install --upgrade pip
```

## 🚀 빠른 시작

### 방법 1: 자동 실행 스크립트 사용 (권장)

#### 1단계: 백엔드 서버 시작
터미널 1에서:
```bash
./start_backend.sh
```

#### 2단계: 프론트엔드 서버 시작
터미널 2에서:
```bash
./start_frontend.sh
```

### 방법 2: 수동 설치 및 실행

#### 백엔드 설정

1. 백엔드 디렉토리로 이동
```bash
cd backend
```

2. Python 가상환경 생성
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. 필요한 디렉토리 생성
```bash
mkdir -p ../data/voice_models
mkdir -p ../data/uploads
mkdir -p ../data/outputs
```

5. 서버 시작
```bash
uvicorn main:app --reload
```

서버 실행 확인: http://localhost:8000

#### 프론트엔드 설정

1. 프론트엔드 디렉토리로 이동
```bash
cd frontend
```

2. Node 패키지 설치
```bash
npm install
```

3. React 앱 시작
```bash
npm start
```

앱 실행 확인: http://localhost:3000

## 📱 사용 방법

### 1. AI 음성학습 (페이지 1)

1. 상단에 고유한 User ID 입력 (예: "user001")
2. "1. AI 음성학습" 페이지 선택
3. 표시되는 문장을 읽으며 녹음
4. 최소 30개 문장 녹음 완료
5. "🧠 모델 학습 시작" 버튼 클릭
6. 학습 완료까지 대기 (수 분 소요)

### 2. 영상 처리 (페이지 2)

1. "2. STT & 번역 & TTS" 페이지 선택
2. 번역할 언어 선택 (인도네시아어/베트남어 등)
3. 옵션 선택:
   - **유튜브 URL 입력**: 유튜브 링크 붙여넣기
   - **파일 업로드**: 로컬 비디오 파일 선택
4. "🚀 처리 시작" 버튼 클릭
5. 진행 상황 확인 (STT → 번역 → TTS → 비디오 결합)

### 3. 결과 확인 (페이지 3)

1. "3. 결과 확인" 페이지 선택
2. 생성된 파일 목록에서 원하는 파일 클릭
3. 비디오 미리보기로 결과 확인
4. 다운로드 버튼으로 파일 저장

## 🔍 문제 해결

### 문제: "마이크 접근 실패"
- **해결**: 브라우저 설정에서 마이크 권한 허용
- Chrome: 설정 → 개인정보 및 보안 → 사이트 설정 → 마이크

### 문제: "ffmpeg not found"
- **해결**: FFmpeg 설치 후 PATH 환경변수에 추가

### 문제: "CUDA out of memory"
- **해결**: CPU 모드로 실행하거나 더 작은 모델 사용
- `requirements.txt`에서 torch를 CPU 버전으로 변경

### 문제: "Port already in use"
- **해결**: 다른 포트 사용
```bash
# 백엔드
uvicorn main:app --reload --port 8001

# 프론트엔드
PORT=3001 npm start
```

### 문제: 모델 다운로드 느림
- **해결**: 첫 실행 시 Whisper와 TTS 모델이 자동으로 다운로드됩니다 (수 GB)
- 안정적인 인터넷 연결 필요

## 📚 API 문서

백엔드 서버 실행 후 다음 URL에서 API 문서 확인:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## ⚙️ 고급 설정

### GPU 가속 사용

CUDA가 설치된 시스템에서는 자동으로 GPU 사용:
```bash
# CUDA 버전 확인
nvidia-smi

# PyTorch GPU 버전 설치
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 다른 TTS 모델 사용

`backend/api/tts.py`에서 모델 변경 가능:
```python
tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
# 또는
tts_model = TTS("tts_models/ko/fairseq/vits")  # 한국어 전용
```

## 🎯 성능 최적화

1. **더 빠른 STT**: Whisper "tiny" 모델 사용
   ```python
   whisper_model = whisper.load_model("tiny")
   ```

2. **메모리 사용량 감소**: 배치 처리 크기 조정

3. **프로덕션 배포**: Gunicorn 또는 Docker 사용

## 📞 지원

문제가 발생하면 이슈를 생성하거나 README.md를 참조하세요.
