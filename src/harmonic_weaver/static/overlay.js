// Harmonic Weaver — live overlay.
// Renders the serpentine 4x8 harmonic pad grid over the webcam feed, mirroring
// the static overlay-preview.html but redrawing every requestAnimationFrame.

// --- layout constants ---
const COLS = 4, ROWS = 8, N = 32;
const W = 1280, H = 720;
const gap = 3;
const cellW = (W - gap * (COLS + 1)) / COLS;
const cellH = (H - gap * (ROWS + 1)) / ROWS;

// Serpentine: even cols (0,2) run bottom->top, odd cols (1,3) run top->bottom.
// row 0 = bottom of the grid model.
function padIndex(col, row) {
  if (col % 2 === 0) {
    return col * ROWS + row;                 // even: bottom->top
  } else {
    return col * ROWS + (ROWS - 1 - row);    // odd: top->bottom
  }
}

// Same 32 hues as overlay-preview.html.
const activeColors = [
  '#ff4466', '#ff6644', '#ff8844', '#ffaa44',
  '#ffcc44', '#ffee44', '#ddff44', '#bbff44',
  '#44ff88', '#44ffaa', '#44ffcc', '#44ffee',
  '#44ddff', '#44bbff', '#4499ff', '#4477ff',
  '#6644ff', '#8844ff', '#aa44ff', '#cc44ff',
  '#ee44ff', '#ff44dd', '#ff44bb', '#ff4499',
  '#ff6644', '#ff8844', '#ffaa44', '#ffcc44',
  '#ddff44', '#bbff44', '#44ff88', '#44ffaa',
];

// --- DOM ---
const cam = document.getElementById('cam');
const bg = document.getElementById('bg');
const grid = document.getElementById('grid');
const statusEl = document.getElementById('status');
const statusText = document.getElementById('statusText');

bg.width = W; bg.height = H;
grid.width = W; grid.height = H;
const bgctx = bg.getContext('2d');
const gctx = grid.getContext('2d');

// ---------------------------------------------------------------------------
// Activation state
// ---------------------------------------------------------------------------
// `activePads` is the Set the renderer reads. It is the union of three sources,
// each tracked separately so one source removing a pad never clobbers a pad
// another source still wants.
const activePads = new Set();
const wsPads = new Set();       // driven by the websocket
const randomPads = new Set();   // placeholder simulation
let hoverIdx = null;            // mouse hover (single pad)

function recomputeActive() {
  activePads.clear();
  for (const i of wsPads) activePads.add(i);
  for (const i of randomPads) activePads.add(i);
  if (hoverIdx != null) activePads.add(hoverIdx);
}

// ---------------------------------------------------------------------------
// Status pill
// ---------------------------------------------------------------------------
let cameraState = 'waiting';   // waiting | live | denied
let wsState = 'connecting';    // connecting | live | offline

function updateStatus() {
  const both = cameraState === 'live' && wsState === 'live';
  statusEl.classList.toggle('live', both);
  statusText.textContent = `cam ${cameraState} · ws ${wsState}`;
}

// ---------------------------------------------------------------------------
// Background feed
// ---------------------------------------------------------------------------
// Simulated feed used when the webcam is unavailable — same radial gradient and
// grid texture as overlay-preview.html. Drawn once; the frame loop "holds" it.
function drawFallback() {
  const bgGrad = bgctx.createRadialGradient(W / 2, H / 2, 100, W / 2, H / 2, 800);
  bgGrad.addColorStop(0, '#1a1a2e');
  bgGrad.addColorStop(0.4, '#16213e');
  bgGrad.addColorStop(1, '#0a0a15');
  bgctx.fillStyle = bgGrad;
  bgctx.fillRect(0, 0, W, H);

  bgctx.strokeStyle = 'rgba(255,255,255,0.02)';
  bgctx.lineWidth = 0.5;
  for (let x = 0; x < W; x += 40) { bgctx.beginPath(); bgctx.moveTo(x, 0); bgctx.lineTo(x, H); bgctx.stroke(); }
  for (let y = 0; y < H; y += 40) { bgctx.beginPath(); bgctx.moveTo(0, y); bgctx.lineTo(W, y); bgctx.stroke(); }
}

