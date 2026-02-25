import React, { useState } from 'react';
import axios from 'axios';

const API_BASE_URL = (process.env.REACT_APP_API_BASE_URL || '').replace(/\/$/, '');

const SessionManager = ({ patient, onSessionStarted }) => {
  const [isCreating, setIsCreating] = useState(false);

  const handleStartSession = async () => {
    setIsCreating(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/sessions/`, {
        patient_id: patient.id
      });
      onSessionStarted(response.data);
    } catch (error) {
      console.error('Error creating session:', error);
      alert('Error starting session. Please try again.');
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="session-manager-layout">
      <section className="session-manager-hero" aria-label="Session start introduction">
        <div className="session-manager-hero-inner">
          <h2 className="session-manager-hero-title">LET'S START
            <br />YOUR
            <br />SESSION
          </h2>

          <div className="session-manager-hero-contact">
            <div className="session-manager-hero-contact-title">SESSION INFO</div>
            <div className="session-manager-hero-contact-item">Patient: {patient.name}</div>
            <div className="session-manager-hero-contact-item">DOB: {patient.dob}</div>
            <div className="session-manager-hero-contact-item">Diagnosis: {patient.diagnosis}</div>
          </div>
        </div>
      </section>

      <section className="session-manager-panel" aria-label="Start session form">
        <div className="session-manager-panel-inner">
          <h3 className="session-manager-panel-title">Start New Session</h3>

          <div className="session-manager-patient-info">
            <div className="session-manager-info-row">
              <span className="session-manager-info-label">Patient</span>
              <span className="session-manager-info-value">{patient.name}</span>
            </div>
            <div className="session-manager-info-row">
              <span className="session-manager-info-label">Diagnosis</span>
              <span className="session-manager-info-value">{patient.diagnosis}</span>
            </div>
          </div>

          <button
            onClick={handleStartSession}
            className="btn session-manager-submit"
            disabled={isCreating}
          >
            {isCreating ? 'Starting...' : 'Start Session'}
          </button>
        </div>
      </section>
    </div>
  );
};

export default SessionManager;
