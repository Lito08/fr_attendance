from django.urls import path
from . import views

urlpatterns = [
    path("",                  views.home_view,         name="home"),
    path("dashboard/",        views.dashboard_view,    name="dashboard"),
    path("export_today_csv/", views.export_today_csv,  name="export_today_csv"),
]