async function initCamera() {
  drawFallback();  // always show something immediately
  updateStatus();
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    cameraState = 'denied';
    updateStatus();
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 } });
    cam.srcObject = stream;
    cam.addEventListener('loadeddata', () => { cameraState = 'live'; updateStatus(); }, { once: true });
    try { await cam.play(); } catch (_e) { /* autoplay policy — muted+playsinline usually covers it */ }
  } catch (_err) {
    cameraState = 'denied';  // permission denied / no device — fallback already on screen
    updateStatus();
  }
}

// ---------------------------------------------------------------------------
// Grid overlay (mirrors overlay-preview.html, redrawn every frame)
// ---------------------------------------------------------------------------
function drawGrid() {
  gctx.clearRect(0, 0, W, H);

  for (let col = 0; col < COLS; col++) {
    for (let row = 0; row < ROWS; row++) {
      const idx = padIndex(col, row);
      const harmonic = idx + 1;
      const x = gap + col * (cellW + gap);
      const canvasRow = ROWS - 1 - row;  // row 0 = bottom in model, canvas y=0 is top
      const y = gap + canvasRow * (cellH + gap);

      const isActive = activePads.has(idx);

      // Pad fill colour: use the first owning slot's skeleton colour when
      // active, falling back to the fixed per-pad hue when inactive.
      let fillColor;
      if (isActive && padOwners[idx].size > 0) {
        const firstOwner = padOwners[idx].values().next().value;
        const slot = firstOwner >> 1;
        fillColor = SLOT_PALETTE[slot % MAX_SLOTS] + '55';
      } else if (isActive) {
        fillColor = activeColors[idx] + '55';
      } else {
        fillColor = 'rgba(10,15,25,0.4)';
      }
      gctx.fillStyle = fillColor;
      gctx.fillRect(x, y, cellW, cellH);

      // border — use the owning slot's skeleton colour when active
      let borderColor;
      if (isActive && padOwners[idx].size > 0) {
        const firstOwner = padOwners[idx].values().next().value;
        const slot = firstOwner >> 1;
        borderColor = SLOT_PALETTE[slot % MAX_SLOTS] + 'cc';
      } else if (isActive) {
        borderColor = activeColors[idx] + 'cc';
      } else {
        borderColor = 'rgba(100,140,200,0.35)';
      }
      gctx.strokeStyle = borderColor;
      gctx.lineWidth = isActive ? 2.5 : 1.5;
      gctx.strokeRect(x, y, cellW, cellH);

      // harmonic number
      const fontSize = Math.min(cellW, cellH) * 0.38;
      gctx.font = `700 ${fontSize}px ui-monospace, SFMono, monospace`;
      gctx.textAlign = 'center';
      gctx.textBaseline = 'middle';
      gctx.fillStyle = isActive ? '#fff' : 'rgba(180,200,230,0.7)';
      gctx.fillText(`H${harmonic}`, x + cellW / 2, y + cellH / 2);
    }
  }

  // --- serpentine path arrows ---
  gctx.strokeStyle = 'rgba(255,255,255,0.15)';
  gctx.lineWidth = 2;
  gctx.setLineDash([8, 12]);

  for (let col = 0; col < COLS; col++) {
    const cx = gap + col * (cellW + gap) + cellW / 2;
    const y0 = gap + cellH / 2;
    const y1 = H - gap - cellH / 2;

    gctx.beginPath();
    gctx.moveTo(cx, col % 2 === 0 ? y1 : y0);  // start bottom for even, top for odd
    gctx.lineTo(cx, col % 2 === 0 ? y0 : y1);  // end top for even, bottom for odd
    gctx.stroke();

    if (col < COLS - 1) {
      const nx = gap + (col + 1) * (cellW + gap) + cellW / 2;
      const connectY = col % 2 === 0 ? y0 : y1;
      gctx.beginPath();
      gctx.moveTo(cx, connectY);
      gctx.lineTo(nx, connectY);
      gctx.stroke();
    }
  }

  // --- column labels ---
  gctx.setLineDash([]);
  gctx.fillStyle = 'rgba(200,220,255,0.5)';
  gctx.font = '600 14px ui-monospace, SFMono, monospace';
  gctx.textAlign = 'center';
  for (let col = 0; col < COLS; col++) {
    const cx = gap + col * (cellW + gap) + cellW / 2;
    const dir = col % 2 === 0 ? '↑' : '↓';
    gctx.fillText(`col ${col + 1} ${dir}`, cx, H - 8);
  }
}

