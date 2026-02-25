import React, { useState, useEffect } from 'react';
import axios from 'axios';
import PatientForm from './components/PatientForm';
import SessionManager from './components/SessionManager';
import AudioStreamer from './components/AudioStreamer';
import InsightReport from './components/InsightReport';
import './App.css';

const API_BASE_URL = (process.env.REACT_APP_API_BASE_URL || '').replace(/\/$/, '');

function App() {
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [currentSession, setCurrentSession] = useState(null);
  const [transcript, setTranscript] = useState('');
  const [partialTranscript, setPartialTranscript] = useState('');
  const [insightReport, setInsightReport] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');

  useEffect(() => {
    loadPatients();
  }, []);

  const loadPatients = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/patients/`);
      const data = Array.isArray(response.data) ? response.data : [];
      if (!Array.isArray(response.data)) {
        console.error('Unexpected patients response shape:', response.data);
      }
      setPatients(data);
    } catch (error) {
      console.error('Error loading patients:', error);
      setPatients([]);
    }
  };

  const handlePatientCreated = (newPatient) => {
    setPatients([...patients, newPatient]);
    setSelectedPatient(newPatient);
  };

  const handleSessionStarted = (session) => {
    setCurrentSession(session);
    setTranscript('');
    setPartialTranscript('');
    setInsightReport(null);
  };

  const handleTranscriptUpdate = (data) => {
    if (data.type === 'partial_transcript') {
      setPartialTranscript(data.text);
    } else if (data.type === 'final_transcript') {
      setTranscript(data.text);
      setPartialTranscript('');
    } else if (data.type === 'insight_report') {
      setInsightReport(data.report);
      setIsRecording(false);
    } else if (data.type === 'status_update') {
      console.log('Status update:', data.message);
    } else if (data.type === 'error') {
      console.error('WebSocket error:', data.message);
      setIsRecording(false);
    }
  };

  const handleRecordingStateChange = (recording) => {
    setIsRecording(recording);
  };

  const handleConnectionStatusChange = (status) => {
    setConnectionStatus(status);
  };

  return (
    <div className="App App--landing">
      <main className="App-main">
        {!selectedPatient ? (
          <PatientForm onPatientCreated={handlePatientCreated} />
        ) : (
          !currentSession ? (
            <SessionManager
              patient={selectedPatient}
              onSessionStarted={handleSessionStarted}
            />
          ) : (
            <div className="session-active-layout">
              <section className="session-active-hero" aria-label="Session active introduction">
                <div className="session-active-hero-inner">
                  <h2 className="session-active-hero-title">SESSION
                    <br />IN
                    <br />PROGRESS
                  </h2>

                  <div className="session-active-hero-contact">
                    <div className="session-active-hero-contact-title">SESSION INFO</div>
                    <div className="session-active-hero-contact-item">Patient: {selectedPatient.name}</div>
                    <div className="session-active-hero-contact-item">DOB: {selectedPatient.dob}</div>
                    <div className="session-active-hero-contact-item">Diagnosis: {selectedPatient.diagnosis}</div>
                    <div className="session-active-hero-contact-item">Session ID: {currentSession.id}</div>
                    <div className="session-active-hero-contact-item">Status: {currentSession.status}</div>
                  </div>
                </div>
              </section>

              <section className="session-active-panel" aria-label="Recording and transcript">
                <div className="session-active-panel-inner">
                  <div className="session-active-header">
                    <h3 className="session-active-panel-title">Session Active</h3>
                    <button
                      onClick={() => {
                        setSelectedPatient(null);
                        setCurrentSession(null);
                        setTranscript('');
                        setPartialTranscript('');
                        setInsightReport(null);
                      }}
                      className="session-active-back-button"
                    >
                      ← Back
                    </button>
                  </div>

                  <AudioStreamer
                    sessionId={currentSession.id}
                    onTranscriptUpdate={handleTranscriptUpdate}
                    onRecordingStateChange={handleRecordingStateChange}
                    onConnectionStatusChange={handleConnectionStatusChange}
                  />

                  <div className="transcript-section">
                    <h3>Live Transcript</h3>
                    {partialTranscript && (
                      <div className="partial-transcript">
                        <em>{partialTranscript}</em>
                      </div>
                    )}
                    {transcript && (
                      <div className="final-transcript">
                        <strong>Final Transcript:</strong>
                        <p>{transcript}</p>
                      </div>
                    )}
                  </div>

                  {insightReport && (
                    <InsightReport report={insightReport} />
                  )}
                </div>
              </section>
            </div>
          )
        )}
      </main>
    </div>
  );
}

export default App;
