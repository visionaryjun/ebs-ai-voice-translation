import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './VideoProcessing.css';

function VideoProcessing({ userId }) {
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [targetLanguage, setTargetLanguage] = useState('id');
  const [languages, setLanguages] = useState({});
  const [processing, setProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState('');
  const [result, setResult] = useState(null);
  const [message, setMessage] = useState('');
  const [transcript, setTranscript] = useState('');
  const [translation, setTranslation] = useState('');

  useEffect(() => {
    fetchLanguages();
  }, []);

  const fetchLanguages = async () => {
    try {
      const response = await axios.get('/api/translate/languages');
      setLanguages(response.data.languages);
    } catch (error) {
      console.error('언어 목록 로드 실패:', error);
    }
  };

  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0]);
  };

  const processYoutube = async () => {
    if (!userId) {
      setMessage('User ID를 입력해주세요!');
      return;
    }
    if (!youtubeUrl) {
      setMessage('유튜브 URL을 입력해주세요!');
      return;
    }

    setProcessing(true);
    setMessage('');
    setResult(null);

    try {
      // 1. STT - 유튜브에서 텍스트 추출
      setCurrentStep('🎧 음성을 텍스트로 변환 중...');
      const sttResponse = await axios.post('/api/stt/youtube',
        new URLSearchParams({ url: youtubeUrl }),
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
      );
      setTranscript(sttResponse.data.text);

      // 2. 번역
      setCurrentStep('🌐 번역 중...');
      const translateResponse = await axios.post('/api/translate/translate-segments', {
        segments: sttResponse.data.segments,
        source_lang: sttResponse.data.language,
        target_lang: targetLanguage
      });

      const translatedText = translateResponse.data.segments
        .map(seg => seg.translated_text)
        .join(' ');
      setTranslation(translatedText);

      // 3. TTS - 학습된 음성으로 변환
      setCurrentStep('🎤 학습된 음성으로 변환 중...');
      const ttsResponse = await axios.post('/api/tts/synthesize-segments',
        new URLSearchParams({
          segments: JSON.stringify(translateResponse.data.segments),
          user_id: userId,
          language: targetLanguage
        }),
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
      );

      // 4. 비디오 결합
      setCurrentStep('🎬 비디오와 음성 결합 중...');
      const videoResponse = await axios.post('/api/video/combine',
        new URLSearchParams({
          video_path: sttResponse.data.audio_file.replace('.wav', '.mp4'),
          audio_segments: JSON.stringify(ttsResponse.data.segments),
          output_filename: `output_${Date.now()}.mp4`
        }),
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
      );

      setResult(videoResponse.data);
      setMessage('✅ 처리 완료!');
      setCurrentStep('');
    } catch (error) {
      setMessage(`❌ 처리 실패: ${error.response?.data?.detail || error.message}`);
      setCurrentStep('');
    } finally {
      setProcessing(false);
    }
  };

  const processUpload = async () => {
    if (!userId) {
      setMessage('User ID를 입력해주세요!');
      return;
    }
    if (!selectedFile) {
      setMessage('파일을 선택해주세요!');
      return;
    }

    setProcessing(true);
    setMessage('');
    setResult(null);

    try {
      // 1. 파일 업로드 및 STT
      setCurrentStep('📤 파일 업로드 및 음성 인식 중...');
      const formData = new FormData();
      formData.append('file', selectedFile);

      const sttResponse = await axios.post('/api/stt/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setTranscript(sttResponse.data.text);

      // 2. 번역
      setCurrentStep('🌐 번역 중...');
      const translateResponse = await axios.post('/api/translate/translate-segments', {
        segments: sttResponse.data.segments,
        source_lang: sttResponse.data.language,
        target_lang: targetLanguage
      });

      const translatedText = translateResponse.data.segments
        .map(seg => seg.translated_text)
        .join(' ');
      setTranslation(translatedText);

      // 3. TTS
      setCurrentStep('🎤 학습된 음성으로 변환 중...');
      const ttsResponse = await axios.post('/api/tts/synthesize-segments',
        new URLSearchParams({
          segments: JSON.stringify(translateResponse.data.segments),
          user_id: userId,
          language: targetLanguage
        }),
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
      );

      // 4. 비디오 결합
      setCurrentStep('🎬 비디오와 음성 결합 중...');
      const videoResponse = await axios.post('/api/video/combine',
        new URLSearchParams({
          video_path: sttResponse.data.audio_file,
          audio_segments: JSON.stringify(ttsResponse.data.segments),
          output_filename: `output_${Date.now()}.mp4`
        }),
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
      );

      setResult(videoResponse.data);
      setMessage('✅ 처리 완료!');
      setCurrentStep('');
    } catch (error) {
      setMessage(`❌ 처리 실패: ${error.response?.data?.detail || error.message}`);
      setCurrentStep('');
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="component-container video-processing">
      <h2 className="component-title">🎬 2. STT & 번역 & TTS</h2>

      {!userId && (
        <div className="error-message">
          ⚠️ 상단에서 User ID를 먼저 입력하고, 음성 학습을 완료해주세요!
        </div>
      )}

      <div className="language-selector">
        <label>🌍 번역 언어 선택:</label>
        <select
          value={targetLanguage}
          onChange={(e) => setTargetLanguage(e.target.value)}
        >
          <option value="id">Indonesian (인도네시아어)</option>
          <option value="vi">Vietnamese (베트남어)</option>
          <option value="en">English (영어)</option>
          <option value="ja">Japanese (일본어)</option>
          <option value="zh-CN">Chinese (중국어)</option>
          <option value="th">Thai (태국어)</option>
        </select>
      </div>

      <div className="input-section">
        <h3>📺 유튜브 URL 입력</h3>
        <div className="youtube-input">
          <input
            type="text"
            placeholder="https://www.youtube.com/watch?v=..."
            value={youtubeUrl}
            onChange={(e) => setYoutubeUrl(e.target.value)}
          />
          <button
            className="btn btn-process"
            onClick={processYoutube}
            disabled={processing || !userId}
          >
            🚀 처리 시작
          </button>
        </div>
      </div>

      <div className="divider">또는</div>

      <div className="input-section">
        <h3>📁 영상 파일 업로드</h3>
        <div className="file-input">
          <input
            type="file"
            accept="video/*,audio/*"
            onChange={handleFileChange}
          />
          <button
            className="btn btn-process"
            onClick={processUpload}
            disabled={processing || !userId}
          >
            🚀 처리 시작
          </button>
        </div>
        {selectedFile && (
          <p className="file-name">선택된 파일: {selectedFile.name}</p>
        )}
      </div>

      {processing && (
        <div className="processing-status">
          <div className="loading">{currentStep}</div>
          <div className="spinner"></div>
        </div>
      )}

      {transcript && (
        <div className="result-section">
          <h3>📝 원본 텍스트</h3>
          <div className="text-box">{transcript}</div>
        </div>
      )}

      {translation && (
        <div className="result-section">
          <h3>🌐 번역된 텍스트</h3>
          <div className="text-box">{translation}</div>
        </div>
      )}

      {result && (
        <div className="success-message">
          <h3>✅ 처리 완료!</h3>
          <p>출력 파일: {result.output_file}</p>
          <p>세그먼트 수: {result.segments_count}</p>
        </div>
      )}

      {message && (
        <div className={message.includes('❌') || message.includes('⚠️') ? 'error-message' : 'success-message'}>
          {message}
        </div>
      )}

      <div className="info-box">
        <h4>📌 안내사항</h4>
        <ul>
          <li>먼저 '1. AI 음성학습'에서 음성 학습을 완료해주세요</li>
          <li>유튜브 URL 또는 비디오 파일을 선택하세요</li>
          <li>처리 시간은 영상 길이에 따라 다를 수 있습니다</li>
          <li>완료 후 '3. 결과 확인' 페이지에서 결과를 확인하세요</li>
        </ul>
      </div>
    </div>
  );
}

export default VideoProcessing;
