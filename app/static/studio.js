const state = { projectId: null, project: null, tab: "design", busy: false, toastTimer: null, nativeAgentAvailable: false, modelRouter: null };
const $ = (id) => document.getElementById(id);

function routeInfo(tier) {
  const fallback = tier === "premium"
    ? { model: "gpt-6-astra", provider: "codex-app-server" }
    : { model: "gpt-6-sol", reasoning_effort: "medium", provider: "codex-app-server" };
  return state.modelRouter?.[tier] || fallback;
}

function routeAvailable(tier) {
  const route = routeInfo(tier);
  if (!state.modelRouter) return state.nativeAgentAvailable;
  return !!state.modelRouter.providers?.[route.provider]?.available;
}

function refreshTierLabels() {
  const select = $("conversation-tier");
  if (!select) return;
  const economy = select.querySelector('option[value="economy"]');
  const premium = select.querySelector('option[value="premium"]');
  const economyRoute = routeInfo("economy");
  const premiumRoute = routeInfo("premium");
  economy.textContent = `Economy · ${economyRoute.model}（默认${routeAvailable("economy") ? "" : " · 未配置"}）`;
  premium.textContent = `精修 · ${premiumRoute.model}（仅本轮${routeAvailable("premium") ? "" : " · 未配置"}）`;
}

const modelStatusLabels = {
  ready: "方案研究",
  building: "正在建模",
  built: "模型已建立",
  agentic: "Agent 自由建模",
  edited: "已完成修改",
  partial: "部分完成",
  unavailable: "连接不可用",
};

const artifactTypeLabels = {
  dxf: "DXF 图纸",
  "drawing-preview": "图纸预览",
  viewport: "模型视口",
  presentation: "A3 展板",
  skp: "SketchUp 模型",
};

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) throw new Error(body?.detail || body?.error || `请求失败（${response.status}）`);
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

