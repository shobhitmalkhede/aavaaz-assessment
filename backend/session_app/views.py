from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import uuid
from datetime import datetime
from core.models import Patient, Session


class PatientView(APIView):
    def post(self, request):
        """Create a new patient"""
        try:
            data = request.data  # DRF automatically parses JSON
            
            patient = Patient.objects.create(
                name=data['name'],
                dob=data['dob'],
                address=data['address'],
                diagnosis=data['diagnosis']
            )
            
            return JsonResponse({
                'id': str(patient.id),
                'name': patient.name,
                'dob': str(patient.dob),
                'address': patient.address,
                'diagnosis': patient.diagnosis,
                'created_at': patient.created_at.isoformat()
            }, status=201)
            
        except KeyError as e:
            return JsonResponse({'error': f'Invalid data: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def get(self, request):
        """List all patients"""
        patients = Patient.objects.all()
        data = []
        for patient in patients:
            data.append({
                'id': str(patient.id),
                'name': patient.name,
                'dob': str(patient.dob),
                'address': patient.address,
                'diagnosis': patient.diagnosis,
                'created_at': patient.created_at.isoformat()
            })
        
        return JsonResponse(data, safe=False)


class SessionView(APIView):
    def post(self, request):
        """Create a new session"""
        try:
            data = request.data  # DRF automatically parses JSON
            patient_id = data['patient_id']
            
            patient = Patient.objects.get(id=patient_id)
            
            session = Session.objects.create(
                patient=patient,
                status='STARTED'
            )
            
            return JsonResponse({
                'id': str(session.id),
                'patient_id': str(session.patient.id),
                'patient_name': session.patient.name,
                'status': session.status,
                'started_at': session.started_at.isoformat()
            }, status=201)
            
        except Patient.DoesNotExist:
            return JsonResponse({'error': 'Patient not found'}, status=404)
        except KeyError as e:
            return JsonResponse({'error': f'Invalid data: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def get(self, request, session_id=None):
        """Get session details or list sessions"""
        if session_id:
            try:
                session = Session.objects.get(id=session_id)
                data = {
                    'id': str(session.id),
                    'patient_id': str(session.patient.id),
                    'patient_name': session.patient.name,
                    'status': session.status,
                    'started_at': session.started_at.isoformat(),
                    'stopped_at': session.stopped_at.isoformat() if session.stopped_at else None,
                    'final_transcript': session.final_transcript,
                    'audio_events': session.audio_events,
                    'video_events': session.video_events,
                    'insight_report': session.insight_report
                }
                return JsonResponse(data)
            except Session.DoesNotExist:
                return JsonResponse({'error': 'Session not found'}, status=404)
        else:
            # List all sessions
            sessions = Session.objects.all()
            data = []
            for session in sessions:
                data.append({
                    'id': str(session.id),
                    'patient_id': str(session.patient.id),
                    'patient_name': session.patient.name,
                    'status': session.status,
                    'started_at': session.started_at.isoformat(),
                    'stopped_at': session.stopped_at.isoformat() if session.stopped_at else None
                })
            return JsonResponse(data, safe=False)


@api_view(['POST'])
def stop_session(request, session_id):
    """Stop a session"""
    try:
        session = Session.objects.get(id=session_id)
        session.stop()
        
        return Response({
            'id': str(session.id),
            'status': session.status,
            'stopped_at': session.stopped_at.isoformat() if session.stopped_at else None
        })
        
    except Session.DoesNotExist:
        return Response({'error': 'Session not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
