// EcoPredict — 3D inverter lab (lab 12).
//
// One page for every client:
//   * the website embeds it as a Streamlit component (dashboard/components/lab3d.py):
//     arguments arrive as "streamlit:render" messages, events go back with
//     setComponentValue and Python grades them;
//   * the mobile app opens it in a WebView from the API server
//     (/static/lab3d/index.html?lang=kk&api=<server>): the test is fetched from and
//     graded by the API, and every event is also written to the console as
//     "LAB3D {json}", which the app reads through WebView.on_console_message;
//   * a plain browser works like the mobile case.
//
// Modes: explore (tap a part, read what it is), fix (a fault scenario: inspect
// parts, operate them, check the board) and test (graded questions, some of
// which are answered by tapping the model or fixing a board).

import {
  AmbientLight, Box3, BoxGeometry, CanvasTexture, Color, DirectionalLight, DoubleSide, Group,
  HemisphereLight, Mesh, MeshBasicMaterial, MeshStandardMaterial, PerspectiveCamera, Raycaster,
  RepeatWrapping, Scene, SRGBColorSpace, TextureLoader, Vector2, Vector3, WebGLRenderer,
  OrbitControls, OBJLoader,
} from './vendor/three-lab.min.js';

const LAB_ID = 'lab_inverter_wiring';
const Q = new URLSearchParams(location.search);
const IN_STREAMLIT = Q.has('streamlitUrl');

const UI = {
  en: {
    explore: 'Explore', fix: 'Fix faults', test: 'Test',
    loading: 'Loading the 3D model…', webgl: 'This device cannot show 3D (WebGL is off). You can still pick parts from the list.',
    hintExplore: 'Drag to rotate · pinch or scroll to zoom · tap a part',
    hintFix: 'Inspect parts by tapping them, fix what is wrong, then press Check',
    hintTest: 'Answer each question; some are answered by tapping the model',
    parts: 'Parts of the system', pickPart: 'Tap a part in the model or in the list.',
    scenario: 'Scenario', reset: 'Start again', check: 'Check the system',
    plant: 'What the plant shows', display: 'Inverter display', pac: 'Output Pac', vpv: 'PV voltage', vac: 'Grid voltage',
    meter: 'Meter', counting: 'counting', stopped: 'stopped', cloud: 'Monitoring', online: 'online', offline: 'offline',
    state: 'State', inspect: 'Tap a part to inspect it.', noControl: 'Nothing to operate here — watch its readings.',
    allOk: 'All correct — the plant exports to the grid.', notYet: 'Not yet: {n} of {t} items are right. Keep inspecting.',
    toggleOn: 'Switch ON', toggleOff: 'Switch OFF', swapDc: 'Swap the DC plugs', swapLn: 'Swap L and N',
    pePlug: 'Connect PE to the earth bar', peUnplug: 'Disconnect PE', loggerIn: 'Plug the logger in', loggerOut: 'Pull the logger out',
    q: 'Question {i} of {n}', tapModel: 'Tap the part in the 3D model.', selected: 'Part selected.', noneSelected: 'No part selected yet.',
    fixThis: 'Fix this system in the model, then press Next.', next: 'Next', prev: 'Back', submit: 'Submit the test',
    score: 'Score: {s} of {t} ({p}%)', passed: 'Passed', failed: 'Not passed — review and try again', retry: 'Try again',
    correct: 'Correct', wrong: 'Wrong', loadingTest: 'Loading the test…', testError: 'Could not load the test: {e}',
    gradeError: 'Could not grade: {e}', grading: 'Grading…', yourAnswer: 'Your answer',
    added: 'Added for the lab (not in the CAD model).',
  },
  kk: {
    explore: 'Зерттеу', fix: 'Ақауды түзету', test: 'Тест',
    loading: '3D модель жүктелуде…', webgl: 'Бұл құрылғы 3D көрсете алмайды (WebGL өшірулі). Бөліктерді тізімнен таңдауға болады.',
    hintExplore: 'Айналдыру — сүйреңіз · масштаб — екі саусақ не дөңгелек · бөлікті басыңыз',
    hintFix: 'Бөліктерді басып тексеріңіз, қатесін түзетіп, «Тексеру» басыңыз',
    hintTest: 'Сұрақтарға жауап беріңіз; кейбіріне модельдегі бөлікті басып жауап бересіз',
    parts: 'Жүйе бөліктері', pickPart: 'Модельдегі немесе тізімдегі бөлікті басыңыз.',
    scenario: 'Сценарий', reset: 'Қайта бастау', check: 'Жүйені тексеру',
    plant: 'Станция көрсеткіштері', display: 'Инвертор экраны', pac: 'Шығыс Pac', vpv: 'PV кернеуі', vac: 'Желі кернеуі',
    meter: 'Есептегіш', counting: 'санап тұр', stopped: 'тоқтап тұр', cloud: 'Мониторинг', online: 'онлайн', offline: 'офлайн',
    state: 'Күйі', inspect: 'Тексеру үшін бөлікті басыңыз.', noControl: 'Мұнда басқаратын нәрсе жоқ — көрсеткіштерін бақылаңыз.',
    allOk: 'Барлығы дұрыс — станция желіге қуат береді.', notYet: 'Әзірге {t} тармақтың {n}-і дұрыс. Тексеруді жалғастырыңыз.',
    toggleOn: 'Қосу', toggleOff: 'Ажырату', swapDc: 'DC ашаларын ауыстыру', swapLn: 'L мен N-ді ауыстыру',
    pePlug: 'PE-ні жер шинасына қосу', peUnplug: 'PE-ні ажырату', loggerIn: 'Логгерді қосу', loggerOut: 'Логгерді суыру',
    q: '{n} сұрақтың {i}-і', tapModel: '3D модельдегі бөлікті басыңыз.', selected: 'Бөлік таңдалды.', noneSelected: 'Бөлік әлі таңдалмады.',
    fixThis: 'Модельде осы жүйені түзетіп, «Келесі» басыңыз.', next: 'Келесі', prev: 'Артқа', submit: 'Тестті тапсыру',
    score: 'Нәтиже: {t} сұрақтың {s}-і ({p}%)', passed: 'Өтті', failed: 'Өтпеді — қайталап, қайта көріңіз', retry: 'Қайта тапсыру',
    correct: 'Дұрыс', wrong: 'Қате', loadingTest: 'Тест жүктелуде…', testError: 'Тестті жүктеу мүмкін болмады: {e}',
    gradeError: 'Бағалау мүмкін болмады: {e}', grading: 'Бағалануда…', yourAnswer: 'Сіздің жауабыңыз',
    added: 'Зертхана үшін қосылған (CAD моделінде жоқ).',
  },
};