function friendlyError(error) {
  const message = String(error?.message || "");
  if (!message || /^[\u0000-\u00ff]*$/.test(message)) {
    if (/ECONNREFUSED|bridge connection failed/i.test(message)) return "SketchUp 本地桥接未响应，请检查 SketchUp 是否已打开并启动 Kongxing Local Bridge。";
    if (/not the disposable|blank-disposable/i.test(message)) return "当前 SketchUp 模型不是空白演示模型，请先打开本地生成的空白副本。";
    if (/already has a live|new project/i.test(message)) return "该项目已绑定 SketchUp 模型，请新建项目后再开始新的建模。";
    if (/Codex output failed|deterministic validation/i.test(message)) return "Codex 返回的方案未通过校验，请调整要求后重试。";
    return "操作未能完成，请检查本地运行状态后重试。";
  }
  return message;
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
      main.textContent = label || "处理中…";
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
  refreshTierLabels();
  const project = state.project;
  if (!project) return;
  const context = project.context;
  const model = project.model_state;
  const agent = project.agent_session || {};
  const agentReady = agent.status === "ready" && !!agent.model_path;
  $("project-title").textContent = context.project_name;
  $("project-name").value = context.project_name;
  $("sidebar-project-name").textContent = context.project_name.replace(" · ", " ");
  $("sidebar-project-status").textContent = modelStatusLabels[model.status] || String(model.status || "").replaceAll("_", " ");
  $("project-subtitle").textContent = project.design_ir?.concept?.summary || context.site.summary || "在社区与水岸之间形成开放、可穿行的公共空间。";
  $("brief").value = context.brief.summary || "";
  $("site-note").value = context.site.summary || "";
  $("intent").value = context.user_intent || "";
  $("reference-url").value = context.references.find((item) => item.type === "url")?.source || "";
  const urlReference = context.references.find((item) => item.type === "url");
  const referenceStatus = $("reference-status");
  if (urlReference?.status === "readable") {
    referenceStatus.textContent = `已读取网页${urlReference.title ? `：${urlReference.title}` : ""}，正文摘要将用于方案分析。`;
    referenceStatus.classList.remove("unreadable");
  } else if (urlReference?.status === "unreadable") {
    referenceStatus.textContent = urlReference.error || "网页暂时无法读取，请上传网页截图或参考图片。";
    referenceStatus.classList.add("unreadable");
  } else {
    referenceStatus.textContent = "";
    referenceStatus.classList.remove("unreadable");
  }
  const prepared = !!project.design_ir && !!project.build_plan;
  const built = (model.objects || []).length > 0 || agentReady || model.status === "agentic";
  const status = $("project-status");
  status.classList.toggle("built", built);
  status.innerHTML = `<i></i> ${agentReady ? "Agent 会话已连接" : built ? "模型已建立" : prepared ? "方案已生成" : "输入已就绪"}`;
  $("build-model").disabled = !prepared || !$("disposable-confirm").checked || state.busy || built;
  $("edit-height").disabled = !built || state.busy || !project.design_ir.objects.some((item) => item.type === "building_mass");
  const masses = (model.objects || []).filter((item) => item.object_type === "building_mass");
  const editedCount = masses.filter((item) => item.last_change).length;
  $("edit-count").textContent = `${Math.min(editedCount, 2)} / 2`;
  $("edit-position").disabled = !built || state.busy || editedCount < 1 || masses.length < 2 || !!masses[1]?.last_change;
  $("edit-height").disabled = !built || state.busy || !masses.length || !!masses[0]?.last_change;
  $("agent-session-state").textContent = agentReady
    ? `已连接同一份 SketchUp 空白副本 · ${agent.model_path.split("/").at(-1)}`
    : agent.status === "conversation" ? "Agent 对话已建立 · SketchUp 建模工具尚未启用" : "尚未打开项目专属空白副本";
  $("start-agent-session").disabled = state.busy || !state.nativeAgentAvailable;
  $("start-agent-session").querySelector("span:first-child").textContent = agentReady ? "重连此项目的同一份模型" : "打开空白副本并连接 Agent";
  const hasAgentTurn = agent.status === "conversation" || agent.status === "ready";
  const activeTier = hasAgentTurn ? agent.routing_tier : "economy";
  const activeModel = hasAgentTurn && agent.model ? agent.model : routeInfo("economy").model;
  $("model-tier-status").textContent = (activeTier === "premium" ? "精修 · " : "Economy · ") + activeModel;
  $("conversation-input").placeholder = $("workflow-mode").value === "image_reconstruction"
    ? "按这张图尽可能还原成可编辑 SketchUp 模型"
    : agentReady ? "描述设计修改；Agent 会自行调用工具、查看结果并继续修正…" : "先讨论设计方向；启动空白模型后，Agent 可直接建模并继续修改…";
  $("conversation-hint").textContent = agentReady
    ? "每轮对话都在同一份 SketchUp 副本上执行；Agent 可连续调用工具、查看截图/状态并保存检查点。"
    : "可以先讨论与上传项目资料；未启动空白模型前，SketchUp 工具保持关闭。";
  $("conversation-send").disabled = state.busy || !routeAvailable($("conversation-tier").value) || !$("conversation-input").value.trim();
  setStage("design", true);
  setStage("model", prepared);
  setStage("drawing", !!artifactByType("dxf"));
  setStage("render", !!artifactByType("viewport"));
  setStage("present", !!artifactByType("presentation"));
  renderArtifacts();
  renderConversation();
  renderPreview();
}

function renderConversation() {
  const messages = state.project?.context?.conversation || [];
  const history = $("conversation-history");
  if (!messages.length) {
    history.innerHTML = '<div class="conversation-empty">可以直接用中文描述想法，建筑 Agent 会把讨论落实到方案或当前模型。</div>';
    return;
  }
  history.innerHTML = messages.map((message) => {
    const isUser = message.role === "user";
    const speaker = isUser ? "你" : "建筑 Agent";
    const phase = message.phase === "agent" ? "Agent 对话 / 建模" : message.phase === "after_build" ? "模型修改" : "方案讨论";
    const meta = message.metadata || {};
    const detail = !isUser && meta.model
      ? '<small class="chat-metadata">' + escapeHtml(meta.tier === "premium" ? "精修" : "Economy")
        + " · " + escapeHtml(meta.model)
        + (Number.isInteger(meta.input_tokens) ? " · " + meta.input_tokens + " 输入 token" : "")
        + (Number.isInteger(meta.output_tokens) ? " · " + meta.output_tokens + " 输出 token" : "")
        + (Number.isFinite(meta.latency_ms) ? " · " + meta.latency_ms + " ms" : " · 耗时未报告")
        + "</small>"
      : "";
    return '<article class="chat-message ' + (isUser ? "user" : "assistant") + '"><header><span>'
      + speaker + "</span><span>" + phase + "</span></header><p>" + escapeHtml(message.content)
      + "</p>" + detail + "</article>";
  }).join("");
  history.scrollTop = history.scrollHeight;
}

