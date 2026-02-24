import React, { useState } from 'react';
import axios from 'axios';

const SessionManager = ({ patient, onSessionStarted }) => {
  const [isCreating, setIsCreating] = useState(false);

  const handleStartSession = async () => {
    setIsCreating(true);

    try {
      const response = await axios.post('/api/sessions/', {
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
    <div className="session-manager">
      <div className="form-container">
        <h3>Start New Session</h3>
        <p>
          <strong>Patient:</strong> {patient.name}<br />
          <strong>Diagnosis:</strong> {patient.diagnosis}
        </p>
        <button 
          onClick={handleStartSession}
          className="btn btn-success"
          disabled={isCreating}
        >
          {isCreating ? 'Starting...' : 'Start Session'}
        </button>
      </div>
    </div>
  );
};

export default SessionManager;
