"""
optimise.py – Optuna search for best distance threshold τ
Run: docker compose exec web python experiments/optimise.py /code/data/validation
"""
import pathlib, sys, os, json, numpy as np, optuna, face_recognition, time

# ── Django setup ──────────────────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django; django.setup()

from attendance.models import Student

VAL_DIR   = pathlib.Path(sys.argv[1])
students  = list(Student.objects.all())
encodings = [np.frombuffer(s.face_encoding, dtype=np.float64) for s in students]
labels    = [s.user.username for s in students]

def evaluate(tau: float):
    good = total = 0
    times = []
    for img_path in VAL_DIR.glob("*.jpg"):
        image = face_recognition.load_image_file(img_path)
        encs  = face_recognition.face_encodings(image)
        if not encs: continue
        start = time.time()
        dist  = face_recognition.face_distance(encodings, encs[0])
        idx   = np.argmin(dist)
        times.append((time.time() - start) * 1000)
        if dist[idx] < tau and labels[idx] == img_path.stem.split("_")[0]:
            good += 1
        total += 1
    return (good / total), (np.mean(times) if times else 0)

def objective(trial):
    tau = trial.suggest_float("threshold", 0.40, 0.80, step=0.01)
    acc, lat = evaluate(tau)
    trial.set_user_attr("latency_ms", lat)
    return acc - (lat / 2000) * 0.1      # accuracy primary, slight latency penalty

study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=40)

best = study.best_params | {
    "accuracy": round(study.best_value, 4),
    "latency_ms": int(study.best_trial.user_attrs["latency_ms"]),
}

print("Best params:", best)
(ROOT / "experiments" / "best_params.json").write_text(json.dumps(best, indent=2))
