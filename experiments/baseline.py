import json, sys, face_recognition, numpy as np, cv2, time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(sys.argv[1])
USE_BEST = "--use-best" in sys.argv

best = {}
if USE_BEST:
    best = json.loads((BASE_DIR / "best_params.json").read_text())

TAU    = best.get("threshold", 0.6)
RESIZE = best.get("resize", 1.0)

def evaluate():
    correct = 0; lat = []
    subs = [p for p in DATA_DIR.iterdir() if p.is_dir()]
    if not subs:
        print(f"No subject directories found in {DATA_DIR!r}.")
        print("Please create data/validation/<subjectname>/ with some .jpg files.")
        sys.exit(1)
    for s in subs:
        encs = [face_recognition.face_encodings(
                cv2.resize(face_recognition.load_image_file(p),
                           None, fx=RESIZE, fy=RESIZE))[0]
                for p in s.glob("*.jpg")]
        ref, test = np.mean(encs[:-1], axis=0), encs[-1]
        t0 = time.time()
        d  = np.linalg.norm(test-ref)
        lat.append((time.time()-t0)*1000)
        if d < TAU: correct +=1
    return correct/len(subs), sum(lat)/len(lat)

acc, ms = evaluate()
print(f"total {len(list(DATA_DIR.iterdir()))}\naccuracy {acc:.3f}\nlatency {ms:.0f}ms")
