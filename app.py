import random
import json
import math
from pathlib import Path
import streamlit as st

BANK_PATH  = Path(__file__).parent / "bank.txt"
WORDS_PATH = Path(__file__).parent / "words.txt"

st.set_page_config(page_title="Morse Monkeytype", page_icon="·–", layout="centered")

MORSE = {
    "A": ".-",    "B": "-...", "C": "-.-.", "D": "-..",  "E": ".",
    "F": "..-.",  "G": "--.",  "H": "....", "I": "..",   "J": ".---",
    "K": "-.-",   "L": ".-..", "M": "--",   "N": "-.",   "O": "---",
    "P": ".--.",  "Q": "--.-", "R": ".-.",  "S": "...",  "T": "-",
    "U": "..-",   "V": "...-", "W": ".--",  "X": "-..-", "Y": "-.--",
    "Z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-",
    "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.",
    ".": ".-.-.-", ",": "--..--", "?": "..--..", "!": "-.-.--",
    "'": ".----.", "-": "-....-", "/": "-..-.",  "(": "-.--.",
    ")": "-.--.-", ":": "---...", ";": "-.-.-.", "@": ".--.-.",
}

def _load_words() -> list:
    lines = WORDS_PATH.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip()]


def _load_bank() -> list:
    lines = BANK_PATH.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip()]


def _clean_word(w: str) -> str:
    return "".join(ch for ch in w if ch.upper() in MORSE)


def _word_lm(w: str) -> list:
    return [MORSE[ch] for ch in w.upper() if ch in MORSE]


def prepare_data(sentences: list) -> dict:
    all_words = _load_words()
    weights = [
        math.exp(-0.5 * ((len(w) - 4) / 1.5) ** 2) if len(w) >= 2 else 0.0
        for w in all_words
    ]
    pool = random.choices(all_words, weights=weights, k=200)
    quotes = []
    for sent in sentences:
        wds = [_clean_word(t) for t in sent.split()]
        wds = [w for w in wds if w]
        if wds:
            quotes.append({"words": wds, "lm": [_word_lm(w) for w in wds]})
    return {
        "words": pool,
        "words_lm": [_word_lm(w) for w in pool],
        "quotes": quotes,
    }


with st.sidebar:
    st.title("Settings")
    hard_mode = st.toggle("Hard mode (hide Morse reference)", value=False)
    if st.button("New session", use_container_width=True):
        for k in [k for k in st.session_state if k.startswith("morse_data_")]:
            del st.session_state[k]
        st.rerun()
    st.divider()
    with st.expander("Source", expanded=False):
        uploaded = st.file_uploader(
            "Upload quote bank (.txt, one quote per line)",
            type="txt",
            label_visibility="collapsed",
        )
        st.caption("One quote per line — same format as the default bank.txt.")
    st.divider()
    with st.expander("Key bindings"):
        c1, c2 = st.columns(2)
        with c1:
            dot_raw  = st.text_input("Dot",          value=".",      max_chars=1)
            lsep_raw = st.text_input("Submit letter", value="",       placeholder="Space", max_chars=10)
            esc_raw  = st.text_input("Clear letter",  value="Escape", max_chars=10)
        with c2:
            dash_raw = st.text_input("Dash",          value="-",  max_chars=1)
            wsep_raw = st.text_input("Next word",      value="/",  max_chars=1)
    if not hard_mode:
        with st.expander("Morse reference", expanded=False):
            cols = st.columns(2)
            items = list(MORSE.items())
            half = len(items) // 2
            with cols[0]:
                for k, v in items[:half]:
                    st.caption(f"`{k}` {v}")
            with cols[1]:
                for k, v in items[half:]:
                    st.caption(f"`{k}` {v}")

if uploaded is not None:
    raw = uploaded.read().decode("utf-8")
    sentences = [line.strip() for line in raw.splitlines() if line.strip()]
    source_id = uploaded.name
else:
    sentences = _load_bank()
    source_id = "__default__"

session_key = f"morse_data_{source_id}"
if session_key not in st.session_state:
    for k in [k for k in st.session_state if k.startswith("morse_data_")]:
        del st.session_state[k]
    st.session_state[session_key] = prepare_data(sentences)

data = st.session_state[session_key]
data_json = json.dumps(data)
hard_mode_js = "true" if hard_mode else "false"

dot_key  = (dot_raw  or ".")[0]
dash_key = (dash_raw or "-")[0]
lsep_key = (lsep_raw or " ")[0]
wsep_key = (wsep_raw or "/")[0]
esc_key  = esc_raw or "Escape"


def _disp(k: str) -> str:
    return "Space" if k == " " else k


dot_js  = json.dumps(dot_key)
dash_js = json.dumps(dash_key)
lsep_js = json.dumps(lsep_key)
wsep_js = json.dumps(wsep_key)
esc_js  = json.dumps(esc_key)

HTML = f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
:root {{
  --bg: #0e1117;
  --text: #e4e4e7;
  --muted: #71717a;
  --ok: #86efac;
  --bad: #f87171;
  --cur: #ffffff;
  --caret: #facc15;
  --panel: #1c1c27;
  --border: #27272a;
  --pill-active: #e4e4e7;
  --pill-bg: transparent;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  background: var(--bg);
  color: var(--text);
  padding: 20px 20px 12px;
  user-select: none;
}}

