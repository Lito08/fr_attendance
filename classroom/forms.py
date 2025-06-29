# classroom/forms.py
from django import forms
from catalog.models import Offering          # or wherever Class lives
from classroom.models import ClassSession    # still your original model

class SessionForm(forms.ModelForm):
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

        # lecturer sees only their own classes
        if user is not None:
            self.fields["offering"].queryset = Offering.objects.filter(lecturer=user)
            self.fields["offering"].label_from_instance = lambda o: f"{o.subject.code} {o.section}"

        # add Bootstrap classes here – no template filter needed
        self.fields["offering"].widget.attrs["class"] = "form-select"
        for f in ("start_at", "end_at", "room"):
            self.fields[f].widget.attrs.update({"class": "form-control"})
