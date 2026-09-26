const state = { projectId: null, project: null, tab: "design", busy: false, toastTimer: null };
const $ = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) throw new Error(body?.detail || body?.error || `Request failed (${response.status})`);
  return body;
}

function showToast(message, isError = false) {
  const toast = $("toast");
  toast.textContent = message;
  toast.style.borderColor = isError ? "#af573e" : "#294247";
  toast.classList.add("visible");
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => toast.classList.remove("visible"), 5200);
}

function setStatus(message, tone = "ready") {
  const line = $("status-line");
  line.lastElementChild.previousElementSibling.textContent = message;
  line.classList.toggle("error", tone === "error");
}

function setBusy(button, busy, label) {
  if (!button) return;
  button.disabled = busy;
  const main = button.querySelector("span:first-child");
  if (main) {
    if (busy) {
      button.dataset.originalLabel = main.textContent;
      main.textContent = label || "Working…";
    } else if (button.dataset.originalLabel) {
      main.textContent = button.dataset.originalLabel;
      delete button.dataset.originalLabel;
    }
  }
}

function artifactByType(type) {
  const manifest = state.project?.output_manifest;
  if (!manifest) return null;
  const all = ["drawing", "render", "presentation", "model_captures"].flatMap((key) => manifest[key] || []);
  return all.filter((item) => item.type === type).at(-1) || null;
}

function allArtifacts() {
  const manifest = state.project?.output_manifest;
  if (!manifest) return [];
  return ["drawing", "render", "presentation", "model_captures"].flatMap((key) => manifest[key] || []);
}

function updateHeader() {
  const project = state.project;
  if (!project) return;
  const context = project.context;
  const model = project.model_state;
  $("project-title").textContent = context.project_name;
  $("project-name").value = context.project_name;
  $("sidebar-project-name").textContent = context.project_name.replace(" · ", " ");
  $("sidebar-project-status").textContent = model.status === "ready" ? "Design study" : model.status.replaceAll("_", " ");
  $("project-subtitle").textContent = project.design_ir?.concept?.summary || context.site.summary || "An open civic room between neighborhood and water.";
  $("brief").value = context.brief.summary || "";
  $("site-note").value = context.site.summary || "";
  $("intent").value = context.user_intent || "";
  $("reference-url").value = context.references.find((item) => item.type === "url")?.source || "";
  const prepared = !!project.design_ir && !!project.build_plan;
  const built = (model.objects || []).length > 0;
  const status = $("project-status");
  status.classList.toggle("built", built);
  status.innerHTML = `<i></i> ${built ? "MODEL BUILT" : prepared ? "DESIGN PREPARED" : "INPUTS READY"}`;
  $("build-model").disabled = !prepared || !$("disposable-confirm").checked || state.busy || built;
  $("edit-height").disabled = !built || state.busy || !project.design_ir.objects.some((item) => item.type === "building_mass");
  const masses = (model.objects || []).filter((item) => item.object_type === "building_mass");
  const editedCount = masses.filter((item) => item.last_change).length;
  $("edit-count").textContent = `${Math.min(editedCount, 2)} / 2`;
  $("edit-position").disabled = !built || state.busy || editedCount < 1 || masses.length < 2 || !!masses[1]?.last_change;
  $("edit-height").disabled = !built || state.busy || !masses.length || !!masses[0]?.last_change;
  setStage("design", true);
  setStage("model", prepared);
  setStage("drawing", !!artifactByType("dxf"));
  setStage("render", !!artifactByType("viewport"));
  setStage("present", !!artifactByType("presentation"));
  renderArtifacts();
  renderPreview();
}

function setStage(stage, complete) {
  const indicator = $(`stage-${stage}`);
  indicator.textContent = complete ? "●" : "○";
  indicator.classList.toggle("complete", complete);
}

function renderArtifacts() {
  const artifacts = allArtifacts();
  const unique = [...new Map(artifacts.map((item) => [item.path, item])).values()];
  $("artifact-total").textContent = `${unique.length} ${unique.length === 1 ? "file" : "files"}`;
  const container = $("artifact-list");
  if (!unique.length) {
    container.innerHTML = '<div class="artifact-empty">Design artifacts will collect here as the project takes shape.</div>';
    $("artifact-links").innerHTML = "";
    return;
  }
  container.innerHTML = unique.slice(-6).map((item) => {
    const extension = item.path.split(".").at(-1).toUpperCase();
    const name = item.path.split("/").at(-1);
    return `<a class="artifact-card" href="${item.url}" target="_blank" rel="noreferrer"><span class="artifact-glyph">${extension.slice(0, 4)}</span><span class="artifact-copy"><strong>${escapeHtml(name)}</strong><small>${escapeHtml(item.type.replaceAll("-", " ").toUpperCase())}</small></span></a>`;
  }).join("");
  const dxf = artifactByType("dxf");
  const board = artifactByType("presentation");
  $("artifact-links").innerHTML = [
    dxf ? `<a class="artifact-link" href="${dxf.url}" download>↓ DXF</a>` : "",
    board ? `<a class="artifact-link" href="${board.url}" target="_blank" rel="noreferrer">↗ A3 board</a>` : "",
  ].join("");
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character]);
}

