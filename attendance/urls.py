from django.urls import path
from . import views

urlpatterns = [
    path("enrol/",      views.enrol_view,     name="enrol"),
    path("enrol_api/", views.enrol_api, name="enrol_api"),
    path("recognise/",  views.recognise_page, name="recognise"),
    path("dashboard/",  views.dashboard_view, name="dashboard"),
    path("profile/",    views.profile_view,   name="profile"),
    path("recognise_api/", views.recognise_api, name="recognise_api"),
    path("export_today_csv/", views.export_today_csv, name="export_today_csv"),
]
