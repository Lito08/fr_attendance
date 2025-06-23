#!/usr/bin/env python
import json, time, cv2, optuna, numpy as np, face_recognition, sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(sys.argv[1])  # e.g. /code/data/validation

# ---------------------------------------------------------------------------
def evaluate(tau, resize):
    correct = 0; latencies = []
    subjects = [p for p in DATA_DIR.iterdir() if p.is_dir()]
    if not subjects:
        print(f"No subject directories found in {DATA_DIR!r}.")
        print("Please create data/validation/<subjectname>/ with some .jpg files.")
        sys.exit(1)
    for subj in subjects:
        encs = []
        for img_path in subj.glob("*.jpg"):
            img = face_recognition.load_image_file(img_path)
            if resize != 1.0:
                h, w = img.shape[:2]
                img = cv2.resize(img, (int(w*resize), int(h*resize)))
            enc = face_recognition.face_encodings(img)
            if enc: encs.append(enc[0])

        if not encs: continue
        ref = np.mean(encs[:-1], axis=0)        # use N-1 images as template
        test= encs[-1]                          # last image as probe

        t0 = time.time()
        dist = np.linalg.norm(test - ref)
        latencies.append((time.time()-t0)*1000)

        if dist < tau: correct += 1

    total = len(subjects)
    acc   = correct / total
    if latencies:
        avg_lat = sum(latencies) / len(latencies)
    else:
        avg_lat = float("inf")
    return acc, avg_lat

# ---------------------------------------------------------------------------
def objective(trial):
    tau    = trial.suggest_float("threshold", 0.30, 0.80, step=0.01)
    resize = trial.suggest_float("resize",    0.25, 1.0,  step=0.05)

    acc, lat = evaluate(tau, resize)
    trial.set_user_attr("latency", lat)
    # we want highest accuracy; Optuna maximises by default
    return acc

study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=40)

best = study.best_params
best["accuracy"]   = study.best_value
best["latency_ms"] = study.best_trial.user_attrs["latency"]

print("Best params:", best)

# save for runtime
(BASE_DIR / "best_params.json").write_text(json.dumps(best, indent=2))
