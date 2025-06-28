from django.urls import path
from django.contrib.auth.views import PasswordChangeDoneView
from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("login/", views.FirstLoginCheckLoginView.as_view(), name="login"),
    path("face_login_api/", views.face_login_api, name="face_login_api"),
    path("accounts/password_change/", views.PasswordChangeAndFlagView.as_view(), name="password_change"),
    path("accounts/password_change/done/", PasswordChangeDoneView.as_view(template_name="registration/password_change_done.html"), name="password_change_done"),
    
    path("enrol/", views.enrol_view, name="enrol"),
    path("enrol_api/", views.enrol_api, name="enrol_api"),
    path("recognise/", views.recognise_page, name="recognise"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("profile/", views.profile_view, name="profile"),
    
    path("recognise_api/", views.recognise_api, name="recognise_api"),
    path("export_today_csv/", views.export_today_csv, name="export_today_csv"),
]
