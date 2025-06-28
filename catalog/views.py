from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect, get_object_or_404

from .forms  import (
    ProgrammeForm, MajorForm, SubjectForm,
    OfferingForm, TrimesterForm
)
from .models import Programme, Major, Subject, Offering, Trimester


# ─── root-only decorator (superuser) ─────────────────────
root_only = user_passes_test(lambda u: u.is_superuser, login_url="login")


# ─── index listing everything ───────────────────────────
@root_only
def curriculum_index(request):
    return render(request, "catalog/curriculum_index.html", {
        "programmes": Programme.objects.all(),
        "majors":     Major.objects.select_related("programme"),
        "subjects":   Subject.objects.all(),
        "trimesters": Trimester.objects.all(),
        "offerings":  Offering.objects.select_related("subject", "trimester", "lecturer"),
    })


# ─── generic create / edit helper ───────────────────────
def _crud(request, instance, form_cls, redirect_to="curriculum_index"):
    """
    Render <form>, save on POST, then redirect back to the index.
    """
    if request.method == "POST":
        form = form_cls(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect(redirect_to)
    else:
        form = form_cls(instance=instance)
    return render(request, "catalog/form.html", {"form": form})


# ─── Programme ──────────────────────────────────────────
@root_only
def programme_create(request):
    return _crud(request, Programme(), ProgrammeForm)

@root_only
def programme_edit(request, pk):
    return _crud(request, get_object_or_404(Programme, pk=pk), ProgrammeForm)


# ─── Major ──────────────────────────────────────────────
@root_only
def major_create(request):
    return _crud(request, Major(), MajorForm)

@root_only
def major_edit(request, pk):
    return _crud(request, get_object_or_404(Major, pk=pk), MajorForm)


# ─── Subject ────────────────────────────────────────────
@root_only
def subject_create(request):
    return _crud(request, Subject(), SubjectForm)

@root_only
def subject_edit(request, pk):
    return _crud(request, get_object_or_404(Subject, pk=pk), SubjectForm)


# ─── Trimester ──────────────────────────────────────────
@root_only
def trimester_create(request):
    return _crud(request, Trimester(), TrimesterForm)

@root_only
def trimester_edit(request, pk):
    return _crud(request, get_object_or_404(Trimester, pk=pk), TrimesterForm)


# ─── Offering / Class ───────────────────────────────────
@root_only
def offering_create(request):
    return _crud(request, Offering(), OfferingForm)

@root_only
def offering_edit(request, pk):
    return _crud(request, get_object_or_404(Offering, pk=pk), OfferingForm)
