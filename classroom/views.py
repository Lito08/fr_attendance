import base64, io, json, qrcode
import numpy as np, face_recognition
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import (
    get_object_or_404, redirect, render
)
from django.views.generic import CreateView, DetailView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, FileResponse
from django.db.models import Count
from django.urls import reverse
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from accounts.models     import Student
from attendance.utils    import find_match
from .forms              import SessionForm
from .models             import ClassSession, AttendanceLog

from django.contrib import messages
from django.urls import reverse
import socket

LAN_IP = "192.168.68.114"
channel_layer = get_channel_layer()

# ─── mixin for lecturer-only views ───────────────────────
class LecturerRequired(UserPassesTestMixin):
    def test_func(self):
        u = self.request.user
        return u.is_staff and not u.is_superuser


# ─── create session form ─────────────────────────────────
class CreateSessionView(LecturerRequired, CreateView):
    model         = ClassSession
    form_class    = SessionForm
    template_name = "attendance/session_form.html"

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["user"] = self.request.user
        return kw

    def get_success_url(self):
        return reverse("session_qr", args=[self.object.pk])


# ─── QR page ─────────────────────────────────────────────
@login_required
def session_qr_view(request, pk):
    sess = get_object_or_404(ClassSession, pk=pk)

    # absolute HTTPS URL, e.g. https://192.168.68.114/checkin/<uuid>/
    url = request.build_absolute_uri(
        reverse("session_checkin", args=[pk])
    )

    buf = io.BytesIO()
    qrcode.make(url).save(buf, format="PNG")
    qr = base64.b64encode(buf.getvalue()).decode()

    return render(request, "attendance/session_qr.html",
                  {"session": sess, "qr": qr, "url": url})

@login_required
def session_checkin_view(request, pk):
    """
    GET  /checkin/<session-uuid>/

    • must be a student
    • create one AttendanceLog row per student+session
    • second (or later) scans do NOT increment the head-count,
      but show a gentle “already present” message.
    """
    sess = get_object_or_404(ClassSession, pk=pk)

    # ----- only students allowed ------------------------------------------------
    try:
        student = request.user.student
    except AttributeError:
        return render(request, "attendance/not_student.html", status=403)

    # ----- create-or-fetch log row ---------------------------------------------
    log, created = AttendanceLog.objects.get_or_create(
        session  = sess,
        student  = student,
        defaults = {"verified": False, "latency_ms": 0},
    )

    if created:
        # 1st scan → notify live roster
        async_to_sync(channel_layer.group_send)(
            f"sess_{sess.pk}",
            {"type": "attendance.event",
             "payload": {"action": "add",
                         "user": student.user.username}}
        )
        msg = "✓ Your attendance has been recorded."
    else:
        # duplicate scan → no counter bump
        msg = "You’re already marked present for this class."

    messages.success(request, msg)

    # tiny thank-you page (auto-redirect after 2 s)
    return render(request, "attendance/checkin_done.html",
                  {"session": sess, "duplicate": not created})

# ─── live roster page ───────────────────────────────────
class SessionLiveView(LecturerRequired, DetailView):
    model = ClassSession
    template_name = "attendance/session_live.html"
    context_object_name = "session"


# ─── manual toggle API ──────────────────────────────────
@login_required
def toggle_attendance_api(request, pk, student_id):
    sess = get_object_or_404(ClassSession, pk=pk)
    if not (request.user.is_staff and sess.offering.lecturer == request.user):
        return JsonResponse({"error": "forbidden"}, status=403)

    st  = get_object_or_404(Student, pk=student_id)
    log, created = AttendanceLog.objects.get_or_create(
        session=sess, student=st,
        defaults={"verified": True, "latency_ms": 0},
    )
    if not created:
        log.delete()
    return JsonResponse({"present": created})


# ─── CSV export ─────────────────────────────────────────
@login_required
def session_csv(request, pk):
    sess = get_object_or_404(ClassSession, pk=pk)
    if not (request.user.is_staff and sess.offering.lecturer == request.user):
        return FileResponse(io.BytesIO(b"Forbidden"), status=403)

    logs = AttendanceLog.objects.filter(session=sess)\
                                .select_related("student__user")
    buf = io.StringIO()
    import csv; w = csv.writer(buf)
    w.writerow(["Username", "Timestamp"])
    for log in logs:
        w.writerow([log.student.user.username,
                    log.timestamp.strftime("%Y-%m-%d %H:%M:%S")])
    buf.seek(0)
    return FileResponse(
        io.BytesIO(buf.read().encode()),
        as_attachment=True,
        filename=f"attendance_{sess.id}.csv"
    )


# ─── recognise page (camera) ────────────────────────────
@login_required
def recognise_page(request):
    return render(request, "attendance/recognise.html")


# ─── recognise API (face match + log) ───────────────────
@csrf_exempt
@login_required
def recognise_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=400)

    try:
        _, b64 = json.loads(request.body)["frame"].split(",", 1)
        img    = face_recognition.load_image_file(io.BytesIO(base64.b64decode(b64)))
    except Exception:
        return JsonResponse({"error": "bad image"}, status=400)

    student, dist, latency = find_match(img,
        list(Student.objects.select_related("user")))
    if not student:
        return JsonResponse({"match": False})

    # attach to session if ?session=uuid present
    session_id = request.GET.get("session")
    sess = ClassSession.objects.filter(pk=session_id).first() if session_id else None

    AttendanceLog.objects.create(
        student=student, session=sess,
        latency_ms=latency, verified=True
    )

    if sess:
        async_to_sync(channel_layer.group_send)(
            f"sess_{sess.pk}",
            {"type":"attendance.event",
             "payload":{"action":"add","user":student.user.username}}
        )

    return JsonResponse({
        "match":    True,
        "name":     student.user.get_full_name() or student.user.username,
        "distance": round(dist, 3),
        "latency":  latency,
    })
