#!/bin/bash

echo "🚀 EBS AI Frontend 시작..."

# 프론트엔드 디렉토리로 이동
cd frontend

# Node modules 설치 확인
if [ ! -d "node_modules" ]; then
    echo "📦 Node 패키지 설치 중..."
    npm install
fi

# React 앱 시작
echo "✅ React 앱 시작 (http://localhost:3000)"
npm start
