from django.urls import path
from . import views

urlpatterns = [
    path('patients/', views.PatientView.as_view(), name='patient-list-create'),
    path('sessions/', views.SessionView.as_view(), name='session-list-create'),
    path('sessions/<uuid:session_id>/', views.SessionView.as_view(), name='session-detail'),
    path('sessions/<uuid:session_id>/stop/', views.stop_session, name='session-stop'),
]