const S = {
  lang: Q.get('lang') === 'en' ? 'en' : 'kk',
  mode: ['explore', 'fix', 'test'].includes(Q.get('mode')) ? Q.get('mode') : 'explore',
  api: (Q.get('api') || '').replace(/\/$/, ''),
  scenario: Q.get('scenario') || 'reversed_dc',
  board: null,
  selected: null,
  checkResult: null,
  test: { questions: null, pass: 70, index: 0, answers: {}, result: null, error: '', busy: false },
  args: {},
  no3d: false,
  meterKwh: 1523.4,
};

const tr = (k, vars = {}) => (UI[S.lang][k] ?? UI.en[k] ?? k).replace(/\{(\w+)\}/g, (_, v) => vars[v] ?? '');
const L = (o) => (o && typeof o === 'object' ? (o[S.lang] ?? o.en ?? '') : (o ?? ''));
const $ = (sel) => document.querySelector(sel);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

// ---------------------------------------------------------------- host messaging
function toStreamlit(type, extra = {}) {
  window.parent.postMessage({ isStreamlitMessage: true, type, ...extra }, '*');
}
let seq = 0;
// Streamlit reruns the whole page on every component value, so it only gets
// the events it acts on; the console (mobile app) and postMessage get all.
const STREAMLIT_EVENTS = new Set(['check', 'test_submit']);
function emit(msg) {
  const m = { lab: LAB_ID, ...msg, nonce: `${Date.now()}-${++seq}` };
  try { console.log('LAB3D ' + JSON.stringify(m)); } catch (_) { /* ignore */ }
  if (IN_STREAMLIT) {
    if (STREAMLIT_EVENTS.has(m.type)) toStreamlit('streamlit:setComponentValue', { value: m, dataType: 'json' });
  }
  else if (window.parent !== window) window.parent.postMessage({ lab3d: m }, '*');
}
function setFrameHeight() {
  if (IN_STREAMLIT) toStreamlit('streamlit:setFrameHeight', { height: Number(S.args.height) || 640 });
}

// ---------------------------------------------------------------- data
let ASSEMBLY = null;
let LABSTATE = null;

async function getJSON(url, opts) {
  const r = await fetch(url, opts);
  if (!r.ok) {
    let detail = r.statusText;
    try { detail = (await r.json()).detail || detail; } catch (_) { /* not JSON */ }
    throw new Error(`HTTP ${r.status} ${detail}`);
  }
  return r.json();
}

function stateKey(board) {
  return LABSTATE.order.map((k) => `${k}=${board[k]}`).join(',');
}
function plantStatus(board) {
  return LABSTATE.status[stateKey(board)];
}
function loadScenario(id) {
  const sc = LABSTATE.scenarios[id] || LABSTATE.scenarios.healthy;
  S.scenario = LABSTATE.scenarios[id] ? id : 'healthy';
  S.board = { ...sc.initial };
  S.checkResult = null;
}
function gradeLocal(board) {
  const keys = LABSTATE.order;
  const ok = keys.filter((k) => board[k] === LABSTATE.correct[k]).length;
  return { ok: ok === keys.length, score: ok, total: keys.length };
}

