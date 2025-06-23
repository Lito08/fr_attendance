# attendance/views.py
import base64, io, csv, numpy as np, face_recognition
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Count

from .models import Student, AttendanceLog
from .utils  import find_match


# ─────────────────────────────────────────────────────────── ENROL ──
@login_required
def enrol_view(request):
    if request.method == "POST" and request.FILES.get("photo"):
        img_bytes = request.FILES["photo"].read()
        img       = face_recognition.load_image_file(io.BytesIO(img_bytes))
        encodings = face_recognition.face_encodings(img)

        if not encodings:
            return render(
                request,
                "attendance/enrol.html",
                {"error": "No face detected – try another photo."},
            )

        Student.objects.update_or_create(
            user=request.user,
            defaults={"face_encoding": encodings[0].tobytes()},
        )

        # success toast
        messages.success(request, "Face enrolled successfully!")
        return redirect("dashboard")

    return render(request, "attendance/enrol.html")


# ──────────────────────────────────────────────── REAL-TIME PAGE ──
@login_required
def recognise_page(request):
    return render(request, "attendance/recognise.html")


# ────────────────────────────────────────────────────────── API ──
@csrf_exempt   # demo: fetch() doesn't include CSRF token
@login_required
def recognise_api(request):
    """
    Expects frame in header X-Frame-Data: data:image/jpeg;base64,...
    Returns JSON with match info.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=400)

    data_uri = request.POST.get("frame") or request.headers.get("X-Frame-Data")
    if not data_uri:
        return JsonResponse({"error": "no frame"}, status=400)

    _, b64 = data_uri.split(",", 1)
    img_bytes = base64.b64decode(b64)
    img       = face_recognition.load_image_file(io.BytesIO(img_bytes))

    students = Student.objects.select_related("user")
    student, dist, latency = find_match(img, list(students))

    if student:
        AttendanceLog.objects.create(
            student=student, latency_ms=latency, verified=True
        )
        name = student.user.get_full_name() or student.user.username
        return JsonResponse(
            {"match": True, "name": name, "distance": round(dist, 3), "latency": latency}
        )

    return JsonResponse({"match": False, "latency": latency})


# ────────────────────────────────────────────────── DASHBOARD ──
@login_required
def dashboard_view(request):
    today = timezone.localdate()
    logs_today = AttendanceLog.objects.filter(timestamp__date=today)

    start = today - timedelta(days=6)
    qs = (
        AttendanceLog.objects
        .filter(timestamp__date__gte=start)
        .values("timestamp__date")
        .annotate(total=Count("id"))
        .order_by("timestamp__date")
    )
    counts = {row["timestamp__date"]: row["total"] for row in qs}
    labels = [start + timedelta(days=i) for i in range(7)]
    values = [counts.get(d, 0) for d in labels]

    ctx = {
        "logs_today": logs_today,
        "labels": [d.strftime("%d %b") for d in labels],
        "values": values,
    }
    return render(request, "attendance/dashboard.html", ctx)


# ─────────────────────────────────────────────── CSV EXPORT ──
@login_required
def export_today_csv(request):
    today = timezone.localdate()
    logs  = AttendanceLog.objects.filter(timestamp__date=today)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="attendance_{today}.csv"'
    writer = csv.writer(response)
    writer.writerow(["Username", "Timestamp", "Latency (ms)", "Verified"])
    for log in logs.select_related("student__user"):
        writer.writerow([
            log.student.user.username,
            log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            log.latency_ms,
            "yes" if log.verified else "no",
        ])
    return response
