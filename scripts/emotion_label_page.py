"""HTML template for the offline emotion labelling tool.

The candidate data is embedded directly into the page rather than fetched, so the
file can be opened straight from disk — a `fetch()` against a `file://` URL is
blocked by browser CORS rules.

Design constraint that matters: the page must never show the model's prediction
while you are labelling. Seeing "the machine said sad" before you decide turns the
eval set into a measure of your agreement with the model rather than a measure of
the truth.
"""

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EditEase — Emotion Labelling</title>
<style>
  :root {
    --bg: #0d1117; --panel: #161b22; --border: #30363d;
    --text: #e6edf3; --muted: #8b949e; --accent: #58a6ff;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--text);
    font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
    display: flex; flex-direction: column; min-height: 100vh;
  }
  header {
    padding: 12px 20px; border-bottom: 1px solid var(--border);
    display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
  }
  h1 { font-size: 15px; margin: 0; font-weight: 600; }
  .progress { flex: 1; min-width: 160px; height: 6px; background: var(--panel);
              border-radius: 3px; overflow: hidden; }
  .progress > div { height: 100%; background: var(--accent); width: 0%; transition: width .2s; }
  .count { font-variant-numeric: tabular-nums; color: var(--muted); font-size: 13px; }
  main { flex: 1; display: flex; flex-direction: column; align-items: center;
         justify-content: center; padding: 20px; gap: 16px; }
  .stage {
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 12px; max-width: min(880px, 94vw);
  }
  .stage img {
    max-width: 100%; max-height: 58vh; display: block; border-radius: 6px; background: #000;
  }
  .meta { color: var(--muted); font-size: 12px; margin-top: 8px;
          display: flex; gap: 14px; flex-wrap: wrap; }
  .buttons { display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; }
  button {
    background: var(--panel); color: var(--text); border: 1px solid var(--border);
    border-radius: 8px; padding: 11px 18px; font-size: 14px; cursor: pointer;
    font-family: inherit; transition: border-color .12s, background .12s;
  }
  button:hover { border-color: var(--accent); }
  button .key {
    display: inline-block; min-width: 17px; margin-right: 7px; color: var(--muted);
    font-size: 11px; border: 1px solid var(--border); border-radius: 4px;
    padding: 1px 4px; text-align: center;
  }
  .secondary { background: transparent; color: var(--muted); }
  .done { text-align: center; max-width: 560px; line-height: 1.6; }
  .done h2 { color: var(--accent); }
  a.download {
    display: inline-block; margin-top: 14px; background: var(--accent); color: #06121f;
    padding: 11px 20px; border-radius: 8px; text-decoration: none; font-weight: 600;
  }
  .hint { color: var(--muted); font-size: 12px; text-align: center; max-width: 620px; }
  .missing { color: #f85149; padding: 40px; text-align: center; }
</style>
</head>
<body>
<header>
  <h1>Emotion labelling</h1>
  <div class="progress"><div id="bar"></div></div>
  <span class="count" id="count"></span>
  <button class="secondary" id="back">&larr; Back</button>
  <button class="secondary" id="reset">Reset</button>
</header>
<main id="main"></main>

<script>
const DATA = __CANDIDATES__;
const SCHEME = [
  { key: "1", value: "sad",     label: "Sad" },
  { key: "2", value: "happy",   label: "Happy" },
  { key: "3", value: "neutral", label: "Neutral" },
  { key: "4", value: "other",   label: "Other emotion" },
  { key: "5", value: "none",    label: "No face / can't tell" },
];
const STORE = "editease_emotion_labels_v1";

let answers = JSON.parse(localStorage.getItem(STORE) || "{}");
let idx = 0;
const items = DATA.candidates;

function firstUnlabelled() {
  const i = items.findIndex(c => !(c.scene_ref in answers));
  return i === -1 ? items.length : i;
}

function save() { localStorage.setItem(STORE, JSON.stringify(answers)); }

function choose(value) {
  answers[items[idx].scene_ref] = value;
  save();
  idx = Math.min(idx + 1, items.length);
  render();
}

function render() {
  const done = Object.keys(answers).length;
  document.getElementById("bar").style.width = (done / items.length * 100) + "%";
  document.getElementById("count").textContent = done + " / " + items.length + " labelled";

  const main = document.getElementById("main");
  main.innerHTML = "";

  if (idx >= items.length) {
    const rows = items
      .filter(c => c.scene_ref in answers)
      .map(c => JSON.stringify({
        scene_ref: c.scene_ref, video: c.video, scene_id: c.scene_id,
        human_emotion: answers[c.scene_ref], split: "test"
      }))
      .join("\\n");
    const blob = new Blob([rows + "\\n"], { type: "application/x-ndjson" });
    const wrap = document.createElement("div");
    wrap.className = "done";
    wrap.innerHTML = "<h2>All done — " + done + " labelled</h2>" +
      "<p>Save this file as <code>annotations.jsonl</code> next to this page, " +
      "then run the scorer.</p>";
    const a = document.createElement("a");
    a.className = "download";
    a.href = URL.createObjectURL(blob);
    a.download = "annotations.jsonl";
    a.textContent = "Download annotations.jsonl";
    wrap.appendChild(a);
    main.appendChild(wrap);
    return;
  }

  const c = items[idx];
  const stage = document.createElement("div");
  stage.className = "stage";
  const img = document.createElement("img");
  img.src = c.image;
  img.alt = "scene frame";
  img.onerror = () => {
    img.replaceWith(Object.assign(document.createElement("div"), {
      className: "missing",
      textContent: "Image unavailable — press 5 to mark it unusable."
    }));
  };
  stage.appendChild(img);
  const meta = document.createElement("div");
  meta.className = "meta";
  meta.innerHTML = "<span>" + c.video + " &middot; scene " + c.scene_id + "</span>" +
                   "<span>" + (c.start_sec ?? "?") + "s &rarr; " + (c.end_sec ?? "?") + "s</span>";
  stage.appendChild(meta);
  main.appendChild(stage);

  const buttons = document.createElement("div");
  buttons.className = "buttons";
  SCHEME.forEach(s => {
    const b = document.createElement("button");
    b.innerHTML = '<span class="key">' + s.key + "</span>" + s.label;
    b.onclick = () => choose(s.value);
    buttons.appendChild(b);
  });
  main.appendChild(buttons);

  const hint = document.createElement("p");
  hint.className = "hint";
  hint.textContent = "Judge the dominant feeling of the moment. Press 1-5, or click. " +
                     "Progress is saved automatically.";
  main.appendChild(hint);
}

document.addEventListener("keydown", e => {
  const s = SCHEME.find(x => x.key === e.key);
  if (s) { choose(s.value); return; }
  if (e.key === "ArrowLeft") { idx = Math.max(0, idx - 1); render(); }
});
document.getElementById("back").onclick = () => { idx = Math.max(0, idx - 1); render(); };
document.getElementById("reset").onclick = () => {
  if (confirm("Clear all labels and start over?")) {
    answers = {}; save(); idx = 0; render();
  }
};

idx = firstUnlabelled();
render();
</script>
</body>
</html>
"""


def render_page(candidates_payload: str) -> str:
    """Inject the candidate JSON into the template.

    `</script>` inside the data would terminate the script block early, so it is
    escaped defensively even though scene refs should never contain it.
    """
    safe = candidates_payload.replace("</", "<\\/")
    return TEMPLATE.replace("__CANDIDATES__", safe)
