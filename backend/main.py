from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import voice_training, stt, translation, tts, video

app = FastAPI(title="EBS AI Voice Translation System")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(voice_training.router, prefix="/api/voice", tags=["Voice Training"])
app.include_router(stt.router, prefix="/api/stt", tags=["Speech to Text"])
app.include_router(translation.router, prefix="/api/translate", tags=["Translation"])
app.include_router(tts.router, prefix="/api/tts", tags=["Text to Speech"])
app.include_router(video.router, prefix="/api/video", tags=["Video Processing"])

@app.get("/")
async def root():
    return {"message": "EBS AI Voice Translation System API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