/* ── Mode bar ── */
#mode-bar {{
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 28px;
}}
.pill-group {{
  display: flex;
  gap: 4px;
}}
.pill {{
  background: var(--pill-bg);
  border: none;
  color: var(--muted);
  font-family: inherit;
  font-size: 13px;
  padding: 4px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: color 0.15s;
}}
.pill:hover {{ color: var(--text); }}
.pill.active {{ color: var(--pill-active); font-weight: 600; }}
.pill-sep {{ color: var(--border); font-size: 18px; align-self: center; }}

/* ── Stats bar ── */
.stats {{
  display: flex;
  gap: 24px;
  margin-bottom: 20px;
  font-size: 13px;
  color: var(--muted);
  min-height: 20px;
}}
.stat-val {{ color: var(--text); font-weight: 600; }}
#stat-timer {{
  font-size: 36px;
  font-weight: 700;
  color: var(--caret);
  margin-bottom: 12px;
  min-height: 44px;
  display: none;
}}

/* ── Rolling word display ── */
#words-wrapper {{
  overflow: hidden;
  /* height set dynamically after first row measured */
  margin-bottom: 20px;
  position: relative;
}}
#words-display {{
  display: flex;
  flex-wrap: wrap;
  gap: 4px 14px;
  align-items: flex-start;
  transition: transform 0.25s ease;
}}
.word-wrap {{
  display: inline-flex;
  gap: 4px;
  align-items: flex-start;
}}
.lb {{
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}}
.lc {{
  font-size: 28px;
  font-weight: 700;
  line-height: 1.1;
}}
.lm {{
  font-size: 10px;
  color: var(--muted);
  letter-spacing: 0.06em;
  line-height: 1;
}}
.lb-ok  .lc {{ color: var(--ok); }}
.lb-err .lc {{ color: var(--bad); }}
.lb-pen .lc {{ color: var(--muted); }}
.lb-cur .lc {{
  color: var(--cur);
  border-bottom: 3px solid var(--caret);
  padding-bottom: 2px;
  animation: blink 1s step-end infinite;
}}
@keyframes blink {{ 50% {{ border-color: transparent; opacity: 0.4; }} }}

/* ── Morse bar ── */
#morse-bar {{
  height: 38px;
  display: flex;
  align-items: center;
  font-size: 20px;
  letter-spacing: 0.12em;
  color: var(--caret);
  margin-bottom: 16px;
}}
.morse-caret {{
  display: inline-block;
  width: 2px;
  height: 0.9em;
  background: var(--caret);
  margin-left: 3px;
  vertical-align: text-bottom;
  animation: blink 1s step-end infinite;
}}

