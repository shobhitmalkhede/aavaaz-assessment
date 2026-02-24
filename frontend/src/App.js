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
    <div className="App">
      <header className="App-header">
        <h1>Aavaaz Clinical Interaction System</h1>
        <div className="connection-status">
          Status: <span className={`status-${connectionStatus}`}>{connectionStatus}</span>
        </div>
        <div className="connection-status">
          Recording: <span className={`status-${isRecording ? 'connected' : 'disconnected'}`}>{isRecording ? 'on' : 'off'}</span>
        </div>
      </header>

      <main className="App-main">
        {!selectedPatient ? (
          <div className="patient-section">
            <h2>Select or Create Patient</h2>
            <div className="patient-list">
              {(Array.isArray(patients) ? patients : []).map(patient => (
                <div
                  key={patient.id}
                  className="patient-card"
                  onClick={() => setSelectedPatient(patient)}
                >
                  <h3>{patient.name}</h3>
                  <p><strong>DOB:</strong> {patient.dob}</p>
                  <p><strong>Diagnosis:</strong> {patient.diagnosis}</p>
                </div>
              ))}
            </div>
            <PatientForm onPatientCreated={handlePatientCreated} />
          </div>
        ) : (
          <div className="session-section">
            <div className="patient-info">
              <h2>{selectedPatient.name}</h2>
              <p><strong>DOB:</strong> {selectedPatient.dob}</p>
              <p><strong>Diagnosis:</strong> {selectedPatient.diagnosis}</p>
              <button
                onClick={() => {
                  setSelectedPatient(null);
                  setCurrentSession(null);
                  setTranscript('');
                  setPartialTranscript('');
                  setInsightReport(null);
                }}
                className="back-button"
              >
                ← Back to Patients
              </button>
            </div>

            {!currentSession ? (
              <SessionManager
                patient={selectedPatient}
                onSessionStarted={handleSessionStarted}
              />
            ) : (
              <div className="session-active">
                <div className="session-info">
                  <h3>Session Active</h3>
                  <p><strong>Session ID:</strong> {currentSession.id}</p>
                  <p><strong>Status:</strong> {currentSession.status}</p>
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
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
