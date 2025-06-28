import base64, csv, io, os, time, json, uuid, secrets
import numpy as np, face_recognition
from pathlib import Path
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail
from django.urls import reverse_lazy

from .models import Student, AttendanceLog, User
from .utils  import find_match
from .forms  import AdminRegisterUserForm

@staff_member_required
def admin_register_user(request):
    if request.method == "POST":
        form = AdminRegisterUserForm(request.POST)
        if form.is_valid():
            role   = form.cleaned_data["role"]
            email  = form.cleaned_data["email"].lower()
            frames = json.loads(form.cleaned_data["frames"])

            # --- username generator ---
            prefix = "s" if role == "student" else "lec"
            username = f"{prefix}{timezone.now():%y}{uuid.uuid4().hex[:6]}"

            # --- face encoding averaging ---
            enc_list = []
            for uri in frames:
                _, b64 = uri.split(",", 1)
                img = face_recognition.load_image_file(io.BytesIO(base64.b64decode(b64)))
                enc = face_recognition.face_encodings(img)
                if enc:
                    enc_list.append(enc[0])
            if not enc_list:
                messages.error(request, "No face detected in frames.")
                return redirect("register_user")

            avg = np.mean(enc_list, axis=0)

            # --- create user & student row ---
            temp_pass = secrets.token_urlsafe(8)
            user = User.objects.create_user(
                username=username,
                password=temp_pass,
                email=email,
                is_staff = role == "lecturer"
            )
            if role == "student":
                Student.objects.create(
                    user=user,
                    face_encoding=avg.tobytes(),
                    must_change_password=True
                )

            # --- send email ---
            subject = "Your F-Rec Attendance login"
            body    = (f"Hi,\n\nYour account has been created.\n"
                       f"Username: {username}\n"
                       f"Temporary password: {temp_pass}\n\n"
                       "Log in at https://attendance.youruni.edu/login/\n"
                       "You will be asked to set a new password.\n\n"
                       "Regards,\nAdmin")
            send_mail(subject, body, None, [email])

            messages.success(request, f"User {username} created & e-mailed.")
            return redirect("register_user")
    else:
        form = AdminRegisterUserForm()

    return render(request, "attendance/register_user.html", {"form": form})

class FirstLoginCheckLoginView(LoginView):
    """
    After authenticating, redirect students who must change their password.
    """
    def form_valid(self, form):
        response = super().form_valid(form)
        # Only students have the flag
        try:
            if self.request.user.student.must_change_password:
                return redirect("password_change")
        except Student.DoesNotExist:
            pass  # Lecturer or admin — skip
        return response
    
class PasswordChangeAndFlagView(PasswordChangeView):
    success_url = reverse_lazy("password_change_done")  # or wherever
    template_name = "registration/password_change_form.html"

    def form_valid(self, form):
        # call super() first so the password is actually changed
        response = super().form_valid(form)
        # flip the flag
        try:
            student = self.request.user.student
            if student.must_change_password:
                student.must_change_password = False
                student.save(update_fields=["must_change_password"])
        except Student.DoesNotExist:
            pass
        return response

def home_view(request):
    """
    If you’re logged in, go to dashboard.
    Otherwise, send you to the login page.
    """
    if not request.user.is_authenticated:
        return redirect("login")
    return redirect("dashboard")

# ───── ENROL ────────────────────────────────────────────
@login_required
def enrol_view(request):
    if request.method == "POST" and request.FILES.get("photo"):
        img_bytes=request.FILES["photo"].read()
        img=face_recognition.load_image_file(io.BytesIO(img_bytes))
        enc=face_recognition.face_encodings(img)
        if not enc:
            return render(request,"attendance/enrol.html",{"error":"No face detected."})
        Student.objects.update_or_create(
            user=request.user, defaults={"face_encoding":enc[0].tobytes()}
        )
        messages.success(request,"Face enrolled successfully!")
        return redirect("dashboard")
    return render(request,"attendance/enrol.html")

@csrf_exempt
@login_required
def enrol_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=400)

    try:
        data   = json.loads(request.body)
        frames = data["frames"]
    except (ValueError, KeyError):
        return JsonResponse({"error": "bad payload"}, status=422)

    # —── Save frames to disk ───────────────────────────────
    username = request.user.username
    data_root = Path(settings.BASE_DIR) / "data" / "enrol" / username
    data_root.mkdir(parents=True, exist_ok=True)

    for idx, uri in enumerate(frames):
        try:
            header, b64 = uri.split(",", 1)
            img_data    = base64.b64decode(b64)
        except Exception:
            continue
        # use a timestamp to avoid name collisions
        fname = data_root / f"{int(time.time()*1000)}_{idx}.jpg"
        fname.write_bytes(img_data)

    # —── Now do the averaging and DB save (same as before) ───
    enc_list = []
    for uri in frames:
        try:
            _, b64 = uri.split(",", 1)
            img    = face_recognition.load_image_file(io.BytesIO(base64.b64decode(b64)))
            encs   = face_recognition.face_encodings(img)
            if encs:
                enc_list.append(encs[0])
        except Exception:
            continue

    if not enc_list:
        return JsonResponse({"error": "no face found"}, status=422)

    avg = np.mean(enc_list, axis=0)
    Student.objects.update_or_create(
        user=request.user, defaults={"face_encoding": avg.tobytes()}
    )

    return JsonResponse({"ok": True, "redirect": "/dashboard/"})

