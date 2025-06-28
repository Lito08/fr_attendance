from django.contrib import admin
from .models import (
    Programme, Major, Subject, Requirement,
    Trimester, Offering
)

# ── Inline for requirements on Major admin ───────────────
class RequirementInline(admin.TabularInline):
    model = Requirement
    extra = 1

@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "credit_need")

@admin.register(Major)
class MajorAdmin(admin.ModelAdmin):
    list_display = ("code", "programme", "name")
    inlines      = [RequirementInline]

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display  = ("code", "title", "credit_hrs")
    filter_horizontal = ("prereqs",)

@admin.register(Trimester)
class TrimesterAdmin(admin.ModelAdmin):
    list_display = ("code", "start", "end")

@admin.register(Offering)
class OfferingAdmin(admin.ModelAdmin):
    list_display = ("subject", "trimester", "section", "lecturer", "room")
    list_filter  = ("trimester", "lecturer")