// ---------------------------------------------------------------- three.js scene
const canvas = $('#c');
const stage = $('#stage');
let renderer, scene, camera, controls;
const root = new Group();
const partMeshes = {};      // part -> [mesh]
const roleObj = {};         // role -> Object3D
const anchors = {};         // name -> Vector3 (model coordinates, metres)
const hitMeshes = [];
let logger = null;
let dcHandlePivot = null;
const overlayEls = {};

function initRenderer() {
  try {
    renderer = new WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
  } catch (e) {
    S.no3d = true;
    return false;
  }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.outputColorSpace = SRGBColorSpace;
  scene = new Scene();
  scene.background = new Color(0x0b1220);
  camera = new PerspectiveCamera(38, 1, 0.01, 100);
  controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.minDistance = 0.6;
  controls.maxDistance = 8;
  scene.add(new AmbientLight(0xffffff, 0.8));
  const key = new DirectionalLight(0xffffff, 1.4);
  key.position.set(-4, 5, 3);
  scene.add(key);
  const fill = new DirectionalLight(0xbcd7ff, 0.5);
  fill.position.set(3, 2, -4);
  scene.add(fill);
  scene.add(new HemisphereLight(0xe6f0ff, 0x1f2937, 0.45));
  scene.add(root);
  return true;
}

function material(meta, textures) {
  const map = meta.texture ? textures[meta.texture] : null;
  return new MeshStandardMaterial({
    map: map || null,
    color: map ? 0xffffff : new Color(meta.color || '#9aa3af'),
    metalness: 0.15,
    roughness: 0.6,
    side: DoubleSide,
  });
}

function boxOf(obj) { return new Box3().setFromObject(obj); }

async function loadModel() {
  const texLoader = new TextureLoader();
  const texNames = [...new Set(ASSEMBLY.meshes.map((m) => m.texture).filter(Boolean))];
  const textures = {};
  await Promise.all(texNames.map((n) => new Promise((res) => {
    texLoader.load(`models/${n}`, (t) => {
      t.colorSpace = SRGBColorSpace; t.wrapS = t.wrapT = RepeatWrapping; textures[n] = t; res();
    }, undefined, () => res());
  })));

  const loader = new OBJLoader();
  let done = 0;
  await Promise.all(ASSEMBLY.meshes.map(async (meta) => {
    const text = await fetch(`models/${meta.file}`).then((r) => r.text());
    const obj = loader.parse(text);
    obj.traverse((ch) => {
      if (!ch.isMesh) return;
      ch.material = material(meta, textures);
      ch.userData.part = meta.part;
      (partMeshes[meta.part] ||= []).push(ch);
      hitMeshes.push(ch);
    });
    obj.userData.part = meta.part;
    if (meta.role) roleObj[meta.role] = obj;
    roleObj[meta.file] = obj;
    root.add(obj);
    done += 1;
    $('#loadmsg').textContent = `${tr('loading')} ${done}/${ASSEMBLY.meshes.length}`;
  }));

  // Anchors in model coordinates, before the model is centred and scaled.
  const inv = boxOf(roleObj['model_11.obj']);
  const invH = inv.max.y - inv.min.y;
  const zc = (inv.min.z + inv.max.z) / 2;
  anchors.display = new Vector3(inv.min.x - 0.004, inv.min.y + 0.40 * invH, zc + 0.004);
  const neg = boxOf(roleObj.dc_neg_tag); const pos = boxOf(roleObj.dc_pos_tag);
  anchors.dcInputs = neg.getCenter(new Vector3()).lerp(pos.getCenter(new Vector3()), 0.5).add(new Vector3(-0.004, -0.032, 0));
  const acIso = boxOf(roleObj['model_0.obj']);
  anchors.acIso = new Vector3(acIso.min.x - 0.004, acIso.max.y + 0.012, (acIso.min.z + acIso.max.z) / 2);
  const dcIso = boxOf(roleObj['model_4.obj']);
  anchors.dcIso = new Vector3(dcIso.min.x - 0.004, dcIso.max.y + 0.012, (dcIso.min.z + dcIso.max.z) / 2);
  // The kWh reading sits on the meter's display window.
  anchors.meter = boxOf(roleObj.meter_display).getCenter(new Vector3()).add(new Vector3(-0.004, 0, 0));

  // DC isolator handle turns about its own centre (the face points to −x).
  const handle = roleObj.dc_handle;
  const hc = boxOf(handle).getCenter(new Vector3());
  dcHandlePivot = new Group();
  dcHandlePivot.position.copy(hc);
  root.remove(handle);
  handle.position.sub(hc);
  dcHandlePivot.add(handle);
  root.add(dcHandlePivot);

  // Wi-Fi logger stick under the inverter (not in the CAD file).
  const stickMat = new MeshStandardMaterial({ color: 0x1f2937, roughness: 0.5, metalness: 0.2 });
  logger = new Mesh(new BoxGeometry(0.012, 0.048, 0.02), stickMat);
  const led = new Mesh(new BoxGeometry(0.002, 0.004, 0.006), new MeshBasicMaterial({ color: 0x38bdf8 }));
  led.position.set(-0.0065, -0.012, 0);
  logger.add(led);
  logger.userData.part = 'logger';
  logger.userData.led = led;
  const loggerHome = new Vector3(inv.min.x + 0.03, inv.min.y - 0.024, zc + 0.075);
  logger.userData.home = loggerHome;
  logger.position.copy(loggerHome);
  root.add(logger);
  (partMeshes.logger ||= []).push(logger);
  hitMeshes.push(logger);

  // Invisible, larger targets for the small DC input tags so they are tappable.
  for (const role of ['dc_neg_tag', 'dc_pos_tag']) {
    const b = boxOf(roleObj[role]);
    const size = b.getSize(new Vector3());
    const hit = new Mesh(
      new BoxGeometry(size.x + 0.02, size.y + 0.03, size.z + 0.012),
      new MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false }),
    );
    hit.position.copy(b.getCenter(new Vector3()));
    hit.userData.part = 'dc_inputs';
    hit.userData.hitOnly = true;
    root.add(hit);
    hitMeshes.push(hit);
  }

  // Centre and scale the assembly to about 2.4 scene units.
  const all = boxOf(root);
  const size = all.getSize(new Vector3());
  const s = 2.4 / Math.max(size.x, size.y, size.z);
  const c = all.getCenter(new Vector3());
  root.scale.setScalar(s);
  root.position.copy(c).multiplyScalar(-s);
  frame();
}

