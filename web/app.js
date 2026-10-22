import { startScene, updateScene } from "./scene.js";

const MOODS = ["positive", "neutral", "negative"];
const $ = id => document.getElementById(id);

// Small helper: ask our API for something and return the JSON answer
async function api(path, options) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Something went wrong");
  return data;
}

// Review text comes from uploaded files, so never put it into the page as raw HTML
function esc(text) {
  return String(text).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// Animate a number counting up (e.g. 0 → 392)
function countUp(el, target) {
  const t0 = performance.now();
  const step = now => {
    const p = Math.min((now - t0) / 1400, 1);
    el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3)));
    if (p < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

// A stacked positive / neutral / negative bar
function stackBar(c) {
  const total = c.positive + c.neutral + c.negative || 1;
  return `<div class="stack">${MOODS.map(m => `<span class="${m}" style="width:${(c[m] / total) * 100}%"></span>`).join("")}</div>`;
}

// One labelled horizontal bar
function barRow(label, value, max, colorClass) {
  return `<div class="bar-row"><span class="what">${label}</span><span class="n">${value}</span>
    <div class="bar-track"><div class="bar-fill ${colorClass}" style="width:${(value / max) * 100}%"></div></div></div>`;
}

// "+ 4 similar wordings" note for a grouped point
function wordings(n) {
  return n > 1 ? `<span class="similar">+ ${n - 1} similar ${n === 2 ? "wording" : "wordings"}</span>` : "";
}

// Clickable review-ID tags that open the full review
function idTags(ids) {
  return ids.map(id => `<button type="button" class="id" data-review="${esc(id)}">#${esc(id)}</button>`).join("");
}

// ---------- Hero + 01 Aspects ----------
async function loadSummary() {
  const data = await api("/api/summary");
  const mentions = data.aspects.reduce((s, a) => s + a.positive + a.neutral + a.negative, 0);
  $("hero-count").textContent = data.total_reviews;
  countUp($("kpi-reviews"), data.total_reviews);
  countUp($("kpi-mentions"), mentions);
  const worst = [...data.aspects].sort((a, b) => b.negative - a.negative)[0];
  $("kpi-issue").textContent = worst ? worst.aspect : "–";
  updateScene(data.aspects);

  // Aspect tiles with a net score: % positive minus % negative
  $("aspect-grid").innerHTML = data.aspects.map(a => {
    const total = a.positive + a.neutral + a.negative;
    const net = Math.round(((a.positive - a.negative) / total) * 100);
    const color = net > 10 ? "var(--positive)" : net < -10 ? "var(--negative)" : "var(--text)";
    return `<button type="button" class="tile" data-aspect="${esc(a.aspect)}">
      <div class="name">${esc(a.aspect)}</div>
      <div class="score" style="color:${color}">${net > 0 ? "+" : net < 0 ? "−" : ""}${Math.abs(net)}</div>
      <div class="sub">${total} mentions · ${a.positive} positive · ${a.negative} negative</div>
      <div class="mini">${stackBar(a)}</div>
    </button>`;
  }).join("");

  $("complaints").innerHTML = data.top_complaints.map(c => `
    <li><span class="quote">“${esc(c.sentence)}”</span>
    <span class="meta"><i class="dot negative"></i> ${esc(c.aspect)} · ${c.count} ${c.count === 1 ? "review" : "reviews"} ${wordings(c.wordings)}</span></li>`).join("");
}

// Clicking a tile asks a question about that aspect
$("aspect-grid").addEventListener("click", e => {
  const tile = e.target.closest(".tile");
  if (!tile) return;
  const q = `How do customers feel about ${tile.dataset.aspect}?`;
  $("question").value = q;
  ask(q);
  $("ask").scrollIntoView();
});

// ---------- 02 Ask ----------
function donut(b) {
  const total = b.positive + b.neutral + b.negative;
  const r = 80, circumference = 2 * Math.PI * r;
  let offset = 0;
  const arcs = MOODS.map(m => {
    const length = (b[m] / total) * circumference;
    const arc = `<circle r="${r}" cx="100" cy="100" stroke="var(--${m})"
      stroke-dasharray="${length} ${circumference - length}" stroke-dashoffset="${-offset}"></circle>`;
    offset += length;
    return arc;
  }).join("");
  const pct = Math.round((b.positive / total) * 100);
  return `<div class="donut-wrap">
      <svg viewBox="0 0 200 200" role="img" aria-label="${b.positive} positive, ${b.neutral} neutral, ${b.negative} negative">
        <circle r="${r}" cx="100" cy="100" stroke="var(--line)"></circle>${arcs}
      </svg>
      <div class="donut-center"><b>${pct}%</b><span>positive</span></div>
    </div>
    <ul class="legend">${MOODS.map(m => `<li><i class="dot ${m}"></i>${b[m]} ${m}</li>`).join("")}</ul>`;
}

async function ask(question) {
  const box = $("answer");
  box.innerHTML = `<p class="verdict none">Reading the reviews…</p>`;
  let data;
  try {
    data = await api("/api/ask", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question }),
    });
  } catch (error) {
    box.innerHTML = `<p class="verdict none">${esc(error.message)}</p>`;
    return;
  }

  // No evidence: say so plainly
  if (!data.evidence.length) {
    box.innerHTML = `<p class="verdict none">${esc(data.verdict)}</p>
      <p class="muted">None of the reviews mention this, so Aspectra won't guess.</p>`;
    return;
  }

  // 1. Verdict  2. Mood donut  3. Bar chart of the top points  4. Mood split per aspect
  const max = Math.max(...data.evidence.map(e => e.count));
  const points = data.evidence.map(e => `
    <div class="point">${barRow(`“${esc(e.sentence)}”`, e.count, max, e.sentiment)}
      <div class="ids">${idTags(e.review_ids)}${wordings(e.wordings)}</div></div>`).join("");

  // Left column: a mood donut, or (if the question asked for one mood) which aspects it comes from
  const moods = MOODS.filter(m => data.breakdown[m] > 0);
  let left;
  if (moods.length > 1) {
    left = donut(data.breakdown);
  } else {
    const counts = Object.entries(data.by_aspect).map(([a, c]) => [a, c[moods[0]]]).sort((x, y) => y[1] - x[1]);
    left = `<h4>Where the ${moods[0]} mentions come from</h4>` +
      counts.map(([a, n]) => barRow(esc(a), n, counts[0][1], moods[0])).join("");
  }
  const byAspect = Object.entries(data.by_aspect)
    .map(([aspect, c]) => `<div><span class="name">${esc(aspect)}</span>${stackBar(c)}</div>`).join("");

  box.innerHTML = `
    <p class="verdict">${esc(data.verdict)}</p>
    <div class="answer-grid">
      <div>${left}</div>
      <div><h4>Most common points · number of reviews · click an ID to read it</h4>${points}</div>
    </div>
    ${moods.length > 1 && Object.keys(data.by_aspect).length > 1 ? `<div class="by-aspect">${byAspect}</div>` : ""}`;
}

