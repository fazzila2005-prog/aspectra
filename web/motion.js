// All the movement that isn't the 3D orb:
// words that rise out of a blur, a light that follows the mouse, cards whose border glows under the mouse,
// magnetic buttons, shooting stars, a sliding tab, light beams between the method steps,
// and the tilted wall of review cards. None of it changes what the page says.

const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const finePointer = window.matchMedia("(pointer: fine)").matches;  // a mouse, not a finger
const esc = text => String(text).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

// ---------- 1. Split a heading into words that animate in one after another ----------
export function splitWords(el) {
  let i = 0;
  const wrapWord = content => {
    const outer = document.createElement("span");
    outer.className = "w";
    const inner = document.createElement("span");
    inner.style.setProperty("--i", i++);
    inner.append(content);
    outer.append(inner);
    return outer;
  };
  for (const child of [...el.childNodes]) {
    if (child.nodeType === Node.TEXT_NODE) {
      const frag = document.createDocumentFragment();
      for (const part of child.textContent.split(/(\s+)/)) {
        if (!part) continue;
        frag.append(/^\s+$/.test(part) ? part : wrapWord(part));
      }
      child.replaceWith(frag);
    } else if (child.nodeType === Node.ELEMENT_NODE && child.tagName !== "BR") {
      const placeholder = document.createComment("");
      child.replaceWith(placeholder);
      placeholder.replaceWith(wrapWord(child));  // keep elements like <em> whole
    }
  }
  el.classList.add("split");
}

