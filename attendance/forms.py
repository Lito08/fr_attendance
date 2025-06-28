from django import forms
from django.contrib.auth import get_user_model
from .models import Subject, ClassSession

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
    
class SessionForm(forms.ModelForm):
    class Meta:
        model  = ClassSession
        fields = ["subject", "start_at", "end_at", "room"]
        widgets = {
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_at":   forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kw):
        user = kw.pop("user", None)
        super().__init__(*args, **kw)
        if user is not None:
            self.fields["subject"].queryset = Subject.objects.filter(owner=user)