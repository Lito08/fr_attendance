from django import forms
from django.contrib.auth import get_user_model
from .models import Student

class AdminRegisterUserForm(forms.Form):
    ROLE_CHOICES = (
        ("student", "Student"),
        ("lecturer", "Lecturer"),
    )
    full_name = forms.CharField(label="Full name", max_length=80)
    role   = forms.ChoiceField(choices=ROLE_CHOICES)
    email  = forms.EmailField()
    # JavaScript will POST up to 5 frames as base64 strings
    frames = forms.CharField(widget=forms.HiddenInput())
