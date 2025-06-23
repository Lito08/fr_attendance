import numpy as np, face_recognition
from . import faceconf

def bytes_to_enc(b: bytes) -> np.ndarray:
    return np.frombuffer(b, dtype=np.float64)

def find_match(img, students, threshold=faceconf.THRESHOLD):
    import time
    start = time.time()

    encs = face_recognition.face_encodings(img)
    if not encs:
        return None, None, int((time.time()-start)*1000)

    unknown = encs[0]
    enc_list = [bytes_to_enc(s.face_encoding) for s in students]
    if not enc_list:
        return None, None, int((time.time()-start)*1000)

    dist = face_recognition.face_distance(enc_list, unknown)
    idx  = np.argmin(dist)
    latency = int((time.time()-start)*1000)

    if dist[idx] < threshold:
        return students[idx], float(dist[idx]), latency
    return None, float(dist[idx]), latency
