import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# ───────────── 1  Programme (whole degree) ───────────────
class Programme(models.Model):
    code        = models.CharField(max_length=10, unique=True)     # BCS
    name        = models.CharField(max_length=120)
    credit_need = models.PositiveSmallIntegerField()               # 120

    def __str__(self):
        return self.name

# ───────────── 2  Major (inside a programme) ─────────────
class Major(models.Model):
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE)
    code      = models.CharField(max_length=10)                    # CYB
    name      = models.CharField(max_length=120)

    class Meta:
        unique_together = ("programme", "code")

    def __str__(self):
        return f"{self.code} – {self.programme.code}"

# ───────────── 3  Subject (a course unit) ────────────────
class Subject(models.Model):
    code       = models.CharField(max_length=10, unique=True)      # CSC2204
    title      = models.CharField(max_length=120)
    credit_hrs = models.PositiveSmallIntegerField()
    prereqs    = models.ManyToManyField("self", symmetrical=False, blank=True)

    def __str__(self):
        return f"{self.code} – {self.title}"

# ───────────── 4  Requirement (core / elective) ─────────
class Requirement(models.Model):
    CORE       = "core"
    MAJOR_CORE = "major"
    ELECTIVE   = "elective"
    KIND_CHOICES = [
        (CORE,       "Programme core"),
        (MAJOR_CORE, "Major core"),
        (ELECTIVE,   "Elective"),
    ]

    major   = models.ForeignKey(Major, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    kind    = models.CharField(max_length=8, choices=KIND_CHOICES)

    class Meta:
        unique_together = ("major", "subject")

# ───────────── 5  Trimester / term ──────────────────────
class Trimester(models.Model):
    code  = models.CharField(max_length=12, unique=True)           # 2025T1
    start = models.DateField()
    end   = models.DateField()

    def __str__(self):
        return self.code

# ───────────── 6  Offering (subject in a term) ──────────
class Offering(models.Model):
    id        = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject   = models.ForeignKey(Subject, on_delete=models.CASCADE)
    trimester = models.ForeignKey(Trimester, on_delete=models.CASCADE)
    lecturer  = models.ForeignKey(User,
                                  on_delete=models.CASCADE,
                                  limit_choices_to={"is_staff": True})
    section   = models.CharField(max_length=20, default="")
    room      = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together = ("subject", "trimester", "lecturer", "section")

    def __str__(self):
        return f"{self.subject.code} {self.trimester.code}"
