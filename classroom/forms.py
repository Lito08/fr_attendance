from django import forms
from .models import ClassSession
from catalog.models import Offering


class SessionForm(forms.ModelForm):
    """
    Lecturer chooses one of *their* offerings + date/time window.
    """
    class Meta:
        model  = ClassSession
        fields = ["offering", "start_at", "end_at", "room"]
        widgets = {
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_at":   forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kw):
        user = kw.pop("user", None)
        super().__init__(*args, **kw)
        if user is not None:
            self.fields["offering"].queryset = Offering.objects.filter(lecturer=user)