$("ask-form").addEventListener("submit", e => {
  e.preventDefault();
  const q = $("question").value.trim();
  if (q) ask(q);
  else $("answer").innerHTML = `<p class="verdict none">Type a question first.</p>`;
});
$("chips").addEventListener("click", e => {
  if (!e.target.matches(".chip")) return;
  $("question").value = e.target.textContent;
  ask(e.target.textContent);
});

// ---------- 03 Evidence ----------
const PAGE = 10;
let shown = 0;
let latest = 0;  // which request is the newest, so a slow old answer can't overwrite a newer one

// Load the first page (more = false) or the next page (more = true) of matching sentences
async function loadReviews(more = false) {
  const aspect = $("filter-aspect").value;
  const sentiment = $("filter-sentiment").value;
  const request = ++latest;
  const offset = more ? shown : 0;
  const data = await api(`/api/reviews?aspect=${aspect}&sentiment=${sentiment}&limit=${PAGE}&offset=${offset}`);
  if (request !== latest) return;
  shown = offset;
  // One line per distinct sentence; open it to see which reviews said it
  const rows = data.rows.map(r => `
    <details class="group">
      <summary class="row">
        <i class="dot ${r.sentiment}"></i><span>${esc(r.sentence)}</span>
        <small>${esc(r.aspect)} · ${r.count} ${r.count === 1 ? "review" : "reviews"}${r.wordings > 1 ? ` · ${r.wordings} wordings` : ""}</small>
      </summary>
      <div class="ids">${idTags(r.review_ids)}</div>
    </details>`).join("");
  shown += data.rows.length;
  if (more) $("review-list").insertAdjacentHTML("beforeend", rows);
  else $("review-list").innerHTML = rows || `<p class="muted">No sentences match these filters.</p>`;
  $("review-count").textContent = data.total
    ? `${data.mentions} mentions, grouped into ${data.total} recurring points` +
      (shown < data.total ? ` · showing ${shown}` : "") : "";
  $("more-reviews").hidden = shown >= data.total;
}
$("filter-aspect").addEventListener("change", () => loadReviews());
$("filter-sentiment").addEventListener("change", () => loadReviews());
$("more-reviews").addEventListener("click", () => loadReviews(true));