// Distance that fits the whole assembly (2.4 × 1.4 scene units) in view.
function fitDistance() {
  const t = Math.tan((camera.fov * Math.PI) / 360);
  return 1.15 * Math.max(1.2 / (t * camera.aspect), 0.7 / t);
}
let userMoved = false;
function frame(target = new Vector3(0, 0, 0), dist = fitDistance()) {
  controls.target.copy(target);
  camera.position.copy(target).add(new Vector3(-dist, dist * 0.32, dist * 0.18));
  camera.updateProjectionMatrix();
  controls.update();
}

function toWorld(v) { return root.localToWorld(v.clone()); }

function focusPart(part) {
  const meshes = partMeshes[part];
  if (!meshes || !meshes.length || !controls) return;
  const b = new Box3();
  meshes.forEach((m) => b.expandByObject(m));
  const c = b.getCenter(new Vector3());
  const r = Math.max(b.getSize(new Vector3()).length(), 0.35);
  const dist = Math.min(Math.max(r * 2.2, 0.9), 3.2);
  tween(controls.target.clone(), c, camera.position.clone(), c.clone().add(new Vector3(-dist, dist * 0.3, dist * 0.15)));
}
let tweenState = null;
function tween(t0, t1, p0, p1) { tweenState = { t0, t1, p0, p1, k: 0 }; }

function highlight() {
  for (const [part, meshes] of Object.entries(partMeshes)) {
    const on = part === S.selected;
    for (const m of meshes) {
      if (m.userData.hitOnly || !m.material || !m.material.emissive) continue;
      m.material.emissive.set(on ? 0x0ea5e9 : 0x000000);
      m.material.emissiveIntensity = on ? 0.55 : 0;
    }
  }
}

// ---------------------------------------------------------------- board visuals
let ledPhase = 0;
function applyBoardVisuals() {
  const board = currentBoard() || S.board;
  if (!board || !dcHandlePivot) return;
  dcHandlePivot.rotation.x = board.dc_isolator === 'on' ? 0 : Math.PI / 2;
  if (logger) {
    const home = logger.userData.home;
    const seated = board.logger === 'seated';
    logger.position.set(home.x, home.y - (seated ? 0 : 0.03), home.z + (seated ? 0 : 0.01));
    logger.rotation.set(seated ? 0 : 0.35, 0, 0);
  }
}

function overlay(name, cls, html, anchor) {
  let el = overlayEls[name];
  if (!el) {
    el = document.createElement('div');
    el.className = 'tag3d';
    $('#overlays').appendChild(el);
    overlayEls[name] = el;
  }
  el.className = `tag3d ${cls}`;
  if (el.innerHTML !== html) el.innerHTML = html;
  el.dataset.anchor = anchor;
  el.hidden = false;
}
function hideOverlays() { Object.values(overlayEls).forEach((el) => { el.hidden = true; }); }

function currentBoard() {
  // Fix questions in the test show their own board.
  if (S.mode === 'test') {
    const q = activeQuestion();
    return q && q.kind === 'fix' ? S.test.answers[q.id] : null;
  }
  return S.mode === 'fix' ? S.board : LABSTATE.scenarios.healthy.initial;
}