// ---------------------------------------------------------------------------
// Hand position dots — HarMoCAP detected wrist positions
// ---------------------------------------------------------------------------
function drawHandDot(color) {
  // Draw a single dot at (px, py) in the given colour.
  // (Called inline from drawHandDots below.)
  return function(px, py) {
    const r = 14;
    gctx.beginPath();
    gctx.arc(px, py, r, 0, Math.PI * 2);
    gctx.fillStyle = color + '66';
    gctx.fill();
    gctx.strokeStyle = color;
    gctx.lineWidth = 2.5;
    gctx.stroke();
    gctx.beginPath();
    gctx.moveTo(px - r - 4, py); gctx.lineTo(px + r + 4, py);
    gctx.moveTo(px, py - r - 4); gctx.lineTo(px, py + r + 4);
    gctx.strokeStyle = '#fff';
    gctx.lineWidth = 1;
    gctx.stroke();
  };
}

function drawHandDots() {
  for (let s = 0; s < MAX_SLOTS; s++) {
    const color = SLOT_PALETTE[s % MAX_SLOTS];
    const draw = drawHandDot(color);
    for (const hand of ['r', 'l']) {
      const x = handPos[s][hand].x, y = handPos[s][hand].y;
      if (x == null || y == null) continue;
      const px = (1 - x) * W, py = y * H;
      draw(px, py);
    }
  }
}

// ---------------------------------------------------------------------------
// Frame loop
// ---------------------------------------------------------------------------
function frame() {
  if (cameraState === 'live' && cam.readyState >= 2) {
    // Mirror the camera feed horizontally (dancer's perspective)
    bgctx.save();
    bgctx.translate(W, 0);
    bgctx.scale(-1, 1);
    try { bgctx.drawImage(cam, 0, 0, W, H); } catch (_e) { /* frame not ready */ }
    bgctx.restore();
  }
  // else: bg holds the fallback drawn once at startup
  drawGrid();
  drawHandDots();
  requestAnimationFrame(frame);
}

// ---------------------------------------------------------------------------
// Mouse hover -> pad
// ---------------------------------------------------------------------------
function padAt(px, py) {
  for (let col = 0; col < COLS; col++) {
    const x = gap + col * (cellW + gap);
    if (px < x || px > x + cellW) continue;
    for (let row = 0; row < ROWS; row++) {
      const canvasRow = ROWS - 1 - row;
      const y = gap + canvasRow * (cellH + gap);
      if (py >= y && py <= y + cellH) return padIndex(col, row);
    }
  }
  return null;  // in a gap / outside a cell
}

function setHover(idx) {
  if (idx === hoverIdx) return;
  hoverIdx = idx;
  recomputeActive();
}

grid.addEventListener('mousemove', (e) => {
  const r = grid.getBoundingClientRect();
  if (!r.width || !r.height) return;
  const px = (e.clientX - r.left) / r.width * W;
  const py = (e.clientY - r.top) / r.height * H;
  setHover(padAt(px, py));
});
grid.addEventListener('mouseleave', () => setHover(null));

