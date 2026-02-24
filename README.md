# Aavaaz Clinical Interaction System

A simplified full-stack system for real-time clinical conversation analysis with multimodal insight generation.

## System Overview

- **Audio Streaming**: Real-time WebSocket audio capture from doctor-patient conversations
- **Speech-to-Text**: ElevenLabs Realtime ASR for live transcription
- **Multimodal Analysis**: Combines verbal content with audio tone and simulated video signals
- **Clinical Insights**: Structured reports with evidence-backed hidden cues

## Technology Stack

- **Frontend**: React (deployed on Vercel)
- **Backend**: Django with Django Channels (WebSockets)
- **ASR**: ElevenLabs Realtime Speech-to-Text
- **AI Analysis**: Google Gemini for clinical insight generation
- **Database**: SQLite (development), PostgreSQL (production)

## Architecture

```
React Frontend → WebSocket → Django Backend → ElevenLabs ASR
                                    ↓
                              Multimodal Analysis
                                    ↓
                              Clinical Insight Report
```

## Key Features

### Part 1: Real-Time Audio Streaming
- Start/stop conversation sessions
- Live audio streaming via WebSockets
- Real-time transcript updates
- Reliability features (STOP handling, overload protection, disconnect cleanup)

### Part 2: Multimodal Insight Workflow
- **Step 1**: Extract meaning from transcript text
- **Step 2**: Analyze non-verbal signals (audio tones + video events)
- **Step 3**: Compose multimodal insights with evidence

## Project Structure

```
dd/
├── backend/                 # Django application
│   ├── aavaaz/             # Main Django project
│   ├── core/               # Core models and utilities
│   ├── sessions/           # Session management
│   ├── insights/           # Multimodal analysis
│   └── requirements.txt
├── frontend/               # React application
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   └── App.js
│   └── package.json
└── README.md
```

## Getting Started

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## Environment Variables

Create `.env` file in backend:
```
ELEVENLABS_API_KEY=your_api_key_here
GEMINI_API_KEY=your_gemini_key_here
DEBUG=True
```

## Demo Flow

1. Create/select patient record
2. Start conversation session
3. Stream audio with live transcription
4. Stop session to trigger analysis
5. View generated Insight Report

## Key Design Decisions

- **Reliability**: Handles duplicate STOP signals, audio overload, client disconnections
- **Evidence-Based**: Every insight includes timestamp/transcript evidence
- **Simple Architecture**: No heavy frameworks, focused on core functionality
- **Real-Time Focus**: WebSocket-first design for live feedback
