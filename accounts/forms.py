from django import forms


class AdminRegisterUserForm(forms.Form):
    ROLE_CHOICES = (("student", "Student"), ("lecturer", "Lecturer"))

    full_name = forms.CharField(label="Full name", max_length=80)
    email     = forms.EmailField()
    role      = forms.ChoiceField(choices=ROLE_CHOICES)
    frames    = forms.CharField(widget=forms.HiddenInput())   # JSON array
