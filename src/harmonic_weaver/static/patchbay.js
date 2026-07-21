(() => {
  "use strict";

  const PROTOCOL_VERSION = "0.1-draft";
  const CONTRACT_ID = "cc2f83205e0dccf6d0b5d488883d73ad";
  const TOPICS = ["stage", "routes", "scenes", "sources", "instruments", "metrics"];
  const MAX_BACKOFF_MS = 10000;

  const $ = (selector) => document.querySelector(selector);
  const elements = {
    connection: $("#connection-status"),
    revision: $("#revision-status"),
    sceneSelect: $("#scene-select"),
    sceneSwitch: $("#scene-switch"),
    activeScene: $("#active-scene"),
    recoveryScene: $("#recovery-scene"),
    panicButton: $("#panic-button"),
    panicLabel: $("#panic-label"),
    panicBanner: $("#panic-banner"),
    panicDetail: $("#panic-detail"),
    panicClear: $("#panic-clear"),
    sourceCount: $("#source-count"),
    sourcesList: $("#sources-list"),
    routeCount: $("#route-count"),
    routesList: $("#routes-list"),
    instrumentCount: $("#instrument-count"),
    instrumentsList: $("#instruments-list"),
    patchIntent: $("#patch-intent"),
    patchIntentText: $("#patch-intent-text"),
    clearSelection: $("#clear-selection"),
    toasts: $("#toast-region"),
    dialog: $("#transform-dialog"),
    transformTitle: $("#transform-title"),
    transformList: $("#transform-list"),
    transformType: $("#transform-type"),
    transformAdd: $("#transform-add"),
    transformSave: $("#transform-save"),
  };

  const model = {
    connected: false,
    mutationBusy: false,
    stageRevision: 0,
    projection: {
      stage: {active_scene_id: null, activation_generation: 0, panic: {active: false, panic_generation: 0}},
      scenes: [],
      routes: [],
      sources: [],
      instruments: [],
      metrics: {},
    },
  };
  const view = {
    selectedChannel: null,
    selectedSceneId: null,
    deleteArmed: null,
    editingRoute: null,
    editorTransforms: [],
  };

  let socket = null;
  let reconnectTimer = null;
  let reconnectAttempt = 0;
  let requestSequence = 0;
  let socketNonce = "boot";
  let refreshTimer = null;
  const pending = new Map();

  const clone = (value) => JSON.parse(JSON.stringify(value));
  const escapeHtml = (value) => String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
  const fmt = (value) => Number.isFinite(Number(value)) ? Number(value).toLocaleString(undefined, {maximumFractionDigits: 4}) : "—";
  const rangeText = (range) => Array.isArray(range) && range.length === 2 ? `${fmt(range[0])}…${fmt(range[1])}` : "range —";
  const bindingText = (bindings) => Object.entries(bindings || {}).map(([key, value]) => `${key}=${value}`).join(", ");

  function clientId() {
    const key = "harmonic-weaver-patchbay-client-id";
    try {
      let value = localStorage.getItem(key);
      if (!value) {
        value = `patchbay-${crypto.randomUUID()}`;
        localStorage.setItem(key, value);
      }
      return value;
    } catch (_error) {
      return `patchbay-${Math.random().toString(16).slice(2)}`;
    }
  }

  function requestId(prefix) {
    requestSequence += 1;
    return `${prefix}-${socketNonce}-${requestSequence}`;
  }

  function setConnection(kind, text) {
    elements.connection.className = `connection status-${kind}`;
    elements.connection.textContent = text;
  }

  function connect() {
    clearTimeout(reconnectTimer);
    setConnection("connecting", reconnectAttempt ? "Reconnecting" : "Connecting");
    socketNonce = Math.random().toString(36).slice(2, 8);
    requestSequence = 0;
    const scheme = location.protocol === "https:" ? "wss:" : "ws:";
    socket = new WebSocket(`${scheme}//${location.host}/ws`);

    socket.addEventListener("message", (event) => {
      let message;
      try {
        message = JSON.parse(event.data);
      } catch (_error) {
        toast("The stage sent an unreadable message.", "error");
        return;
      }
      handleMessage(message);
    });

    socket.addEventListener("close", () => {
      model.connected = false;
      model.mutationBusy = false;
      setConnection("offline", "Offline");
      for (const item of pending.values()) item.reject(new Error("Stage connection closed"));
      pending.clear();
      render();
      const base = Math.min(MAX_BACKOFF_MS, 400 * (2 ** reconnectAttempt));
      const delay = Math.round(base * (.85 + Math.random() * .3));
      reconnectAttempt += 1;
      reconnectTimer = setTimeout(connect, delay);
    });

    socket.addEventListener("error", () => setConnection("offline", "Connection error"));
  }

  function send(messageType, payload, {track = false} = {}) {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      return Promise.reject(new Error("Stage is offline"));
    }
    const id = requestId(messageType.replace(".", "-"));
    socket.send(JSON.stringify({
      type: messageType,
      protocol_version: PROTOCOL_VERSION,
      request_id: id,
      payload,
    }));
    if (!track) return Promise.resolve(id);
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        pending.delete(id);
        model.mutationBusy = pending.size > 0;
        render();
        reject(new Error(`${messageType} timed out`));
      }, 8000);
      pending.set(id, {resolve, reject, timeout, messageType});
    });
  }

  function runCommand(messageType, payload, successText) {
    if (model.mutationBusy && messageType !== "panic.trigger") {
      toast("Wait for the current stage change to settle.");
      return Promise.reject(new Error("mutation already in flight"));
    }
    model.mutationBusy = true;
    render();
    return send(messageType, payload, {track: true})
      .then((message) => {
        if (successText) toast(successText, "success");
        scheduleRefresh(0);
        return message;
      })
      .catch((error) => {
        model.mutationBusy = false;
        render();
        if (error.message !== "mutation already in flight") toast(error.message, "error");
        throw error;
      });
  }

  function subscribe() {
    if (!model.connected) return;
    send("state.subscribe", {topics: TOPICS}).catch(() => {});
  }

  function scheduleRefresh(delay = 35) {
    clearTimeout(refreshTimer);
    refreshTimer = setTimeout(subscribe, delay);
  }

  function handleMessage(message) {
    if (message.protocol_version !== PROTOCOL_VERSION) {
      toast(`Unsupported stage protocol ${message.protocol_version || "unknown"}.`, "error");
      return;
    }
    if (message.type === "server.hello") {
      if (message.payload.gate_state === "awaiting_client") {
        if (message.payload.contract_id !== CONTRACT_ID) {
          toast("Stage contract mismatch. Patching is disabled.", "error");
          return;
        }
        send("client.hello", {
          client_id: clientId(),
          expected_contract_id: CONTRACT_ID,
          supported_protocol_versions: [PROTOCOL_VERSION],
        }).catch(() => {});
      } else if (message.payload.gate_state === "ready") {
        model.connected = true;
        reconnectAttempt = 0;
        setConnection("online", "Live");
        subscribe();
        render();
      } else if (message.payload.gate_state === "incompatible") {
        model.connected = false;
        setConnection("offline", "Incompatible");
        toast(message.payload.reason || "Stage contract mismatch.", "error");
        render();
      }
      return;
    }

    if (Number.isInteger(message.stage_revision)) {
      model.stageRevision = message.stage_revision;
      elements.revision.textContent = `Stage ${message.stage_revision}`;
    }

    if (message.type === "state.snapshot") {
      model.projection = message.payload;
      model.mutationBusy = pending.size > 0;
      reconcileSelection();
      render();
      return;
    }

    if (message.type === "command.ack" || message.type === "command.error") {
      const item = pending.get(message.request_id);
      if (item) {
        clearTimeout(item.timeout);
        pending.delete(message.request_id);
        if (message.type === "command.ack") {
          item.resolve(message);
        } else {
          const details = message.payload.details ? ` (${JSON.stringify(message.payload.details)})` : "";
          const error = new Error(`${message.payload.message}${details}`);
          error.code = message.payload.code;
          item.reject(error);
        }
        model.mutationBusy = pending.size > 0;
      }
      if (message.type === "command.error" && message.payload.current_stage_revision !== undefined) {
        model.stageRevision = message.payload.current_stage_revision;
      }
      scheduleRefresh(0);
      return;
    }

    if (message.type === "panic.event") {
      const panic = model.projection.stage?.panic || {};
      if (message.payload.phase === "latched") {
        panic.active = true;
        panic.panic_generation = message.payload.panic_generation;
        panic.reason = message.payload.reason || null;
      } else if (message.payload.phase === "recovered") {
        panic.active = false;
      }
      if (model.projection.stage) model.projection.stage.panic = panic;
      renderPanic();
      scheduleRefresh();
      return;
    }

    if (["state.event", "registry.source", "registry.instrument"].includes(message.type)) {
      scheduleRefresh();
    }
  }

  function reconcileSelection() {
    const scenes = model.projection.scenes || [];
    const ids = new Set(scenes.map((scene) => scene.scene_id));
    if (!ids.has(view.selectedSceneId)) {
      view.selectedSceneId = ids.has(model.projection.stage?.active_scene_id)
        ? model.projection.stage.active_scene_id
        : scenes[0]?.scene_id || null;
    }
    if (view.selectedChannel && !findChannel(view.selectedChannel)) view.selectedChannel = null;
  }

  function currentScene() {
    return (model.projection.scenes || []).find((scene) => scene.scene_id === model.projection.stage?.active_scene_id) || null;
  }

  function selectedScene() {
    return (model.projection.scenes || []).find((scene) => scene.scene_id === view.selectedSceneId) || null;
  }

  function findChannel(address) {
    for (const source of model.projection.sources || []) {
      const name = address.startsWith(`${source.source_id}.`) ? address.slice(source.source_id.length + 1) : null;
      if (name === null) continue;
      const spec = (source.channel_specs || []).find((item) => item.name === name);
      if (spec || Object.hasOwn(source.channels || {}, name)) return {source, name, spec: spec || {name}};
    }
    return null;
  }

  function findCapability(instrumentId, capabilityName) {
    const instrument = (model.projection.instruments || []).find((item) => item.instrument_id === instrumentId);
    const capability = (instrument?.capabilities || []).find((item) => item.name === capabilityName);
    return instrument && capability ? {instrument, capability} : null;
  }

  function render() {
    elements.revision.textContent = model.connected ? `Stage ${model.stageRevision}` : "Stage —";
    renderScenes();
    renderPanic();
    renderSources();
    renderRoutes();
    renderInstruments();
    renderIntent();
  }

  function renderScenes() {
    const scenes = model.projection.scenes || [];
    const activeId = model.projection.stage?.active_scene_id;
    const options = scenes.length
      ? scenes.map((scene) => `<option value="${escapeHtml(scene.scene_id)}">${escapeHtml(scene.name)} · v${scene.scene_version}</option>`).join("")
      : '<option value="">No scenes installed</option>';
    elements.sceneSelect.innerHTML = options;
    elements.recoveryScene.innerHTML = options;
    elements.sceneSelect.value = view.selectedSceneId || "";
    elements.recoveryScene.value = view.selectedSceneId || activeId || "";
    const active = scenes.find((scene) => scene.scene_id === activeId);
    elements.activeScene.textContent = active ? `Live: ${active.name}` : "No active scene";
    elements.sceneSwitch.disabled = !model.connected || model.mutationBusy || !selectedScene() || activeId === view.selectedSceneId || model.projection.stage?.panic?.active;
  }

  function renderPanic() {
    const panic = model.projection.stage?.panic || {active: false, panic_generation: 0};
    document.body.classList.toggle("panic-active", Boolean(panic.active));
    elements.panicBanner.hidden = !panic.active;
    elements.panicButton.setAttribute("aria-pressed", String(Boolean(panic.active)));
    elements.panicButton.disabled = !model.connected || model.mutationBusy || panic.active;
    elements.panicLabel.textContent = panic.active ? "PANIC LATCHED" : "PANIC";
    elements.panicDetail.textContent = panic.active
      ? `Generation ${panic.panic_generation}. All instrument output is held safe${panic.reason ? ` — ${panic.reason}` : "."}`
      : "All instrument output is held safe.";
    const recovery = (model.projection.scenes || []).find((scene) => scene.scene_id === elements.recoveryScene.value)
      || selectedScene()
      || currentScene();
    elements.panicClear.disabled = !model.connected || model.mutationBusy || !panic.active || !recovery;
  }

  function renderSources() {
    const sources = model.projection.sources || [];
    elements.sourceCount.textContent = String(sources.length);
    if (!sources.length) {
      elements.sourcesList.replaceChildren(emptyState("No source manifests are installed yet."));
      return;
    }
    elements.sourcesList.innerHTML = sources.map((source) => {
      const specs = source.channel_specs?.length
        ? source.channel_specs
        : Object.keys(source.channels || {}).map((name) => ({name}));
      const channels = specs.map((spec) => {
        const address = `${source.source_id}.${spec.name}`;
        const value = source.channels?.[spec.name];
        const selected = view.selectedChannel === address;
        const stateClass = value?.state === "observed" ? "value-observed" : value?.state === "held" ? "value-held" : "";
        return `<button class="channel-button${selected ? " selected" : ""}" type="button" data-channel="${escapeHtml(address)}" title="${escapeHtml(spec.description || address)}">
          <span class="channel-name">${escapeHtml(spec.name)}</span>
          <span class="channel-range">${escapeHtml(rangeText(spec.range))}</span>
          <span class="channel-value ${stateClass}">${escapeHtml(value?.state || "unknown")} · ${escapeHtml(fmt(value?.value))} · conf ${escapeHtml(fmt(value?.confidence))}</span>
        </button>`;
      }).join("");
      return `<article class="registry-card">
        <header class="registry-card-header">
          <div><h3>${escapeHtml(source.source_id)}</h3><p>${escapeHtml(source.description || `${source.kind || "external"} source`)}</p></div>
          <span class="status-pill status-${escapeHtml(source.gate_state)}">${escapeHtml(source.gate_state)}</span>
        </header>
        <div class="channel-list">${channels}</div>
      </article>`;
    }).join("");
  }

  function renderRoutes() {
    const routes = model.projection.routes || [];
    elements.routeCount.textContent = String(routes.length);
    if (!currentScene()) {
      elements.routesList.replaceChildren(emptyState("Activate a scene to start weaving routes."));
      return;
    }
    if (!routes.length) {
      elements.routesList.replaceChildren(emptyState("This scene is open. Select a source channel and patch it to an instrument."));
      return;
    }
    elements.routesList.innerHTML = routes.map((route) => {
      const destination = route.destination || {};
      const bindings = bindingText(destination.bindings);
      const target = `${destination.instrument_id}.${destination.capability}${bindings ? ` (${bindings})` : ""}.${destination.argument}`;
      const transforms = route.transforms?.length
        ? route.transforms.map((item) => `<span class="transform-chip">${escapeHtml(transformLabel(item))}</span>`).join("")
        : '<span class="no-transforms">Direct — no transforms</span>';
      const runtimeActive = route.runtime?.active;
      const deleteLabel = view.deleteArmed === route.route_id ? "Confirm delete" : "Delete";
      return `<article class="route-card${runtimeActive ? " route-active" : ""}${route.enabled ? "" : " route-disabled"}" data-route-id="${escapeHtml(route.route_id)}">
        <header class="route-card-header">
          <div><h3 class="route-label">${escapeHtml(route.label || route.route_id)}</h3><span class="route-id">${escapeHtml(route.route_id)} · v${route.route_version}</span></div>
          <span class="status-pill ${runtimeActive ? "status-ready" : ""}">${runtimeActive ? "sounding" : route.enabled ? "waiting" : "disabled"}</span>
        </header>
        <div class="route-path">
          <div class="route-node"><span>Source</span><strong>${escapeHtml((route.inputs || []).map((item) => item.channel).join(" + "))}</strong></div>
          <span class="route-arrow" aria-hidden="true">→</span>
          <div class="route-node"><span>Destination</span><strong>${escapeHtml(target)}</strong></div>
        </div>
        <div class="transform-summary">${transforms}</div>
        <footer class="route-actions">
          <label class="toggle"><input type="checkbox" data-action="toggle" ${route.enabled ? "checked" : ""} ${model.mutationBusy || !model.connected ? "disabled" : ""}> Enabled</label>
          <button class="button" type="button" data-action="edit" ${model.mutationBusy ? "disabled" : ""}>Edit chain</button>
          <button class="button button-danger" type="button" data-action="delete" ${model.mutationBusy || !model.connected ? "disabled" : ""}>${deleteLabel}</button>
        </footer>
      </article>`;
    }).join("");
  }

  function renderInstruments() {
    const instruments = model.projection.instruments || [];
    elements.instrumentCount.textContent = String(instruments.length);
    if (!instruments.length) {
      elements.instrumentsList.replaceChildren(emptyState("No instrument manifests are installed yet."));
      return;
    }
    elements.instrumentsList.innerHTML = instruments.map((instrument) => {
      const capabilities = (instrument.capabilities || []).filter((capability) => capability.write === true);
      const capabilityHtml = capabilities.map((capability) => {
        const parameters = Object.entries(capability.parameters || {}).map(([name, spec]) => {
          const bounds = spec.bounds || [0, 0];
          return `<label class="binding-field">${escapeHtml(name)}
            <input type="number" data-binding="${escapeHtml(name)}" min="${escapeHtml(bounds[0])}" max="${escapeHtml(bounds[1])}" step="1" value="${escapeHtml(bounds[0])}" aria-label="${escapeHtml(`${capability.name} binding ${name}`)}">
          </label>`;
        }).join("");
        const argumentsHtml = (capability.arguments || []).filter((argument) => Array.isArray(argument.range)).map((argument) => `
          <button class="button patch-button" type="button" data-action="patch" data-instrument="${escapeHtml(instrument.instrument_id)}" data-capability="${escapeHtml(capability.name)}" data-argument="${escapeHtml(argument.name)}" ${!view.selectedChannel || !model.connected || model.mutationBusy || !currentScene() ? "disabled" : ""}>
            <span>Patch → ${escapeHtml(argument.name)}</span><span class="argument-range">${escapeHtml(rangeText(argument.range))}</span>
          </button>`).join("");
        return `<section class="capability" data-capability-name="${escapeHtml(capability.name)}">
          <div class="capability-top"><span class="capability-name">${escapeHtml(capability.name)}</span><span class="capability-lag">${escapeHtml(fmt(capability.lag_ms))} ms lag</span></div>
          ${parameters ? `<div class="binding-row">${parameters}</div>` : ""}
          <div class="argument-list">${argumentsHtml || '<span class="no-transforms">No numeric writable arguments</span>'}</div>
        </section>`;
      }).join("");
      return `<article class="registry-card">
        <header class="registry-card-header">
          <div><h3>${escapeHtml(instrument.instrument_id)}</h3><p>${escapeHtml(instrument.description || "Instrument control endpoint")}</p></div>
          <span class="status-pill status-${escapeHtml(instrument.gate_state)}">${escapeHtml(instrument.gate_state)}</span>
        </header>
        <div class="capability-list">${capabilityHtml || '<div class="capability"><span class="no-transforms">No writable capabilities</span></div>'}</div>
      </article>`;
    }).join("");
  }

  function renderIntent() {
    const found = view.selectedChannel && findChannel(view.selectedChannel);
    elements.patchIntent.classList.toggle("armed", Boolean(found));
    elements.clearSelection.hidden = !found;
    elements.patchIntentText.textContent = found
      ? `${view.selectedChannel} is armed — choose a destination on the right.`
      : "Select a source channel to begin.";
  }

  function emptyState(text) {
    const fragment = $("#empty-template").content.cloneNode(true);
    fragment.querySelector("p").textContent = text;
    return fragment;
  }

  function transformLabel(transform) {
    if (transform.type === "scale_range") return `scale ${rangeText(transform.in)} → ${rangeText(transform.out)}`;
    if (transform.type === "curve") return `curve · ${transform.kind}`;
    if (transform.type === "smoothing") return `${transform.kind} · ${fmt(transform.time_ms)}ms`;
    if (transform.type === "gate") return `gate · ${transform.mode}`;
    if (transform.type === "combine") return `combine · ${transform.operator}`;
    return transform.type;
  }

  function toast(message, kind = "info") {
    const node = document.createElement("div");
    node.className = `toast toast-${kind}`;
    node.textContent = message;
    elements.toasts.append(node);
    setTimeout(() => node.remove(), 4200);
  }

  function cleanRoute(route) {
    const result = clone(route);
    delete result.runtime;
    return result;
  }

  function uniqueRouteId(sourceAddress, capability, argument, bindings) {
    const bindingPart = Object.values(bindings).join("-");
    const base = `${sourceAddress}-to-${capability}-${bindingPart}-${argument}`
      .toLowerCase()
      .replace(/[^a-z0-9_-]+/g, "-")
      .replace(/-+/g, "-")
      .replace(/^-|-$/g, "") || "route";
    const existing = new Set((model.projection.routes || []).map((route) => route.route_id));
    if (!existing.has(base)) return base;
    let suffix = 2;
    while (existing.has(`${base}-${suffix}`)) suffix += 1;
    return `${base}-${suffix}`;
  }

  function createPatch(button) {
    const channel = findChannel(view.selectedChannel);
    const capabilityMatch = findCapability(button.dataset.instrument, button.dataset.capability);
    const scene = currentScene();
    if (!channel || !capabilityMatch || !scene) {
      toast("Select a source channel and activate a scene first.", "error");
      return;
    }
    const capabilityNode = button.closest(".capability");
    const bindings = {};
    for (const input of capabilityNode.querySelectorAll("[data-binding]")) {
      const value = Number(input.value);
      if (!Number.isInteger(value) || value < Number(input.min) || value > Number(input.max)) {
        input.focus();
        toast(`${input.dataset.binding} must be an integer from ${input.min} to ${input.max}.`, "error");
        return;
      }
      bindings[input.dataset.binding] = value;
    }
    const argument = capabilityMatch.capability.arguments.find((item) => item.name === button.dataset.argument);
    const sourceRange = channel.spec.range;
    const destinationRange = argument?.range;
    const transforms = Array.isArray(sourceRange) && Array.isArray(destinationRange)
      && (Number(sourceRange[0]) !== Number(destinationRange[0]) || Number(sourceRange[1]) !== Number(destinationRange[1]))
      ? [{type: "scale_range", in: sourceRange.map(Number), out: destinationRange.map(Number), clamp: true}]
      : [];
    const routeId = uniqueRouteId(view.selectedChannel, capabilityMatch.capability.name, argument.name, bindings);
    const route = {
      route_id: routeId,
      route_version: 1,
      enabled: true,
      label: `${channel.spec.name} → ${argument.name}`,
      inputs: [{channel: view.selectedChannel}],
      transforms,
      destination: {
        instrument_id: capabilityMatch.instrument.instrument_id,
        capability: capabilityMatch.capability.name,
        bindings,
        argument: argument.name,
      },
      validity: {held: "accept", min_confidence: 0, invalid: "suppress"},
    };
    runCommand("route.create", {
      scene_id: scene.scene_id,
      expected_stage_revision: model.stageRevision,
      route,
    }, `Patched ${channel.spec.name} to ${argument.name}.`).catch(() => {});
  }

  function updateRoute(route, successText) {
    const scene = currentScene();
    if (!scene) return;
    const replacement = cleanRoute(route);
    replacement.route_version += 1;
    runCommand("route.update", {
      scene_id: scene.scene_id,
      route_id: route.route_id,
      expected_route_version: route.route_version,
      expected_stage_revision: model.stageRevision,
      route: replacement,
    }, successText).catch(() => {});
  }

  function deleteRoute(route) {
    const scene = currentScene();
    if (!scene) return;
    runCommand("route.delete", {
      scene_id: scene.scene_id,
      route_id: route.route_id,
      expected_route_version: route.route_version,
      expected_stage_revision: model.stageRevision,
    }, `Deleted ${route.label || route.route_id}.`).catch(() => {});
  }

  function openTransformEditor(route) {
    view.editingRoute = cleanRoute(route);
    view.editorTransforms = clone(route.transforms || []);
    elements.transformTitle.textContent = `Edit ${route.label || route.route_id}`;
    elements.transformType.querySelector('option[value="combine"]').disabled = route.inputs.length < 2;
    renderTransformEditor();
    if (typeof elements.dialog.showModal === "function") elements.dialog.showModal();
    else elements.dialog.setAttribute("open", "");
  }

  function defaultTransform(type) {
    const inputRange = findChannel(view.editingRoute?.inputs?.[0]?.channel)?.spec?.range || [0, 1];
    const match = view.editingRoute && findCapability(view.editingRoute.destination.instrument_id, view.editingRoute.destination.capability);
    const outputRange = match?.capability.arguments.find((item) => item.name === view.editingRoute.destination.argument)?.range || [0, 1];
    if (type === "scale_range") return {type, in: clone(inputRange), out: clone(outputRange), clamp: true};
    if (type === "curve") return {type, kind: "linear"};
    if (type === "smoothing") return {type, kind: "one_pole", time_ms: 35};
    if (type === "gate") return {type, threshold: .5, hysteresis: .05, mode: "level", closed: "suppress"};
    return {type: "combine", operator: "mean"};
  }

  function option(value, label, selected) {
    return `<option value="${escapeHtml(value)}"${value === selected ? " selected" : ""}>${escapeHtml(label)}</option>`;
  }

  function numberField(label, field, value, extra = "") {
    return `<label class="transform-field">${escapeHtml(label)}<input type="number" step="any" data-field="${escapeHtml(field)}" value="${escapeHtml(value)}" ${extra}></label>`;
  }

  function selectField(label, field, values, selected) {
    return `<label class="transform-field">${escapeHtml(label)}<select data-field="${escapeHtml(field)}">${values.map(([value, text]) => option(value, text, selected)).join("")}</select></label>`;
  }

  function transformFields(transform) {
    if (transform.type === "scale_range") {
      return `${numberField("Input min", "in.0", transform.in?.[0])}${numberField("Input max", "in.1", transform.in?.[1])}${numberField("Output min", "out.0", transform.out?.[0])}${numberField("Output max", "out.1", transform.out?.[1])}<label class="transform-field check"><input type="checkbox" data-field="clamp" ${transform.clamp ? "checked" : ""}> Clamp to input range</label>`;
    }
    if (transform.type === "curve") {
      const kinds = [["linear", "Linear"], ["power", "Power"], ["exponential", "Exponential"], ["smoothstep", "Smoothstep"], ["piecewise", "Piecewise"]];
      let fields = selectField("Kind", "kind", kinds, transform.kind);
      if (transform.kind === "power") fields += numberField("Gamma", "gamma", transform.gamma ?? 1.6, 'min="0.000001"');
      if (transform.kind === "exponential") fields += numberField("Amount", "amount", transform.amount ?? transform.k ?? 1);
      if (transform.kind === "piecewise") fields += `<label class="transform-field wide">Monotonic points (x,y; x,y)<input type="text" data-field="points" value="${escapeHtml((transform.points || [[0, 0], [1, 1]]).map((point) => point.join(",")).join("; "))}"></label>`;
      return fields;
    }
    if (transform.type === "smoothing") {
      return `${selectField("Kind", "kind", [["one_pole", "One pole"], ["ramp", "Bounded ramp"]], transform.kind)}${numberField("Time (ms)", "time_ms", transform.time_ms, 'min="0"')}`;
    }
    if (transform.type === "gate") {
      const closedMode = transform.closed === "suppress" ? "suppress" : "value";
      let fields = `${numberField("Threshold", "threshold", transform.threshold)}${numberField("Hysteresis", "hysteresis", transform.hysteresis, 'min="0"')}`;
      fields += selectField("Mode", "mode", [["level", "Level"], ["rising_edge", "Rising edge"], ["falling_edge", "Falling edge"]], transform.mode);
      fields += selectField("When closed", "closedMode", [["suppress", "Suppress"], ["value", "Emit value"]], closedMode);
      if (closedMode === "value") fields += numberField("Closed value", "closed.value", transform.closed.value);
      return fields;
    }
    const operators = [["mean", "Mean"], ["sum", "Sum"], ["min", "Minimum"], ["max", "Maximum"], ["weighted_sum", "Weighted sum"], ["difference", "Difference"]];
    let fields = selectField("Operator", "operator", operators, transform.operator);
    if (transform.operator === "weighted_sum") fields += `<label class="transform-field wide">Weights (comma-separated)<input type="text" data-field="weights" value="${escapeHtml((transform.weights || []).join(", "))}"></label>`;
    return fields;
  }

  function renderTransformEditor() {
    if (!view.editorTransforms.length) {
      elements.transformList.replaceChildren(emptyState("No transforms: source values pass directly to the destination."));
      return;
    }
    elements.transformList.innerHTML = view.editorTransforms.map((transform, index) => `
      <section class="transform-row" data-transform-index="${index}">
        <header class="transform-row-head">
          <span class="transform-index">${index + 1}</span><span class="transform-name">${escapeHtml(transform.type)}</span>
          <button class="mini-button" type="button" data-transform-action="up" aria-label="Move transform up" ${index === 0 ? "disabled" : ""}>↑</button>
          <button class="mini-button" type="button" data-transform-action="down" aria-label="Move transform down" ${index === view.editorTransforms.length - 1 ? "disabled" : ""}>↓</button>
          <button class="mini-button" type="button" data-transform-action="remove" aria-label="Remove transform">×</button>
        </header>
        <div class="transform-fields">${transformFields(transform)}</div>
      </section>`).join("");
  }

  function parseNumberList(value, pairs = false) {
    if (pairs) {
      const result = value.split(";").map((item) => item.split(",").map((part) => Number(part.trim())));
      return result.length >= 2 && result.every((item) => item.length === 2 && item.every(Number.isFinite)) ? result : null;
    }
    const result = value.split(",").map((item) => Number(item.trim()));
    return result.length && result.every(Number.isFinite) ? result : null;
  }

  function setNested(target, path, value) {
    const parts = path.split(".");
    let cursor = target;
    for (let index = 0; index < parts.length - 1; index += 1) {
      const key = /^\d+$/.test(parts[index]) ? Number(parts[index]) : parts[index];
      if (cursor[key] === undefined) cursor[key] = /^\d+$/.test(parts[index + 1]) ? [] : {};
      cursor = cursor[key];
    }
    const last = /^\d+$/.test(parts.at(-1)) ? Number(parts.at(-1)) : parts.at(-1);
    cursor[last] = value;
  }

  function changeTransformField(input) {
    const row = input.closest("[data-transform-index]");
    const index = Number(row.dataset.transformIndex);
    const transform = view.editorTransforms[index];
    const field = input.dataset.field;
    if (!transform || !field) return;
    if (field === "closedMode") {
      transform.closed = input.value === "suppress" ? "suppress" : {value: 0};
      renderTransformEditor();
      return;
    }
    if (field === "points" || field === "weights") {
      const parsed = parseNumberList(input.value, field === "points");
      input.setCustomValidity(parsed ? "" : field === "points" ? "Use at least two x,y pairs separated by semicolons." : "Use comma-separated finite numbers.");
      if (parsed) transform[field] = parsed;
      return;
    }
    const value = input.type === "checkbox" ? input.checked : input.type === "number" ? Number(input.value) : input.value;
    setNested(transform, field, value);
    if (transform.type === "curve" && field === "kind") {
      delete transform.gamma;
      delete transform.amount;
      delete transform.k;
      delete transform.points;
      if (value === "power") transform.gamma = 1.6;
      if (value === "exponential") transform.amount = 1;
      if (value === "piecewise") transform.points = [[0, 0], [1, 1]];
      renderTransformEditor();
    } else if (transform.type === "combine" && field === "operator") {
      if (value === "weighted_sum") transform.weights = Array(view.editingRoute.inputs.length).fill(1);
      else delete transform.weights;
      renderTransformEditor();
    }
  }

  elements.sceneSelect.addEventListener("change", () => {
    view.selectedSceneId = elements.sceneSelect.value || null;
    elements.recoveryScene.value = view.selectedSceneId || "";
    renderScenes();
    renderPanic();
  });

  elements.recoveryScene.addEventListener("change", renderPanic);

  elements.sceneSwitch.addEventListener("click", () => {
    const scene = selectedScene();
    if (!scene) return;
    runCommand("scene.switch", {
      scene_id: scene.scene_id,
      expected_scene_version: scene.scene_version,
      expected_stage_revision: model.stageRevision,
    }, `Switched to ${scene.name}.`).catch(() => {});
  });

  elements.panicButton.addEventListener("click", () => {
    runCommand("panic.trigger", {reason: "Patchbay operator"}, "Panic latched. Instruments are held safe.").catch(() => {});
  });

  elements.panicClear.addEventListener("click", () => {
    const sceneId = elements.recoveryScene.value;
    const scene = (model.projection.scenes || []).find((item) => item.scene_id === sceneId);
    const panic = model.projection.stage?.panic;
    if (!scene || !panic?.active) return;
    runCommand("panic.clear", {
      panic_generation: panic.panic_generation,
      scene_id: scene.scene_id,
      expected_scene_version: scene.scene_version,
    }, `Recovered into ${scene.name}.`).catch(() => {});
  });

  elements.sourcesList.addEventListener("click", (event) => {
    const button = event.target.closest("[data-channel]");
    if (!button) return;
    view.selectedChannel = button.dataset.channel;
    renderSources();
    renderInstruments();
    renderIntent();
  });

  elements.clearSelection.addEventListener("click", () => {
    view.selectedChannel = null;
    renderSources();
    renderInstruments();
    renderIntent();
  });

  elements.instrumentsList.addEventListener("click", (event) => {
    const button = event.target.closest('[data-action="patch"]');
    if (button) createPatch(button);
  });

  elements.routesList.addEventListener("change", (event) => {
    const input = event.target.closest('[data-action="toggle"]');
    if (!input) return;
    const routeId = input.closest("[data-route-id]").dataset.routeId;
    const route = (model.projection.routes || []).find((item) => item.route_id === routeId);
    if (!route) return;
    const replacement = cleanRoute(route);
    replacement.enabled = input.checked;
    updateRoute(replacement, `${replacement.enabled ? "Enabled" : "Disabled"} ${route.label || route.route_id}.`);
  });

  elements.routesList.addEventListener("click", (event) => {
    const button = event.target.closest("[data-action]");
    if (!button || button.dataset.action === "toggle") return;
    const routeId = button.closest("[data-route-id]").dataset.routeId;
    const route = (model.projection.routes || []).find((item) => item.route_id === routeId);
    if (!route) return;
    if (button.dataset.action === "edit") openTransformEditor(route);
    if (button.dataset.action === "delete") {
      if (view.deleteArmed === routeId) {
        view.deleteArmed = null;
        deleteRoute(route);
      } else {
        view.deleteArmed = routeId;
        renderRoutes();
        setTimeout(() => {
          if (view.deleteArmed === routeId) {
            view.deleteArmed = null;
            renderRoutes();
          }
        }, 2500);
      }
    }
  });

  elements.transformAdd.addEventListener("click", () => {
    const type = elements.transformType.value;
    if (type === "combine" && view.editingRoute.inputs.length < 2) {
      toast("Combine is only valid for routes with multiple inputs.", "error");
      return;
    }
    if (type === "combine") view.editorTransforms.unshift(defaultTransform(type));
    else view.editorTransforms.push(defaultTransform(type));
    renderTransformEditor();
  });

  elements.transformList.addEventListener("click", (event) => {
    const button = event.target.closest("[data-transform-action]");
    if (!button) return;
    const index = Number(button.closest("[data-transform-index]").dataset.transformIndex);
    const action = button.dataset.transformAction;
    if (action === "remove") view.editorTransforms.splice(index, 1);
    if (action === "up" && index > 0) [view.editorTransforms[index - 1], view.editorTransforms[index]] = [view.editorTransforms[index], view.editorTransforms[index - 1]];
    if (action === "down" && index < view.editorTransforms.length - 1) [view.editorTransforms[index + 1], view.editorTransforms[index]] = [view.editorTransforms[index], view.editorTransforms[index + 1]];
    renderTransformEditor();
  });

  elements.transformList.addEventListener("input", (event) => changeTransformField(event.target));
  elements.transformList.addEventListener("change", (event) => changeTransformField(event.target));

  elements.transformSave.addEventListener("click", () => {
    if (!elements.dialog.querySelector("form").reportValidity() || !view.editingRoute) return;
    const replacement = cleanRoute(view.editingRoute);
    replacement.transforms = clone(view.editorTransforms);
    elements.dialog.close();
    updateRoute(replacement, `Updated ${replacement.label || replacement.route_id} transform chain.`);
  });

  window.addEventListener("beforeunload", () => {
    clearTimeout(reconnectTimer);
    if (socket) socket.close();
  });

  // ── Convergence knobs (HTTP, independent of Stage WS) ──────────────
  const knobsStatus = $("#knobs-status");
  const knobInputs = Array.from(document.querySelectorAll("[data-param]"));

  function formatKnobValue(input, value) {
    const kind = input.dataset.kind;
    const n = Number(value);
    if (kind === "int") return String(Math.round(n));
    const step = Number(input.step) || 0.01;
    if (step >= 1) return String(n);
    const decimals = (String(step).split(".")[1] || "").length || 2;
    return n.toFixed(decimals);
  }

  function setKnobOutputs(params) {
    for (const input of knobInputs) {
      const key = input.dataset.param;
      if (!(key in params)) continue;
      const value = params[key];
      input.value = String(value);
      const output = document.getElementById(`out-${key}`);
      if (output) output.textContent = formatKnobValue(input, value);
    }
  }

  function setKnobsStatus(text, ok) {
    if (!knobsStatus) return;
    knobsStatus.textContent = text;
    knobsStatus.classList.toggle("knobs-status-ok", !!ok);
    knobsStatus.classList.toggle("knobs-status-err", ok === false);
  }

  async function loadSceneParams() {
    try {
      const response = await fetch("/api/scene/params", {cache: "no-store"});
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const params = await response.json();
      setKnobOutputs(params);
      setKnobsStatus("synced", true);
    } catch (error) {
      setKnobsStatus("offline", false);
      console.warn("scene params load failed", error);
    }
  }

  async function postSceneParam(key, value) {
    const body = {};
    body[key] = value;
    try {
      const response = await fetch("/api/scene/params", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        setKnobsStatus("error", false);
        toast(payload.message || `Knob ${key} rejected`, "error");
        return;
      }
      if (payload.params) setKnobOutputs(payload.params);
      const push = Array.isArray(payload.pushed) ? payload.pushed[0] : null;
      if (push && push.error) {
        setKnobsStatus("push err", false);
        toast(`${key}: ${push.error}`, "error");
      } else if (push && push.skipped) {
        setKnobsStatus("body tempo", true);
      } else if (push && push.address) {
        setKnobsStatus(push.address, true);
      } else {
        setKnobsStatus("updated", true);
      }
    } catch (error) {
      setKnobsStatus("error", false);
      toast(`Knob ${key} failed: ${error.message || error}`, "error");
    }
  }

  for (const input of knobInputs) {
    const emit = () => {
      const key = input.dataset.param;
      const kind = input.dataset.kind;
      let value = Number(input.value);
      if (!Number.isFinite(value)) return;
      if (kind === "int") value = Math.round(value);
      const output = document.getElementById(`out-${key}`);
      if (output) output.textContent = formatKnobValue(input, value);
      postSceneParam(key, value);
    };
    input.addEventListener("input", emit);
    // number inputs also fire change on blur/enter
    if (input.type === "number") input.addEventListener("change", emit);
  }

  loadSceneParams();

  render();
  connect();
})();
