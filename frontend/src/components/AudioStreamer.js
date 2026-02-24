import React, { useState, useEffect, useRef } from 'react';

const AudioStreamer = ({
  sessionId,
  onTranscriptUpdate,
  onRecordingStateChange,
  onConnectionStatusChange
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const audioChunksRef = useRef([]);
  const websocketRef = useRef(null);
  const mediaRecorderRef = useRef(null);

  useEffect(() => {
    return () => {
      // Cleanup on unmount
      if (websocketRef.current) {
        websocketRef.current.close();
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
    };
  }, []);

  const connectWebSocket = () => {
    return new Promise((resolve, reject) => {
      setIsConnecting(true);
      onConnectionStatusChange('connecting');

      const wsBaseUrl = process.env.REACT_APP_WS_BASE_URL;
      const wsOrigin = wsBaseUrl
        ? wsBaseUrl.replace(/\/$/, '')
        : (window.location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host;

      const wsUrl = `${wsOrigin}/ws/session/${sessionId}/`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnecting(false);
        onConnectionStatusChange('connected');
        resolve(ws);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onTranscriptUpdate(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnecting(false);
        onConnectionStatusChange('disconnected');
        websocketRef.current = null;
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnecting(false);
        onConnectionStatusChange('disconnected');
        reject(error);
      };

      websocketRef.current = ws;
    });
  };

  const startRecording = async () => {
    try {
      // Connect WebSocket first
      const ws = await connectWebSocket();

      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true
        }
      });

      // Create MediaRecorder
      const recorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
        audioBitsPerSecond: 16000
      });

      audioChunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);

          // Convert to base64 and send via WebSocket
          const reader = new FileReader();
          reader.onloadend = () => {
            const base64Audio = reader.result.split(',')[1];
            if (ws && ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({
                type: 'audio',
                data: base64Audio
              }));
            }
          };
          reader.readAsDataURL(event.data);
        }
      };

      recorder.onstop = () => {
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };

      // Start recording in 100ms chunks
      recorder.start(100);
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
      onRecordingStateChange(true);

    } catch (error) {
      console.error('Error starting recording:', error);
      setIsConnecting(false);
      onConnectionStatusChange('disconnected');
      alert('Error accessing microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }

    if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
      websocketRef.current.send(JSON.stringify({
        type: 'stop'
      }));
    }

    setIsRecording(false);
    onRecordingStateChange(false);
  };

  const handleToggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <div className="audio-controls">
      <h3>Audio Recording</h3>

      {isConnecting && (
        <div className="connection-message">
          Connecting to server...
        </div>
      )}

      {!isConnecting && (
        <>
          {isRecording && (
            <div className="recording-indicator active">
              <div className="recording-dot"></div>
              Recording...
            </div>
          )}

          <button
            onClick={handleToggleRecording}
            className={`btn ${isRecording ? 'btn-danger' : 'btn-success'}`}
            disabled={isConnecting}
          >
            {isRecording ? 'Stop Recording' : 'Start Recording'}
          </button>

          <div className="audio-info">
            <p><small>
              {isRecording
                ? 'Recording audio and sending to transcription service...'
                : 'Click to start recording the conversation'}
            </small></p>
          </div>
        </>
      )}
    </div>
  );
};

export default AudioStreamer;