function setTab(tab) {
  state.tab = tab;
  document.querySelectorAll("[data-tab]").forEach((button) => button.classList.toggle("active", button.dataset.tab === tab));
  document.querySelectorAll(".stage-link").forEach((button) => button.classList.toggle("active", button.dataset.tab === tab));
  renderPreview();
}

function renderPreview() {
  const project = state.project;
  if (!project) return;
  const canvas = $("preview-canvas");
  const title = $("preview-title");
  const caption = $("preview-caption");
  const meta = $("preview-meta");
  const projectId = encodeURIComponent(state.projectId);
  const drawing = artifactByType("drawing-preview");
  const capture = artifactByType("viewport");
  const board = artifactByType("presentation");
  const ir = project.design_ir;
  const objects = project.model_state?.objects || [];
  if (state.tab === "design") {
    title.textContent = "Design intent";
    caption.textContent = ir ? "Site plan and massing concept" : "Design intent and concept";
    meta.textContent = ir ? `${ir.objects.filter((item) => item.type === "building_mass").length} MASSES · METERS` : "WAITING FOR PREPARE DESIGN";
    if (ir && drawing) {
      const masses = ir.objects.filter((item) => item.type === "building_mass");
      canvas.className = "preview-canvas";
      canvas.innerHTML = `<img class="drawing-preview" src="${drawing.url}" alt="Generated site plan"><div class="design-summary"><strong>${escapeHtml(ir.concept.summary || "Design concept")}</strong><p>${masses.length} building masses · ${ir.objects.filter((item) => item.type === "circulation").length} public-space routes</p></div><div class="canvas-stamp">01 <span>/</span> 05</div>`;
    } else {
      canvas.className = "preview-canvas empty-design";
      canvas.innerHTML = '<div class="canvas-grid"></div><div class="empty-poster"><div class="poster-kicker">A PLACE TO MEET THE WATER</div><div class="poster-title">A public room,<br><em>held lightly.</em></div><div class="poster-rule"></div><div class="poster-foot"><span>60° 00′ N<br>WATERFRONT SITE</span><span>DESIGN STUDY<br>CODEX BRAIN</span></div><div class="poster-sketch"><svg viewBox="0 0 510 220" aria-hidden="true"><path d="M13 184H497M44 178V93H156V178M175 178V66H281V178M301 178V106H457V178" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M44 94L81 62L156 94M175 67L217 36L281 67M301 107L356 78L457 107M0 204H510" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="4 6"/></svg></div></div><div class="canvas-stamp">01 <span>/</span> 05</div>';
    }
  } else if (state.tab === "model") {
    title.textContent = "Editable model";
    caption.textContent = "SketchUp geometry · stable object names";
    meta.textContent = objects.length ? `${objects.length} OBJECTS · ${project.model_state.status.toUpperCase()}` : "WAITING FOR SKETCHUP BUILD";
    const image = capture ? `<img class="preview-image" src="${capture.url}" alt="SketchUp viewport capture">` : '<div class="preview-canvas empty-design"><div class="canvas-grid"></div><div class="empty-poster"><div class="poster-kicker">LIVE GEOMETRY</div><div class="poster-title">Model in<br><em>SketchUp.</em></div><div class="poster-rule"></div><div class="poster-foot"><span>STABLE OBJECT IDS<br>EDITABLE GROUPS</span><span>BUILD WHEN READY</span></div></div></div>';
    const chips = objects.map((item) => `<span class="model-object-chip"><b>${escapeHtml(item.stable_id)}</b>${escapeHtml(item.name)}</span>`).join("");
    canvas.className = "preview-canvas model-preview-content";
    canvas.innerHTML = `${image}${objects.length ? `<div class="model-summary">${chips}</div>` : ""}`;
  } else if (state.tab === "drawing") {
    title.textContent = "Site drawing";
    caption.textContent = "Basic DXF generated from the shared DesignIR";
    meta.textContent = drawing ? "SITE · MASSES · PUBLIC ROUTE" : "WAITING FOR DESIGN PREPARATION";
    canvas.className = "preview-canvas";
    canvas.innerHTML = drawing ? `<img class="drawing-preview" src="${drawing.url}" alt="Site drawing preview"><div class="canvas-stamp">XY <span>/</span> M</div>` : '<div class="preview-canvas empty-design"><div class="canvas-grid"></div><div class="empty-poster"><div class="poster-kicker">DRAWING ADAPTER</div><div class="poster-title">A clear plan,<br><em>in true scale.</em></div><div class="poster-rule"></div><div class="poster-foot"><span>SITE BOUNDARY<br>MASS FOOTPRINTS</span><span>DXF · METERS</span></div></div></div>';
  } else if (state.tab === "render") {
    title.textContent = "Viewport render";
    caption.textContent = "SketchUp viewport capture · RenderAdapter fallback";
    meta.textContent = capture ? "LIVE SKETCHUP CAPTURE" : "CAPTURE AFTER MODEL BUILD";
    canvas.className = "preview-canvas";
    canvas.innerHTML = capture ? `<img class="preview-image" src="${capture.url}" alt="SketchUp viewport render"><div class="canvas-stamp">SU <span>/</span> LIVE</div>` : '<div class="preview-canvas empty-design"><div class="canvas-grid"></div><div class="empty-poster"><div class="poster-kicker">RENDER ADAPTER</div><div class="poster-title">A view from<br><em>the model.</em></div><div class="poster-rule"></div><div class="poster-foot"><span>SKETCHUP VIEWPORT<br>NO IMAGE API REQUIRED</span><span>RENDER FALLBACK</span></div></div></div>';
  } else {
    title.textContent = "A3 presentation";
    caption.textContent = "Landscape presentation preview · HTML";
    meta.textContent = board ? "A3 LANDSCAPE · READY" : "GENERATED AFTER DESIGN PREPARATION";
    canvas.className = "preview-canvas";
    canvas.innerHTML = board ? `<iframe class="preview-frame" title="A3 presentation preview" src="${board.url}"></iframe>` : '<div class="preview-canvas empty-design"><div class="canvas-grid"></div><div class="empty-poster"><div class="poster-kicker">A3 LANDSCAPE</div><div class="poster-title">The project,<br><em>in one frame.</em></div><div class="poster-rule"></div><div class="poster-foot"><span>CONCEPT<br>PLAN + MODEL</span><span>HTML PREVIEW</span></div></div></div>';
  }
}

