#!/usr/bin/env python
"""
Test script to verify Gemini API integration
"""
import os
import sys
import google.generativeai as genai
import django
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aavaaz.settings')
django.setup()

from insights.workflows import InsightWorkflow

def test_gemini_integration():
    """Test the Gemini API integration"""
    print("Testing Gemini API integration...")
    
    # Create workflow instance
    workflow = InsightWorkflow()
    
    # Check if Gemini model is initialized
    if workflow.gemini_model:
        print("✓ Gemini model successfully initialized")
        
        # Test with sample data
        sample_session_data = {
            'patient_info': {
                'name': 'John Doe',
                'diagnosis': 'Anxiety'
            },
            'transcript': 'Patient reports feeling anxious and worried about work. Mentions trouble sleeping and loss of appetite. Currently taking medication as prescribed.',
            'audio_events': [],
            'video_events': []
        }
        
        try:
            # Test the text analysis step
            import asyncio
            result = asyncio.run(workflow.step1_extract_text_meaning(
                sample_session_data['transcript'],
                sample_session_data['patient_info']
            ))
            
            print("✓ Text analysis completed successfully")
            print(f"  Symptoms found: {result.get('symptoms', [])}")
            print(f"  Sentiment: {result.get('sentiment', 'neutral')}")
            print(f"  Key topics: {result.get('key_topics', [])}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error during analysis: {e}")
            return False
    else:
        print("✗ Gemini model not initialized - check GEMINI_API_KEY environment variable")
        return False

if __name__ == "__main__":
    success = test_gemini_integration()
    if success:
        print("\n✓ All tests passed! Gemini integration is working correctly.")
    else:
        print("\n✗ Tests failed. Please check your configuration.")
        sys.exit(1)