// ---------- 2. Numbers that count up to their value, e.g. "0.81", "76%" or "−68" ----------
export function countUpAll(root) {
  if (reduceMotion) return;
  root.querySelectorAll("[data-count]").forEach(el => {
    const match = el.textContent.trim().match(/^([^\d]*)([\d.]+)(.*)$/);
    if (!match) return;
    const [, before, number, after] = match;
    const target = parseFloat(number), decimals = (number.split(".")[1] || "").length;
    const t0 = performance.now();
    const step = now => {
      const p = Math.min(Math.max((now - t0) / 1400, 0), 1);
      el.textContent = before + (target * (1 - Math.pow(1 - p, 4))).toFixed(decimals) + after;
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  });
}

// ---------- 3. The tilted wall of review sentences ----------
export function buildWall(rows) {
  const wall = document.getElementById("wall");
  if (!wall || !rows.length) return;
  const columns = 5;
  const cards = rows.map(r => `
    <div class="wall-card ${esc(r.sentiment)}">
      <small><i class="dot ${esc(r.sentiment)}"></i>${esc(r.aspect)} · ${r.count} ${r.count === 1 ? "review" : "reviews"}</small>
      <p>“${esc(r.sentence)}”</p>
    </div>`);
  let html = "";
  for (let c = 0; c < columns; c++) {
    let col = cards.filter((_, i) => i % columns === c);
    while (col.length < 5) col = col.concat(cards.slice(0, 5 - col.length));  // short lists still fill the column
    html += `<div class="wall-col">${col.join("")}${col.join("")}</div>`;  // twice, so it loops without a gap
  }
  wall.innerHTML = html;
}

// ---------- 4. Light following the mouse, and card borders that glow where the mouse is ----------
function spotlights() {
  const light = document.querySelector(".spotlight");
  document.addEventListener("pointermove", e => {
    light.style.setProperty("--mx", `${e.clientX}px`);
    light.style.setProperty("--my", `${e.clientY}px`);
    const card = e.target.closest?.(".spot");
    if (card) {
      const r = card.getBoundingClientRect();
      card.style.setProperty("--x", `${e.clientX - r.left}px`);
      card.style.setProperty("--y", `${e.clientY - r.top}px`);
    }
  });
}

// ---------- 5. Magnetic buttons lean towards the mouse; aspect cards tilt in 3D ----------
function magnetic() {
  let active = null;
  document.addEventListener("pointermove", e => {
    const btn = e.target.closest?.(".btn, .chip");
    if (active && active !== btn) { active.style.setProperty("--px", "0px"); active.style.setProperty("--py", "0px"); }
    active = btn;
    if (btn) {
      const r = btn.getBoundingClientRect();
      btn.style.setProperty("--px", `${(e.clientX - r.left - r.width / 2) * 0.2}px`);
      btn.style.setProperty("--py", `${(e.clientY - r.top - r.height / 2) * 0.3}px`);
    }
    const tile = e.target.closest?.(".tile");
    document.querySelectorAll(".tile").forEach(t => { if (t !== tile) t.style.transform = ""; });
    if (tile) {
      const r = tile.getBoundingClientRect();
      const px = (e.clientX - r.left) / r.width - 0.5, py = (e.clientY - r.top) / r.height - 0.5;
      tile.style.transform = `perspective(800px) rotateX(${-py * 12}deg) rotateY(${px * 14}deg) translateZ(8px)`;
    }
  });
}

// ---------- 6. Shooting stars in the hero ----------
function meteors() {
  const box = document.querySelector(".meteors");
  for (let i = 0; i < 14; i++) {
    const m = document.createElement("i");
    m.style.left = `${Math.random() * 110}%`;
    m.style.setProperty("--delay", `${Math.random() * 8}s`);
    m.style.setProperty("--d", `${4 + Math.random() * 6}s`);
    box.append(m);
  }
}

// ---------- 7. Progress line in the menu, and the current section's link lit up ----------
function progressBar() {
  const bar = document.getElementById("progress");
  const update = () => {
    const max = document.documentElement.scrollHeight - innerHeight;
    bar.style.transform = `scaleX(${max > 0 ? scrollY / max : 0})`;
    let current = "";
    document.querySelectorAll("main section[id]").forEach(s => { if (s.getBoundingClientRect().top < innerHeight * 0.4) current = s.id; });
    document.querySelectorAll(".nav-links a").forEach(a => a.classList.toggle("here", a.getAttribute("href") === "#" + current));
  };
  addEventListener("scroll", update, { passive: true });
  update();
}

// ---------- 8. The evaluation tabs: a white "thumb" slides under the chosen tab ----------
export function moveThumb() {
  const toggle = document.querySelector(".toggle");
  const active = toggle.querySelector("button.active");
  const thumb = toggle.querySelector(".toggle-thumb");
  if (!active || !active.offsetWidth) return;
  thumb.style.width = `${active.offsetWidth}px`;
  thumb.style.transform = `translateX(${active.offsetLeft}px)`;
  toggle.classList.add("ready");
}

// ---------- 9. Light beams travelling between the five method steps ----------
function beams() {
  const svg = document.getElementById("beams");
  const draw = () => {
    const box = svg.getBoundingClientRect();
    const nodes = [...document.querySelectorAll(".pipeline .node")].map(n => {
      const r = n.getBoundingClientRect();
      return { x: r.left + r.width / 2 - box.left, y: r.top + r.height / 2 - box.top };
    });
    let paths = "";
    for (let i = 0; i < nodes.length - 1; i++) {
      const a = nodes[i], b = nodes[i + 1];
      // From the edge of one step's icon to the edge of the next (side by side, or stacked on phones)
      const across = Math.abs(b.x - a.x) > Math.abs(b.y - a.y);
      const d = across ? `M${a.x + 30},${a.y} L${b.x - 30},${b.y}` : `M${a.x},${a.y + 30} L${b.x},${b.y - 30}`;
      paths += `<path class="base" d="${d}"/><path class="light" d="${d}" style="animation-delay:${i * 0.5}s"/>`;
    }
    svg.innerHTML = `<defs><linearGradient id="beamGrad" x1="0" x2="1"><stop offset="0" stop-color="#5b8cff" stop-opacity="0"/>
      <stop offset="0.4" stop-color="#3dffd0"/><stop offset="1" stop-color="#c6ff3d"/></linearGradient></defs>${paths}`;
  };
  addEventListener("resize", draw);
  new ResizeObserver(draw).observe(svg.parentElement);
  draw();
}

// A shared gradient used by the evaluation rings
function sharedDefs() {
  document.body.insertAdjacentHTML("beforeend", `<svg width="0" height="0" style="position:absolute" aria-hidden="true">
    <defs><linearGradient id="ringGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#5b8cff"/>
    <stop offset="0.5" stop-color="#3dffd0"/><stop offset="1" stop-color="#c6ff3d"/></linearGradient></defs></svg>`);
}

// ---------- 10. Sections slide up out of a blur as they scroll into view ----------
function reveals() {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(en => {
      if (!en.isIntersecting) return;
      en.target.classList.add("visible");
      countUpAll(en.target);
      observer.unobserve(en.target);
    });
  }, { threshold: 0.08 });
  document.querySelectorAll(".section, .wall-wrap").forEach(s => { s.classList.add("reveal"); observer.observe(s); });
}

export function startMotion() {
  sharedDefs();
  document.querySelectorAll("h1, .section-head h2, .big-title").forEach(splitWords);
  document.querySelectorAll(".pipeline li").forEach((li, i) => li.style.setProperty("--i", i));
  reveals();
  progressBar();
  beams();
  moveThumb();
  addEventListener("resize", moveThumb);
  if (reduceMotion) return;
  meteors();
  spotlights();
  if (finePointer) magnetic();
}