// Open the full review in a pop-up, from anywhere on the page
document.addEventListener("click", async e => {
  const btn = e.target.closest("[data-review]");
  if (!btn) return;
  let r;
  try {
    r = await api(`/api/review/${encodeURIComponent(btn.dataset.review)}`);
  } catch (error) {
    $("review-body").innerHTML = `<p class="big">This review could not be loaded.</p><p class="muted">${esc(error.message)}</p>`;
    $("review-dialog").showModal();
    return;
  }
  $("review-body").innerHTML = `
    <p class="label">Review #${esc(r.review_id)}${r.product && r.product !== "Unknown" ? " · " + esc(r.product) : ""}${r.rating ? " · " + r.rating + "/5 stars" : ""}</p>
    <p class="big">“${esc(r.text)}”</p>
    <h4 class="muted">What Aspectra found</h4>
    <ul class="found">${r.aspects.map(a => `<li><i class="dot ${a.sentiment}"></i><b>${esc(a.aspect)}</b>${esc(a.sentence)}</li>`).join("")}</ul>`;
  $("review-dialog").showModal();
});

// ---------- 04 Evaluation ----------
let evaluation;

function heat(value, max, isCorrect) {
  const alpha = max ? 0.15 + (value / max) * 0.85 : 0.15;
  const rgb = isCorrect ? "94,224,160" : "255,106,69";
  return value ? `rgba(${rgb},${alpha})` : "var(--surface)";
}