function setStage(stage, complete) {
  const indicator = $(`stage-${stage}`);
  indicator.textContent = complete ? "●" : "○";
  indicator.classList.toggle("complete", complete);
}

function renderArtifacts() {
  const artifacts = allArtifacts();
  const unique = [...new Map(artifacts.map((item) => [item.path, item])).values()];
  $("artifact-total").textContent = `${unique.length} 个文件`;
  const container = $("artifact-list");
  if (!unique.length) {
    container.innerHTML = '<div class="artifact-empty">方案、模型、图纸和展示成果会集中显示在这里。</div>';
    $("artifact-links").innerHTML = "";
    return;
  }
  container.innerHTML = unique.slice(-6).map((item) => {
    const extension = item.path.split(".").at(-1).toUpperCase();
    const name = item.path.split("/").at(-1);
    const typeLabel = artifactTypeLabels[item.type] || item.type.replaceAll("-", " ").toUpperCase();
    return `<a class="artifact-card" href="${item.url}" target="_blank" rel="noreferrer"><span class="artifact-glyph">${extension.slice(0, 4)}</span><span class="artifact-copy"><strong>${escapeHtml(name)}</strong><small>${escapeHtml(typeLabel)}</small></span></a>`;
  }).join("");
  const dxf = artifactByType("dxf");
  const board = artifactByType("presentation");
  $("artifact-links").innerHTML = [
    dxf ? `<a class="artifact-link" href="${dxf.url}" download>↓ 下载 DXF</a>` : "",
    board ? `<a class="artifact-link" href="${board.url}" target="_blank" rel="noreferrer">↗ 查看 A3 展板</a>` : "",
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
  const drawing = artifactByType("drawing-preview");
  const capture = artifactByType("viewport");
  const board = artifactByType("presentation");
  const ir = project.design_ir;
  const objects = project.model_state?.objects || [];
  if (state.tab === "design") {
    title.textContent = "设计意图";
    caption.textContent = ir ? "场地与体块方案" : "设计意图与概念";
    meta.textContent = ir ? `${ir.objects.filter((item) => item.type === "building_mass").length} 个建筑体块 · 米制` : "等待生成方案";
    if (ir && drawing) {
      const masses = ir.objects.filter((item) => item.type === "building_mass");
      canvas.className = "preview-canvas";
      canvas.innerHTML = `<img class="drawing-preview" src="${drawing.url}" alt="生成的场地图"><div class="design-summary"><strong>${escapeHtml(ir.concept.summary || "设计概念")}</strong><p>${masses.length} 个建筑体块 · ${ir.objects.filter((item) => item.type === "circulation").length} 条公共空间/流线</p></div><div class="canvas-stamp">01 <span>/</span> 05</div>`;
    } else {
      canvas.className = "preview-canvas empty-design";
      canvas.innerHTML = '<div class="canvas-grid"></div><div class="empty-poster"><div class="poster-kicker">面向水岸的公共空间</div><div class="poster-title">一座开放、<br><em>轻盈的公共客厅。</em></div><div class="poster-rule"></div><div class="poster-foot"><span>60° 00′ N<br>滨水场地</span><span>方案研究<br>CODEX 大脑</span></div><div class="poster-sketch"><svg viewBox="0 0 510 220" aria-hidden="true"><path d="M13 184H497M44 178V93H156V178M175 178V66H281V178M301 178V106H457V178" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M44 94L81 62L156 94M175 67L217 36L281 67M301 107L356 78L457 107M0 204H510" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="4 6"/></svg></div></div><div class="canvas-stamp">01 <span>/</span> 05</div>';
    }
  } else if (state.tab === "model") {
    title.textContent = "可编辑模型";
    caption.textContent = "SketchUp 真实几何 · 稳定对象名称";
    meta.textContent = objects.length ? `${objects.length} 个对象 · ${modelStatusLabels[project.model_state.status] || project.model_state.status}` : project.agent_session?.status === "ready" ? `${project.agent_session.model || "Codex Agent"} · 自由几何` : "等待启动 Agent 模型会话";
    const image = capture ? `<img class="preview-image" src="${capture.url}" alt="SketchUp 视口截图">` : '<div class="preview-canvas empty-design"><div class="canvas-grid"></div><div class="empty-poster"><div class="poster-kicker">真实几何</div><div class="poster-title">模型将在<br><em>SketchUp 中生成。</em></div><div class="poster-rule"></div><div class="poster-foot"><span>稳定对象 ID<br>可编辑分组</span><span>准备后开始建模</span></div></div></div>';
    const chips = objects.map((item) => `<span class="model-object-chip"><b>${escapeHtml(item.stable_id)}</b>${escapeHtml(item.name)}</span>`).join("");
    canvas.className = "preview-canvas model-preview-content";
    canvas.innerHTML = `${image}${objects.length ? `<div class="model-summary">${chips}</div>` : ""}`;
  } else if (state.tab === "drawing") {
    title.textContent = "场地图纸";
    caption.textContent = "由同一份 DesignIR 生成基础 DXF";
    meta.textContent = drawing ? "场地 · 建筑体块 · 公共流线" : "等待生成方案";
    canvas.className = "preview-canvas";
    canvas.innerHTML = drawing ? `<img class="drawing-preview" src="${drawing.url}" alt="场地图纸预览"><div class="canvas-stamp">XY <span>/</span> M</div>` : '<div class="preview-canvas empty-design"><div class="canvas-grid"></div><div class="empty-poster"><div class="poster-kicker">图纸适配器</div><div class="poster-title">清晰、真实比例的<br><em>基础图纸。</em></div><div class="poster-rule"></div><div class="poster-foot"><span>场地边界<br>体块轮廓</span><span>DXF · 米制</span></div></div></div>';
  } else if (state.tab === "render") {
    title.textContent = "视口渲染";
    caption.textContent = "SketchUp 视口截图 · RenderAdapter 当前回退方案";
    meta.textContent = capture ? "SketchUp 实时截图" : "模型建立后生成截图";
    canvas.className = "preview-canvas";
    canvas.innerHTML = capture ? `<img class="preview-image" src="${capture.url}" alt="SketchUp 视口渲染"><div class="canvas-stamp">SU <span>/</span> LIVE</div>` : '<div class="preview-canvas empty-design"><div class="canvas-grid"></div><div class="empty-poster"><div class="poster-kicker">渲染适配器</div><div class="poster-title">直接来自<br><em>真实模型的视角。</em></div><div class="poster-rule"></div><div class="poster-foot"><span>SKETCHUP 视口<br>当前无需图像 API</span><span>渲染回退方案</span></div></div></div>';
  } else {
    title.textContent = "A3 排版";
    caption.textContent = "横版展示预览 · HTML";
    meta.textContent = board ? "A3 横版 · 已生成" : "生成方案后自动创建";
    canvas.className = "preview-canvas";
    canvas.innerHTML = board ? `<iframe class="preview-frame" title="A3 排版预览" src="${board.url}"></iframe>` : '<div class="preview-canvas empty-design"><div class="canvas-grid"></div><div class="empty-poster"><div class="poster-kicker">A3 横版</div><div class="poster-title">把整个项目，<br><em>放进一张版面。</em></div><div class="poster-rule"></div><div class="poster-foot"><span>概念<br>图纸 + 模型</span><span>HTML 预览</span></div></div></div>';
  }
}

async function loadProject(projectId) {
  state.projectId = projectId;
  state.project = await api(`/api/projects/${encodeURIComponent(projectId)}`);
  updateHeader();
  setStatus(state.project.design_ir ? "方案和场地图纸已准备完成。" : "工作区已就绪。上传参考图片，打开空白副本后即可开始复刻。");
}

async function boot() {
  try {
    const [runtime, projects] = await Promise.all([api("/api/status"), api("/api/projects")]);
    state.nativeAgentAvailable = !!runtime.native_agent_available;
    state.modelRouter = runtime.model_router || null;
    refreshTierLabels();
    const economyRoute = routeInfo("economy");
    const premiumRoute = routeInfo("premium");
    const routeStatus = routeAvailable("economy")
      ? `Economy · ${economyRoute.model} · ${(economyRoute.reasoning_effort || "low").toUpperCase()} 已就绪`
      : routeAvailable("premium") ? `Economy 未配置 · 精修 ${premiumRoute.model} 可用` : "本地模型提供方尚未配置";
    $("brain-status").textContent = `建筑 Agent · ${routeStatus}`;
    $("brain-status").previousElementSibling.classList.toggle("ready", state.nativeAgentAvailable);
    if (projects.length) await loadProject(projects[0].project_id);
  } catch (error) {
    showToast(friendlyError(error), true);
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
    showToast(`${result.filename} 已保存到当前项目的本地输入目录。`);
  } catch (error) { showToast(friendlyError(error), true); }
}

async function prepareDesign() {
  if (state.busy) return;
  state.busy = true;
  const button = $("prepare-design");
  setBusy(button, true, "Codex 正在分析…");
  $("build-model").disabled = true;
  setStatus("Codex 正在把你的资料整理成 DesignIR 和 BuildPlan。");
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
      $("prepare-note").textContent = `任务 ${result.job.job_id} 已生成，等待当前 Codex 会话处理。`;
      setStatus("Codex 任务模式：请求包已保存，等待返回结构化 DesignIR 和 BuildPlan。");
      showToast("当前无法直接调用 Codex CLI，已保存可继续执行的任务包。", true);
    } else {
      state.project = result.project;
      updateHeader();
      const warnings = result.reference_warnings || [];
      setStatus(warnings.length ? "方案已生成；参考网页无法读取，请上传网页截图或参考图片。" : "Codex 已返回有效方案，场地图纸和 A3 预览已生成。");
      $("prepare-note").textContent = warnings.length ? "参考网页暂时无法读取，请上传网页截图或参考图片。" : "已更新结构化方案和场地图纸。";
      showToast(warnings.length ? "方案已生成。参考网页无法读取，请上传网页截图或参考图片。" : "方案、DXF、图纸预览和 A3 展板已创建。");
      setTab("design");
    }
  } catch (error) {
    setStatus(friendlyError(error), "error");
    showToast(friendlyError(error), true);
  } finally {
    state.busy = false;
    setBusy(button, false);
    updateHeader();
  }
}