// ---------------------------------------------------------------------------
// WebSocket — Stage Contract protocol.
// Handshake: server.hello → client.hello → server.hello(ready) →
// state.subscribe(sources) → state.snapshot + state.event stream.
// Pad highlights come from derived sources hand_r_pad.pad / hand_l_pad.pad.
// ---------------------------------------------------------------------------
const PROTOCOL_VERSION = '0.1-draft';
const STAGE_CONTRACT_ID = 'cc2f83205e0dccf6d0b5d488883d73ad';
const PAD_SOURCE_CHANNELS = {
  hand_r_pad: 'pad',
  hand_l_pad: 'pad',
};
const POS_SOURCE_CHANNELS = {
  hand_r_x: 'x',
  hand_r_y: 'y',
  hand_l_x: 'x',
  hand_l_y: 'y',
};

let ws = null;
let reconnectTimer = null;
let lastPadMsgAt = 0;  // when we last got real pad data (gates the simulation)
let requestSeq = 0;
let stageGated = false;
// Per-slot color palette — matches HarMoCAP skeleton colours (BGR→CSS hex).
const SLOT_PALETTE = [
  '#4285f4', '#34a853', '#fbbc05', '#ea4335',
  '#ab47bc', '#00acc1', '#ff7043', '#9e9d24',
];
const MAX_SLOTS = 8;

// --- Active-pad tracking per slot+hand ---
// Each pad (0..31) tracks a Set of (slot << 1 | handBit) owners.
// handBit: 0 = right, 1 = left.  The Set tells us WHICH slot-hand combos
// are overlapping this pad.
const padOwners = new Array(N).fill(null).map(() => new Set());

// Raw hand positions for dot rendering: handPos[slot][hand][axis].
const handPos = {};
for (let s = 0; s < MAX_SLOTS; s++) {
  handPos[s] = {r: {x: null, y: null}, l: {x: null, y: null}};
}

// Latest pad index per slot+hand, or null if invalid/unknown.
const handPads = {};
for (let s = 0; s < MAX_SLOTS; s++) {
  handPads[`${s}_r`] = null;
  handPads[`${s}_l`] = null;
}

function clientId() {
  try {
    const key = 'harmonic-weaver-overlay-client-id';
    let value = localStorage.getItem(key);
    if (!value) {
      value = `overlay-${crypto.randomUUID()}`;
      localStorage.setItem(key, value);
    }
    return value;
  } catch (_e) {
    return `overlay-${Math.random().toString(16).slice(2)}`;
  }
}

function nextRequestId(prefix) {
  requestSeq += 1;
  return `${prefix}-${requestSeq}`;
}

function sendClient(type, payload) {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  ws.send(JSON.stringify({
    type,
    protocol_version: PROTOCOL_VERSION,
    request_id: nextRequestId(type.replace('.', '-')),
    payload,
  }));
}

function padIndexFromEnvelope(envelope) {
  if (!envelope || typeof envelope !== 'object') return null;
  if (envelope.state && envelope.state !== 'observed' && envelope.state !== 'held') return null;
  const n = Number(envelope.value);
  if (!Number.isFinite(n)) return null;
  const idx = Math.round(n);
  if (!Number.isInteger(idx) || idx < 0 || idx >= N) return null;
  return idx;
}

function recomputeWsPadsFromHands() {
  // Clear all owner sets, then rebuild from current handPads state.
  for (let i = 0; i < N; i++) padOwners[i].clear();
  for (const [key, padIdx] of Object.entries(handPads)) {
    if (padIdx == null) continue;
    const [slot, hand] = key.split('_');
    const s = Number(slot), h = (hand === 'r' ? 0 : 1);
    padOwners[padIdx].add(s << 1 | h);
  }
  // Rebuild activePads (union of all pads with at least one owner).
  wsPads.clear();
  for (let i = 0; i < N; i++) {
    if (padOwners[i].size > 0) wsPads.add(i);
  }
  if (wsPads.size) {
    lastPadMsgAt = Date.now();
    randomPads.clear();
  }
  recomputeActive();
}