function updateOverlays() {
  const board = currentBoard();
  const quizId = S.mode === 'test' && activeQuestion() && activeQuestion().kind !== 'fix';
  if (!board || quizId || S.no3d) { hideOverlays(); return; }
  const st = plantStatus(board);
  const cls = !st.inverter_on ? 'lcd off' : (st.code === 'OK' ? 'lcd' : 'lcd err');
  overlay('display', cls, esc(L(st.display)), 'display');
  overlay('meter', 'meter', `${S.meterKwh.toFixed(2)} kWh`, 'meter');
  const rev = board.dc_polarity === 'reversed';
  overlay('dcInputs', `pol${rev ? ' wrong' : ''}`, `DC− ← ${rev ? 'PV+' : 'PV−'} · DC+ ← ${rev ? 'PV−' : 'PV+'}`, 'dcInputs');
  const acOn = board.ac_isolator === 'on';
  overlay('acIso', `pol${acOn ? '' : ' wrong'}`, acOn ? 'I · ON' : '0 · OFF', 'acIso');
  const dcOn = board.dc_isolator === 'on';
  overlay('dcIso', `pol${dcOn ? '' : ' wrong'}`, dcOn ? 'I · ON' : '0 · OFF', 'dcIso');
}

function placeOverlays() {
  const rect = canvas.getBoundingClientRect();
  for (const el of Object.values(overlayEls)) {
    if (el.hidden) continue;
    const a = anchors[el.dataset.anchor];
    if (!a) continue;
    const p = toWorld(a).project(camera);
    const behind = p.z > 1;
    el.style.left = `${((p.x + 1) / 2) * rect.width}px`;
    el.style.top = `${((1 - p.y) / 2) * rect.height}px`;
    el.style.visibility = behind ? 'hidden' : 'visible';
  }
}

// ---------------------------------------------------------------- picking
const ray = new Raycaster();
const ptr = new Vector2();
let down = null;
function onPointerDown(e) {
  down = { x: e.clientX, y: e.clientY, t: performance.now() };
  userMoved = true;
  $('#hint').hidden = true;
}
function onPointerUp(e) {
  if (!down) return;
  const moved = Math.hypot(e.clientX - down.x, e.clientY - down.y);
  const quick = performance.now() - down.t < 600;
  down = null;
  if (moved > 8 || !quick) return;
  const r = canvas.getBoundingClientRect();
  ptr.x = ((e.clientX - r.left) / r.width) * 2 - 1;
  ptr.y = -((e.clientY - r.top) / r.height) * 2 + 1;
  ray.setFromCamera(ptr, camera);
  const hits = ray.intersectObjects(hitMeshes, false);
  if (hits.length) selectPart(hits[0].object.userData.part, 'model');
}

function selectPart(part, via = 'list') {
  S.selected = part;
  highlight();
  if (S.mode === 'test') {
    const q = activeQuestion();
    if (q && q.kind === 'part3d') S.test.answers[q.id] = part;
    render();
    return;
  }
  if (via === 'list') focusPart(part);
  emit({ type: 'select', part });
  render();
}

// ---------------------------------------------------------------- panel UI
function renderTabs() {
  document.querySelectorAll('#tabs button').forEach((b) => {
    b.textContent = tr(b.dataset.mode);
    b.classList.toggle('active', b.dataset.mode === S.mode);
    b.onclick = () => setMode(b.dataset.mode);
  });
  $('#hint').textContent = tr(S.mode === 'explore' ? 'hintExplore' : S.mode === 'fix' ? 'hintFix' : 'hintTest');
}

function setMode(mode) {
  S.mode = mode;
  S.selected = null;
  highlight();
  if (mode === 'test' && !S.test.questions && !S.test.error) loadTest();
  render();
}

function partColor(part) {
  const m = ASSEMBLY.meshes.find((x) => x.part === part && x.color);
  return part === 'logger' ? '#38bdf8' : (m ? m.color : '#f59e0b');
}

function partList() {
  const parts = Object.keys(ASSEMBLY.parts);
  return `<div class="parts">${parts.map((p) => `
    <button data-part="${p}" class="${p === S.selected ? 'active' : ''}">
      <span class="dot" style="background:${partColor(p)}"></span>${esc(L(ASSEMBLY.parts[p].name))}
    </button>`).join('')}</div>`;
}

function partCard(part, withControls) {
  const info = ASSEMBLY.parts[part];
  if (!info) return `<div class="card muted">${tr('pickPart')}</div>`;
  let html = `<div class="card"><h3>${esc(L(info.name))}</h3><div class="muted">${esc(L(info.info))}</div>`;
  if ((ASSEMBLY.added_parts || []).includes(part)) html += `<div class="muted" style="margin-top:6px">${tr('added')}</div>`;
  if (withControls) html += controlsFor(part);
  return html + '</div>';
}

