// The 3D hero: every aspect mention is one glowing particle.
// Particles start scattered, then fly into 4 clusters (one per aspect), coloured by mood.
import * as THREE from "three";

const COLORS = { positive: "#5ee0a0", neutral: "#8f8b82", negative: "#ff6a45" };
// Where each aspect's cluster sits in 3D space
const CENTERS = {
  price: new THREE.Vector3(-2.3, 1.4, 0.5),
  quality: new THREE.Vector3(2.3, 1.5, -0.5),
  delivery: new THREE.Vector3(-1.8, -1.7, -0.6),
  support: new THREE.Vector3(2.0, -1.6, 0.6),
};
const RADIUS = 1.15;

const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
let renderer, scene, camera, group, points, labels = [];
let start = [], target = [], delays = [], startTime = 0;
let mouseX = 0, mouseY = 0, dragging = false, dragRotation = 0, lastX = 0;

// A soft round dot texture, drawn once on a small canvas
function dotTexture() {
  const c = document.createElement("canvas");
  c.width = c.height = 64;
  const g = c.getContext("2d");
  const gradient = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  gradient.addColorStop(0, "rgba(255,255,255,1)");
  gradient.addColorStop(0.35, "rgba(255,255,255,0.9)");
  gradient.addColorStop(1, "rgba(255,255,255,0)");
  g.fillStyle = gradient;
  g.fillRect(0, 0, 64, 64);
  return new THREE.CanvasTexture(c);
}

// A random point inside a ball, bunched towards the middle
function randomInBall(radius) {
  const v = new THREE.Vector3(Math.random() * 2 - 1, Math.random() * 2 - 1, Math.random() * 2 - 1);
  return v.normalize().multiplyScalar(radius * Math.pow(Math.random(), 0.6));
}

export function startScene(container, labelLayer) {
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  container.appendChild(renderer.domElement);

  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
  camera.position.set(0, 0, 9);
  group = new THREE.Group();
  scene.add(group);

  // Thin rings around each cluster, like orbits
  for (const center of Object.values(CENTERS)) {
    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(RADIUS + 0.25, 0.005, 8, 160),
      new THREE.MeshBasicMaterial({ color: 0xefece4, transparent: true, opacity: 0.18 })
    );
    ring.position.copy(center);
    ring.rotation.x = Math.random() * Math.PI;
    ring.rotation.y = Math.random() * Math.PI;
    group.add(ring);
  }

  // Faint background dust, for a sense of depth
  const dust = new THREE.BufferGeometry();
  dust.setAttribute("position", new THREE.Float32BufferAttribute(
    Array.from({ length: 900 }, () => (Math.random() - 0.5) * 30), 3));
  scene.add(new THREE.Points(dust, new THREE.PointsMaterial({ size: 0.03, color: 0x8f8b82, transparent: true, opacity: 0.5 })));

  // Mouse: gentle tilt on hover, spin on drag
  container.addEventListener("pointermove", e => {
    const r = container.getBoundingClientRect();
    mouseX = (e.clientX - r.left) / r.width - 0.5;
    mouseY = (e.clientY - r.top) / r.height - 0.5;
    if (dragging) { dragRotation += (e.clientX - lastX) * 0.01; lastX = e.clientX; }
  });
  container.addEventListener("pointerdown", e => { dragging = true; lastX = e.clientX; });
  window.addEventListener("pointerup", () => { dragging = false; });

  // One HTML label per aspect, moved to follow its cluster
  labels = Object.keys(CENTERS).map(aspect => {
    const el = document.createElement("div");
    el.className = "scene-label";
    labelLayer.appendChild(el);
    return { aspect, el };
  });

  new ResizeObserver(() => resize(container)).observe(container);
  resize(container);
  renderer.setAnimationLoop(animate);
}

function resize(container) {
  const { width, height } = container.getBoundingClientRect();
  renderer.setSize(width, height);
  camera.aspect = width / height;
  // Move the camera back on narrow screens so all clusters fit
  camera.position.z = width / height < 1 ? 15 : 10.5;
  camera.updateProjectionMatrix();
}

// Build (or rebuild) the particles from the summary numbers
export function updateScene(aspects) {
  if (points) { group.remove(points); points.geometry.dispose(); }
  const colors = [];
  start = []; target = []; delays = [];
  const maxPerAspect = 450;  // keep it smooth on slow laptops
  for (const a of aspects) {
    const center = CENTERS[a.aspect];
    if (!center) continue;
    const total = a.positive + a.neutral + a.negative;
    const scale = Math.min(1, maxPerAspect / total);
    for (const mood of ["positive", "neutral", "negative"]) {
      const n = Math.round(a[mood] * scale);
      const color = new THREE.Color(COLORS[mood]);
      for (let i = 0; i < n; i++) {
        target.push(center.clone().add(randomInBall(RADIUS)));
        start.push(randomInBall(7));
        delays.push(Math.random() * 0.8);
        colors.push(color.r, color.g, color.b);
      }
    }
    // Label text: aspect name and its share of negative mentions
    const label = labels.find(l => l.aspect === a.aspect);
    label.el.innerHTML = `<b>${a.aspect}</b><span>${total} mentions · ${Math.round((a.negative / total) * 100)}% negative</span>`;
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(new Array(target.length * 3).fill(0), 3));
  geometry.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
  points = new THREE.Points(geometry, new THREE.PointsMaterial({
    size: 0.16, map: dotTexture(), vertexColors: true, transparent: true,
    depthWrite: false, blending: THREE.AdditiveBlending,
  }));
  group.add(points);
  startTime = performance.now();
  labels.forEach(l => l.el.classList.remove("show"));
}

const easeOut = t => 1 - Math.pow(1 - t, 3);
const projected = new THREE.Vector3();
const above = new THREE.Vector3(0, RADIUS + 0.55, 0);

function animate(now) {
  if (!points) return;
  // 1. Fly each particle from its start to its cluster
  const t = (now - startTime) / 1000;
  const pos = points.geometry.attributes.position;
  let settled = true;
  for (let i = 0; i < target.length; i++) {
    const p = reduceMotion ? 1 : easeOut(Math.min(Math.max((t - delays[i]) / 2.2, 0), 1));
    if (p < 1) settled = false;
    // Add a tiny wobble once settled so the clusters feel alive
    const wobble = reduceMotion ? 0 : Math.sin(now * 0.001 + i) * 0.02;
    pos.setXYZ(i,
      start[i].x + (target[i].x - start[i].x) * p + wobble,
      start[i].y + (target[i].y - start[i].y) * p + wobble,
      start[i].z + (target[i].z - start[i].z) * p);
  }
  pos.needsUpdate = true;

  // 2. Gently sway the whole cloud (so clusters never hide each other), tilt towards the mouse
  if (!reduceMotion) {
    const sway = Math.sin(now * 0.0003) * 0.45;
    group.rotation.y += (dragRotation + sway + mouseX * 0.6 - group.rotation.y) * 0.05;
    group.rotation.x += (mouseY * 0.4 - group.rotation.x) * 0.05;
  }
  renderer.render(scene, camera);

  // 3. Keep the HTML labels on top of their clusters
  const { width, height } = renderer.domElement.getBoundingClientRect();
  for (const l of labels) {
    // Place the label just above the top of its cluster
    projected.copy(CENTERS[l.aspect]).applyMatrix4(group.matrixWorld).add(above).project(camera);
    l.el.style.left = `${(projected.x * 0.5 + 0.5) * width}px`;
    l.el.style.top = `${(-projected.y * 0.5 + 0.5) * height}px`;
    if (settled || t > 2.5) l.el.classList.add("show");
  }
}
