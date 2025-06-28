from django import forms
from .models import Programme, Major, Subject, Offering, Trimester

class ProgrammeForm(forms.ModelForm):
    class Meta:
        model  = Programme
        fields = ["code", "name", "credit_need"]

class MajorForm(forms.ModelForm):
    class Meta:
        model  = Major
        fields = ["programme", "code", "name"]

class SubjectForm(forms.ModelForm):
    class Meta:
        model  = Subject
        fields = ["code", "title", "credit_hrs", "prereqs"]
        widgets = {"prereqs": forms.CheckboxSelectMultiple}

class OfferingForm(forms.ModelForm):
    class Meta:
        model  = Offering
        fields = ["subject", "trimester", "lecturer", "room"]

class TrimesterForm(forms.ModelForm):
    class Meta:
        model  = Trimester
        fields = ["code", "start", "end"]
        widgets = {
            "start": forms.DateInput(attrs={"type": "date"}),
            "end":   forms.DateInput(attrs={"type": "date"}),
        }
