import os
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load scene_index.json once at startup
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(SCRIPT_DIR, "scene_index.json")

def load_index():
    if not os.path.exists(INDEX_PATH):
        return []
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

SCENES = load_index()

@app.get("/health")
def health():
    return jsonify({"status": "ok", "scenes_loaded": len(SCENES)})

@app.get("/search")
def search():
    """
    Example:
      /search?emotion=happy
      /search?emotion=happy&min_conf=60
      /search?scene_id=3
    """
    emotion = request.args.get("emotion")
    min_conf = request.args.get("min_conf", type=float)
    scene_id = request.args.get("scene_id", type=int)

    results = SCENES

    if scene_id is not None:
        results = [s for s in results if s.get("scene_id") == scene_id]

    if emotion:
        results = [s for s in results if (s.get("dominant_emotion") or "").lower() == emotion.lower()]

    if min_conf is not None:
        results = [s for s in results if (s.get("emotion_confidence") or 0) >= min_conf]

    return jsonify({"count": len(results), "results": results})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
