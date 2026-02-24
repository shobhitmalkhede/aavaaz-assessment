import React, { useState } from 'react';
import axios from 'axios';

const API_BASE_URL = (process.env.REACT_APP_API_BASE_URL || '').replace(/\/$/, '');

const PatientForm = ({ onPatientCreated }) => {
  const [formData, setFormData] = useState({
    name: '',
    dob: '',
    address: '',
    diagnosis: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/patients/`, formData);
      onPatientCreated(response.data);
      setFormData({
        name: '',
        dob: '',
        address: '',
        diagnosis: ''
      });
    } catch (error) {
      console.error('Error creating patient:', error);
      alert('Error creating patient. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="form-container">
      <h3>Create New Patient</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="name">Patient Name *</label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
            placeholder="Enter patient name"
          />
        </div>

        <div className="form-group">
          <label htmlFor="dob">Date of Birth *</label>
          <input
            type="date"
            id="dob"
            name="dob"
            value={formData.dob}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="address">Address *</label>
          <textarea
            id="address"
            name="address"
            value={formData.address}
            onChange={handleChange}
            required
            rows={3}
            placeholder="Enter patient address"
          />
        </div>

        <div className="form-group">
          <label htmlFor="diagnosis">Diagnosis *</label>
          <textarea
            id="diagnosis"
            name="diagnosis"
            value={formData.diagnosis}
            onChange={handleChange}
            required
            rows={2}
            placeholder="Enter diagnosis"
          />
        </div>

        <button 
          type="submit" 
          className="btn"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Creating...' : 'Create Patient'}
        </button>
      </form>
    </div>
  );
};

export default PatientForm;
