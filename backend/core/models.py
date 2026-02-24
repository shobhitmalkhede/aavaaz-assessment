from django.db import models
from django.utils import timezone
import uuid


class Patient(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    dob = models.DateField()
    address = models.TextField()
    diagnosis = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']


class Session(models.Model):
    STATUS_CHOICES = [
        ('STARTED', 'Started'),
        ('STOPPED', 'Stopped'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('ERROR', 'Error'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='sessions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='STARTED')
    started_at = models.DateTimeField(auto_now_add=True)
    stopped_at = models.DateTimeField(null=True, blank=True)
    
    # Transcript data
    final_transcript = models.TextField(null=True, blank=True)
    
    # Analysis data
    audio_events = models.JSONField(default=list, blank=True)
    video_events = models.JSONField(default=list, blank=True)
    
    # Insight report
    insight_report = models.JSONField(null=True, blank=True)
    
    def __str__(self):
        return f"Session {self.id} - {self.patient.name}"

    def stop(self):
        if self.status in ['STARTED', 'PROCESSING']:
            self.status = 'STOPPED'
            self.stopped_at = timezone.now()
            self.save()

    class Meta:
        ordering = ['-started_at']
