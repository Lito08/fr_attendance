import base64, io, json, secrets, uuid
import numpy as np, face_recognition

from django.contrib.auth import (
    get_user_model, login,
)
from django.contrib import messages
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.admin.views.decorators import staff_member_required, user_passes_test
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from django.db.models import Q

from attendance.utils  import find_match
from .models           import Student
from .forms            import AdminRegisterUserForm, UserForm

root_only = user_passes_test(lambda u: u.is_superuser, login_url="login")
User = get_user_model()

# ─── Root-only: create account + face template ──────────────────────────
@staff_member_required
def admin_register_user(request):
    if request.method == "POST":
        form = AdminRegisterUserForm(request.POST)
        if form.is_valid():
            full  = form.cleaned_data["full_name"].strip()
            role  = form.cleaned_data["role"]
            email = form.cleaned_data["email"].lower()
            frames= json.loads(form.cleaned_data["frames"])

            # username generator (sYYxxxxxx / lecYYxxxxxx)
            prefix   = "s" if role == "student" else "lec"
            username = f"{prefix}{timezone.now():%y}{uuid.uuid4().hex[:6]}"

            # build average encoding
            encs=[]
            for uri in frames:
                _, b64 = uri.split(",",1)
                img    = face_recognition.load_image_file(io.BytesIO(base64.b64decode(b64)))
                vec    = face_recognition.face_encodings(img)
                if vec: encs.append(vec[0])
            if not encs:
                return render(request, "attendance/register_user.html",
                              {"form": form, "error": "No face detected."})

            avg = np.mean(encs, axis=0) if encs else None

            # create user + student profile
            pw   = secrets.token_urlsafe(8)
            first,*last = full.split()
            user = User.objects.create_user(
                username=username,
                password=pw,
                email=email,
                first_name=first,
                last_name=" ".join(last),
                is_staff=(role=="lecturer"),
            )
            Student.objects.create(
                user=user,
                face_encoding=avg.tobytes(),
                must_change_password=True,
            )

            # email credentials (console backend in dev)
            send_mail(
                "FRA System login",
                f"Hi {full},\n\nUsername: {username}\nTemp password: {pw}\n"
                "Login: http://http://localhost:8000/login/\n",
                None,
                [email],
            )
            messages.success(request, f"User {username} created.")
            return redirect("user_list")
    else:
        form = AdminRegisterUserForm()

    return render(request, "accounts/register_user.html", {"form": form})

@root_only
def user_list_view(request):
    role  = request.GET.get("role", "")          # "", root, lecturer, student
    q     = request.GET.get("q", "").strip()
    sort  = request.GET.get("sort", "username")  # username, name, role, face

    qs = User.objects.all().select_related("student")

    if role == "root":
        qs = qs.filter(is_superuser=True)
    elif role == "lecturer":
        qs = qs.filter(is_staff=True, is_superuser=False)
    elif role == "student":
        qs = qs.filter(student__isnull=False, is_staff=False)

    if q:
        qs = qs.filter(
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q)
        )

    # map “face” to annotation for sorting
    if sort == "face":
        qs = qs.annotate(has_face=~Q(student__face_encoding=None)).order_by("-has_face")
    elif sort == "name":
        qs = qs.order_by("first_name", "last_name")
    else:      # username / role fallback
        qs = qs.order_by(sort)

    return render(request, "accounts/user_list.html", {
        "users": qs,
        "role":  role,
        "q":     q,
        "sort":  sort,
    })

@root_only
def user_edit_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    initial_role = ("root" if user.is_superuser else
                    "lecturer" if user.is_staff else "student")

    if request.method == "POST":
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            role = form.cleaned_data["role"]
            frames = json.loads(form.cleaned_data["frames"] or "[]")

            # update user flags
            user.is_superuser = (role == "root")
            user.is_staff     = (role in ("root", "lecturer"))
            form.save()

            # handle face template update if student + frames provided
            if role == "student":
                st, _ = Student.objects.get_or_create(user=user)
                if frames:
                    encs = []
                    for uri in frames:
                        # same decode logic ↓
                        _, b64 = uri.split(",",1)
                        img = face_recognition.load_image_file(io.BytesIO(base64.b64decode(b64)))
                        vec = face_recognition.face_encodings(img)
                        if vec: encs.append(vec[0])
                    if encs:
                        st.face_encoding = np.mean(encs,axis=0).tobytes()
                        st.save(update_fields=["face_encoding"])

            messages.success(request, "User updated.")
            return redirect("user_list")
    else:
        form = UserForm(instance=user, initial={"role": initial_role})

    return render(request, "accounts/user_form.html", {"form": form, "edit": True})

