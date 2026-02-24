import json
import re
from typing import Dict, List, Any
import google.generativeai as genai
from django.conf import settings


def _is_quota_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return (
        'resource_exhausted' in msg
        or 'quota' in msg
        or '429' in msg
        or 'rate limit' in msg
        or 'rate-limit' in msg
    )


class InsightWorkflow:
    """Three-step multimodal insight generation workflow"""
    
    def __init__(self):
        self.gemini_model = None
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash')
            print(f"Gemini active model (InsightWorkflow): {model_name}")
            self.gemini_model = genai.GenerativeModel(model_name)

    async def generate_insights(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main workflow: Generate clinical insights from multimodal data
        
        Args:
            session_data: {
                'patient_info': {'name': str, 'diagnosis': str, ...},
                'transcript': str,
                'audio_events': List[Dict],
                'video_events': List[Dict]
            }
        
        Returns:
            Complete insight report
        """
        try:
            # Step 1: Extract meaning from text
            text_analysis = await self.step1_extract_text_meaning(
                session_data['transcript'],
                session_data['patient_info']
            )
            
            # Step 2: Analyze non-verbal signals
            signal_analysis = await self.step2_analyze_signals(
                session_data['audio_events'],
                session_data['video_events']
            )
            
            # Step 3: Compose multimodal insights
            final_report = await self.step3_compose_insights(
                session_data['patient_info'],
                text_analysis,
                signal_analysis,
                session_data['transcript']
            )
            
            return final_report
            
        except Exception as e:
            print(f"Insight generation error: {e}")
            return self._generate_fallback_report(session_data)

    async def step1_extract_text_meaning(self, transcript: str, patient_info: Dict) -> Dict[str, Any]:
        """
        Step 1: Extract structured entities from transcript
        
        Extracts:
        - Patient name mentions
        - Symptoms described
        - Medications discussed
        - Emotional signals/concerns
        """
        
        # Simple rule-based extraction (fallback when Gemini not available)
        symptoms = self._extract_symptoms(transcript)
        medications = self._extract_medications(transcript)
        concerns = self._extract_concerns(transcript)
        
        # Use Gemini for more sophisticated analysis if available
        if self.gemini_model:
            try:
                prompt = f"""
                Analyze this clinical transcript and extract key information:
                
                Patient: {patient_info.get('name', 'Unknown')}
                Diagnosis: {patient_info.get('diagnosis', 'Unknown')}
                
                Transcript:
                {transcript}
                
                Extract and return JSON with:
                {{
                    "symptoms": ["list of symptoms mentioned"],
                    "medications": ["list of medications discussed"], 
                    "concerns": ["list of emotional concerns or worries"],
                    "key_topics": ["main topics discussed"],
                    "sentiment": "positive/negative/neutral/mixed"
                }}
                """
                
                response = self.gemini_model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,
                    )
                )
                
                ai_analysis = json.loads(response.text)
                
                # Merge AI analysis with rule-based
                return {
                    'symptoms': list(set(symptoms + ai_analysis.get('symptoms', []))),
                    'medications': list(set(medications + ai_analysis.get('medications', []))),
                    'concerns': list(set(concerns + ai_analysis.get('concerns', []))),
                    'key_topics': ai_analysis.get('key_topics', []),
                    'sentiment': ai_analysis.get('sentiment', 'neutral')
                }
                
            except Exception as e:
                if _is_quota_error(e):
                    print(f"Gemini quota exceeded, falling back to rule-based extraction: {e}")
                else:
                    print(f"Gemini analysis failed: {e}")
        
        return {
            'symptoms': symptoms,
            'medications': medications,
            'concerns': concerns,
            'key_topics': [],
            'sentiment': 'neutral'
        }

    async def step2_analyze_signals(self, audio_events: List[Dict], video_events: List[Dict]) -> Dict[str, Any]:
        """
        Step 2: Analyze non-verbal signals
        
        Analyzes audio tones and video events for emotional indicators
        """
        
        audio_analysis = self._analyze_audio_events(audio_events)
        video_analysis = self._analyze_video_events(video_events)
        
        # Find correlations between audio and video signals
        correlations = self._find_signal_correlations(audio_events, video_events)
        
        return {
            'audio_signals': audio_analysis,
            'video_signals': video_analysis,
            'correlations': correlations,
            'overall_engagement': self._calculate_engagement(audio_events, video_events)
        }

    async def step3_compose_insights(self, patient_info: Dict, text_analysis: Dict, 
                                   signal_analysis: Dict, transcript: str) -> Dict[str, Any]:
        """
        Step 3: Compose multimodal clinical insights
        
        Combines all analysis into evidence-backed clinical report
        """
        
        # Generate clinical summary
        clinical_summary = self._generate_clinical_summary(
            patient_info, text_analysis, signal_analysis
        )
        
        # Extract key entities
        key_entities = {
            'symptoms': text_analysis.get('symptoms', []),
            'medications': text_analysis.get('medications', []),
            'concerns': text_analysis.get('concerns', [])
        }
        
        # Generate hidden cues (key multimodal insights)
        hidden_cues = self._generate_hidden_cues(
            text_analysis, signal_analysis, transcript
        )
        
        return {
            'clinical_summary': clinical_summary,
            'key_entities': key_entities,
            'hidden_cues': hidden_cues,
            'analysis_metadata': {
                'sentiment': text_analysis.get('sentiment'),
                'engagement_level': signal_analysis.get('overall_engagement'),
                'signal_correlations': len(signal_analysis.get('correlations', []))
            }
        }

    def _extract_symptoms(self, transcript: str) -> List[str]:
        """Rule-based symptom extraction"""
        symptom_keywords = [
            'anxiety', 'depressed', 'sad', 'worry', 'stress', 'pain', 'tired',
            'fatigue', 'sleep', 'insomnia', 'appetite', 'nausea', 'headache',
            'nervous', 'panic', 'fear', 'mood', 'energy'
        ]
        
        symptoms = []
        for keyword in symptom_keywords:
            if keyword.lower() in transcript.lower():
                symptoms.append(keyword)
        
        return list(set(symptoms))

    def _extract_medications(self, transcript: str) -> List[str]:
        """Rule-based medication extraction"""
        medication_patterns = [
            r'\bEscitalopram\b',
            r'\bProzac\b',
            r'\bZoloft\b',
            r'\bXanax\b',
            r'\bValium\b',
            r'\b[0-9]+mg\b',
            r'\bmedication\b',
            r'\bmedicine\b',
            r'\bpill[s]?\b'
        ]
        
        medications = []
        for pattern in medication_patterns:
            matches = re.findall(pattern, transcript, re.IGNORECASE)
            medications.extend(matches)
        
        return list(set(medications))

    def _extract_concerns(self, transcript: str) -> List[str]:
        """Rule-based concern extraction"""
        concern_indicators = [
            'worry about', 'concerned about', 'afraid of', 'scared of',
            'difficult', 'hard', 'struggle', 'problem', 'issue',
            'can\'t', 'unable', 'difficulties', 'trouble'
        ]
        
        concerns = []
        for indicator in concern_indicators:
            if indicator.lower() in transcript.lower():
                concerns.append(indicator)
        
        return list(set(concerns))

    def _analyze_audio_events(self, audio_events: List[Dict]) -> Dict[str, Any]:
        """Analyze audio tone events"""
        if not audio_events:
            return {'summary': 'No audio events detected'}
        
        # Count event types
        event_counts = {}
        total_pause_duration = 0
        
        for event in audio_events:
            event_type = event.get('event', 'unknown')
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            if 'pause' in event_type and event.get('duration_s'):
                total_pause_duration += event.get('duration_s')
        
        # Generate insights
        insights = []
        if event_counts.get('long_pause', 0) > 2:
            insights.append("Frequent long pauses suggest hesitation or discomfort")
        
        if event_counts.get('elevated_intensity', 0) > 0:
            insights.append("Elevated speech intensity detected during discussion")
        
        return {
            'event_counts': event_counts,
            'total_pause_duration': total_pause_duration,
            'insights': insights,
            'summary': f"Detected {len(audio_events)} audio events including {list(event_counts.keys())}"
        }

    def _analyze_video_events(self, video_events: List[Dict]) -> Dict[str, Any]:
        """Analyze video events"""
        if not video_events:
            return {'summary': 'No video events detected'}
        
        # Count event types
        event_counts = {}
        
        for event in video_events:
            event_type = event.get('event', 'unknown')
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        # Generate insights
        insights = []
        if event_counts.get('look_away', 0) > 2:
            insights.append("Frequent looking away may indicate discomfort or evasion")
        
        if event_counts.get('frown', 0) > 0:
            insights.append("Frowning detected during conversation")
        
        return {
            'event_counts': event_counts,
            'insights': insights,
            'summary': f"Detected {len(video_events)} video events including {list(event_counts.keys())}"
        }

    def _find_signal_correlations(self, audio_events: List[Dict], video_events: List[Dict]) -> List[Dict]:
        """Find correlations between audio and video signals"""
        correlations = []
        
        # Look for events that occur around the same time
        for audio_event in audio_events:
            audio_time = audio_event.get('timestamp', 0)
            
            for video_event in video_events:
                video_time = video_event.get('timestamp', 0)
                
                # If events occur within 2 seconds of each other
                if abs(audio_time - video_time) <= 2.0:
                    correlations.append({
                        'type': 'temporal_correlation',
                        'audio_event': audio_event.get('event'),
                        'video_event': video_event.get('event'),
                        'timestamp_diff': abs(audio_time - video_time),
                        'approximate_time': (audio_time + video_time) / 2
                    })
        
        return correlations

    def _calculate_engagement(self, audio_events: List[Dict], video_events: List[Dict]) -> str:
        """Calculate overall engagement level"""
        score = 5  # Start with neutral
        
        # Audio factors
        long_pauses = sum(1 for e in audio_events if 'long_pause' in e.get('event', ''))
        if long_pauses > 3:
            score -= 2
        elif long_pauses > 1:
            score -= 1
        
        elevated_intensity = sum(1 for e in audio_events if 'elevated' in e.get('event', ''))
        if elevated_intensity > 0:
            score += 1
        
        # Video factors
        look_away = sum(1 for e in video_events if e.get('event') == 'look_away')
        if look_away > 3:
            score -= 2
        elif look_away > 1:
            score -= 1
        
        smile = sum(1 for e in video_events if e.get('event') == 'smile')
        if smile > 0:
            score += 1
        
        if score >= 6:
            return 'high'
        elif score >= 4:
            return 'medium'
        else:
            return 'low'

    def _generate_clinical_summary(self, patient_info: Dict, text_analysis: Dict, signal_analysis: Dict) -> str:
        """Generate clinical summary"""
        name = patient_info.get('name', 'Patient')
        diagnosis = patient_info.get('diagnosis', 'Unknown diagnosis')
        
        symptoms = text_analysis.get('symptoms', [])
        medications = text_analysis.get('medications', [])
        sentiment = text_analysis.get('sentiment', 'neutral')
        engagement = signal_analysis.get('overall_engagement', 'medium')
        
        summary = f"{name} ({diagnosis}) "
        
        if symptoms:
            summary += f"reports symptoms including {', '.join(symptoms[:3])}. "
        else:
            summary += "reports general stability. "
        
        if medications:
            summary += f"Currently taking {', '.join(medications[:2])}. "
        
        if sentiment == 'negative':
            summary += "Shows signs of emotional distress. "
        elif sentiment == 'positive':
            summary += "Appears in good spirits. "
        
        if engagement == 'low':
            summary += "Limited engagement observed during session."
        elif engagement == 'high':
            summary += "Good engagement throughout session."
        
        return summary.strip()

    def _generate_hidden_cues(self, text_analysis: Dict, signal_analysis: Dict, transcript: str) -> List[Dict]:
        """Generate evidence-backed hidden cues"""
        cues = []
        
        # Look for verbal-nonverbal mismatches
        if 'fine' in transcript.lower() or 'okay' in transcript.lower():
            audio_insights = signal_analysis.get('audio_signals', {}).get('insights', [])
            video_insights = signal_analysis.get('video_signals', {}).get('insights', [])
            
            if any('hesitation' in insight.lower() or 'pause' in insight.lower() for insight in audio_insights):
                cues.append({
                    'cue': 'Verbal-nonverbal mismatch: Patient says "fine" but shows hesitation',
                    'evidence': {
                        'transcript': 'Patient uses words like "fine" or "okay"',
                        'audio': 'Long pauses detected during positive statements',
                        'confidence': 'medium'
                    }
                })
        
        # Look for medication adherence concerns
        if 'medication' in text_analysis.get('concerns', []):
            cues.append({
                'cue': 'Potential medication adherence concerns',
                'evidence': {
                    'transcript': 'Patient expresses concerns about medication',
                    'topics': 'Medication discussed with uncertainty',
                    'confidence': 'high'
                }
            })
        
        # Look for engagement patterns
        engagement = signal_analysis.get('overall_engagement', 'medium')
        if engagement == 'low':
            cues.append({
                'cue': 'Low engagement may indicate unaddressed concerns',
                'evidence': {
                    'audio': signal_analysis.get('audio_signals', {}).get('summary', ''),
                    'video': signal_analysis.get('video_signals', {}).get('summary', ''),
                    'confidence': 'medium'
                }
            })
        
        return cues

    def _generate_fallback_report(self, session_data: Dict) -> Dict[str, Any]:
        """Generate basic report when analysis fails"""
        return {
            'clinical_summary': "Analysis completed with limited data. Please review transcript manually.",
            'key_entities': {
                'symptoms': [],
                'medications': [],
                'concerns': []
            },
            'hidden_cues': [{
                'cue': 'Analysis incomplete',
                'evidence': {'error': 'Analysis workflow encountered an error'},
                'confidence': 'low'
            }],
            'analysis_metadata': {
                'error': 'fallback_report_generated'
            }
        }
