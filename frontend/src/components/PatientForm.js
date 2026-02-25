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
    <div className="patient-form-layout">
      <section className="patient-form-hero" aria-label="Patient form introduction">
        <div className="patient-form-hero-inner">
          <h2 className="patient-form-hero-title">LET'S TALK
            <br />ABOUT YOUR
            <br />PATIENT
          </h2>

          <div className="patient-form-hero-contact">
            <div className="patient-form-hero-contact-title">CONTACT US</div>
            <div className="patient-form-hero-contact-item">admin@aavaaz.local</div>
            <div className="patient-form-hero-contact-item">+91 00000 00000</div>
          </div>
        </div>
      </section>

      <section className="patient-form-panel" aria-label="Create patient form">
        <div className="patient-form-panel-inner">
          <h3 className="patient-form-panel-title">Create New Patient</h3>

          <form onSubmit={handleSubmit}>
            <div className="patient-form-grid">
              <div className="form-group patient-form-field">
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

              <div className="form-group patient-form-field">
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
            </div>

            <div className="form-group patient-form-field">
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

            <div className="form-group patient-form-field">
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
              className="btn patient-form-submit"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Creating...' : 'Create Patient'}
            </button>
          </form>
        </div>
      </section>
    </div>
  );
};

export default PatientForm;