.hint {{
  font-size: 11px;
  color: var(--muted);
  line-height: 1.8;
}}
.hint b {{ color: #a1a1aa; }}

/* ── Complete screen ── */
.comp-h2 {{ font-size: 16px; color: var(--ok); margin-bottom: 22px; font-weight: 700; text-align: center; letter-spacing: 0.06em; text-transform: uppercase; }}
.rings {{ display: flex; justify-content: center; gap: 32px; margin-bottom: 20px; align-items: center; flex-wrap: wrap; }}
.ring-inner {{ position: relative; width: 120px; height: 120px; }}
.ring-inner svg {{ width: 120px; height: 120px; }}
.ring-bg {{ fill: none; stroke: var(--border); stroke-width: 9; }}
.ring-fg {{ fill: none; stroke: var(--ok); stroke-width: 9; stroke-linecap: round; transition: stroke-dashoffset 1.1s cubic-bezier(.4,0,.2,1); }}
.ring-acc {{ stroke: #60a5fa; }}
.ring-label {{ position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }}
.ring-val {{ font-size: 24px; font-weight: 700; color: var(--text); }}
.ring-unit {{ font-size: 9px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.1em; margin-top: 3px; }}
.comp-time {{ text-align: center; font-size: 13px; color: var(--muted); margin-bottom: 22px; }}
.comp-time span {{ color: var(--text); font-weight: 600; }}
.comp-section {{ margin-bottom: 18px; }}
.comp-lbl {{ font-size: 9px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px; }}
.sess-heatmap {{ display: flex; flex-wrap: wrap; gap: 3px; }}
.sess-lc {{ width: 38px; height: 42px; border-radius: 5px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; cursor: default; }}
.sess-lc .spct {{ font-size: 8px; margin-top: 2px; color: #a1a1aa; }}
.restart-hint {{ color: var(--muted); font-size: 11px; text-align: center; margin-top: 14px; }}
.restart-hint b {{ color: var(--text); }}
.hidden {{ display: none !important; }}
</style>
</head>
<body>

<div id="main">
  <div id="mode-bar">
    <div class="pill-group" id="mode-pills">
      <button class="pill active" data-mode="time"  onclick="selectMode('time')">time</button>
      <button class="pill"        data-mode="quote" onclick="selectMode('quote')">quote</button>
    </div>
    <div class="pill-sep">|</div>
    <div class="pill-group" id="sub-pills"></div>
  </div>

  <div id="stat-timer"></div>

  <div class="stats" id="stats-bar">
    <span>acc  <span id="stat-acc"  class="stat-val">—</span></span>
    <span>wpm  <span id="stat-wpm"  class="stat-val">—</span></span>
    <span id="stat-elapsed-wrap">time <span id="stat-time" class="stat-val">0:00</span></span>
  </div>

  <div id="words-wrapper">
    <div id="words-display"></div>
  </div>

  <div id="morse-bar"><span class="morse-caret"></span></div>

  <div class="hint">
    <b>{_disp(dot_key)}</b> dot &nbsp;&nbsp;
    <b>{_disp(dash_key)}</b> dash &nbsp;&nbsp;
    <b>{_disp(lsep_key)}</b> submit &nbsp;&nbsp;
    <b>{_disp(wsep_key)}</b> next word &nbsp;&nbsp;
    <b>Backspace</b> undo &nbsp;&nbsp;
    <b>{_disp(esc_key)}</b> clear &nbsp;&nbsp;
    <b>Tab</b> restart
  </div>
</div>

<div id="complete" class="hidden" style="padding:20px 0 10px">
  <div class="comp-h2">session complete</div>

  <div class="rings">
    <div class="ring-inner">
      <svg viewBox="0 0 120 120">
        <circle class="ring-bg" cx="60" cy="60" r="50"/>
        <circle id="ring-wpm" class="ring-fg" cx="60" cy="60" r="50"
          stroke-dasharray="314" stroke-dashoffset="314"
          transform="rotate(-90 60 60)"/>
      </svg>
      <div class="ring-label">
        <span class="ring-val" id="final-wpm">—</span>
        <span class="ring-unit">wpm</span>
      </div>
    </div>
    <div class="ring-inner">
      <svg viewBox="0 0 120 120">
        <circle class="ring-bg" cx="60" cy="60" r="50"/>
        <circle id="ring-acc" class="ring-fg ring-acc" cx="60" cy="60" r="50"
          stroke-dasharray="314" stroke-dashoffset="314"
          transform="rotate(-90 60 60)"/>
      </svg>
      <div class="ring-label">
        <span class="ring-val" id="final-acc">—</span>
        <span class="ring-unit">acc</span>
      </div>
    </div>
  </div>
  <div class="comp-time">time &nbsp;<span id="final-time">—</span></div>

  <div id="session-chart" class="comp-section"></div>
  <div id="session-heatmap" class="comp-section"></div>
  <div class="restart-hint">press <b>Tab</b> to restart</div>
</div>

<input id="capture" style="position:absolute;opacity:0;pointer-events:none;width:1px;height:1px;" autofocus />

<script>
const DATA      = {data_json};
const HARD_MODE = {hard_mode_js};
const DOT_KEY   = {dot_js};
const DASH_KEY  = {dash_js};
const LSEP_KEY  = {lsep_js};
const WSEP_KEY  = {wsep_js};
const ESC_KEY   = {esc_js};

// ── Mode state ──
let mode        = "time";
let timeLimit   = 30;
let quoteBucket = "short";  // "short" | "medium" | "long"

// ── Session state ──
let sessionWords = [];
let sessionLm    = [];
let wordIdx = 0, letterIdx = 0, currentMorse = "";
let completedLetters = [], waitingForWordSep = false;
let startTime = null, wordsCompleted = 0;
let totalLetters = 0, totalCorrect = 0;
let timeLeft = 30, timerInterval = null;
let wordTimestamps = [];  // [{{t, wc}}] one entry per completed word
let wrapperHeight = 0;

// ── localStorage persistence ──
function getProgression() {{
  try {{
    const raw = localStorage.getItem("morse_progression");
    return raw ? JSON.parse(raw) : {{ sessions: [], letters: {{}} }};
  }} catch(e) {{ return {{ sessions: [], letters: {{}} }}; }}
}}
function saveProgression(d) {{
  try {{ localStorage.setItem("morse_progression", JSON.stringify(d)); }} catch(e) {{}}
}}
function recordLetter(ch, correct) {{
  const d = getProgression();
  const k = ch.toUpperCase();
  if (!d.letters[k]) d.letters[k] = {{ attempts: 0, correct: 0 }};
  d.letters[k].attempts++;
  if (correct) d.letters[k].correct++;
  saveProgression(d);
}}
function recordSession(wpm, acc, modeLabel) {{
  const d = getProgression();
  d.sessions.push({{ ts: Date.now(), wpm, acc, mode: modeLabel }});
  if (d.sessions.length > 200) d.sessions = d.sessions.slice(-200);
  saveProgression(d);
}}

// ── Mode UI ──
function renderModePills() {{
  document.getElementById("mode-pills").querySelectorAll(".pill").forEach(b => {{
    b.classList.toggle("active", b.dataset.mode === mode);
  }});

  const subPills = document.getElementById("sub-pills");
  if (mode === "time") {{
    subPills.innerHTML = [15, 30, 60, 120].map(v =>
      `<button class="pill${{v === timeLimit ? " active" : ""}}" onclick="selectSub(${{v}})">${{v}}s</button>`
    ).join("");
  }} else {{
    subPills.innerHTML = ["short", "medium", "long"].map(b =>
      `<button class="pill${{b === quoteBucket ? " active" : ""}}" onclick="selectSub('${{b}}')">${{b}}</button>`
    ).join("");
  }}

  // Show/hide timer vs elapsed
  const timerEl = document.getElementById("stat-timer");
  const elapsedWrap = document.getElementById("stat-elapsed-wrap");
  if (mode === "time") {{
    timerEl.style.display = "block";
    elapsedWrap.style.display = "none";
  }} else {{
    timerEl.style.display = "none";
    elapsedWrap.style.display = "";
  }}
}}

function selectMode(m) {{
  mode = m;
  renderModePills();
  newSession();
}}

function selectSub(val) {{
  if (mode === "time") timeLimit = val;
  else quoteBucket = val;
  renderModePills();
  newSession();
}}

// ── Session lifecycle ──
function newSession() {{
  clearInterval(timerInterval);
  timerInterval = null;

  if (mode === "time") {{
    sessionWords = DATA.words;
    sessionLm    = DATA.words_lm;
  }} else {{
    const pool = DATA.quotes.filter(q => {{
      const wc = q.words.length;
      if (quoteBucket === "short")  return wc <= 20;
      if (quoteBucket === "medium") return wc > 20 && wc <= 60;
      return wc > 60;  // long
    }});
    const src = pool.length > 0 ? pool[Math.floor(Math.random() * pool.length)] : DATA.quotes[0];
    sessionWords = src.words;
    sessionLm    = src.lm;
  }}

  wordIdx = 0; letterIdx = 0; currentMorse = "";
  completedLetters = []; waitingForWordSep = false;
  startTime = null; wordsCompleted = 0;
  totalLetters = 0; totalCorrect = 0;
  timeLeft = timeLimit;
  wordTimestamps = [];
  wrapperHeight = 0;

  // show main, hide complete
  document.getElementById("main").classList.remove("hidden");
  document.getElementById("complete").classList.add("hidden");

  if (mode === "time") {{
    document.getElementById("stat-timer").textContent = timeLimit + "s";
  }}

  render();
  document.getElementById("capture").focus();
}}

// ── Helpers ──
function formatTime(secs) {{
  const m = Math.floor(secs / 60);
  const s = Math.floor(secs % 60);
  return m + ":" + s.toString().padStart(2, "0");
}}

function compKey(w, l) {{ return w * 10000 + l; }}

function buildCompletedMap() {{
  const map = {{}};
  for (const c of completedLetters) map[compKey(c.w, c.l)] = c.correct;
  return map;
}}

function updateStatsBar() {{
  const elapsed = startTime ? (Date.now() - startTime) / 1000 : 0;
  const minutes = elapsed / 60;
  const acc = totalLetters > 0 ? Math.round(totalCorrect / totalLetters * 100) : null;
  const wpm = minutes > 0.05 ? Math.round(wordsCompleted / minutes) : null;

  if (mode === "time") {{
    const tl = startTime ? Math.max(0, timeLimit - elapsed) : timeLimit;
    document.getElementById("stat-timer").textContent = Math.ceil(tl) + "s";
  }} else {{
    document.getElementById("stat-time").textContent = startTime ? formatTime(elapsed) : "0:00";
  }}
  document.getElementById("stat-acc").textContent = acc !== null ? acc + "%" : "—";
  document.getElementById("stat-wpm").textContent = wpm !== null ? wpm + " wpm" : "—";
}}

// ── Rolling window ──
function scrollToCurrentWord() {{
  const display = document.getElementById("words-display");
  const wrapper = document.getElementById("words-wrapper");
  const wordEls = display.querySelectorAll(".word-wrap");
  if (!wordEls.length) return;

  // Collect unique row tops
  const rows = [];
  for (const el of wordEls) {{
    if (!rows.includes(el.offsetTop)) rows.push(el.offsetTop);
  }}
  rows.sort((a, b) => a - b);

  // Set wrapper height to 3 rows on first render
  if (wrapperHeight === 0 && rows.length >= 1) {{
    const rowH = rows.length >= 2 ? (rows[1] - rows[0]) : (wordEls[0].offsetHeight + 4);
    wrapperHeight = rowH * 3;
    wrapper.style.height = wrapperHeight + "px";
  }}

  const curWrap = display.querySelector(`.word-wrap[data-widx="${{wordIdx}}"]`);
  if (!curWrap) return;

  const curTop = curWrap.offsetTop;
  const rowIdx = rows.indexOf(curTop);
  if (rowIdx < 0 || rows.length < 2) return;

  const rowH = rows[1] - rows[0];
  const shift = Math.max(0, rowIdx - 1);
  display.style.transform = `translateY(${{-(shift * rowH)}}px)`;
}}

// ── Render ──
function render() {{
  const done = buildCompletedMap();

  let html = "";
  for (let w = 0; w < sessionWords.length; w++) {{
    html += `<span class="word-wrap" data-widx="${{w}}">`;
    for (let l = 0; l < sessionWords[w].length; l++) {{
      const key = compKey(w, l);
      const ch = sessionWords[w][l];
      const morseCh = sessionLm[w][l];
      let cls;
      if (key in done) {{
        cls = done[key] ? "lb-ok" : "lb-err";
      }} else if (w === wordIdx && l === letterIdx) {{
        cls = "lb-cur";
      }} else {{
        cls = "lb-pen";
      }}
      html += `<span class="lb ${{cls}}">`;
      html += `<span class="lc">${{ch}}</span>`;
      if (!HARD_MODE) html += `<span class="lm">${{morseCh}}</span>`;
      html += "</span>";
    }}
    html += "</span>";
    // invisible spacer between words
    if (w < sessionWords.length - 1) {{
      html += "<span class='lb lb-pen'><span class='lc' style='color:transparent'>·</span>";
      if (!HARD_MODE) html += "<span class='lm'>&nbsp;</span>";
      html += "</span>";
    }}
  }}
  document.getElementById("words-display").innerHTML = html;

  // Morse bar
  const morseBar = document.getElementById("morse-bar");
  if (waitingForWordSep) {{
    const label = WSEP_KEY === " " ? "Space" : WSEP_KEY;
    morseBar.innerHTML = `<span style="color:var(--muted);font-size:13px;letter-spacing:0">press <b style="color:var(--text)">${{label}}</b> for next word</span>`;
  }} else if (currentMorse.length > 0) {{
    morseBar.innerHTML = `<span>${{currentMorse}}</span><span class="morse-caret"></span>`;
  }} else {{
    morseBar.innerHTML = `<span class="morse-caret"></span>`;
  }}

  updateStatsBar();
  scrollToCurrentWord();
}}

// ── Submit / undo ──
function submitLetter() {{
  if (wordIdx >= sessionWords.length) return;
  if (waitingForWordSep || currentMorse.length === 0) return;

  if (!startTime) {{
    startTime = Date.now();
    if (mode === "time") {{
      timerInterval = setInterval(() => {{
        const elapsed = (Date.now() - startTime) / 1000;
        timeLeft = Math.max(0, timeLimit - elapsed);
        if (timeLeft <= 0) {{
          clearInterval(timerInterval);
          showComplete(timeLimit);
          return;
        }}
        updateStatsBar();
      }}, 100);
    }}
  }}

  const expected = sessionLm[wordIdx][letterIdx];
  const correct = currentMorse === expected;
  const isLastLetter = letterIdx === sessionWords[wordIdx].length - 1;
  const isLastWord   = wordIdx === sessionWords.length - 1;

  completedLetters.push({{ w: wordIdx, l: letterIdx, correct, isLastLetter, isLastWord }});
  totalLetters++;
  if (correct) totalCorrect++;
  recordLetter(sessionWords[wordIdx][letterIdx], correct);
  currentMorse = "";
  letterIdx++;

  if (isLastLetter) {{
    wordsCompleted++;
    wordTimestamps.push({{ t: Date.now(), wc: wordsCompleted }});
    if (isLastWord) {{
      clearInterval(timerInterval);
      const elapsed = startTime ? (Date.now() - startTime) / 1000 : 0;
      render();
      showComplete(elapsed);
      return;
    }} else {{
      waitingForWordSep = true;
    }}
  }}

  render();
}}

function undoLetter() {{
  if (waitingForWordSep) {{
    const prev = completedLetters.pop();
    totalLetters--;
    if (prev.correct) totalCorrect--;
    wordsCompleted--;
    letterIdx = prev.l;
    waitingForWordSep = false;
    currentMorse = "";
    render();
    return;
  }}
  if (currentMorse.length > 0) {{
    currentMorse = currentMorse.slice(0, -1);
    render();
    return;
  }}
  if (completedLetters.length === 0) return;

  const prev = completedLetters.pop();
  totalLetters--;
  if (prev.correct) totalCorrect--;
  if (prev.isLastLetter) wordsCompleted--;
  wordIdx = prev.w;
  letterIdx = prev.l;
  currentMorse = "";
  render();
}}

// ── Complete screen ──
function showComplete(elapsed) {{
  document.getElementById("main").classList.add("hidden");
  document.getElementById("complete").classList.remove("hidden");

  const minutes = elapsed / 60;
  const wpm = minutes > 0 ? Math.round(wordsCompleted / minutes) : 0;
  const acc = totalLetters > 0 ? Math.round(totalCorrect / totalLetters * 100) : 0;

  const modeLabel = mode === "time" ? "time-" + timeLimit + "s" : "quote-" + quoteBucket;
  recordSession(wpm, acc, modeLabel);

  document.getElementById("final-wpm").textContent  = wpm;
  document.getElementById("final-acc").textContent  = acc + "%";
  document.getElementById("final-time").textContent = formatTime(elapsed);

  // Animate rings
  const WPM_MAX = 30;
  setTimeout(function() {{
    document.getElementById("ring-wpm").style.strokeDashoffset = 314 * (1 - Math.min(1, wpm / WPM_MAX));
    document.getElementById("ring-acc").style.strokeDashoffset = 314 * (1 - acc / 100);
  }}, 60);

  // WPM-over-time chart
  const chartEl = document.getElementById("session-chart");
  if (wordTimestamps.length >= 3) {{
    const series = wordTimestamps.map(function(pt) {{
      const secElapsed = (pt.t - startTime) / 1000;
      return {{ x: secElapsed, y: pt.wc / (secElapsed / 60) }};
    }});
    const maxX = series[series.length - 1].x;
    const rawMaxY = Math.max.apply(null, series.map(function(p) {{ return p.y; }}));
    const W = 380, H = 72, padL = 30, padR = 6, padT = 4, padB = 4;

    // nice y ticks (3-4 ticks at round numbers)
    const rawStep = rawMaxY / 3;
    const mag = Math.pow(10, Math.floor(Math.log10(rawStep || 1)));
    const niceStep = [1, 2, 5, 10].map(function(f) {{ return f * mag; }})
      .find(function(s) {{ return s >= rawStep; }}) || rawStep;
    const ticks = [];
    for (let v = 0; v <= rawMaxY + niceStep * 0.5; v += niceStep) {{
      ticks.push(Math.round(v));
    }}
    const tickMax = ticks[ticks.length - 1] || 1;

    function xOf(v) {{ return padL + (v / maxX) * (W - padL - padR); }}
    function yOf(v) {{ return H - padB - (v / tickMax) * (H - padT - padB); }}

    let gridLines = "", yLabels = "", pts = "", circles = "";
    ticks.forEach(function(tick) {{
      const y = Math.round(yOf(tick));
      gridLines += "<line x1='" + padL + "' y1='" + y + "' x2='" + (W - padR) + "' y2='" + y
        + "' stroke='" + (tick === 0 ? "#3f3f46" : "#27272a") + "' stroke-width='1'/>";
      yLabels += "<text x='" + (padL - 5) + "' y='" + (y + 3) + "' text-anchor='end'"
        + " font-size='9' fill='#52525b'>" + tick + "</text>";
    }});
    const pointData = [];
    series.forEach(function(p) {{
      const x = xOf(p.x), y = yOf(p.y);
      pts += x + "," + y + " ";
      pointData.push({{ x: Math.round(x), y: Math.round(y), wpm: Math.round(p.y), sec: Math.round(p.x) }});
      circles += "<circle cx='" + Math.round(x) + "' cy='" + Math.round(y) + "' r='4' fill='#86efac'"
               + " class='chart-dot' data-idx='" + (pointData.length - 1) + "'/>";
    }});
    chartEl.innerHTML = "<div class='comp-lbl'>wpm over session</div>"
      + "<div style='position:relative'>"
      + "<div id='chart-tip' style='display:none;position:absolute;background:#1c1c27;border:1px solid #27272a;"
      + "border-radius:6px;padding:4px 8px;font-size:11px;color:#e4e4e7;pointer-events:none;white-space:nowrap'></div>"
      + "<svg id='chart-svg' viewBox='0 0 " + W + " " + H + "' width='100%' height='" + H + "'"
      + " style='display:block;overflow:visible'>"
      + gridLines + yLabels
      + "<polyline points='" + pts.trim() + "' fill='none' stroke='#86efac'"
      + " stroke-width='2' stroke-linejoin='round' stroke-linecap='round'/>"
      + circles + "</svg></div>";

    // Attach hover listeners after inserting into DOM
    const tip = document.getElementById("chart-tip");
    const svg = document.getElementById("chart-svg");
    document.querySelectorAll(".chart-dot").forEach(function(dot) {{
      const d = pointData[parseInt(dot.dataset.idx)];
      dot.addEventListener("mouseenter", function(e) {{
        tip.textContent = d.wpm + " wpm · " + d.sec + "s";
        const svgRect = svg.getBoundingClientRect();
        const dotRect = dot.getBoundingClientRect();
        const relX = dotRect.left - svgRect.left + dotRect.width / 2;
        const relY = dotRect.top - svgRect.top;
        tip.style.left = Math.round(relX) + "px";
        tip.style.top  = Math.round(relY - 30) + "px";
        tip.style.transform = "translateX(-50%)";
        tip.style.display = "block";
        dot.setAttribute("r", "6");
        dot.setAttribute("fill", "#ffffff");
      }});
      dot.addEventListener("mouseleave", function() {{
        tip.style.display = "none";
        dot.setAttribute("r", "4");
        dot.setAttribute("fill", "#86efac");
      }});
    }});
  }} else {{
    chartEl.innerHTML = "";
  }}

  // Per-letter accuracy heatmap for this session
  const letterStats = {{}};
  completedLetters.forEach(function(c) {{
    const ch = sessionWords[c.w][c.l].toUpperCase();
    if (!letterStats[ch]) letterStats[ch] = {{ a: 0, c: 0 }};
    letterStats[ch].a++;
    if (c.correct) letterStats[ch].c++;
  }});
  const seen = Object.keys(letterStats).sort();
  if (seen.length > 0) {{
    let hmHtml = "<div class='comp-lbl'>this session</div><div class='sess-heatmap'>";
    seen.forEach(function(ch) {{
      const s = letterStats[ch];
      const pct = s.c / s.a;
      const hue = Math.round(pct * 120);
      const bg = "hsl(" + hue + ",60%,28%)";
      hmHtml += "<div class='sess-lc' style='background:" + bg + "' title='" + ch + ": " + s.c + "/" + s.a + " correct'>"
             + "<span>" + ch + "</span><span class='spct'>" + Math.round(pct * 100) + "%</span></div>";
    }});
    hmHtml += "</div>";
    document.getElementById("session-heatmap").innerHTML = hmHtml;
  }}
}}

// ── Key handler ──
document.addEventListener("keydown", function(e) {{
  if (e.key === "Tab") {{
    e.preventDefault();
    newSession();
    return;
  }}

  if (document.getElementById("complete").classList.contains("hidden") === false) return;

  if (waitingForWordSep) {{
    if (e.key === WSEP_KEY) {{
      e.preventDefault();
      wordIdx++;
      letterIdx = 0;
      waitingForWordSep = false;
      render();
    }} else if (e.key === "Backspace") {{
      e.preventDefault();
      undoLetter();
    }}
    return;
  }}

  if (e.key === DOT_KEY) {{
    e.preventDefault();
    currentMorse += ".";
    render();
  }} else if (e.key === DASH_KEY) {{
    e.preventDefault();
    currentMorse += "-";
    render();
  }} else if (e.key === LSEP_KEY) {{
    e.preventDefault();
    submitLetter();
  }} else if (e.key === "Backspace") {{
    e.preventDefault();
    undoLetter();
  }} else if (e.key === ESC_KEY) {{
    e.preventDefault();
    currentMorse = "";
    render();
  }}
}});

// ── Init ──
renderModePills();
newSession();
</script>
</body>
</html>
"""

STATS_HTML = """
<!doctype html><html><head><meta charset="utf-8">
<style>
:root{--bg:#0e1117;--text:#e4e4e7;--muted:#71717a;--ok:#86efac;--bad:#f87171;--panel:#1a1d2e;--border:#27272a}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;background:var(--bg);color:var(--text);padding:20px}
.cards{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:24px}
.card{background:var(--panel);border-radius:10px;padding:14px 18px;min-width:90px}
.card-val{font-size:26px;font-weight:700}
.card-lbl{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-top:4px}
.section-lbl{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px}
.chart-wrap{margin-bottom:24px}
.heatmap{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:20px}
.lc{width:42px;height:46px;border-radius:6px;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:13px;font-weight:700;cursor:default}
.lc .pct{font-size:9px;margin-top:3px;color:#a1a1aa}
.no-data{color:var(--muted);padding:40px 0;text-align:center;font-size:14px}
button{background:var(--panel);border:1px solid var(--border);color:var(--muted);border-radius:8px;padding:8px 14px;font-family:inherit;font-size:12px;cursor:pointer;margin-top:16px}
button:hover{color:var(--text)}
</style></head><body>
<div id="root"></div>
<script>
const LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";

function render() {
  const root = document.getElementById("root");
  let raw;
  try { raw = localStorage.getItem("morse_progression"); } catch(e) {}
  if (!raw) { root.innerHTML = "<div class='no-data'>No data yet — finish a session in the Practice tab to start tracking.</div>"; return; }

  const data = JSON.parse(raw);
  const sessions = data.sessions || [];
  const letters  = data.letters  || {};

  if (!sessions.length && !Object.keys(letters).length) {
    root.innerHTML = "<div class='no-data'>No data yet — finish a session in the Practice tab to start tracking.</div>";
    return;
  }

  const avgWpm = sessions.length ? Math.round(sessions.reduce((s,x)=>s+x.wpm,0)/sessions.length) : 0;
  const avgAcc = sessions.length ? Math.round(sessions.reduce((s,x)=>s+x.acc,0)/sessions.length) : 0;
  const totalTyped = Object.values(letters).reduce((s,x)=>s+x.attempts,0);
  const bestWpm = sessions.length ? Math.max(...sessions.map(s=>s.wpm)) : 0;

  let html = "<div class='cards'>";
  html += `<div class='card'><div class='card-val'>${sessions.length}</div><div class='card-lbl'>sessions</div></div>`;
  html += `<div class='card'><div class='card-val'>${avgWpm}</div><div class='card-lbl'>avg wpm</div></div>`;
  html += `<div class='card'><div class='card-val'>${bestWpm}</div><div class='card-lbl'>best wpm</div></div>`;
  html += `<div class='card'><div class='card-val'>${avgAcc}%</div><div class='card-lbl'>avg acc</div></div>`;
  html += `<div class='card'><div class='card-val'>${totalTyped.toLocaleString()}</div><div class='card-lbl'>letters typed</div></div>`;
  html += "</div>";

  let statsRecent = [];
  if (sessions.length > 1) {
    statsRecent = sessions.slice(-30);
    const maxW = Math.max(...statsRecent.map(s => s.wpm), 1);
    const W = 420, H = 80, padL = 32, padR = 38, padT = 6, padB = 4;

    // WPM ticks (left axis)
    const rawStep = maxW / 3;
    const mag = Math.pow(10, Math.floor(Math.log10(rawStep || 1)));
    const niceStep = [1, 2, 5, 10].map(f => f * mag).find(s => s >= rawStep) || rawStep;
    const wpmTicks = [];
    for (let v = 0; v <= maxW + niceStep * 0.5; v += niceStep) wpmTicks.push(Math.round(v));
    const wpmMax = wpmTicks[wpmTicks.length - 1] || 1;

    const xOf    = i   => padL + (i / Math.max(statsRecent.length - 1, 1)) * (W - padL - padR);
    const yOfWpm = wpm => H - padB - (wpm / wpmMax) * (H - padT - padB);
    const yOfAcc = acc => H - padB - (acc / 100)    * (H - padT - padB);

    let gridLines = "", leftLabels = "", rightLabels = "";
    let wpmPts = "", accPts = "", wpmCircles = "", accCircles = "";

    // Grid lines + left WPM labels
    wpmTicks.forEach(tick => {
      const y = Math.round(yOfWpm(tick));
      gridLines   += `<line x1="${padL}" y1="${y}" x2="${W - padR}" y2="${y}" stroke="${tick === 0 ? '#3f3f46' : '#27272a'}" stroke-width="1"/>`;
      leftLabels  += `<text x="${padL - 5}" y="${y + 3}" text-anchor="end" font-size="9" fill="#52525b">${tick}</text>`;
    });

    // Right acc% labels at 0/25/50/75/100
    [0, 25, 50, 75, 100].forEach(tick => {
      const y = Math.round(yOfAcc(tick));
      rightLabels += `<text x="${W - padR + 5}" y="${y + 3}" text-anchor="start" font-size="9" fill="#3b82f680">${tick}%</text>`;
    });

    statsRecent.forEach((s, i) => {
      const x = xOf(i);
      wpmPts += x + "," + yOfWpm(s.wpm) + " ";
      accPts += x + "," + yOfAcc(s.acc)  + " ";
      wpmCircles += `<circle cx="${Math.round(x)}" cy="${Math.round(yOfWpm(s.wpm))}" r="4" fill="#86efac" class="sdot" data-i="${i}" data-type="wpm"/>`;
      accCircles += `<circle cx="${Math.round(x)}" cy="${Math.round(yOfAcc(s.acc))}"  r="4" fill="#60a5fa" class="sdot" data-i="${i}" data-type="acc"/>`;
    });

    html += `<div class='chart-wrap'><div class='section-lbl'>wpm &amp; accuracy — last ${statsRecent.length} sessions</div>`;
    html += "<div style='position:relative'>";
    html += `<div id='stip' style='display:none;position:absolute;background:#1c1c27;border:1px solid #27272a;border-radius:6px;padding:4px 8px;font-size:11px;color:#e4e4e7;pointer-events:none;white-space:nowrap'></div>`;
    html += `<svg id="schart" viewBox="0 0 ${W} ${H}" width="100%" height="${H}" style="display:block;overflow:visible">`;
    html += gridLines + leftLabels + rightLabels;
    html += `<polyline points="${wpmPts.trim()}" fill="none" stroke="#86efac" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>`;
    html += `<polyline points="${accPts.trim()}"  fill="none" stroke="#60a5fa" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>`;
    html += wpmCircles + accCircles + "</svg></div></div>";
  }

  html += "<div class='section-lbl'>letter accuracy — hover for detail</div><div class='heatmap'>";
  for (const ch of LETTERS) {
    const stat = letters[ch];
    let bg, pctText;
    if (!stat || stat.attempts === 0) {
      bg = "#27272a"; pctText = "–";
    } else {
      const pct = stat.correct / stat.attempts;
      pctText = Math.round(pct*100)+"%";
      const hue = Math.round(pct*120);
      bg = `hsl(${hue},60%,28%)`;
    }
    const title = stat ? `${ch}: ${stat.correct}/${stat.attempts} correct` : `${ch}: no data`;
    html += `<div class='lc' style='background:${bg}' title='${title}'><span>${ch}</span><span class='pct'>${pctText}</span></div>`;
  }
  html += "</div>";
  html += "<button onclick='resetStats()'>Reset all stats</button>";

  root.innerHTML = html;

  // Attach hover listeners after DOM is set
  const stip   = document.getElementById("stip");
  const schart = document.getElementById("schart");
  if (stip && schart) {
    document.querySelectorAll(".sdot").forEach(dot => {
      const s = statsRecent[parseInt(dot.dataset.i)];
      if (!s) return;
      const isWpm = dot.dataset.type === "wpm";
      const origFill = isWpm ? "#86efac" : "#60a5fa";
      dot.addEventListener("mouseenter", () => {
        stip.textContent = isWpm ? s.wpm + " wpm" : s.acc + "% acc";
        const svgRect = schart.getBoundingClientRect();
        const dotRect = dot.getBoundingClientRect();
        stip.style.left      = Math.round(dotRect.left - svgRect.left + dotRect.width / 2) + "px";
        stip.style.top       = Math.round(dotRect.top  - svgRect.top  - 30) + "px";
        stip.style.transform = "translateX(-50%)";
        stip.style.display   = "block";
        dot.setAttribute("r", "6");
        dot.setAttribute("fill", "#ffffff");
      });
      dot.addEventListener("mouseleave", () => {
        stip.style.display = "none";
        dot.setAttribute("r", "4");
        dot.setAttribute("fill", origFill);
      });
    });
  }
}

function resetStats() {
  if (!confirm("Reset all progress data?")) return;
  try { localStorage.removeItem("morse_progression"); } catch(e) {}
  render();
}

render();
</script></body></html>
"""

tab_practice, tab_stats = st.tabs(["Practice", "Stats"])
with tab_practice:
    st.iframe(HTML, height=700)
with tab_stats:
    st.iframe(STATS_HTML, height=600)
