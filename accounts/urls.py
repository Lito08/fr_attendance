from django.urls import path
from django.contrib.auth.views import PasswordChangeDoneView, LogoutView
from .views import (
    admin_register_user, FirstLoginCheckLoginView,
    PasswordChangeAndFlagView, face_login_api,
    profile_view, user_list_view, user_edit_view
)

urlpatterns = [
    path("register-user/", admin_register_user, name="register_user"),
    path("users/", user_list_view, name="user_list"),
    path("users/<int:pk>/", user_edit_view,      name="user_edit"),

    path("login/",  FirstLoginCheckLoginView.as_view(), name="login"),
    path("face_login_api/", face_login_api, name="face_login_api"),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),

    path("profile/", profile_view, name="profile"),
    path("accounts/password_change/", PasswordChangeAndFlagView.as_view(), name="password_change"),
    path("accounts/password_change/done/", PasswordChangeDoneView.as_view(template_name="registration/password_change_done.html"), name="password_change_done"),
]
