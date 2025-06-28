from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from .forms import (
    ProgrammeForm, MajorForm, SubjectForm,
    OfferingForm, TrimesterForm
)
from .models import Programme, Major, Subject, Offering, Trimester

# decorator: only superusers (root)
root_only = user_passes_test(lambda u: u.is_superuser, login_url="login")

# ─── index listing everything ────────────────────────────
@root_only
def curriculum_index(request):
    return render(request, "catalog/curriculum_index.html", {
        "programmes": Programme.objects.all(),
        "majors":     Major.objects.select_related("programme"),
        "subjects":   Subject.objects.all(),
        "trimesters": Trimester.objects.all(),
        "offerings":  Offering.objects.select_related("subject","trimester","lecturer"),
    })

# generic helpers ----------------------------------------------------------
def _crud(request, queryset, form_cls, tmpl, redirect_to):
    obj = queryset if isinstance(queryset, (Programme, Major, Subject, Offering, Trimester)) else None
    if request.method == "POST":
        form = form_cls(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect(redirect_to)
    else:
        form = form_cls(instance=obj)
    return render(request, tmpl, {"form": form})

# ─── create / edit views ─────────────────────────────────
@root_only
def programme_create(request):
    return _crud(request, Programme(), ProgrammeForm,
                 "catalog/form.html", "curriculum_index")

@root_only
def programme_edit(request, pk):
    return _crud(request, get_object_or_404(Programme, pk=pk), ProgrammeForm,
                 "catalog/form.html", "curriculum_index")

@root_only
def major_create(request):
    return _crud(request, Major(), MajorForm, "catalog/form.html", "curriculum_index")

@root_only
def major_edit(request, pk):
    return _crud(request, get_object_or_404(Major, pk=pk), MajorForm,
                 "catalog/form.html", "curriculum_index")

@root_only
def subject_create(request):
    return _crud(request, Subject(), SubjectForm, "catalog/form.html", "curriculum_index")

@root_only
def subject_edit(request, pk):
    return _crud(request, get_object_or_404(Subject, pk=pk), SubjectForm,
                 "catalog/form.html", "curriculum_index")

@root_only
def trimester_create(request):
    return _crud(request, Trimester(), TrimesterForm, "catalog/form.html", "curriculum_index")

@root_only
def offering_create(request):
    return _crud(request, Offering(), OfferingForm, "catalog/form.html", "curriculum_index")