@csrf_exempt
@login_required          # we always know which user to update
def enrol_api(request):
    """
    Accepts JSON {frames:[dataURIs]} and overwrites the student's face
    encoding for the *currently logged-in* user (admin editing a student).
    Returns {"ok":True} or {"error":...}.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=400)

    try:
        frames = json.loads(request.body)["frames"]
    except Exception:
        return JsonResponse({"error": "bad payload"}, status=422)

    encs = []
    for uri in frames:
        try:
            _, b64 = uri.split(",", 1)
            img = face_recognition.load_image_file(io.BytesIO(base64.b64decode(b64)))
            fe  = face_recognition.face_encodings(img)
            if fe:
                encs.append(fe[0])
        except Exception:
            continue

    if not encs:
        return JsonResponse({"error": "no face found"}, status=422)

    avg = np.mean(encs, axis=0)
    stu, _ = Student.objects.get_or_create(user=request.user)
    stu.face_encoding = avg.tobytes()
    stu.must_change_password = False
    stu.save(update_fields=["face_encoding", "must_change_password"])

    return JsonResponse({"ok": True})

@root_only
def user_delete_view(request, pk):
    """
    Permanently delete a user account (and linked Student row if any).
    Only super-users can call this view.
    """
    user = get_object_or_404(User, pk=pk)

    # prevent accidental self-deletion
    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect("user_list")

    if request.method == "POST":
        user.delete()
        messages.success(request, "User deleted.")
        return redirect("user_list")

    # GET → simple confirmation page
    return render(request, "accounts/user_confirm_delete.html",
                  {"obj": user})
# ─── Auth helpers ───────────────────────────────────────────────────────
class FirstLoginCheckLoginView(LoginView):
    """
    After successful username/password login, force students with
    must_change_password=True to the password-change form.
    """
    def form_valid(self, form):
        resp = super().form_valid(form)
        try:
            if self.request.user.student.must_change_password:
                return redirect("password_change")
        except Student.DoesNotExist:
            pass
        return resp

class PasswordChangeAndFlagView(PasswordChangeView):
    template_name = "registration/password_change_form.html"
    success_url   = reverse_lazy("password_change_done")

    def form_valid(self, form):
        resp = super().form_valid(form)
        try:
            st = self.request.user.student
            if st.must_change_password:
                st.must_change_password = False
                st.save(update_fields=["must_change_password"])
        except Student.DoesNotExist:
            pass
        return resp

# ─── Face-login (no credentials) ────────────────────────────────────────
@csrf_exempt
def face_login_api(request):
    if request.method != "POST":
        return JsonResponse({"error":"POST only"}, status=400)

    try:
        _, b64 = json.loads(request.body)["frame"].split(",",1)
        img    = face_recognition.load_image_file(io.BytesIO(base64.b64decode(b64)))
    except Exception:
        return JsonResponse({"error":"bad image"}, status=400)

    student, *_ = find_match(img, list(Student.objects.select_related("user")))
    if not student:
        return JsonResponse({"error":"no match"}, status=404)

    login(request, student.user,
          backend="django.contrib.auth.backends.ModelBackend")

    dest = "/accounts/password_change/" if student.must_change_password else "/dashboard/"
    return JsonResponse({"ok": True, "redirect": dest})

@login_required
def profile_view(request):
    """
    Show full name, matric-ID (username), e-mail and a link to Django’s
    built-in password-change form.
    """
    student = Student.objects.filter(user=request.user).first()  # may be None for lecturers
    return render(request, "accounts/profile.html", {
        "student": student,
    })