@login_required
def profile_view(request):
    """Show current enrol status and let the user re-enrol."""
    student = Student.objects.filter(user=request.user).first()

    # POST behaves exactly like enrol: overwrite encoding
    if request.method == "POST" and request.FILES.get("photo"):
        img_bytes = request.FILES["photo"].read()
        img = face_recognition.load_image_file(io.BytesIO(img_bytes))
        enc = face_recognition.face_encodings(img)

        if not enc:
            return render(request, "attendance/profile.html",
                          {"student": student,
                           "error": "No face detected – try another photo."})

        Student.objects.update_or_create(
            user=request.user, defaults={"face_encoding": enc[0].tobytes()}
        )
        messages.success(request, "Face template updated!")
        return redirect("profile")

    return render(request, "attendance/profile.html", {"student": student})

# ───── RECOGNISE PAGE ───────────────────────────────────
@login_required
def recognise_page(request):
    return render(request,"attendance/recognise.html")

# ───── API ──────────────────────────────────────────────
@csrf_exempt
@login_required
def recognise_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=400)

    # 1) Try JSON body first
    data_uri = None
    if request.content_type == "application/json":
        try:
            payload = json.loads(request.body)
            data_uri = payload.get("frame")
        except json.JSONDecodeError:
            return JsonResponse({"error": "invalid JSON"}, status=400)

    # 2) Fallback to header or form
    if not data_uri:
        data_uri = request.POST.get("frame") or request.headers.get("X-Frame-Data")

    if not data_uri:
        return JsonResponse({"error": "no frame"}, status=400)

    # Strip the "data:image/…" prefix
    try:
        _, b64 = data_uri.split(",", 1)
    except ValueError:
        return JsonResponse({"error": "invalid frame data"}, status=400)

    # Decode & load image
    try:
        img_bytes = base64.b64decode(b64)
        img = face_recognition.load_image_file(io.BytesIO(img_bytes))
    except Exception:
        return JsonResponse({"error": "cannot decode image"}, status=400)

    # Run matching logic
    students = Student.objects.select_related("user").all()
    student, dist, latency = find_match(img, list(students))

    if student:
        # Log attendance on success
        AttendanceLog.objects.create(
            student=student, latency_ms=latency, verified=True
        )
        name = student.user.get_full_name() or student.user.username
        return JsonResponse({
            "match": True,
            "name": name,
            "distance": round(dist, 3),
            "latency": latency,
        })

    # No match
    return JsonResponse({"match": False, "latency": latency})

@csrf_exempt
def face_login_api(request):
    """
    Accept a single camera frame, try to match a user, and log them in.
    Returns JSON {ok, redirect} on success or {error} on failure.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=400)

    try:
        payload  = json.loads(request.body)
        data_uri = payload["frame"]
        _, b64   = data_uri.split(",", 1)
        img      = face_recognition.load_image_file(io.BytesIO(base64.b64decode(b64)))
    except Exception:
        return JsonResponse({"error": "bad image"}, status=400)

    students = Student.objects.select_related("user").all()
    student, dist, latency = find_match(img, list(students))

    if student:
        # ----- log user in -----
        login(request, student.user, backend="django.contrib.auth.backends.ModelBackend")

        # ----- where to send them? -----
        if getattr(student, "must_change_password", False):
            redirect_url = "/accounts/password_change/"
        else:
            redirect_url = "/dashboard/"

        # log attendance automatically if you like:
        # AttendanceLog.objects.create(student=student, verified=True, latency_ms=latency)

        return JsonResponse({"ok": True, "redirect": redirect_url})

    return JsonResponse({"error": "no match"}, status=404)
# ───── DASHBOARD & CSV ──────────────────────────────────
@login_required
def dashboard_view(request):
    today=timezone.localdate()
    logs_today=AttendanceLog.objects.filter(timestamp__date=today)
    start=today-timedelta(days=6)
    qs=(AttendanceLog.objects.filter(timestamp__date__gte=start)
        .values("timestamp__date").annotate(total=Count("id")).order_by("timestamp__date"))
    counts={row["timestamp__date"]:row["total"] for row in qs}
    labels=[start+timedelta(days=i) for i in range(7)]
    values=[counts.get(d,0) for d in labels]
    return render(request,"attendance/dashboard.html",{
        "logs_today":logs_today,
        "labels":[d.strftime("%d %b") for d in labels],
        "values":values,
    })

@login_required
def export_today_csv(request):
    today=timezone.localdate()
    logs=AttendanceLog.objects.filter(timestamp__date=today)
    resp=HttpResponse(content_type="text/csv")
    resp["Content-Disposition"]=f'attachment; filename="attendance_{today}.csv"'
    w=csv.writer(resp); w.writerow(["Username","Timestamp","Latency (ms)","Verified"])
    for log in logs.select_related("student__user"):
        w.writerow([log.student.user.username,log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    log.latency_ms,"yes" if log.verified else "no"])
    return resp