async function checkConnector() {
  if (!state.projectId) return;
  $("connector-state").textContent = "正在检查…";
  try {
    const result = await api(`/api/projects/${encodeURIComponent(state.projectId)}/connector`);
    $("connector-state").textContent = result.reachable ? "已连接 · SketchUp" : "本地桥接未响应";
    $("connector-state").style.color = result.reachable ? "#557568" : "#a0523a";
    setStatus(result.reachable ? "现有 SketchUp MCP 与本地桥接已正常响应。" : friendlyError(new Error(result.detail || "")), result.reachable ? "ready" : "error");
    if (result.reachable) showToast("现有 SketchUp MCP 与本地桥接连接正常。");
    else showToast(friendlyError(new Error(result.detail || "")), true);
  } catch (error) { $("connector-state").textContent = "不可用"; showToast(friendlyError(error), true); }
}

async function startAgentSession() {
  if (!state.projectId || state.busy || !state.nativeAgentAvailable) return;
  state.busy = true;
  const button = $("start-agent-session");
  setBusy(button, true, "正在启动 SketchUp 空白副本…");
  setStatus("正在复制 SketchUp Simple 模板，并校验活动模型路径。原始模型不会参与本次会话。");
  try {
    const result = await api(`/api/projects/${encodeURIComponent(state.projectId)}/agent/session`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ confirm_disposable_model: true }),
    });
    state.project = result.project;
    updateHeader();
    setTab("model");
    setStatus("项目专属空白副本已校验；现在可以用自然语言要求 Agent 建模。", "ready");
    showToast("Codex Agent 已连接到项目专属 SketchUp 空白副本。", false);
  } catch (error) {
    setStatus(friendlyError(error), "error");
    showToast(friendlyError(error), true);
  } finally {
    state.busy = false;
    setBusy(button, false);
    updateHeader();
  }
}

