import io, json, time, cv2, numpy as np, face_recognition
from pathlib import Path
from . import faceconf   # uses your existing THRESHOLD constant

BASE_DIR = Path(__file__).resolve().parent.parent
try:
    _best = json.loads((BASE_DIR / "best_params.json").read_text())
except FileNotFoundError:
    _best = {}

THRESHOLD = _best.get("threshold", faceconf.THRESHOLD)
RESIZE    = _best.get("resize",    1.0)   # 1.0 = no down-scale


def _bytes_to_vec(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float64)


def find_match(rgb_img, students, threshold: float = THRESHOLD):
    """
    Return (student|None, distance|None, latency_ms)
    """
    t0 = time.perf_counter()

    if RESIZE != 1.0:
        h, w = rgb_img.shape[:2]
        rgb_img = cv2.resize(rgb_img, (int(w * RESIZE), int(h * RESIZE)))

    encs = face_recognition.face_encodings(rgb_img)
    if not encs:
        return None, None, int((time.perf_counter() - t0) * 1000)

    probe = encs[0]
    ref   = [_bytes_to_vec(s.face_encoding) for s in students]
    if not ref:
        return None, None, int((time.perf_counter() - t0) * 1000)

    dist  = face_recognition.face_distance(ref, probe)
    idx   = int(np.argmin(dist))
    bestd = float(dist[idx])
    ms    = int((time.perf_counter() - t0) * 1000)

    return (students[idx], bestd, ms) if bestd < threshold else (None, bestd, ms)
