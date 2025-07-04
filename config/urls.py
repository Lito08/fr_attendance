from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # Project apps
    path("", include("accounts.urls")),
    path("", include("classroom.urls")),
    path("", include("attendance.urls")),
    path("", include("catalog.urls")),
]