// Parse a derived source_id like "slot_0_pad_r" → {slot, kind, hand}.
// pad source:  slot_N_pad_{r,l}
// pos source:   slot_N_pos_{r,l}_{x,y}
// Returns null if the pattern doesn't match.
function applyPadChannel(sourceId, channel, envelope) {
  const parsed = parseSlotSource(sourceId);
  // Position data: update handPos[slot][hand][axis].
  if (parsed && parsed.kind === 'pos') {
    const { slot, hand, axis } = parsed;
    if (envelope && typeof envelope.value === 'number') {
      handPos[slot][hand][axis] = envelope.value;
    }
    return;
  }
  // Pad data: update handPads[slot_hand] and rebuild owners.
  if (parsed && parsed.kind === 'pad') {
    const key = `${parsed.slot}_${parsed.hand}`;
    handPads[key] = padIndexFromEnvelope(envelope);
    recomputeWsPadsFromHands();
    return;
  }
}

// Parse a derived source_id like "slot_0_pad_r" → {slot, kind, hand}.
function parseSlotSource(sourceId) {
  const m = sourceId.match(/^slot_(\d+)_(pad|pos)_(r|l)(?:_([xy]))?$/);
  if (!m) return null;
  return { slot: Number(m[1]), kind: m[2], hand: m[3], axis: m[4] || null };
}

function applySourcesSnapshot(sources) {
  if (!Array.isArray(sources)) return;
  let touched = false;
  for (const source of sources) {
    if (!source || typeof source !== 'object') continue;
    const sourceId = source.source_id;
    const parsed = parseSlotSource(sourceId);
    if (!parsed) continue;
    // Position sources
    if (parsed.kind === 'pos') {
      const ch = parsed.axis || parsed.hand;
      const env = source.channels?.[ch];
      if (env && typeof env.value === 'number') {
        handPos[parsed.slot][parsed.hand][parsed.axis || parsed.hand] = env.value;
      }
    }
    // Pad sources
    if (parsed.kind === 'pad') {
      const ch = 'pad';
      const envelope = source.channels?.[ch];
      const key = `${parsed.slot}_${parsed.hand}`;
      handPads[key] = padIndexFromEnvelope(envelope);
      touched = true;
    }
  }
  if (touched) recomputeWsPadsFromHands();
}

function applySourceChannelsUpdated(payload) {
  if (!payload || typeof payload !== 'object') return;
  const entity = payload.entity || payload;
  const sourceId = entity.source_id || payload.entity_id;
  const channels = entity.channels;
  if (!channels || typeof channels !== 'object') return;
  const parsed = parseSlotSource(sourceId);
  if (!parsed) return;
  // Position sources
  if (parsed.kind === 'pos') {
    const ch = parsed.axis;
    if (ch && ch in channels) {
      const env = channels[ch];
      if (env && typeof env.value === 'number') {
        handPos[parsed.slot][parsed.hand][parsed.axis] = env.value;
      }
    }
    return;
  }
  // Pad sources
  if (parsed.kind === 'pad') {
    const ch = 'pad';
    if (!(ch in channels)) return;
    applyPadChannel(sourceId, ch, channels[ch]);
  }
}

// Legacy defensive parsers (route_state / pad_activation) kept as no-ops if a
// future feed still uses them — they merge into wsPads without clobbering hands.
function toPadList(value) {
  const out = [];
  if (Array.isArray(value)) {
    if (value.length && typeof value[0] === 'boolean') {
      value.forEach((on, i) => { if (on) out.push(i); });
    } else {
      for (const v of value) {
        const n = Number(v);
        if (Number.isInteger(n) && n >= 0 && n < N) out.push(n);
      }
    }
  } else if (value && typeof value === 'object') {
    for (const [k, on] of Object.entries(value)) {
      const n = Number(k);
      if (on && Number.isInteger(n) && n >= 0 && n < N) out.push(n);
    }
  }
  return out;
}

function applyRouteState(payload) {
  if (!payload || typeof payload !== 'object') return;
  const list = toPadList(payload.active_pads ?? payload.pads ?? payload.active ?? payload.routes);
  if (!list.length) return;
  wsPads.clear();
  for (const i of list) wsPads.add(i);
  lastPadMsgAt = Date.now();
  randomPads.clear();
  recomputeActive();
}