async function loadProject(projectId) {
  state.projectId = projectId;
  state.project = await api(`/api/projects/${encodeURIComponent(projectId)}`);
  updateHeader();
  setStatus(state.project.design_ir ? "Design plan and site drawing are ready." : "Workspace ready. Add a brief, then prepare the design.");
}

async function boot() {
  try {
    const [runtime, projects] = await Promise.all([api("/api/status"), api("/api/projects")]);
    $("brain-status").textContent = runtime.codex_available ? "Codex Brain · ready" : "Codex Job Mode · ready";
    $("brain-status").previousElementSibling.classList.toggle("ready", runtime.codex_available);
    if (projects.length) await loadProject(projects[0].project_id);
  } catch (error) {
    showToast(error.message, true);
  }
}

async function uploadFile(category, file, targetId) {
  if (!state.projectId || !file) return;
  try {
    const url = `/api/projects/${encodeURIComponent(state.projectId)}/inputs/${category}?filename=${encodeURIComponent(file.name)}`;
    const result = await api(url, { method: "POST", headers: { "Content-Type": file.type || "application/octet-stream" }, body: file });
    const chip = document.createElement("span");
    chip.className = "file-chip";
    chip.title = result.path;
    chip.textContent = result.filename;
    $(targetId).append(chip);
    showToast(`${result.filename} saved to this project's local inputs.`);
  } catch (error) { showToast(error.message, true); }
}

async function prepareDesign() {
  if (state.busy) return;
  state.busy = true;
  const button = $("prepare-design");
  setBusy(button, true, "Codex is thinking…");
  $("build-model").disabled = true;
  setStatus("Codex is turning your inputs into DesignIR and a BuildPlan.");
  try {
    const result = await api(`/api/projects/${encodeURIComponent(state.projectId)}/prepare`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        project_name: $("project-name").value,
        brief: $("brief").value,
        site_note: $("site-note").value,
        reference_url: $("reference-url").value,
        user_intent: $("intent").value,
      }),
    });
    if (result.status === "awaiting_codex") {
      $("prepare-note").textContent = `Job ${result.job.job_id} is ready for the active Codex session.`;
      setStatus("Codex Job Mode: request package saved; awaiting structured DesignIR and BuildPlan.");
      showToast("Codex CLI was unavailable. A reviewable Job Mode request was saved.", true);
    } else {
      state.project = result.project;
      updateHeader();
      setStatus("Codex returned a valid plan. Site drawing and A3 preview are ready.");
      showToast("DesignIR, BuildPlan, DXF, drawing preview, and A3 board created.");
      setTab("design");
    }
  } catch (error) {
    setStatus(error.message, "error");
    showToast(error.message, true);
  } finally {
    state.busy = false;
    setBusy(button, false);
    updateHeader();
  }
}

