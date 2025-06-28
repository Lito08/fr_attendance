from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", include("attendance.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/password_reset/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("accounts/reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path('admin/', admin.site.urls),
]
