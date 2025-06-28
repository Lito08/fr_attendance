from django.contrib import admin
from .models import ClassSession, AttendanceLog


@admin.register(ClassSession)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("id", "offering", "start_at", "end_at", "room", "created")
    list_filter  = ("offering__trimester", "offering__subject")


@admin.register(AttendanceLog)
class LogAdmin(admin.ModelAdmin):
    list_display = ("student", "session", "timestamp", "verified", "latency_ms")
    list_filter  = ("session", "verified")
