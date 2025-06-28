from django import forms
from django.contrib.auth import get_user_model
from .models import Student
User = get_user_model()

class AdminRegisterUserForm(forms.Form):
    ROLE_CHOICES = (("student", "Student"), ("lecturer", "Lecturer"))

    full_name = forms.CharField(label="Full name", max_length=80)
    email     = forms.EmailField()
    role      = forms.ChoiceField(choices=ROLE_CHOICES)
    frames    = forms.CharField(widget=forms.HiddenInput(), required=False)

class UserForm(forms.ModelForm):
    """Root can edit name / email / role; password via Django admin."""
    ROLE_CHOICES = (("student", "Student"), ("lecturer", "Lecturer"), ("root", "Root"))

    role  = forms.ChoiceField(choices=ROLE_CHOICES)
    frames = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model  = User
        fields = ["first_name", "last_name", "email"]