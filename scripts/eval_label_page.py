"""HTML template for the offline labelling tool (emotion + scene type in one pass).

Two constraints drive this design:

1. The candidate data is embedded, not fetched. A `fetch()` against a `file://`
   URL is blocked by browser CORS rules, so the page must be self-contained.
2. The model's predictions are never rendered. Seeing "the machine said sad"
   before you decide would turn the eval set into a measure of your agreement
   with the model instead of a measure of the truth.

Scene-type definitions are shown inline. Without them the categories drift
between sessions and the dataset ends up measuring labelling inconsistency
rather than model accuracy.
"""

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EditEase — Labelling</title>
<style>
  :root {
    --bg:#0d1117; --panel:#161b22; --border:#30363d;
    --text:#e6edf3; --muted:#8b949e; --accent:#58a6ff; --good:#3fb950;
  }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--text); min-height:100vh;
         font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;
         display:flex; flex-direction:column; }
  header { padding:10px 18px; border-bottom:1px solid var(--border); display:flex;
           align-items:center; gap:14px; flex-wrap:wrap; }
  h1 { font-size:14px; margin:0; font-weight:600; }
  .progress { flex:1; min-width:140px; height:6px; background:var(--panel);
              border-radius:3px; overflow:hidden; }
  .progress>div { height:100%; background:var(--accent); width:0%; transition:width .2s; }
  .count { font-size:12px; color:var(--muted); font-variant-numeric:tabular-nums; }
  main { flex:1; display:flex; gap:20px; padding:16px 20px; align-items:flex-start;
         justify-content:center; flex-wrap:wrap; }
  .stage { background:var(--panel); border:1px solid var(--border); border-radius:10px;
           padding:10px; flex:1 1 460px; max-width:640px; }
  .stage img { width:100%; max-height:56vh; object-fit:contain; display:block;
               border-radius:6px; background:#000; }
  .meta { color:var(--muted); font-size:12px; margin-top:7px; display:flex;
          gap:12px; flex-wrap:wrap; }
  .questions { flex:0 1 340px; display:flex; flex-direction:column; gap:18px; }
  fieldset { border:1px solid var(--border); border-radius:9px; padding:12px; margin:0; }
  legend { font-size:12px; color:var(--muted); padding:0 6px; text-transform:uppercase;
           letter-spacing:.06em; }
  .opts { display:flex; flex-direction:column; gap:7px; }
  button { background:transparent; color:var(--text); border:1px solid var(--border);
           border-radius:7px; padding:9px 11px; font-size:13px; cursor:pointer;
           font-family:inherit; text-align:left; display:flex; align-items:baseline;
           gap:9px; transition:border-color .12s,background .12s; }
  button:hover { border-color:var(--accent); }
  button.sel { border-color:var(--good); background:rgba(63,185,80,.12); }
  .k { min-width:16px; font-size:10px; color:var(--muted); border:1px solid var(--border);
       border-radius:3px; padding:1px 4px; text-align:center; flex:none; }
  .help { display:block; color:var(--muted); font-size:11px; margin-top:2px; }
  .bar { display:flex; gap:8px; align-items:center; }
  .ghost { background:transparent; color:var(--muted); border-color:transparent;
           font-size:12px; padding:5px 8px; }
  .ghost:hover { color:var(--text); border-color:var(--border); }
  .done { text-align:center; max-width:600px; margin:40px auto; line-height:1.6; }
  .done h2 { color:var(--accent); }
  a.dl { display:inline-block; margin:8px 6px 0; background:var(--accent); color:#06121f;
         padding:10px 16px; border-radius:8px; text-decoration:none; font-weight:600;
         font-size:13px; }
  code { background:var(--panel); padding:1px 5px; border-radius:4px; font-size:12px; }
  .missing { color:#f85149; padding:36px; text-align:center; font-size:13px; }
</style>
</head>
<body>
<header>
  <h1>Labelling</h1>
  <div class="progress"><div id="bar"></div></div>
  <span class="count" id="count"></span>
  <div class="bar">
    <button class="ghost" id="back">&larr; Back</button>
    <button class="ghost" id="skip">Skip &rarr;</button>
    <button class="ghost" id="reset">Reset</button>
  </div>
</header>
<main id="main"></main>

<script>
const DATA = __PAYLOAD__;
const STORE = "editease_eval_labels_v1";
const items = DATA.candidates;
const EMO = DATA.emotion_options;
const SCN = DATA.scene_options;

let answers = JSON.parse(localStorage.getItem(STORE) || "{}");
let idx = 0;

function save(){ localStorage.setItem(STORE, JSON.stringify(answers)); }
function rec(ref){ return answers[ref] || {}; }
function complete(ref){ const a = rec(ref); return a.emotion && a.scene_type; }
function doneCount(){ return items.filter(c => complete(c.scene_ref)).length; }

function firstIncomplete(){
  const i = items.findIndex(c => !complete(c.scene_ref));
  return i === -1 ? items.length : i;
}

function choose(kind, value){
  const c = items[idx];
  const a = rec(c.scene_ref);
  a[kind] = value;
  answers[c.scene_ref] = a;
  save();
  if (a.emotion && a.scene_type) {
    // Both questions answered — move on automatically.
    setTimeout(() => { idx = Math.min(idx + 1, items.length); render(); }, 140);
  }
  render(true);
}

function buildFieldset(title, kind, options, current){
  const fs = document.createElement("fieldset");
  const lg = document.createElement("legend");
  lg.textContent = title;
  fs.appendChild(lg);
  const wrap = document.createElement("div");
  wrap.className = "opts";
  options.forEach(o => {
    const b = document.createElement("button");
    if (current === o.value) b.classList.add("sel");
    const k = document.createElement("span");
    k.className = "k"; k.textContent = o.key.toUpperCase();
    const txt = document.createElement("span");
    txt.textContent = o.label;
    if (o.help) {
      const h = document.createElement("span");
      h.className = "help"; h.textContent = o.help;
      txt.appendChild(h);
    }
    b.appendChild(k); b.appendChild(txt);
    b.onclick = () => choose(kind, o.value);
    wrap.appendChild(b);
  });
  fs.appendChild(wrap);
  return fs;
}

function buildDownloads(){
  const labelled = items.filter(c => complete(c.scene_ref));

  const emotionRows = labelled.map(c => JSON.stringify({
    scene_ref: c.scene_ref, video: c.video, scene_id: c.scene_id,
    human_emotion: rec(c.scene_ref).emotion, split: "test",
  })).join("\\n");

  // Shape required by tests/test_ml_classifier_quality.py: label + split + frames,
  // where frames are paths relative to the repo root.
  const sceneRows = labelled.map(c => JSON.stringify({
    label: rec(c.scene_ref).scene_type, split: "test", frames: [c.frame_rel],
    scene_ref: c.scene_ref, video: c.video, scene_id: c.scene_id,
  })).join("\\n");

  const wrap = document.createElement("div");
  wrap.className = "done";
  wrap.innerHTML = "<h2>Done — " + labelled.length + " of " + items.length + " labelled</h2>" +
    "<p>Download both files, then run:</p>" +
    "<p><code>python -m scripts.install_annotations</code></p>" +
    "<p class='help'>That moves them from your Downloads folder into the right " +
    "dataset directories, so you do not have to rename anything.</p>";

  // Distinct filenames. Naming both "annotations.jsonl" means the browser saves the
  // second as "annotations (1).jsonl" and there is no way to tell which is which.
  [["editease-emotion-labels.jsonl", emotionRows, "Download emotion labels"],
   ["editease-scene-type-labels.jsonl", sceneRows, "Download scene-type labels"]]
  .forEach(([name, rows, text]) => {
    const a = document.createElement("a");
    a.className = "dl";
    a.href = URL.createObjectURL(new Blob([rows + "\\n"], {type:"application/x-ndjson"}));
    a.download = name;
    a.textContent = text;
    wrap.appendChild(a);
  });
  return wrap;
}

function render(keepIndex){
  const done = doneCount();
  document.getElementById("bar").style.width = (done / items.length * 100) + "%";
  document.getElementById("count").textContent = done + " / " + items.length;

  const main = document.getElementById("main");
  main.innerHTML = "";

  if (idx >= items.length) { main.appendChild(buildDownloads()); return; }

  const c = items[idx];
  const a = rec(c.scene_ref);

  const stage = document.createElement("div");
  stage.className = "stage";
  const img = document.createElement("img");
  img.src = c.image; img.alt = "scene frame";
  img.onerror = () => img.replaceWith(Object.assign(document.createElement("div"),
    {className:"missing", textContent:"Frame unavailable — Skip this one."}));
  stage.appendChild(img);
  const meta = document.createElement("div");
  meta.className = "meta";
  meta.innerHTML = "<span>" + c.video + " &middot; scene " + c.scene_id + "</span>" +
                   "<span>" + (c.start_sec ?? "?") + "s &rarr; " + (c.end_sec ?? "?") + "s</span>";
  stage.appendChild(meta);
  main.appendChild(stage);

  const qs = document.createElement("div");
  qs.className = "questions";
  qs.appendChild(buildFieldset("Dominant feeling", "emotion", EMO, a.emotion));
  qs.appendChild(buildFieldset("Shot type", "scene_type", SCN, a.scene_type));
  main.appendChild(qs);
}

document.addEventListener("keydown", e => {
  if (idx >= items.length) return;
  const k = e.key.toLowerCase();
  const emo = EMO.find(o => o.key === k);
  if (emo) { choose("emotion", emo.value); return; }
  const scn = SCN.find(o => o.key === k);
  if (scn) { choose("scene_type", scn.value); return; }
  if (e.key === "ArrowLeft") { idx = Math.max(0, idx - 1); render(); }
  if (e.key === "ArrowRight") { idx = Math.min(items.length, idx + 1); render(); }
});
document.getElementById("back").onclick = () => { idx = Math.max(0, idx - 1); render(); };
document.getElementById("skip").onclick = () => { idx = Math.min(items.length, idx + 1); render(); };
document.getElementById("reset").onclick = () => {
  if (confirm("Clear all labels and start over?")) { answers = {}; save(); idx = 0; render(); }
};

idx = firstIncomplete();
render();
</script>
</body>
</html>
"""


def render_page(payload_json: str) -> str:
    """Inject the labelling payload into the template.

    `</script>` inside the data would close the script block early, so it is
    escaped defensively.
    """
    safe = payload_json.replace("</", "<\\/")
    return TEMPLATE.replace("__PAYLOAD__", safe)
