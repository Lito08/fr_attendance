"""
baseline.py – measure current accuracy / latency
Run: docker compose exec web python experiments/baseline.py /code/data/validation
"""
import pathlib, sys, os, json, numpy as np, face_recognition, time

# ── make Django settings importable ───────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parent.parent    # /code
sys.path.append(str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django; django.setup()

from attendance.models import Student
from attendance.utils  import find_match

VAL_DIR  = pathlib.Path(sys.argv[1])
students = list(Student.objects.all())

total = correct = 0
latencies = []

for img_path in VAL_DIR.glob("*.jpg"):
    label = img_path.stem.split("_")[0]
    img   = face_recognition.load_image_file(img_path)
    student, _, lat = find_match(img, students)
    latencies.append(lat)
    if student and student.user.username == label:
        correct += 1
    total += 1

res = {
    "total": total,
    "correct": correct,
    "accuracy": round(correct / total * 100, 2) if total else 0,
    "avg_latency_ms": int(np.mean(latencies)) if latencies else 0,
}
print(json.dumps(res, indent=2))
(ROOT / "experiments" / "baseline.json").write_text(json.dumps(res, indent=2))
