import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './VoiceTraining.css';

function VoiceTraining({ userId }) {
  const [sentences, setSentences] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [progress, setProgress] = useState({ progress: 0, total: 0, completed: [] });
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const [message, setMessage] = useState('');
  const [isTraining, setIsTraining] = useState(false);

  useEffect(() => {
    fetchSentences();
    if (userId) {
      fetchProgress();
    }
  }, [userId]);

  const fetchSentences = async () => {
    try {
      const response = await axios.get('/api/voice/sentences');
      setSentences(response.data.sentences);
    } catch (error) {
      setMessage(`문장 로드 실패: ${error.message}`);
    }
  };

  const fetchProgress = async () => {
    try {
      const response = await axios.get(`/api/voice/progress/${userId}`);
      setProgress(response.data);
    } catch (error) {
      console.error('진행도 로드 실패:', error);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks = [];

      recorder.ondataavailable = (e) => {
        chunks.push(e.data);
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/wav' });
        await uploadAudio(audioBlob);
      };

      setMediaRecorder(recorder);
      setAudioChunks(chunks);
      recorder.start();
      setIsRecording(true);
      setMessage('녹음 중...');
    } catch (error) {
      setMessage(`마이크 접근 실패: ${error.message}`);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      mediaRecorder.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
      setMessage('녹음 완료, 업로드 중...');
    }
  };

  const uploadAudio = async (audioBlob) => {
    if (!userId) {
      setMessage('User ID를 입력해주세요!');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('file', audioBlob, `sample_${currentIndex}.wav`);

      await axios.post(
        `/api/voice/upload/${userId}?sentence_index=${currentIndex}`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );

      setMessage('업로드 성공!');
      fetchProgress();

      // 다음 문장으로
      if (currentIndex < sentences.length - 1) {
        setTimeout(() => {
          setCurrentIndex(currentIndex + 1);
          setMessage('');
        }, 1000);
      }
    } catch (error) {
      setMessage(`업로드 실패: ${error.message}`);
    }
  };

  const trainModel = async () => {
    if (!userId) {
      setMessage('User ID를 입력해주세요!');
      return;
    }

    setIsTraining(true);
    setMessage('모델 학습 중... (수 분 소요될 수 있습니다)');

    try {
      const response = await axios.post(`/api/voice/train/${userId}`);
      setMessage(`학습 완료! 샘플 수: ${response.data.metadata.samples_count}`);
    } catch (error) {
      setMessage(`학습 실패: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsTraining(false);
    }
  };

  const resetData = async () => {
    if (!userId) return;
    if (!window.confirm('모든 학습 데이터를 삭제하시겠습니까?')) return;

    try {
      await axios.delete(`/api/voice/reset/${userId}`);
      setMessage('데이터 초기화 완료');
      setProgress({ progress: 0, total: 0, completed: [] });
      setCurrentIndex(0);
    } catch (error) {
      setMessage(`초기화 실패: ${error.message}`);
    }
  };

  const progressPercentage = progress.total > 0
    ? Math.round((progress.progress / progress.total) * 100)
    : 0;

  return (
    <div className="component-container voice-training">
      <h2 className="component-title">🎤 1. AI 음성학습</h2>

      {!userId && (
        <div className="error-message">
          ⚠️ 상단에서 User ID를 먼저 입력해주세요!
        </div>
      )}

      <div className="progress-section">
        <h3>학습 진행도: {progress.progress} / {progress.total}</h3>
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progressPercentage}%` }}>
            {progressPercentage}%
          </div>
        </div>
      </div>

      {sentences.length > 0 && (
        <div className="recording-section">
          <div className="sentence-display">
            <span className="sentence-number">문장 {currentIndex + 1}/{sentences.length}</span>
            <p className="sentence-text">{sentences[currentIndex]}</p>
          </div>

          <div className="recording-controls">
            {!isRecording ? (
              <button
                className="btn btn-record"
                onClick={startRecording}
                disabled={!userId || progress.completed.includes(currentIndex)}
              >
                🎙️ 녹음 시작
              </button>
            ) : (
              <button className="btn btn-stop" onClick={stopRecording}>
                ⏹️ 녹음 중지
              </button>
            )}
          </div>

          <div className="navigation-controls">
            <button
              className="btn btn-prev"
              onClick={() => setCurrentIndex(Math.max(0, currentIndex - 1))}
              disabled={currentIndex === 0}
            >
              ← 이전
            </button>
            <button
              className="btn btn-next"
              onClick={() => setCurrentIndex(Math.min(sentences.length - 1, currentIndex + 1))}
              disabled={currentIndex === sentences.length - 1}
            >
              다음 →
            </button>
          </div>
        </div>
      )}

      {message && (
        <div className={message.includes('실패') || message.includes('⚠️') ? 'error-message' : 'success-message'}>
          {message}
        </div>
      )}

      <div className="action-buttons">
        <button
          className="btn btn-train"
          onClick={trainModel}
          disabled={!userId || progress.progress < 30 || isTraining}
        >
          {isTraining ? '학습 중...' : '🧠 모델 학습 시작'}
        </button>
        <button
          className="btn btn-reset"
          onClick={resetData}
          disabled={!userId}
        >
          🗑️ 데이터 초기화
        </button>
      </div>

      <div className="info-box">
        <h4>📌 안내사항</h4>
        <ul>
          <li>최소 30개 이상의 문장을 녹음해야 학습이 가능합니다</li>
          <li>조용한 환경에서 명확하게 발음해주세요</li>
          <li>각 문장은 자연스러운 억양으로 읽어주세요</li>
          <li>녹음 완료 후 자동으로 다음 문장으로 이동합니다</li>
        </ul>
      </div>
    </div>
  );
}

export default VoiceTraining;
