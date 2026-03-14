import os
import requests
import streamlit as st
from typing import Dict, Any, List, Optional

import config

API_BASE = f"http://{config.API_HOST}:{config.API_PORT}"

SCENE_LABELS = ["testimonial", "presenter", "b-roll", "audience_reaction", "establishing_shot", "other"]
EMOTIONS = ["happy", "sad", "angry", "fear", "surprise", "disgust", "neutral"]


# -------------------- API helpers --------------------
def api_get(path: str, params: Optional[dict] = None, timeout: int = 10) -> Dict[str, Any]:
    r = requests.get(f"{API_BASE}{path}", params=params, timeout=timeout)
    if r.status_code != 200:
        raise RuntimeError(f"{r.status_code} — {r.text}")
    return r.json()

def api_post(path: str, payload: dict, timeout: int = 30) -> Dict[str, Any]:
    r = requests.post(f"{API_BASE}{path}", json=payload, timeout=timeout)
    if r.status_code != 200:
        raise RuntimeError(f"{r.status_code} — {r.text}")
    return r.json()

def exists(p: Optional[str]) -> bool:
    return bool(p) and os.path.exists(p)

def doc_key(d: Dict[str, Any]) -> str:
    return f"{d.get('video')}::{int(d.get('scene_id', 0))}"

def pill(text: str):
    st.markdown(
        f"""
        <span style="
        display:inline-block;
        padding: 3px 10px;
        border-radius: 999px;
        background: rgba(0,0,0,0.06);
        font-size: 0.80rem;
        margin-right: 6px;
        ">
        {text}
        </span>
        """,
        unsafe_allow_html=True,
    )

def counts(results: List[Dict[str, Any]]) -> Dict[str, int]:
    total = len(results)
    reviewed = sum(1 for d in results if d.get("reviewed"))
    unreviewed = total - reviewed
    has_emo = sum(1 for d in results if d.get("dominant_emotion_overall") is not None)
    return {"total": total, "reviewed": reviewed, "unreviewed": unreviewed, "has_emo": has_emo}


# -------------------- Page --------------------
st.set_page_config(page_title="EditEase", layout="wide")