function controlsFor(part) {
  const board = S.mode === 'fix' ? S.board : currentBoard();
  if (!board) return '';
  const ctrls = LABSTATE.order.map((k) => [k, LABSTATE.controls[k]]).filter(([, c]) => c.part === part || (part === 'dc_cables' && c.part === 'dc_inputs'));
  if (!ctrls.length) return `<div class="muted" style="margin-top:8px">${tr('noControl')}</div>`;
  return ctrls.map(([key, c]) => {
    const stateObj = c.states.find((s) => s.id === board[key]) || c.states[0];
    return `<div class="card" style="margin:8px 0 0">
      <div class="muted">${esc(L(c.label))}</div>
      <div><b>${tr('state')}:</b> ${esc(L(stateObj))}</div>
      <button class="btn block" data-toggle="${key}">${esc(toggleLabel(key, board[key]))}</button>
    </div>`;
  }).join('');
}

function toggleLabel(key, value) {
  switch (key) {
    case 'dc_isolator':
    case 'ac_isolator': return tr(value === 'on' ? 'toggleOff' : 'toggleOn');
    case 'dc_polarity': return tr('swapDc');
    case 'ac_ln': return tr('swapLn');
    case 'pe': return tr(value === 'connected' ? 'peUnplug' : 'pePlug');
    case 'logger': return tr(value === 'seated' ? 'loggerOut' : 'loggerIn');
    default: return key;
  }
}

function toggle(key) {
  const board = S.mode === 'fix' ? S.board : currentBoard();
  const states = LABSTATE.controls[key].states.map((s) => s.id);
  board[key] = states[(states.indexOf(board[key]) + 1) % states.length];
  S.checkResult = null;
  applyBoardVisuals();
  emit({ type: 'operate', control: key, value: board[key], scenario: S.scenario });
  render();
}

function statusBox(board) {
  const st = plantStatus(board);
  const yes = (b, a, z) => `<b class="${b ? 'good' : 'bad'}">${b ? a : z}</b>`;
  return `<div class="card"><div class="muted" style="margin-bottom:6px">${tr('plant')}</div>
    <div class="status">
      <div style="grid-column:1/-1">${tr('display')}<b class="${st.code === 'OK' ? 'good' : (st.inverter_on ? 'warn' : 'bad')}">${esc(L(st.display))}</b></div>
      <div>${tr('pac')}<b>${st.pac_kw.toFixed(1)} kW</b></div>
      <div>${tr('vpv')}<b>${st.vpv} V</b></div>
      <div>${tr('vac')}<b>${st.vac} V</b></div>
      <div>${tr('meter')}${yes(st.meter_running, tr('counting'), tr('stopped'))}</div>
      <div style="grid-column:1/-1">${tr('cloud')}${yes(st.cloud_online, tr('online'), tr('offline'))}</div>
    </div></div>`;
}

function renderExplore() {
  return `<p class="muted">${tr('pickPart')}</p>${partCard(S.selected, false)}<div class="muted" style="margin-top:10px">${tr('parts')}</div>${partList()}`;
}

function renderFix() {
  const opts = Object.entries(LABSTATE.scenarios).map(([id, sc]) =>
    `<option value="${id}" ${id === S.scenario ? 'selected' : ''}>${esc(L(sc.title))}</option>`).join('');
  const sc = LABSTATE.scenarios[S.scenario];
  let res = '';
  if (S.checkResult) {
    const r = S.checkResult;
    res = `<div class="card ${r.ok ? 'result-ok' : 'result-bad'}"><b class="${r.ok ? 'good' : 'bad'}">${r.ok ? tr('allOk') : tr('notYet', { n: r.score, t: r.total })}</b></div>`;
  }
  return `<label class="muted">${tr('scenario')}</label><select id="scenario">${opts}</select>
    <p class="muted">${esc(L(sc.story))}</p>
    ${statusBox(S.board)}
    ${S.selected ? partCard(S.selected, true) : `<div class="card muted">${tr('inspect')}</div>`}
    <button class="btn primary block" id="check">${tr('check')}</button>
    <button class="btn block" id="reset">${tr('reset')}</button>
    ${res}
    ${S.no3d ? `<div class="muted" style="margin-top:10px">${tr('parts')}</div>${partList()}` : ''}`;
}

function activeQuestion() {
  const qs = S.test.questions;
  return qs && !S.test.result ? qs[S.test.index] : null;
}

