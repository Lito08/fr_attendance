from django.urls import path
from . import views

urlpatterns = [
    path("sessions/new/",              views.CreateSessionView.as_view(), name="session_new"),
    path("sessions/<uuid:pk>/qr/",     views.session_qr_view,             name="session_qr"),
    path("sessions/<uuid:pk>/live/",   views.SessionLiveView.as_view(),   name="session_live"),
    path("sessions/<uuid:pk>/export/", views.session_csv,                 name="session_csv"),
    path("api/sessions/<uuid:pk>/<int:student_id>/toggle/",
         views.toggle_attendance_api,  name="toggle_attendance"),

    path("recognise/",     views.recognise_page, name="recognise"),
    path("recognise_api/", views.recognise_api,  name="recognise_api"),
]
