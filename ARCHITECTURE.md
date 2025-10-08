# 시스템 아키텍처

## 📐 전체 구조

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  Voice   │  │  Video   │  │ Results  │                  │
│  │ Training │  │Processing│  │          │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST API
┌────────────────────┴────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   API Routes                          │  │
│  │  /voice  /stt  /translate  /tts  /video             │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   AI/ML Models                        │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │  │
│  │  │ Whisper  │  │  Google  │  │  XTTS-v2 │          │  │
│  │  │  (STT)   │  │Translate │  │  (TTS)   │          │  │
│  │  └──────────┘  └──────────┘  └──────────┘          │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  Media Processing                     │  │
│  │     FFmpeg, yt-dlp, MoviePy, PyDub                   │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────────┐
│                      Data Storage                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Voice Models │  │   Uploads    │  │   Outputs    │     │
│  │   (.wav)     │  │  (.mp4/.wav) │  │    (.mp4)    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 데이터 플로우

### 1. 음성 학습 플로우
```
사용자 → 마이크 녹음 → Frontend (MediaRecorder API)
         ↓
    Audio Blob (WAV)
         ↓
    POST /api/voice/upload/{user_id}
         ↓
    Backend: 파일 저장
         ↓
    data/voice_models/{user_id}/sample_N.wav
         ↓
    POST /api/voice/train/{user_id}
         ↓
    XTTS-v2: 음성 복제 모델 학습
         ↓
    모델 저장 → metadata.json
```

### 2. 영상 처리 플로우 (유튜브)
```
유튜브 URL → POST /api/stt/youtube
         ↓
    yt-dlp: 비디오 다운로드
         ↓
    FFmpeg: 오디오 추출 (.wav)
         ↓
    Whisper: 음성 → 텍스트 + 세그먼트
         ↓
    POST /api/translate/translate-segments
         ↓
    GoogleTranslator: 원본 언어 → 목표 언어
         ↓
    POST /api/tts/synthesize-segments
         ↓
    XTTS-v2: 번역된 텍스트 → 학습된 음성
         ↓
    POST /api/video/combine
         ↓
    FFmpeg: 원본 비디오 + 새 오디오 합성
         ↓
    최종 출력 파일 (.mp4)
```

### 3. 영상 처리 플로우 (파일 업로드)
```
파일 선택 → POST /api/stt/upload
         ↓
    파일 저장 (uploads/)
         ↓
    FFmpeg: 오디오 추출 (비디오인 경우)
         ↓
    [동일한 STT → 번역 → TTS → 결합 과정]
         ↓
    최종 출력 파일
```

## 🧩 컴포넌트 상세

### Frontend 컴포넌트

#### 1. VoiceTraining.js
- **역할**: 음성 녹음 및 학습 인터페이스
- **주요 기능**:
  - MediaRecorder API로 마이크 녹음
  - 40개 문장 순차 녹음
  - 진행도 추적
  - 모델 학습 트리거
- **API 호출**:
  - GET /api/voice/sentences
  - POST /api/voice/upload/{user_id}
  - GET /api/voice/progress/{user_id}
  - POST /api/voice/train/{user_id}

#### 2. VideoProcessing.js
- **역할**: 영상 입력 및 처리 인터페이스
- **주요 기능**:
  - 유튜브 URL 입력
  - 파일 업로드
  - 언어 선택
  - 처리 상태 표시
  - 원본/번역 텍스트 미리보기
- **API 호출**:
  - POST /api/stt/youtube
  - POST /api/stt/upload
  - POST /api/translate/translate-segments
  - POST /api/tts/synthesize-segments
  - POST /api/video/combine

#### 3. Results.js
- **역할**: 결과 파일 조회 및 재생
- **주요 기능**:
  - 생성된 파일 목록 표시
  - 비디오 미리보기
  - 파일 다운로드
- **API 호출**:
  - GET /api/video/outputs

### Backend API 엔드포인트

#### Voice Training API (`/api/voice`)
- `GET /sentences`: 학습용 문장 목록
- `POST /upload/{user_id}`: 음성 샘플 업로드
- `GET /progress/{user_id}`: 학습 진행도 조회
- `POST /train/{user_id}`: 음성 모델 학습 시작
- `DELETE /reset/{user_id}`: 학습 데이터 초기화

#### STT API (`/api/stt`)
- `POST /youtube`: 유튜브 URL → 텍스트
- `POST /upload`: 파일 업로드 → 텍스트
- `POST /transcribe-file`: 기존 파일 → 텍스트

