import React, { useState } from 'react';

const Card = ({ title, children, noPadding = false }) => (
  <div className="insight-card">
    <div className="insight-card-header">
      <h4 style={{ margin: 0, color: 'rgba(255, 255, 255, 0.95)', fontSize: '1.05rem', fontWeight: '600', letterSpacing: '0.5px' }}>{title}</h4>
    </div>
    <div className="insight-card-body" style={{ padding: noPadding ? 0 : '16px' }}>
      {children}
    </div>
  </div>
);

const Badge = ({ children, color = '#3793ff' }) => (
  <span className="insight-badge" style={{ backgroundColor: `${color}20`, color: color, border: `1px solid ${color}40` }}>
    {children}
  </span>
);

const InsightReport = ({ report }) => {
  const [activeTab, setActiveTab] = useState('summary');

  if (!report) return null;

  // Handles both the raw string (if error) and the new JSON object
  const isRaw = typeof report === 'string' || report.error;
  const data = isRaw ? null : report;

  return (
    <div className="insight-report-container">
      <div className="insight-report-header">
        <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '1.4rem' }}>✨</span> Clinical Insight Report
        </h3>
        <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'rgba(255, 255, 255, 0.6)' }}>AI-Generated Analysis</p>
      </div>

      {isRaw ? (
        <div className="insight-raw">
          <p style={{ color: '#ff6b6b', marginBottom: '10px' }}><em>Failed to parse structured JSON. Showing raw output:</em></p>
          <pre className="insight-pre">{JSON.stringify(report, null, 2)}</pre>
        </div>
      ) : (
        <div className="insight-content">
          <div className="insight-tabs">
            <button className={`insight-tab ${activeTab === 'summary' ? 'active' : ''}`} onClick={() => setActiveTab('summary')}>Summary & Entities</button>
            <button className={`insight-tab ${activeTab === 'signals' ? 'active' : ''}`} onClick={() => setActiveTab('signals')}>Audio Signals</button>
            <button className={`insight-tab ${activeTab === 'cues' ? 'active' : ''}`} onClick={() => setActiveTab('cues')}>Hidden Cues</button>
          </div>

          <div className="insight-tab-content">
            {activeTab === 'summary' && (
              <div className="insight-grid">
                <Card title="Clinical Summary">
                  <p style={{ margin: 0, lineHeight: '1.6', color: 'rgba(255, 255, 255, 0.85)', fontSize: '0.95rem' }}>{data.clinical_summary}</p>
                </Card>

                {data.key_entities && (
                  <Card title="Key Entities" noPadding>
                    <div className="entity-list">
                      {data.key_entities.patient_name && (
                        <div className="entity-row">
                          <span className="entity-label">Patient Name</span>
                          <span className="entity-value">{data.key_entities.patient_name}</span>
                        </div>
                      )}

                      {data.key_entities.symptoms && data.key_entities.symptoms.length > 0 && (
                        <div className="entity-row">
                          <span className="entity-label">Symptoms</span>
                          <div className="entity-tags">
                            {data.key_entities.symptoms.map((sym, i) => <Badge key={`sym-${i}`} color="#ff6b6b">{sym}</Badge>)}
                          </div>
                        </div>
                      )}

                      {data.key_entities.medications && data.key_entities.medications.length > 0 && (
                        <div className="entity-row">
                          <span className="entity-label">Medications</span>
                          <div className="entity-tags">
                            {data.key_entities.medications.map((med, i) => <Badge key={`med-${i}`} color="#28a745">{med}</Badge>)}
                          </div>
                        </div>
                      )}

                      {data.key_entities.emotional_indicators_from_text && data.key_entities.emotional_indicators_from_text.length > 0 && (
                        <div className="entity-row">
                          <span className="entity-label">Emotions</span>
                          <div className="entity-tags">
                            {data.key_entities.emotional_indicators_from_text.map((emo, i) => <Badge key={`emo-${i}`} color="#9b59b6">{emo}</Badge>)}
                          </div>
                        </div>
                      )}
                    </div>
                  </Card>
                )}
              </div>
            )}

            {activeTab === 'signals' && (
              <div className="insight-signals">
                {(!data.audio_signal_analysis || data.audio_signal_analysis.length === 0) ? (
                  <p style={{ color: 'rgba(255, 255, 255, 0.5)', textAlign: 'center', padding: '20px' }}>No audio signals detected.</p>
                ) : (
                  data.audio_signal_analysis.map((signal, idx) => (
                    <div key={idx} className="signal-item">
                      <div className="signal-header">
                        <span className="signal-event">{signal.event?.replace(/_/g, ' ').toUpperCase()}</span>
                        {signal.confidence && (
                          <span className="signal-confidence" title="Confidence Score">
                            {(signal.confidence * 100).toFixed(0)}% Conf
                          </span>
                        )}
                      </div>
                      <p className="signal-meaning">{signal.interpreted_meaning}</p>
                      <div className="signal-meta">
                        <span>⏱️ {signal.timestamp}s</span>
                        {signal.duration_s && <span>⏳ {signal.duration_s}s duration</span>}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {activeTab === 'cues' && (
              <div className="insight-cues">
                {(!data.hidden_cues || data.hidden_cues.length === 0) ? (
                  <p style={{ color: 'rgba(255, 255, 255, 0.5)', textAlign: 'center', padding: '20px' }}>No hidden cues detected.</p>
                ) : (
                  data.hidden_cues.map((cue, idx) => (
                    <div key={idx} className="cue-item">
                      <div className="cue-header">
                        <h5 style={{ margin: 0, fontSize: '1.05rem', color: '#3793ff' }}>{cue.cue_title}</h5>
                        {cue.confidence && (
                          <div className="cue-confidence">
                            <div className="confidence-bar" style={{ width: `${cue.confidence * 100}%`, backgroundColor: cue.confidence > 0.8 ? '#28a745' : cue.confidence > 0.6 ? '#f39c12' : '#ff6b6b' }}></div>
                          </div>
                        )}
                      </div>
                      <p className="cue-desc">{cue.description}</p>

                      {cue.evidence && (
                        <div className="cue-evidence">
                          <div className="evidence-quote">
                            <span className="quote-mark">"</span>
                            {cue.evidence.spoken_text}
                            <span className="quote-mark">"</span>
                          </div>
                          <div className="evidence-meta">
                            {cue.evidence.transcript_line && <span className="meta-pill">Line {cue.evidence.transcript_line}</span>}
                            {cue.evidence.audio_event?.event && <span className="meta-pill err">{cue.evidence.audio_event.event}</span>}
                          </div>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default InsightReport;
