import json
import logging
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
import base64

logger = logging.getLogger(__name__)


class AudioStreamConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = None
        self.session = None
        self.is_processing = False
        self.audio_chunks = []          # Collect all audio bytes during recording
        self.transcript_parts = []
        self.final_transcript_sent = False
        self._stop_task = None

    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        
        try:
            self.session = await self.get_session()
            if not self.session:
                await self.close()
                return
                
            await self.accept()
            logger.info(f"WebSocket connected for session {self.session_id}")
                
        except Exception as e:
            logger.error(f"Connection error: {e}")
            await self.close()

    async def disconnect(self, close_code):
        # Cancel any in-flight processing to avoid hanging shutdown.
        if self._stop_task and not self._stop_task.done():
            self._stop_task.cancel()

        # Clean up session
        if self.session and self.session.status in ['STARTED', 'PROCESSING']:
            await database_sync_to_async(self.session.stop)()
        
        logger.info(f"WebSocket disconnected: {close_code}")

    async def receive(self, text_data=None, bytes_data=None):
        try:
            # Overload protection
            if len(self.audio_chunks) >= 45:  # Near buffer limit
                await self.send_warning("Audio buffer near capacity, may drop data")
            
            # Parse message
            if text_data is not None:
                message = json.loads(text_data)
            elif bytes_data is not None:
                message = json.loads(bytes_data.decode('utf-8'))
            else:
                return
            
            if message.get('type') == 'audio':
                await self.handle_audio_data(message)
            elif message.get('type') == 'stop':
                await self.handle_stop()
            else:
                logger.warning(f"Unknown message type: {message.get('type')}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
            await self.send_error("Invalid message format")
        except Exception as e:
            logger.error(f"Receive error: {e}")
            await self.send_error(f"Processing error: {str(e)}")

    async def handle_audio_data(self, message):
        if self.is_processing or self.final_transcript_sent:
            return
            
        audio_data = message.get('data')
        if not audio_data:
            return
            
        try:
            # Decode base64 audio and collect chunks
            audio_bytes = base64.b64decode(audio_data)
            self.audio_chunks.append(audio_bytes)
            
            # Send live update to show recording is active
            await self.send_text({
                'type': 'partial_transcript',
                'text': f'🎤 Recording... ({len(self.audio_chunks)} chunks received)',
                'timestamp': datetime.now().isoformat()
            })
                
        except Exception as e:
            logger.error(f"Audio processing error: {e}")

    async def handle_stop(self):
        if self.final_transcript_sent:
            logger.warning("Stop already processed, ignoring")
            return
            
        if self.is_processing:
            logger.warning("Stop received while processing, will handle after current processing")
            return
            
        self.is_processing = True

        # Run heavy work in background so the connection can close cleanly without hanging.
        import asyncio
        if self._stop_task and not self._stop_task.done():
            logger.warning("Stop task already running")
            return

        self._stop_task = asyncio.create_task(self._process_stop())

    async def _process_stop(self):
        try:
            # Update session status
            await database_sync_to_async(self.session.stop)()

            # Send status - transcribing
            await self.send_text({
                'type': 'partial_transcript',
                'text': '⏳ Processing audio...',
                'timestamp': datetime.now().isoformat()
            })

            # Transcribe the full collected audio
            final_transcript = await self.transcribe_full_audio()

            # Save transcript
            await self.save_transcript(final_transcript)

            # Send final transcript
            await self.send_text({
                'type': 'final_transcript',
                'text': final_transcript,
                'timestamp': datetime.now().isoformat()
            })

            self.final_transcript_sent = True

            # Trigger insight generation
            await self.trigger_insight_generation()

        except Exception as e:
            logger.error(f"Stop processing error: {e}")
            try:
                await self.send_error(f"Stop processing failed: {str(e)}")
            except Exception:
                pass
        finally:
            self.is_processing = False

    async def transcribe_full_audio(self):
        """Transcribe all collected audio chunks using ElevenLabs Speech-to-Text."""
        import asyncio
        import os
        import re
        import tempfile

        if not self.audio_chunks:
            return "[No audio recorded]"

        if not getattr(settings, 'GEMINI_API_KEY', None):
            return "[Transcription failed: GEMINI_API_KEY not configured]"

        try:
            # Combine all chunks into one webm file
            combined = b''.join(self.audio_chunks)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
                tmp.write(combined)
                tmp_path = tmp.name

            try:
                def _do_transcribe() -> str:
                    import google.generativeai as genai

                    if not hasattr(genai, '_configured'):
                        genai.configure(api_key=settings.GEMINI_API_KEY)
                        genai._configured = True

                    model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash')
                    logger.info(f"Gemini active model (transcribe): {model_name}")
                    model = genai.GenerativeModel(model_name)
                    
                    with open(tmp_path, "rb") as f:
                        audio_data = f.read()

                    prompt = "Please transcribe this audio. It is a clinical dialogue between a doctor and a patient (or similar context). Format it clearly with speaker labels (e.g. Doctor:, Patient:). Provide only the transcription, no extra conversational text."
                    
                    try:
                        response = model.generate_content([
                            prompt,
                            {"mime_type": "audio/webm", "data": audio_data}
                        ])
                        transcript = (getattr(response, 'text', '') or '').strip()
                        if transcript:
                            return transcript
                        return "[Transcription generated empty text]"
                    except Exception as e:
                        logger.error(f"Gemini transcription failed: {e}")
                        raise

                transcript = await asyncio.to_thread(_do_transcribe)

                # If user speaks Hindi, STT will return Hindi text. Translate to English when detected.
                # (Language forcing can't translate spoken content; it only guides recognition.)
                if transcript and re.search(r"[\u0900-\u097F]", transcript):
                    try:
                        import google.generativeai as genai

                        if not hasattr(genai, '_configured'):
                            genai.configure(api_key=settings.GEMINI_API_KEY)
                            genai._configured = True

                        model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash')
                        logger.info(f"Gemini active model (translate): {model_name}")
                        model = genai.GenerativeModel(model_name)

                        translate_prompt = (
                            "Translate the following text to English. "
                            "Return only the English translation (no quotes, no extra text).\n\n"
                            f"Text:\n{transcript}"
                        )

                        def _do_translate() -> str:
                            resp = model.generate_content(translate_prompt)
                            return (getattr(resp, 'text', '') or '').strip()

                        translated = await asyncio.to_thread(_do_translate)
                        if translated:
                            return translated
                    except Exception as e:
                        msg = str(e).lower()
                        if '429' in msg or 'quota' in msg or 'resource_exhausted' in msg:
                            logger.warning(f"Gemini quota exceeded; returning original (non-English) transcript: {e}")
                        else:
                            logger.error(f"Transcript translation failed; returning original transcript: {e}")

                return transcript
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return f"[Transcription failed: {str(e)}]"

    async def trigger_insight_generation(self):
        """Trigger the multimodal insight generation workflow"""
        try:
            # Update session status
            self.session.status = 'PROCESSING'
            await database_sync_to_async(self.session.save)()
            
            # Send status update
            await self.send_text({
                'type': 'status_update',
                'status': 'PROCESSING',
                'message': 'Generating clinical insights...'
            })
            
            # Generate insights from actual transcript using Gemini
            transcript_text = self.session.final_transcript or ''
            insight_report = await self.generate_insights_from_transcript(transcript_text)
            
            # Save insights
            await self.save_insights(insight_report)
            
            # Update session status
            self.session.status = 'COMPLETED'
            await database_sync_to_async(self.session.save)()
            
            # Send final insights
            await self.send_text({
                'type': 'insight_report',
                'report': insight_report,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Insight generation error: {e}")
            self.session.status = 'ERROR'
            await database_sync_to_async(self.session.save)()
            await self.send_error(f"Insight generation failed: {str(e)}")

    async def generate_insights_from_transcript(self, transcript):
        """Use Gemini to generate clinical insights from the actual transcript"""
        import json as json_module
        import re
        import google.generativeai as genai

        if not transcript or transcript.startswith('['):
            return {"clinical_summary": transcript, "key_entities": {}, "hidden_cues": []}

        try:
            # Configure Gemini if not already configured
            if not hasattr(genai, '_configured'):
                genai.configure(api_key=settings.GEMINI_API_KEY)
                genai._configured = True
            
            model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash')
            logger.info(f"Gemini active model (consumer): {model_name}")
            model = genai.GenerativeModel(model_name)

            prompt = f"""You are a clinical AI assistant. Analyze the following patient session transcript and return a JSON with:
- clinical_summary: a brief 2-3 sentence clinical summary
- key_entities: object with symptoms (list), medications (list), concerns (list)
- hidden_cues: list of objects with 'cue' (string) and 'evidence' (object with 'transcript' string)

Transcript:
{transcript}

Return only valid JSON, no explanation."""

            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                )
            )

            raw_text = getattr(response, 'text', '') or ''
            logger.info(f"Gemini raw response (first 400 chars): {raw_text[:400]}")

            def _extract_json(text: str) -> str | None:
                if not text:
                    return None

                fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
                if fenced:
                    return fenced.group(1)

                start = text.find('{')
                end = text.rfind('}')
                if start != -1 and end != -1 and end > start:
                    return text[start:end + 1]

                return None

            json_text = _extract_json(raw_text) or raw_text
            try:
                return json_module.loads(json_text)
            except Exception as parse_err:
                logger.error(f"Gemini insight JSON parse error: {parse_err}")
                return {
                    "clinical_summary": transcript,
                    "key_entities": {},
                    "hidden_cues": [],
                    "error": "Gemini returned non-JSON output",
                    "raw": raw_text[:800],
                }
        except Exception as e:
            msg = str(e)
            lower = msg.lower()
            if (
                'resource_exhausted' in lower
                or 'quota' in lower
                or '429' in lower
                or 'rate limit' in lower
                or 'rate-limit' in lower
            ):
                logger.warning(f"Gemini quota exceeded; returning minimal insight report: {e}")
                return {
                    "clinical_summary": transcript,
                    "key_entities": {},
                    "hidden_cues": [],
                    "error": "Gemini quota exceeded"
                }

            logger.error(f"Gemini insight generation error: {e}")
            return {"clinical_summary": transcript, "key_entities": {}, "hidden_cues": [], "error": msg}

    @database_sync_to_async
    def get_session(self):
        try:
            from core.models import Session
            return Session.objects.get(id=self.session_id)
        except ObjectDoesNotExist:
            return None

    @database_sync_to_async
    def save_transcript(self, transcript):
        self.session.final_transcript = transcript
        self.session.save()

    @database_sync_to_async
    def save_insights(self, insights):
        self.session.insight_report = insights
        self.session.save()

    async def send_text(self, data):
        await self.send(text_data=json.dumps(data))

    async def send_error(self, message):
        await self.send_text({
            'type': 'error',
            'message': message,
            'timestamp': datetime.now().isoformat()
        })

    async def send_warning(self, message):
        await self.send_text({
            'type': 'warning', 
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
