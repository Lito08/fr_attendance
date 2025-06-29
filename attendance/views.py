import csv, io
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import FileResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from classroom.models import AttendanceLog


# ─── Landing: / -> dashboard or login ────────────────────
def home_view(request):
    if not request.user.is_authenticated:
        return redirect("login")
    return redirect("dashboard")

# ─── Dashboard (7-day chart + today’s list) ─────────────
@login_required
def dashboard_view(request):
    today = timezone.localdate()
    today_qs = AttendanceLog.objects.filter(timestamp__date=today)

    start = today - timedelta(days=6)
    qs = (AttendanceLog.objects.filter(timestamp__date__gte=start)
          .values("timestamp__date")
          .annotate(total=Count("id"))
          .order_by("timestamp__date"))
    totals = {row["timestamp__date"]: row["total"] for row in qs}
    labels = [start + timedelta(days=i) for i in range(7)]
    values = [totals.get(d, 0) for d in labels]
    
    rows   = list(zip(labels, values))

    return render(request, "attendance/dashboard.html", {
        "logs_today": today_qs,
        "rows": rows,
        "labels": [d.strftime("%d %b") for d in labels],
        "values": values,
        "total_week": sum(values),
    })

# ─── CSV export for today ───────────────────────────────
@login_required
def export_today_csv(request):
    today = timezone.localdate()
    logs  = AttendanceLog.objects.filter(timestamp__date=today)\
                                 .select_related("student__user")

    buf = io.StringIO()
    w   = csv.writer(buf)
    w.writerow(["Username", "Timestamp", "Latency (ms)", "Verified"])
    for lg in logs:
        w.writerow([
            lg.student.user.username,
            lg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            lg.latency_ms,
            "yes" if lg.verified else "no",
        ])
    buf.seek(0)
    return FileResponse(
        io.BytesIO(buf.read().encode()),
        as_attachment=True,
        filename=f"attendance_{today}.csv",
    )