async function buildModel() {
  if (state.busy) return;
  if (!$("disposable-confirm").checked) return showToast("请先打开一个空白或可丢弃的 SketchUp 模型。", true);
  state.busy = true;
  const button = $("build-model");
  setBusy(button, true, "正在建立可编辑模型…");
  setStatus("正在通过现有 SketchUp MCP 执行确认后的 BuildPlan。");
  try {
    const result = await api(`/api/projects/${encodeURIComponent(state.projectId)}/build`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ confirm_disposable_model: true }),
    });
    state.project = result.project;
    updateHeader();
    setTab("model");
    setStatus(`SketchUp 回读完成 · 已在当前模型中创建 ${result.completed_ids.length} 个命名对象。`);
    showToast("可编辑 SketchUp 模型已建立并保存，可以继续连续修改。");
  } catch (error) {
    setStatus(friendlyError(error), "error");
    showToast(friendlyError(error), true);
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
  setBusy(button, true, "正在规划并修改…");
  setStatus("Codex 正在根据当前模型状态规划一次定向修改。");
  try {
    const result = await api(`/api/projects/${encodeURIComponent(state.projectId)}/edit`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ instruction }),
    });
    state.project = result.project;
    updateHeader();
    setTab("model");
    setStatus(`${result.edit_plan.target_id} 已原位修改，并完成连接器回读和视口截图。`);
    showToast(`已修改 ${result.edit_plan.target_id}，没有重新生成整个模型。`);
  } catch (error) {
    setStatus(friendlyError(error), "error");
    showToast(friendlyError(error), true);
  } finally {
    state.busy = false;
    setBusy(button, false);
    updateHeader();
  }
}

