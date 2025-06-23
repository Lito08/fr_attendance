import json, pathlib
THRESHOLD = 0.60
_best = pathlib.Path(__file__).resolve().parent.parent / "experiments" / "best_params.json"
if _best.exists():
    with _best.open() as f:
        THRESHOLD = json.load(f).get("threshold", THRESHOLD)