function renderEval(set) {
  const e = evaluation[set];
  const d = e.detection;
  const metric = (v, k, p) => `<div class="metric"><div class="v">${v}</div><div class="k">${k}</div><p>${p}</p></div>`;
  const maxCell = Math.max(...e.confusion.flat());
  const matrix = `<div class="matrix">
      <span></span>${e.moods.map(m => `<span class="h">said ${m}</span>`).join("")}
      ${e.confusion.map((row, i) => `<span class="h row-h">really ${e.moods[i]}</span>` +
        row.map((v, j) => `<span class="cell" style="background:${heat(v, maxCell, i === j)}">${v}</span>`).join("")).join("")}
    </div>`;
  const aspectBars = ["price", "quality", "delivery", "support"]
    .map(a => barRow(a, d[a].f1.toFixed(2), 1, "accent")).join("");
  const showAll = $("eval-body").dataset.all === "1";
  const failures = (showAll ? e.failures : e.failures.slice(0, 6)).map(f => `
    <li><span class="p">${esc(f.review_id)} · ${esc(f.problem)}</span><q>${esc(f.text)}</q></li>`).join("");

  const f1 = name => evaluation[name].detection.all.f1.toFixed(2);
  $("eval-body").innerHTML = `
    <div class="metrics">
      ${metric(d.all.f1.toFixed(2), "Aspect F1", "One score combining precision and recall (1.00 = perfect).")}
      ${metric(d.all.precision.toFixed(2), "Precision", "When it names an aspect, how often it's right.")}
      ${metric(d.all.recall.toFixed(2), "Recall", "Of all real mentions, how many it finds.")}
      ${metric(Math.round(e.sentiment_accuracy * 100) + "%", "Mood accuracy", `On the ${e.sentiment_examples} aspect mentions it found correctly.`)}
    </div>
    <div class="eval-grid">
      <div><h3>F1 per aspect</h3>${aspectBars}
        <p class="muted">${e.labels} hand-labelled examples from ${e.reviews} reviews.</p></div>
      <div><h3>Mood: right vs wrong</h3>${matrix}
        <p class="matrix-note">Green diagonal = correct. Red = mistakes (row = the right answer, column = what Aspectra said).</p></div>
    </div>
    <div class="gap-note">Practice set F1 <b>${f1("practice")}</b> and old exam <b>${f1("old_exam")}</b>, but new exam
      <b>${f1("exam")}</b>. The first two look better because the keyword list was improved using their mistakes
      (that's <b>overfitting</b>). Every fix came only from practice and old-exam mistakes, never from the new exam.
      Its first 37 labels were made before those fixes and went from 0.69 to 0.83; 12 more labels were added later
      and scored once, with no changes, giving ${f1("exam")} on all ${evaluation.exam.labels}. Its weak spot is quality words the list doesn't know yet, like "grip",
      "audio" or "heating".</div>
    <div style="margin-top:48px"><h3>Failure cases (${e.failures.length})</h3>
      <ul class="failures">${failures}</ul>
      ${e.failures.length > 6 ? `<button type="button" class="btn more" id="toggle-failures">${showAll ? "Show fewer" : "Show all"}</button>` : ""}
    </div>`;
  $("toggle-failures")?.addEventListener("click", () => {
    $("eval-body").dataset.all = showAll ? "0" : "1";
    renderEval(set);
  });
}

document.querySelector(".toggle").addEventListener("click", e => {
  const btn = e.target.closest("button");
  if (!btn) return;
  document.querySelectorAll(".toggle button").forEach(b => b.classList.toggle("active", b === btn));
  renderEval(btn.dataset.set);
});

async function loadEval() {
  evaluation = await api("/api/eval");
  renderEval("exam");
}

// ---------- Upload a CSV ----------
$("file").addEventListener("change", async e => {
  const file = e.target.files[0];
  if (!file) return;
  e.target.value = "";  // so choosing the same file again still triggers an upload
  const form = new FormData();
  form.append("file", file);
  $("upload-msg").textContent = "Reading your file…";
  try {
    const data = await api("/api/upload", { method: "POST", body: form });
    $("upload-msg").textContent = "Done: " + data.message + ". Everything above now uses your file.";
    $("data-pill").textContent = "Your uploaded data";
    loadSummary();
    loadReviews();
    $("answer").innerHTML = "";
  } catch (error) {
    $("upload-msg").textContent = "Could not use that file: " + error.message;
  }
});

// ---------- Sections fade in as you scroll ----------
const observer = new IntersectionObserver(entries => {
  entries.forEach(en => { if (en.isIntersecting) en.target.classList.add("visible"); });
}, { threshold: 0.1 });
document.querySelectorAll(".section").forEach(s => { s.classList.add("reveal"); observer.observe(s); });

// Start!
startScene($("scene"), $("scene-labels"));
loadSummary();
loadReviews();
loadEval();