async function checkConnector() {
  if (!state.projectId) return;
  $("connector-state").textContent = "Checking…";
  try {
    const result = await api(`/api/projects/${encodeURIComponent(state.projectId)}/connector`);
    $("connector-state").textContent = result.reachable ? "Connected · SketchUp" : "Bridge not reachable";
    $("connector-state").style.color = result.reachable ? "#557568" : "#a0523a";
    setStatus(result.reachable ? "Existing SketchUp MCP and local bridge responded." : result.detail || "Open SketchUp and start the Kongxing Local Bridge.", result.reachable ? "ready" : "error");
    if (result.reachable) showToast("Existing SketchUp MCP and local bridge are reachable.");
    else showToast(result.detail || "SketchUp bridge is not reachable yet.", true);
  } catch (error) { $("connector-state").textContent = "Unavailable"; showToast(error.message, true); }
}

async function buildModel() {
  if (state.busy) return;
  if (!$("disposable-confirm").checked) return showToast("Open a blank or disposable model before building.", true);
  state.busy = true;
  const button = $("build-model");
  setBusy(button, true, "Building editable groups…");
  setStatus("Sending the approved BuildPlan through the existing SketchUp MCP.");
  try {
    const result = await api(`/api/projects/${encodeURIComponent(state.projectId)}/build`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ confirm_disposable_model: true }),
    });
    state.project = result.project;
    updateHeader();
    setTab("model");
    setStatus(`SketchUp readback complete · ${result.completed_ids.length} named objects created on the existing model.`);
    showToast("Editable SketchUp model built and saved. It is ready for sequential edits.");
  } catch (error) {
    setStatus(error.message, "error");
    showToast(error.message, true);
  } finally {
    state.busy = false;
    setBusy(button, false);
    updateHeader();
  }
}

async function applyEdit(instruction) {
  if (state.busy) return;
  state.busy = true;
  const button = instruction.startsWith("Raise") ? $("edit-height") : $("edit-position");
  setBusy(button, true, "Planning and editing…");
  setStatus("Codex is planning one targeted edit against the current model state.");
  try {
    const result = await api(`/api/projects/${encodeURIComponent(state.projectId)}/edit`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ instruction }),
    });
    state.project = result.project;
    updateHeader();
    setTab("model");
    setStatus(`${result.edit_plan.target_id} changed in place. Connector readback and viewport were captured.`);
    showToast(`Sequential edit applied to ${result.edit_plan.target_id}; the model was not rebuilt.`);
  } catch (error) {
    setStatus(error.message, "error");
    showToast(error.message, true);
  } finally {
    state.busy = false;
    setBusy(button, false);
    updateHeader();
  }
}

document.querySelectorAll("[data-tab]").forEach((button) => button.addEventListener("click", () => setTab(button.dataset.tab)));
$("prepare-design").addEventListener("click", prepareDesign);
$("build-model").addEventListener("click", buildModel);
$("disposable-confirm").addEventListener("change", updateHeader);
$("check-connector").addEventListener("click", checkConnector);
$("brief-file").addEventListener("change", (event) => uploadFile("brief", event.target.files[0], "brief-files"));
$("site-file").addEventListener("change", (event) => uploadFile("site", event.target.files[0], "site-files"));
$("reference-file").addEventListener("change", (event) => uploadFile("reference", event.target.files[0], "reference-files"));
$("edit-height").addEventListener("click", () => {
  const masses = state.project?.model_state?.objects.filter((item) => item.object_type === "building_mass") || [];
  const target = masses[0];
  const source = state.project?.design_ir?.objects.find((item) => item.id === target?.stable_id);
  if (target && source) applyEdit(`Raise ${target.name} by one floor while preserving its footprint. Set floors to ${Number(target.floors || source.floors) + 1} and height to ${(Number(target.floors || source.floors) + 1) * Number(source.floor_height)} meters.`);
});
$("edit-position").addEventListener("click", () => {
  const masses = state.project?.model_state?.objects.filter((item) => item.object_type === "building_mass") || [];
  const target = masses[1];
  if (target) applyEdit(`Move ${target.name} exactly 3 meters east (+X), preserving its size, height, and footprint shape.`);
});
$("new-project").addEventListener("click", () => $("project-dialog").showModal());
$("create-project-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const name = $("new-project-name").value.trim();
  if (!name) return;
  try {
    const result = await api("/api/projects", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ project_name: name, brief: $("new-project-brief").value }),
    });
    $("project-dialog").close();
    await loadProject(result.project_id);
    showToast("New local project created. Add a site note and design intent.");
  } catch (error) { showToast(error.message, true); }
});

boot();
