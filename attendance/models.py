from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Student(models.Model):
    user          = models.OneToOneField(User, on_delete=models.CASCADE)
    face_encoding = models.BinaryField()            # 128-d NumPy vector → bytes
    created       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class AttendanceLog(models.Model):
    student    = models.ForeignKey(Student, on_delete=models.CASCADE)
    timestamp  = models.DateTimeField(auto_now_add=True)
    verified   = models.BooleanField(default=True)  # liveness passed?
    latency_ms = models.PositiveIntegerField()