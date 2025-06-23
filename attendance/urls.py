from django.urls import path
from . import views

urlpatterns = [
    path("enrol/",      views.enrol_view,      name="enrol"),
    path("recognise/",  views.recognise_page,  name="recognise"),   # HTML page
    path("api/recognise/", views.recognise_api, name="recognise_api"),  # JSON POST
    path("dashboard/",  views.dashboard_view,  name="dashboard"),
    path("dashboard/export/", views.export_today_csv, name="export_today_csv"),
]