#### Translation API (`/api/translate`)
- `GET /languages`: 지원 언어 목록
- `POST /translate`: 단일 텍스트 번역
- `POST /translate-segments`: 세그먼트별 번역
- `POST /batch-translate`: 일괄 번역

#### TTS API (`/api/tts`)
- `POST /synthesize`: 텍스트 → 학습된 음성
- `POST /synthesize-segments`: 세그먼트별 음성 합성
- `GET /voices`: 학습된 음성 모델 목록

#### Video API (`/api/video`)
- `POST /combine`: 비디오 + 오디오 결합
- `POST /process-pipeline`: 전체 파이프라인 실행
- `GET /outputs`: 결과 파일 목록

## 🤖 AI/ML 모델

### 1. Whisper (OpenAI)
- **역할**: Speech-to-Text (STT)
- **모델**: base (기본) / tiny, small, medium, large 선택 가능
- **기능**:
  - 다국어 음성 인식
  - 타임스탬프 포함 세그먼트 생성
  - 자동 언어 감지
- **입력**: 오디오 파일 (.wav, .mp3, .mp4)
- **출력**: 텍스트 + 세그먼트 (시작/종료 시간)

### 2. Google Translator (deep-translator)
- **역할**: 텍스트 번역
- **지원 언어**: 100+ 언어
- **주요 언어**:
  - Korean (ko)
  - Indonesian (id)
  - Vietnamese (vi)
  - English (en)
  - Japanese (ja)
  - Chinese (zh-CN, zh-TW)
- **입력**: 텍스트 (문자열 또는 세그먼트 배열)
- **출력**: 번역된 텍스트

### 3. Coqui XTTS-v2
- **역할**: Text-to-Speech with Voice Cloning
- **특징**:
  - 다국어 지원 (17개 언어)
  - 음성 복제 (Voice Cloning)
  - 참조 음성 기반 합성
- **입력**:
  - 텍스트
  - 참조 음성 파일 (.wav)
  - 언어 코드
- **출력**: 합성된 음성 (.wav)

## 💾 데이터 구조

### 디렉토리 구조
```
data/
├── voice_models/          # 사용자별 음성 모델
│   └── {user_id}/
│       ├── sample_0.wav
│       ├── sample_1.wav
│       ├── ...
│       ├── model.pth      # 학습된 모델 (선택사항)
│       └── metadata.json  # 모델 메타데이터
│
├── uploads/               # 업로드된 파일
│   ├── {video_id}.mp4
│   ├── {video_id}.wav
│   └── {filename}.mp4
│
└── outputs/               # 생성된 결과 파일
    ├── output_*.mp4       # 최종 비디오
    ├── segment_*.wav      # 세그먼트별 오디오
    └── combined_audio.wav # 결합된 오디오
```

### metadata.json 구조
```json
{
  "user_id": "user001",
  "samples_count": 40,
  "status": "trained",
  "model_path": "../data/voice_models/user001/model.pth",
  "created_at": "2025-01-15T10:30:00Z"
}
```

### 세그먼트 데이터 구조
```json
{
  "id": 0,
  "start": 0.0,
  "end": 3.5,
  "original_text": "Hello, world!",
  "translated_text": "Halo, dunia!",
  "audio_file": "../data/outputs/segment_0_0.wav"
}
```

## 🔐 보안 고려사항

1. **파일 업로드 제한**:
   - 파일 크기 제한 (예: 100MB)
   - 허용된 MIME 타입만 업로드
   - 파일명 sanitization

2. **사용자 분리**:
   - User ID별 데이터 격리
   - 다른 사용자의 모델 접근 불가

3. **API 보안** (프로덕션 시):
   - API Key 인증
   - Rate limiting
   - CORS 설정

## 🚀 확장 가능성

1. **데이터베이스 추가**:
   - PostgreSQL 또는 MongoDB
   - 사용자 정보, 작업 이력 저장

2. **비동기 작업 처리**:
   - Celery + Redis
   - 장시간 작업을 백그라운드에서 처리

3. **클라우드 스토리지**:
   - AWS S3, Google Cloud Storage
   - 파일 저장 및 배포

4. **컨테이너화**:
   - Docker / Docker Compose
   - Kubernetes 배포

5. **모니터링**:
   - Prometheus + Grafana
   - 성능 및 오류 추적

## 📊 성능 지표

### 예상 처리 시간 (기준: 1분 영상)
- STT (Whisper base): ~30초
- 번역: ~5초
- TTS (XTTS-v2): ~60초
- 비디오 결합: ~10초
- **총 처리 시간**: ~105초

### 리소스 사용량
- **CPU 모드**: 4-8GB RAM
- **GPU 모드**: 6-10GB VRAM
- **디스크**: 1분 영상당 약 50-100MB
