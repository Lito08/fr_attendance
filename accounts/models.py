from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Student(models.Model):
    user                 = models.OneToOneField(User, on_delete=models.CASCADE)
    face_encoding        = models.BinaryField(blank=True, null=True)          # 128-D vector → bytes
    must_change_password = models.BooleanField(default=True)
    created              = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username
