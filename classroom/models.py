import uuid
from django.db import models
from django.utils import timezone

from accounts.models import Student
from catalog.models   import Offering


class ClassSession(models.Model):
    """
    One lecture / tutorial / lab slot bound to an Offering.
    """
    id        = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    offering  = models.ForeignKey(Offering, on_delete=models.CASCADE)
    start_at  = models.DateTimeField()
    end_at    = models.DateTimeField()
    room      = models.CharField(max_length=50, blank=True)
    created   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.offering} @ {self.start_at:%d-%b %H:%M}"


class AttendanceLog(models.Model):
    """
    One successful face-recognition tick for a student in a session.
    """
    student    = models.ForeignKey(Student,      on_delete=models.CASCADE)
    session    = models.ForeignKey(ClassSession, on_delete=models.CASCADE)
    timestamp  = models.DateTimeField(auto_now_add=True)
    verified   = models.BooleanField(default=True)   # liveness passed
    latency_ms = models.PositiveIntegerField()

    class Meta:
        ordering = ("-timestamp",)

    def __str__(self):
        return f"{self.student} {self.session} {self.timestamp:%d-%b %H:%M}"
