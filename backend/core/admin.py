from django.contrib import admin
from .models import Patient, Session


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['name', 'dob', 'diagnosis', 'created_at']
    search_fields = ['name', 'diagnosis']
    list_filter = ['created_at']


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'patient', 'status', 'started_at', 'stopped_at']
    list_filter = ['status', 'started_at']
    search_fields = ['patient__name']
    readonly_fields = ['id']