function renderTest() {
  const T = S.test;
  if (T.error) return `<div class="card result-bad">${esc(T.error)}</div><button class="btn block" id="retry">${tr('retry')}</button>`;
  if (!T.questions) return `<div class="card muted">${tr('loadingTest')}</div>`;
  if (T.result) return renderTestResult();
  const q = T.questions[T.index];
  const n = T.questions.length;
  let body = `<div class="muted">${tr('q', { i: T.index + 1, n })}</div>
    <div class="progress"><i style="width:${(100 * T.index) / n}%"></i></div>
    <div class="card"><b>${esc(q.prompt)}</b></div>`;
  if (q.kind === 'choice') {
    body += q.choices.map((c, i) => `<button class="choice ${T.answers[q.id] === i ? 'picked' : ''}" data-choice="${i}">${esc(c)}</button>`).join('');
  } else if (q.kind === 'part3d') {
    body += `<div class="card muted">${T.answers[q.id] ? tr('selected') : tr('tapModel')}</div>`;
    if (S.no3d) body += partList();
  } else if (q.kind === 'fix') {
    if (!T.answers[q.id]) T.answers[q.id] = { ...(q.initial || LABSTATE.scenarios.healthy.initial) };
    body += `<div class="muted">${tr('fixThis')}</div>${statusBox(T.answers[q.id])}`;
    body += S.selected ? partCard(S.selected, true) : `<div class="card muted">${tr('inspect')}</div>`;
  }
  const answered = T.answers[q.id] !== undefined && T.answers[q.id] !== null;
  const last = T.index === n - 1;
  body += `<div class="row" style="margin-top:10px">
    <button class="btn" id="prev" ${T.index === 0 ? 'disabled' : ''}>${tr('prev')}</button>
    <button class="btn primary" id="${last ? 'submit' : 'next'}" ${answered && !T.busy ? '' : 'disabled'}>${T.busy ? tr('grading') : tr(last ? 'submit' : 'next')}</button>
  </div>`;
  return body;
}

function renderTestResult() {
  const r = S.test.result;
  const byId = Object.fromEntries((r.details || []).map((d) => [d.id, d]));
  const items = S.test.questions.map((q, i) => {
    const d = byId[q.id] || {};
    return `<div class="card ${d.correct ? 'result-ok' : 'result-bad'}">
      <div class="muted">${i + 1}. ${esc(q.prompt)}</div>
      <b class="${d.correct ? 'good' : 'bad'}">${d.correct ? tr('correct') : tr('wrong')}</b>
      ${d.explain ? `<div class="muted" style="margin-top:4px">${esc(d.explain)}</div>` : ''}
    </div>`;
  }).join('');
  return `<div class="card ${r.passed ? 'result-ok' : 'result-bad'}">
      <b>${tr('score', { s: r.score, t: r.total, p: Math.round(r.percent) })}</b><br>
      <b class="${r.passed ? 'good' : 'bad'}">${r.passed ? tr('passed') : tr('failed')}</b></div>
    ${items}<button class="btn block" id="retry">${tr('retry')}</button>`;
}

function render() {
  renderTabs();
  const body = $('#body');
  body.innerHTML = S.mode === 'explore' ? renderExplore() : S.mode === 'fix' ? renderFix() : renderTest();
  body.querySelectorAll('[data-part]').forEach((b) => { b.onclick = () => selectPart(b.dataset.part, 'list'); });
  body.querySelectorAll('[data-toggle]').forEach((b) => { b.onclick = () => toggle(b.dataset.toggle); });
  body.querySelectorAll('[data-choice]').forEach((b) => {
    b.onclick = () => { S.test.answers[activeQuestion().id] = Number(b.dataset.choice); render(); };
  });
  const sel = $('#scenario');
  if (sel) sel.onchange = () => { loadScenario(sel.value); S.selected = null; highlight(); applyBoardVisuals(); render(); };
  const on = (id, fn) => { const el = document.getElementById(id); if (el) el.onclick = fn; };
  on('check', () => {
    S.checkResult = gradeLocal(S.board);
    emit({ type: 'check', scenario: S.scenario, state: { ...S.board }, ok: S.checkResult.ok, score: S.checkResult.score, total: S.checkResult.total });
    render();
  });
  on('reset', () => { loadScenario(S.scenario); S.selected = null; highlight(); applyBoardVisuals(); render(); });
  on('prev', () => { S.test.index -= 1; S.selected = null; highlight(); render(); });
  on('next', () => { S.test.index += 1; S.selected = null; highlight(); render(); });
  on('submit', submitTest);
  on('retry', () => { S.test = { ...S.test, index: 0, answers: {}, result: null, error: '', busy: false }; if (!S.test.questions) loadTest(); render(); });
  applyBoardVisuals();
  updateOverlays();
  setFrameHeight();
}

// ---------------------------------------------------------------- test (host or API)
async function loadTest() {
  if (IN_STREAMLIT) return; // questions arrive in the component arguments
  S.test.error = '';
  try {
    const t = await getJSON(`${S.api}/labs/${LAB_ID}/test?lang=${S.lang}`);
    S.test.questions = t.questions;
    S.test.pass = t.pass_percent ?? 70;
  } catch (e) {
    S.test.error = tr('testError', { e: e.message });
  }
  render();
}