async function sendConversation(event) {
  event.preventDefault();
  const message = $("conversation-input").value.trim();
  if (!message || state.busy) return;
  state.busy = true;
  const button = $("conversation-send");
  const requestedTier = $("conversation-tier").value;
  const route = routeInfo(requestedTier);
  setBusy(button, true, `${requestedTier === "premium" ? "精修" : "Economy"} · ${route.model} 处理中…`);
  const built = state.project?.agent_session?.status === "ready";
  setStatus(built ? "建筑 Agent 正在查看当前模型并执行这一轮自然语言设计任务。" : "建筑 Agent 正在根据项目资料讨论设计；此时 SketchUp 工具保持关闭。");
  try {
    const result = await api(`/api/projects/${encodeURIComponent(state.projectId)}/conversation`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        tier: requestedTier,
        workflow_mode: $("workflow-mode").value,
        project_name: $("project-name").value,
        brief: $("brief").value,
        site_note: $("site-note").value,
        reference_url: $("reference-url").value,
        user_intent: $("intent").value,
      }),
    });
    state.project = result.project;
    $("conversation-input").value = "";
    $("conversation-tier").value = "economy";
    updateHeader();
    setStatus(result.reply);
    const calls = result.agent?.tool_calls?.length || 0;
    const agent = result.agent || {};
    showToast((agent.tier === "premium" ? "精修" : "Economy") + " · " + (agent.model || "Agent")
      + " 已处理" + (built ? "当前模型" + (calls ? " · " + (agent.tool_call_count || calls) + " 次工具调用" : "") : "设计讨论") + "。", false);
    if (agent.premium_rescue_pending && requestedTier === "economy") {
      showToast("普通档连续遇到工具问题；如需使用 Astra Low，请显式选择精修。", true);
    }
    if (built) setTab("model");
  } catch (error) {
    setStatus(friendlyError(error), "error");
    showToast(friendlyError(error), true);
  } finally {
    state.busy = false;
    setBusy(button, false);
    updateHeader();
  }
}

document.querySelectorAll("[data-tab]").forEach((button) => button.addEventListener("click", () => setTab(button.dataset.tab)));
$("conversation-form").addEventListener("submit", sendConversation);
$("conversation-input").addEventListener("input", () => {
  $("conversation-send").disabled = state.busy || !routeAvailable($("conversation-tier").value) || !$("conversation-input").value.trim();
});
$("conversation-tier").addEventListener("change", updateHeader);
$("workflow-mode").addEventListener("change", () => {
  const reconstruction = $("workflow-mode").value === "image_reconstruction";
  $("workflow-help").textContent = reconstruction
    ? "上传参考图片 → 打开空白副本 → 发送复刻要求。Agent 会建模、看截图并修正，无需任务书或场地。"
    : "结合任务书、场地与参考资料讨论建筑方案，启动空白模型后继续建模。";
  $("conversation-input").placeholder = reconstruction
    ? "按这张图尽可能还原成可编辑 SketchUp 模型"
    : "输入设计方向或模型修改要求…";
});
$("start-agent-session").addEventListener("click", startAgentSession);
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
    showToast("新的本地项目已创建，请继续添加场地说明和设计想法。");
  } catch (error) { showToast(friendlyError(error), true); }
});

boot();
