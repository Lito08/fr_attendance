import io, json, time, os
from pathlib import Path
import cv2
import numpy as np
import face_recognition
from . import faceconf

# ─── Load tuned parameters (threshold τ and resize r) ────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent   # project root

try:
    _best = json.loads((BASE_DIR / "best_params.json").read_text())
except FileNotFoundError:
    _best = {}

THRESHOLD = _best.get("threshold", faceconf.THRESHOLD)  # distance cutoff
RESIZE    = _best.get("resize",    1.0)                 # 1.0 = no down-scale

# ─── Helpers ─────────────────────────────────────────────────────────────────
def bytes_to_enc(b: bytes) -> np.ndarray:
    """Convert DB-stored BLOB back to 128-D numpy vector."""
    return np.frombuffer(b, dtype=np.float64)

# ─── Main matcher ────────────────────────────────────────────────────────────
def find_match(img, students, threshold: float = THRESHOLD):
    """
    img: numpy array (RGB)
    students: iterable of Student objects (with face_encoding bytes)
    threshold: distance cutoff τ
    Returns (student|None, distance|None, latency_ms)
    """
    t0 = time.time()

    # optional down-scaling for speed
    if RESIZE != 1.0:
        h, w = img.shape[:2]
        img  = cv2.resize(img, (int(w * RESIZE), int(h * RESIZE)))

    encs = face_recognition.face_encodings(img)
    if not encs:
        return None, None, int((time.time() - t0) * 1000)

    unknown = encs[0]
    enc_list = [bytes_to_enc(s.face_encoding) for s in students]
    if not enc_list:
        return None, None, int((time.time() - t0) * 1000)

    dist = face_recognition.face_distance(enc_list, unknown)
    idx  = int(np.argmin(dist))
    latency = int((time.time() - t0) * 1000)

    if dist[idx] < threshold:
        return students[idx], float(dist[idx]), latency
    return None, float(dist[idx]), latency