async function submitTest() {
  const answers = { ...S.test.answers };
  if (IN_STREAMLIT) {
    S.test.busy = true;
    emit({ type: 'test_submit', answers });
    render();
    return;
  }
  S.test.busy = true;
  render();
  try {
    const r = await getJSON(`${S.api}/labs/${LAB_ID}/test/grade`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ answers, lang: S.lang }),
    });
    S.test.result = r;
    emit({ type: 'test_result', score: r.score, total: r.total, percent: r.percent, passed: r.passed });
  } catch (e) {
    S.test.error = tr('gradeError', { e: e.message });
  }
  S.test.busy = false;
  render();
}

// Streamlit arguments: language, starting mode, the test and its grading.
function onStreamlitRender(args) {
  const prev = S.args;
  S.args = args || {};
  if (S.args.lang && S.args.lang !== S.lang) S.lang = S.args.lang === 'en' ? 'en' : 'kk';
  if (S.args.test && S.args.test.questions && (!prev.test || prev.test.version !== S.args.test.version)) {
    S.test.questions = S.args.test.questions;
    S.test.pass = S.args.test.pass_percent ?? 70;
  }
  if (S.args.test_result && (!prev.test_result || prev.test_result.nonce !== S.args.test_result.nonce)) {
    S.test.result = S.args.test_result;
    S.test.busy = false;
  }
  if (LABSTATE) render();
  else setFrameHeight();
}

// ---------------------------------------------------------------- main loop
function resize() {
  if (!renderer) return;
  const w = stage.clientWidth; const h = stage.clientHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w / Math.max(h, 1);
  camera.updateProjectionMatrix();
  if (!userMoved && root.children.length) frame();
}

let last = performance.now();
function tick(now) {
  requestAnimationFrame(tick);
  const dt = Math.min((now - last) / 1000, 0.1);
  last = now;
  if (tweenState) {
    tweenState.k = Math.min(1, tweenState.k + dt * 2.5);
    const k = 1 - (1 - tweenState.k) ** 3;
    controls.target.lerpVectors(tweenState.t0, tweenState.t1, k);
    camera.position.lerpVectors(tweenState.p0, tweenState.p1, k);
    if (tweenState.k >= 1) tweenState = null;
  }
  const board = currentBoard();
  const st = board ? plantStatus(board) : null;
  // 1000 imp/kWh: at 3.2 kW the LED flashes about 0.9 times a second.
  const led = roleObj.meter_led;
  if (led) {
    let lit = false;
    if (st && st.meter_running) {
      ledPhase += dt * st.pac_kw * 1000 / 3600;
      lit = (ledPhase % 1) < 0.18;
      S.meterKwh += dt * st.pac_kw / 60; // one second of the lab = one minute of the plant
      if (overlayEls.meter && !overlayEls.meter.hidden) overlayEls.meter.textContent = `${S.meterKwh.toFixed(2)} kWh`;
    }
    led.traverse((m) => { if (m.isMesh) { m.material.emissive.set(lit ? 0xff9900 : 0x000000); m.material.emissiveIntensity = lit ? 1.4 : 0; } });
  }
  if (logger) logger.userData.led.material.color.set(st && st.cloud_online ? 0x38bdf8 : 0x334155);
  controls.update();
  renderer.render(scene, camera);
  placeOverlays();
}

async function main() {
  $('#loadmsg').textContent = tr('loading');
  if (IN_STREAMLIT) {
    window.addEventListener('message', (e) => {
      if (e.data && e.data.type === 'streamlit:render') onStreamlitRender(e.data.args);
    });
    toStreamlit('streamlit:componentReady', { apiVersion: 1 });
    setFrameHeight();
  }
  [ASSEMBLY, LABSTATE] = await Promise.all([getJSON('assembly.json'), getJSON('lab_state.json')]);
  loadScenario(S.scenario);
  if (!initRenderer()) {
    $('#loading').hidden = true;
    const g = $('#glerror'); g.hidden = false; g.textContent = tr('webgl');
    render();
    if (S.mode === 'test') loadTest();
    emit({ type: 'ready', webgl: false });
    return;
  }
  new ResizeObserver(resize).observe(stage);
  setTimeout(() => { $('#hint').hidden = true; }, 7000);
  resize();
  await loadModel();
  applyBoardVisuals();
  $('#loading').hidden = true;
  canvas.addEventListener('pointerdown', onPointerDown);
  canvas.addEventListener('pointerup', onPointerUp);
  render();
  if (S.mode === 'test') loadTest();
  requestAnimationFrame(tick);
  emit({ type: 'ready', webgl: true });
}

// Hook for automated UI tests (scripts/android_emulator_smoke.sh, Playwright).
window.__lab3d = { select: (part) => selectPart(part, 'list'), state: S };

main().catch((e) => {
  $('#loading').hidden = true;
  const g = $('#glerror'); g.hidden = false; g.textContent = String(e && e.message ? e.message : e);
  console.error(e);
});