function applyPadActivation(payload) {
  if (!payload || typeof payload !== 'object') return;
  const raw = payload.index ?? payload.pad ?? payload.idx ?? payload.harmonic;
  const n = Number(raw);
  if (!Number.isInteger(n) || n < 0 || n >= N) return;
  const on = payload.active ?? payload.on ?? payload.state ?? payload.value ?? true;
  if (on) wsPads.add(n); else wsPads.delete(n);
  lastPadMsgAt = Date.now();
  randomPads.clear();
  recomputeActive();
}

function handleWSMessage(data) {
  let msg;
  try { msg = JSON.parse(data); } catch (_e) { return; }
  if (!msg || typeof msg !== 'object') return;
  const type = msg.type || '';
  const payload = (msg.payload && typeof msg.payload === 'object') ? msg.payload : {};

  if (type === 'server.hello') {
    if (payload.gate_state === 'awaiting_client') {
      sendClient('client.hello', {
        client_id: clientId(),
        expected_contract_id: STAGE_CONTRACT_ID,
        supported_protocol_versions: [PROTOCOL_VERSION],
      });
    } else if (payload.gate_state === 'ready') {
      stageGated = true;
      wsState = 'live';
      updateStatus();
      sendClient('state.subscribe', { topics: ['sources'] });
    } else if (payload.gate_state === 'incompatible') {
      wsState = 'offline';
      updateStatus();
    }
    return;
  }

  if (type === 'state.snapshot') {
    applySourcesSnapshot(payload.sources);
    return;
  }

  if (type === 'state.event') {
    if (payload.topic === 'sources' && payload.action === 'source.channels_updated') {
      applySourceChannelsUpdated(payload);
    }
    return;
  }

  if (type === 'registry.source' && payload.action === 'derived_ready') {
    // Derived sources just appeared — re-subscribe for a fresh snapshot.
    if (stageGated) sendClient('state.subscribe', { topics: ['sources'] });
    return;
  }

  // Back-compat: ignore silently if never emitted.
  if (type === 'route_state') applyRouteState(payload);
  else if (type === 'pad_activation') applyPadActivation(payload);
}

function connectWS() {
  clearTimeout(reconnectTimer);
  stageGated = false;
  requestSeq = 0;
  handPads.hand_r_pad = null;
  handPads.hand_l_pad = null;
  for (const k of Object.keys(handPos)) handPos[k] = null;
  wsState = 'connecting';
  updateStatus();
  let socket;
  try {
    const scheme = location.protocol === 'https:' ? 'wss:' : 'ws:';
    socket = new WebSocket(`${scheme}//${location.host}/ws`);
  } catch (_e) {
    wsState = 'offline';
    updateStatus();
    reconnectTimer = setTimeout(connectWS, 3000);
    return;
  }
  ws = socket;
  socket.addEventListener('message', (ev) => handleWSMessage(ev.data));
  socket.addEventListener('close', () => {
    stageGated = false;
    wsState = 'offline';
    updateStatus();
    reconnectTimer = setTimeout(connectWS, 3000);
  });
  socket.addEventListener('error', () => { /* close handler drives reconnect */ });
}

// ---------------------------------------------------------------------------
// Placeholder simulation — keeps the grid alive until the WS feed exists.
// Every 6s toggle 2-3 pads, but stand down while real pad data is arriving.
// ---------------------------------------------------------------------------
function startSimulation() {
  setInterval(() => {
    if (Date.now() - lastPadMsgAt < 12000) return;  // real feed is driving; stay quiet
    const count = 2 + Math.floor(Math.random() * 2);  // 2 or 3
    for (let k = 0; k < count; k++) {
      const idx = Math.floor(Math.random() * N);
      if (randomPads.has(idx)) randomPads.delete(idx); else randomPads.add(idx);
    }
    recomputeActive();
  }, 6000);
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------
updateStatus();
initCamera();
connectWS();
startSimulation();
requestAnimationFrame(frame);
