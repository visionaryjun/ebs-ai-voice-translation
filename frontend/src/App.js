import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import VoiceTraining from './components/VoiceTraining';
import VideoProcessing from './components/VideoProcessing';
import Results from './components/Results';
import './App.css';

function App() {
  const [userId, setUserId] = useState(localStorage.getItem('userId') || '');

  const handleUserIdChange = (e) => {
    const newUserId = e.target.value;
    setUserId(newUserId);
    localStorage.setItem('userId', newUserId);
  };

  return (
    <Router>
      <div className="App">
        <header className="App-header">
          <h1>🎙️ EBS AI 음성학습 및 번역 시스템</h1>
          <div className="user-id-input">
            <label>User ID: </label>
            <input
              type="text"
              value={userId}
              onChange={handleUserIdChange}
              placeholder="사용자 ID 입력"
            />
          </div>
        </header>

        <nav className="nav-menu">
          <Link to="/" className="nav-link">1. AI 음성학습</Link>
          <Link to="/video" className="nav-link">2. STT & 번역 & TTS</Link>
          <Link to="/results" className="nav-link">3. 결과 확인</Link>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<VoiceTraining userId={userId} />} />
            <Route path="/video" element={<VideoProcessing userId={userId} />} />
            <Route path="/results" element={<Results />} />
          </Routes>
        </main>

        <footer className="App-footer">
          <p>© 2025 EBS AI Voice Translation System</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;
