import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Results.css';

function Results() {
  const [outputs, setOutputs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [selectedVideo, setSelectedVideo] = useState(null);

  useEffect(() => {
    fetchOutputs();
  }, []);

  const fetchOutputs = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/video/outputs');
      setOutputs(response.data.outputs);
      if (response.data.outputs.length === 0) {
        setMessage('아직 생성된 결과 파일이 없습니다.');
      }
    } catch (error) {
      setMessage(`결과 파일 로드 실패: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const handleVideoSelect = (output) => {
    setSelectedVideo(output);
  };

  const downloadVideo = (output) => {
    // 실제 구현에서는 서버에서 파일을 다운로드하는 API 엔드포인트가 필요합니다
    window.open(`/api/video/download/${output.filename}`, '_blank');
  };

  return (
    <div className="component-container results">
      <h2 className="component-title">📹 3. 결과 확인</h2>

      <div className="refresh-section">
        <button className="btn btn-refresh" onClick={fetchOutputs}>
          🔄 새로고침
        </button>
      </div>

      {loading && <div className="loading">결과 파일을 불러오는 중</div>}

      {!loading && outputs.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">📭</div>
          <h3>생성된 결과 파일이 없습니다</h3>
          <p>먼저 '2. STT & 번역 & TTS' 페이지에서 영상을 처리해주세요.</p>
        </div>
      )}

      {!loading && outputs.length > 0 && (
        <div className="results-grid">
          <div className="outputs-list">
            <h3>📁 생성된 파일 목록</h3>
            {outputs.map((output, index) => (
              <div
                key={index}
                className={`output-item ${selectedVideo?.filename === output.filename ? 'selected' : ''}`}
                onClick={() => handleVideoSelect(output)}
              >
                <div className="output-icon">🎬</div>
                <div className="output-info">
                  <div className="output-filename">{output.filename}</div>
                  <div className="output-size">{formatFileSize(output.size)}</div>
                </div>
                <button
                  className="btn btn-download"
                  onClick={(e) => {
                    e.stopPropagation();
                    downloadVideo(output);
                  }}
                >
                  ⬇️
                </button>
              </div>
            ))}
          </div>

          {selectedVideo && (
            <div className="video-player">
              <h3>🎥 비디오 미리보기</h3>
              <div className="video-container">
                <video
                  controls
                  key={selectedVideo.filename}
                  src={`/api/video/stream/${selectedVideo.filename}`}
                >
                  브라우저가 비디오 재생을 지원하지 않습니다.
                </video>
              </div>
              <div className="video-details">
                <h4>📋 파일 정보</h4>
                <p><strong>파일명:</strong> {selectedVideo.filename}</p>
                <p><strong>크기:</strong> {formatFileSize(selectedVideo.size)}</p>
                <p><strong>경로:</strong> {selectedVideo.path}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {message && (
        <div className={message.includes('실패') ? 'error-message' : 'success-message'}>
          {message}
        </div>
      )}

      <div className="info-box">
        <h4>📌 안내사항</h4>
        <ul>
          <li>생성된 모든 결과 파일이 여기에 표시됩니다</li>
          <li>파일을 클릭하면 미리보기를 볼 수 있습니다</li>
          <li>다운로드 버튼을 클릭하여 파일을 저장할 수 있습니다</li>
          <li>처리가 완료된 후에는 새로고침 버튼을 눌러주세요</li>
        </ul>
      </div>

      <div className="workflow-summary">
        <h3>🔄 전체 작업 흐름</h3>
        <div className="workflow-steps">
          <div className="workflow-step">
            <div className="step-number">1</div>
            <div className="step-content">
              <h4>🎤 AI 음성학습</h4>
              <p>40-50개 문장 녹음 및 음성 모델 학습</p>
            </div>
          </div>
          <div className="workflow-arrow">→</div>
          <div className="workflow-step">
            <div className="step-number">2</div>
            <div className="step-content">
              <h4>🎬 영상 처리</h4>
              <p>유튜브/파일 → STT → 번역 → TTS</p>
            </div>
          </div>
          <div className="workflow-arrow">→</div>
          <div className="workflow-step">
            <div className="step-number">3</div>
            <div className="step-content">
              <h4>📹 결과 확인</h4>
              <p>학습된 음성으로 번역된 영상 출력</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Results;