# light CSS for cleaner spacing
st.markdown(
    """
    <style>
      .block-container { padding-top: 1rem; }
      div[data-testid="stImage"] img { border-radius: 10px; }
      .editease-card-title { font-weight: 700; font-size: 0.95rem; margin-bottom: 4px; }
      .editease-subtle { color: rgba(0,0,0,0.55); font-size: 0.85rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

if "results" not in st.session_state:
    st.session_state.results = []
if "selected_key" not in st.session_state:
    st.session_state.selected_key = None
if "selected_set" not in st.session_state:
    st.session_state.selected_set = set()
if "page" not in st.session_state:
    st.session_state.page = 1
if "last_query" not in st.session_state:
    st.session_state.last_query = {}

st.title("EditEase — Clip Organizer")
st.caption("Card grid + Inspector panel (fast review & export)")

# -------------------- Sidebar Filters (clean) --------------------
st.sidebar.header("Upload Video")
uploaded_file = st.sidebar.file_uploader("Drop a video file", type=["mp4", "mov", "avi", "mkv"])
if uploaded_file is not None:
    if st.sidebar.button("Upload & Process", use_container_width=True):
        with st.spinner("Uploading..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            r = requests.post(f"{API_BASE}/upload", files=files)
            if r.status_code == 200:
                st.sidebar.success("Upload successful! Processing started.")
            else:
                st.sidebar.error(f"Upload failed: {r.text}")
st.sidebar.divider()

st.sidebar.header("Filters")

scene_label_filter = st.sidebar.selectbox("Scene type", [""] + SCENE_LABELS, index=0)
emotion_filter = st.sidebar.selectbox("Emotion", ["", "null"] + EMOTIONS, index=0)
video_filter = st.sidebar.text_input("Video name (optional)", value="")
reviewed_filter = st.sidebar.selectbox("Reviewed?", ["", "true", "false"], index=0)

st.sidebar.markdown("**Duration (sec)**")
min_duration = st.sidebar.number_input("Min", min_value=0.0, value=0.0, step=1.0)
max_duration = st.sidebar.number_input("Max (0=ignore)", min_value=0.0, value=0.0, step=1.0)

limit = st.sidebar.slider("Max results fetched", 20, 200, 120, 20)
page_size = st.sidebar.slider("Cards per page", 6, 24, 12, 3)
show_debug = st.sidebar.toggle("Show debug", value=False)

do_search = st.sidebar.button("🔎 Search", use_container_width=True)
clear_btn = st.sidebar.button("🧹 Clear results", use_container_width=True)

if clear_btn:
    st.session_state.results = []
    st.session_state.selected_key = None
    st.session_state.selected_set = set()
    st.session_state.page = 1
    st.session_state.last_query = {}
    st.rerun()

# Build query
params = {"limit": limit}
if scene_label_filter:
    params["scene_label"] = scene_label_filter

# UI uses "__NULL__" for null emotion; backend should translate to None
if emotion_filter == "null":
    params["emotion"] = "__NULL__"
elif emotion_filter:
    params["emotion"] = emotion_filter

if video_filter.strip():
    params["video"] = video_filter.strip()

if reviewed_filter in ("true", "false"):
    params["reviewed"] = reviewed_filter

if min_duration > 0:
    params["min_duration"] = min_duration
if max_duration > 0:
    params["max_duration"] = max_duration

if do_search:
    try:
        data = api_get("/search", params=params, timeout=15)
        st.session_state.results = data.get("results", [])
        st.session_state.last_query = params
        st.session_state.selected_set = set()
        st.session_state.page = 1

        # pick first as default selection
        if st.session_state.results:
            st.session_state.selected_key = doc_key(st.session_state.results[0])
        else:
            st.session_state.selected_key = None

        st.success(f"Loaded {len(st.session_state.results)} clips")
    except Exception as e:
        st.error("Search failed")
        st.code(str(e))

results: List[Dict[str, Any]] = st.session_state.results
if not results:
    st.info("Use the sidebar to search clips.")
    st.stop()

# -------------------- Top bar: stats + paging + bulk actions --------------------
stats = counts(results)
t1, t2, t3, t4, t5 = st.columns([1, 1, 1, 1, 1.4])
t1.metric("Total", stats["total"])
t2.metric("Reviewed", stats["reviewed"])
t3.metric("Unreviewed", stats["unreviewed"])
t4.metric("With emotion", stats["has_emo"])

with t5:
    st.write("")
    if st.button("✅ Health", use_container_width=True):
        try:
            st.json(api_get("/health", timeout=5))
        except Exception as e:
            st.error("API unreachable")
            st.code(str(e))

# Pagination
total_pages = max(1, (len(results) + page_size - 1) // page_size)
st.session_state.page = max(1, min(st.session_state.page, total_pages))

p1, p2, p3, p4 = st.columns([1, 1, 2, 2])
if p1.button("⬅ Prev page", use_container_width=True, disabled=(st.session_state.page <= 1)):
    st.session_state.page -= 1
if p2.button("Next page ➡", use_container_width=True, disabled=(st.session_state.page >= total_pages)):
    st.session_state.page += 1
p3.caption(f"Page **{st.session_state.page} / {total_pages}**  •  Showing **{page_size}** per page")

with p4:
    b1, b2, b3 = st.columns(3)
    if b1.button("Select page", use_container_width=True):
        start_i = (st.session_state.page - 1) * page_size
        page_docs = results[start_i:start_i + page_size]
        for d in page_docs:
            st.session_state.selected_set.add(doc_key(d))
    if b2.button("Clear select", use_container_width=True):
        st.session_state.selected_set = set()

    bulk_export = b3.button("Export All Results", use_container_width=True)

st.divider()

# -------------------- Main layout: Cards + Inspector --------------------
left, right = st.columns([1.6, 1])

# page slice
start_i = (st.session_state.page - 1) * page_size
page_docs = results[start_i:start_i + page_size]

# -------- Cards --------
with left:
    st.subheader("Clips")

    cols = st.columns(3)  # 3-column grid

    for i, d in enumerate(page_docs):
        c = cols[i % 3]
        with c:
            k = doc_key(d)
            video = d.get("video", "NA")
            scene_id = int(d.get("scene_id", 0))
            label = d.get("scene_label", "other")
            dur = float(d.get("duration_sec", 0.0))
            emo = d.get("dominant_emotion_overall")
            reviewed = bool(d.get("reviewed", False))
            thumb = d.get("thumbnail")

            card = st.container(border=True)
            with card:
                # Header row: select + open
                h1, h2 = st.columns([1, 2])
                checked = h1.checkbox("Select", value=(k in st.session_state.selected_set), key=f"sel_{k}")
                if checked:
                    st.session_state.selected_set.add(k)
                else:
                    st.session_state.selected_set.discard(k)

                open_btn = h2.button("Open", use_container_width=True, key=f"open_{k}")
                if open_btn:
                    st.session_state.selected_key = k

                # Thumbnail
                if exists(thumb):
                    st.image(thumb, use_container_width=True)
                else:
                    st.info("No thumbnail")

                # Title + meta
                st.markdown(f"<div class='editease-card-title'>{video} • Scene {scene_id:03d}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='editease-subtle'>{dur:.1f}s • {'Reviewed' if reviewed else 'Unreviewed'}</div>", unsafe_allow_html=True)

                # Pills
                pill(f"label: {label}")
                if emo is not None:
                    pill(f"emotion: {emo}")

# -------- Inspector (single selected clip) --------
with right:
    st.subheader("Inspector")

    # find selected doc
    sel_doc = None
    if st.session_state.selected_key:
        for d in results:
            if doc_key(d) == st.session_state.selected_key:
                sel_doc = d
                break

    if not sel_doc:
        st.info("Click **Open** on a card to inspect.")
        st.stop()

    video = sel_doc.get("video")
    scene_id = int(sel_doc.get("scene_id", 0))
    start = float(sel_doc.get("start_sec", 0.0))
    end = float(sel_doc.get("end_sec", 0.0))
    dur = float(sel_doc.get("duration_sec", 0.0))

    label = sel_doc.get("scene_label", "other")
    emo = sel_doc.get("dominant_emotion_overall")
    reviewed = bool(sel_doc.get("reviewed", False))
    notes_val = sel_doc.get("notes", "")
    thumb = sel_doc.get("thumbnail")

    st.write(f"**{video} • Scene {scene_id:03d}**")
    st.caption(f"{start:.2f}s → {end:.2f}s  •  {dur:.2f}s")

    if exists(thumb):
        st.image(thumb, use_container_width=True)

    st.markdown("### Manual labels")

    new_label = st.selectbox(
        "Scene type",
        SCENE_LABELS,
        index=SCENE_LABELS.index(label) if label in SCENE_LABELS else 0,
        key=f"ins_label_{video}_{scene_id}",
    )

    new_emo = st.selectbox(
        "Emotion",
        ["null"] + EMOTIONS,
        index=(["null"] + EMOTIONS).index(emo) if emo in EMOTIONS else 0,
        key=f"ins_emo_{video}_{scene_id}",
    )

    new_reviewed = st.checkbox("Reviewed", value=reviewed, key=f"ins_rev_{video}_{scene_id}")
    notes_new = st.text_area("Notes", value=notes_val, height=90, key=f"ins_note_{video}_{scene_id}")

    a1, a2 = st.columns(2)

    if a1.button("💾 Save", use_container_width=True):
        payload = {
            "video": video,
            "scene_id": scene_id,
            "scene_label": new_label,
            "dominant_emotion_overall": None if new_emo == "null" else new_emo,
            "reviewed": bool(new_reviewed),
            "notes": notes_new,
        }
        try:
            api_post("/update_scene", payload, timeout=10)
            st.success("Saved ✅")

            # update local copy so cards reflect changes without re-search
            sel_doc["scene_label"] = new_label
            sel_doc["dominant_emotion_overall"] = None if new_emo == "null" else new_emo
            sel_doc["reviewed"] = bool(new_reviewed)
            sel_doc["notes"] = notes_new

        except Exception as e:
            st.error("Save failed")
            st.code(str(e))

    if a2.button("⬇️ Export + Download", use_container_width=True):
        try:
            out = api_post("/export", {"video": video, "scene_id": scene_id}, timeout=120)
            out_path = out.get("output_path")
            st.success(f"Exported → {out_path}")

            if out_path and os.path.exists(out_path):
                with open(out_path, "rb") as f:
                    st.download_button(
                        "Download MP4",
                        data=f.read(),
                        file_name=os.path.basename(out_path),
                        mime="video/mp4",
                        use_container_width=True,
                        key=f"dl_{video}_{scene_id}",
                    )
            else:
                st.warning("Export succeeded but file not found on disk.")
        except Exception as e:
            st.error("Export failed")
            st.code(str(e))

    if show_debug:
        st.markdown("### Debug")
        st.json(sel_doc)


# -------------------- Bulk export handler --------------------
if bulk_export:
    st.info("Exporting all filtered clips…")
    try:
        out = api_post("/export_batch", st.session_state.last_query, timeout=300)
        ok = out.get("exported_count", 0)
        fail = out.get("failed_count", 0)
        st.success(f"Bulk export done. ✅ {ok}  •  ❌ {fail}")
        st.caption("Saved under: exports/<scene_label>/")
    except Exception as e:
        st.error("Bulk export failed")
        st.code(str(e))
