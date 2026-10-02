const state = { projectId: null, project: null, tab: "design", busy: false, toastTimer: null, nativeAgentAvailable: false, modelRouter: null, planEditing: false };
const $ = (id) => document.getElementById(id);
let projectList = [];
let pendingMessage = null;
let progressTimer = null;
let liveProgressTimer = null;
let progressGeneration = 0;
let planRequestId = 0;

function sourceImages() {
  return (state.project?.context?.references || []).filter((ref) => ref.type === "image" && ref.source.startsWith("inputs/reference/"));
}

function projectFileUrl(path) {
  return `/api/projects/${encodeURIComponent(state.projectId)}/files/${path.split("/").map(encodeURIComponent).join("/")}`;
}

async function refreshProjects() {
  const projects = await api("/api/projects");
  projectList = projects;
  $("project-select").innerHTML = projects.map((project) => `<option value="${escapeHtml(project.project_id)}">${escapeHtml(project.project_name)}</option>`).join("");
  if (state.projectId) $("project-select").value = state.projectId;
  renderProjectHistory();
  return projects;
}

function renderProjectHistory() {
  $("session-count").textContent = projectList.length;
  $("project-history").innerHTML = projectList.map((p) => `<div class="history-row"><button class="history-item${p.project_id === state.projectId ? " active" : ""}" data-project="${escapeHtml(p.project_id)}" title="${escapeHtml(p.project_name)}" ${state.busy ? "disabled" : ""}><span>◷</span><span>${escapeHtml(p.project_name)}</span></button><button class="delete-label" data-delete-project="${escapeHtml(p.project_id)}" aria-label="删除项目 ${escapeHtml(p.project_name)}" ${state.busy ? "disabled" : ""}>删除</button></div>`).join("");
}

function showResults(open) {
  $("result-panel").hidden = !open;
  $("result-toggle").setAttribute("aria-expanded", String(open));
}

function chatText(content) {
  const readable = content.replace(/\[([^\]]+)\]\(<?[^)]*\[本机路径已隐藏\][^)]*\)/g, "$1（请从「模型与文件」查看）");
  const md = window.markdownit({html: false, breaks: true, linkify: false});
  const linkOpen = md.renderer.rules.link_open || ((tokens, i, options, env, self) => self.renderToken(tokens, i, options));
  md.renderer.rules.link_open = (tokens, i, options, env, self) => {
    const href = tokens[i].attrGet("href") || "";
    if (/^(notes|scripts)\/[a-zA-Z0-9_./-]+$/.test(href) && !href.includes("..")) tokens[i].attrSet("href", projectFileUrl("runtime/agent_workspace/" + href));
    else if (!/^https?:\/\//i.test(href)) tokens[i].attrSet("href", "#");
    tokens[i].attrSet("target", "_blank"); tokens[i].attrSet("rel", "noopener noreferrer");
    return linkOpen(tokens, i, options, env, self);
  };
  md.renderer.rules.image = (tokens, i) => escapeHtml(tokens[i].content || "图片请从模型与文件查看");
  return md.render(readable);
}

function beginProgress(label) {
  const started = Date.now();
  $("operation-progress").hidden = false;
  const refresh = () => { $("operation-progress").textContent = `${label} · 已等待 ${Math.floor((Date.now() - started) / 1000)} 秒。可能需要数分钟，请勿重复提交或刷新页面。`; };
  refresh();
  clearInterval(progressTimer);
  progressTimer = setInterval(refresh, 1000);
  updateHeader();
}

function endProgress() {
  clearInterval(progressTimer);
  clearInterval(liveProgressTimer); progressGeneration++;
  $("operation-progress").hidden = true;
}

async function loadParameterPlan() {
  const requestId = ++planRequestId;
  const projectId = state.projectId;
  const visible = ["planned", "building"].includes(state.project?.agent_session?.reconstruction_state);
  $("parameter-plan").hidden = !visible;
  $("parameter-plan-content").textContent = "正在读取计划…";
  if (!visible) return;
  try {
    const card = await api(projectFileUrl("runtime/agent_workspace/notes/reconstruction_card.md"));
    if (requestId === planRequestId && projectId === state.projectId) $("parameter-plan-content").innerHTML = chatText(card);
  } catch (_) {
    if (requestId === planRequestId) $("parameter-plan-content").textContent = "参数文件暂时无法读取，请查看下方 AI 的计划回复后再决定是否批准。";
  }
}

function routeInfo(tier) {
  const fallback = tier === "premium"
    ? { model: "gpt-6-astra", provider: "codex-app-server" }
    : { model: "gpt-6.1-sol", reasoning_effort: "low", provider: "codex-app-server" };
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
  economy.textContent = `${economyRoute.model} · ${(economyRoute.reasoning_effort || "low").toUpperCase()}${routeAvailable("economy") ? "" : " · 未配置"}`;
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
    if (/has not opened the recovery copy/i.test(message)) return "请切换到 SketchUp，处理恢复副本时的保存提示，再点击恢复按钮完成同步；原生成模型已保留。";
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
  $("agent-error").hidden = !agent.error || state.busy;
  $("agent-error").textContent = agent.error ? "上轮未正常完成。已保留项目记录；请查看模型。模型异常时，打开「模型与文件」恢复上轮修改前的模型，再继续。" : "";
  const agentReady = agent.status === "ready" && !!agent.model_path;
  const reconstructionMode = $("workflow-mode").value === "image_reconstruction";
  document.body.classList.toggle("reconstruction-mode", reconstructionMode);
  document.querySelector('.tab-button[data-tab="design"]').childNodes[0].textContent = reconstructionMode ? "图片与计划 " : "方案设计 ";
  $("project-select").disabled = state.busy;
  $("new-project").disabled = state.busy;
  $("conversation-input").disabled = state.busy;
  $("recover-agent-checkpoint").hidden = state.project?.agent_session?.reconstruction_state !== "building";
  $("recover-agent-checkpoint").disabled = state.busy;
  renderProjectHistory();
  for (const id of ["workflow-mode", "conversation-tier", "reference-file", "brief-file", "site-file", "project-name"]) $(id).disabled = state.busy;
  $("reference-status").hidden = reconstructionMode;
  $("reconstruction-guide").hidden = !reconstructionMode;
  $("reference-files").innerHTML = sourceImages().map((ref) => `<span class="file-chip">${escapeHtml(ref.source.split("/").at(-1))}</span>`).join("");
  $("reference-gallery").innerHTML = sourceImages().map((ref) => `<div class="image-item"><a href="${projectFileUrl(ref.source)}" title="${escapeHtml(ref.source.split('/').at(-1))}" target="_blank" rel="noreferrer"><img src="${projectFileUrl(ref.source)}" alt="${escapeHtml(ref.source.split('/').at(-1))}"><span>查看原图 ↗</span></a><button class="delete-label" data-delete-image="${escapeHtml(ref.source)}" aria-label="删除图片 ${escapeHtml(ref.source.split('/').at(-1))}" ${state.busy ? "disabled" : ""}>删除</button></div>`).join("");
  $("project-title").textContent = context.project_name;
  $("project-name").value = context.project_name;
  $("sidebar-project-name").textContent = context.project_name.replace(" · ", " ");
  $("sidebar-project-status").textContent = modelStatusLabels[model.status] || String(model.status || "").replaceAll("_", " ");
  $("project-subtitle").textContent = reconstructionMode ? "图片复刻 · 分析、确认计划、建模与连续修改" : project.design_ir?.concept?.summary || context.site.summary || "添加项目资料，开始方案讨论。";
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
  status.innerHTML = `<i></i> ${agentReady ? "已有项目模型" : built ? "模型已建立" : prepared ? "方案已生成" : "输入已就绪"}`;
  $("build-model").disabled = !prepared || !$("disposable-confirm").checked || state.busy || built;
  $("edit-height").disabled = !built || state.busy || !project.design_ir?.objects.some((item) => item.type === "building_mass");
  const masses = (model.objects || []).filter((item) => item.object_type === "building_mass");
  const editedCount = masses.filter((item) => item.last_change).length;
  $("edit-count").textContent = `${Math.min(editedCount, 2)} / 2`;
  $("edit-position").disabled = !built || state.busy || editedCount < 1 || masses.length < 2 || !!masses[1]?.last_change;
  $("edit-height").disabled = !built || state.busy || !masses.length || !!masses[0]?.last_change;
  $("agent-session-state").textContent = agentReady
    ? `已绑定项目独立模型 · ${agent.model_path.split("/").at(-1)}。实时连接请通过检查连接确认。`
    : agent.status === "conversation" ? "Agent 对话已建立 · SketchUp 建模工具尚未启用" : "尚未打开项目专属空白副本";
  $("start-agent-session").disabled = state.busy || !routeAvailable("economy");
  if (!state.busy) $("start-agent-session").querySelector("span:first-child").textContent = agentReady ? "重连 SketchUp" : "连接 SketchUp";
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
  const reconstruction = $("workflow-mode").value === "image_reconstruction";
  const reconstructionState = agent.reconstruction_state || "idle";
  $("reconstruction-state").hidden = !reconstruction;
  $("reconstruction-state").textContent = state.busy ? "正在处理，请等待" : {idle: "待分析", clarifying: "等待补充信息", planned: "等待批准", building: "已有模型 · 可继续修改"}[reconstructionState] || "待分析";
  const hasImages = sourceImages().length > 0;
  $("prepare-plan").hidden = reconstructionState !== "clarifying";
  $("prepare-plan").disabled = state.busy;
  $("model-settings-toggle").disabled = state.busy;
  renderAttachments();
  $("conversation-send").disabled = state.busy || !routeAvailable($("conversation-tier").value) || (!$("conversation-input").value.trim() && !(reconstruction && reconstructionState === "idle" && hasImages));
  $("next-step").textContent = !hasImages ? "下一步：上传建筑参考图片。" : {idle: "下一步：描述目标或直接点击「分析图片」。", clarifying: "下一步：回答 AI 的问题；若信息已齐全，输入「按上述要求生成计划」。", planned: agentReady ? "下一步：查看参数计划，修改不合适的估算，或批准并开始建模。" : "下一步：查看计划，然后打开项目模型，再批准建模。", building: "下一步：查看模型截图或下载 SKP；在对话中输入具体修改要求。"}[reconstructionState];
  $("revise-reconstruction-plan").hidden = !reconstruction || !["planned", "building"].includes(reconstructionState);
  $("revise-reconstruction-plan").disabled = state.busy;
  $("approve-reconstruction").hidden = !reconstruction || reconstructionState !== "planned";
  $("approve-reconstruction").disabled = state.busy || !routeAvailable($("conversation-tier").value);
  if (!state.busy) $("conversation-send").querySelector("span:first-child").textContent = state.planEditing ? "更新参数计划" : !reconstruction ? "发送消息" : {idle: "发送", clarifying: "继续交流", planned: "继续交流 / 更新计划", building: "发送修改要求"}[reconstructionState];
  $("conversation-send").setAttribute("aria-label", $("conversation-send").querySelector("span:first-child").textContent);
  $("conversation-send").title = $("conversation-send").getAttribute("aria-label");
  if (reconstruction) $("conversation-hint").textContent = reconstructionState === "planned"
    ? agentReady ? "计划已生成。点击批准执行后，Agent 将开始建模。" : "计划已生成。点击批准后按引导连接 SketchUp，再开始建模。"
    : reconstructionState === "building" ? "继续修改同一份模型；Agent 将查看截图并修正。" : "先聊天、补充资料；信息确认后点击「整理建模计划」。批准之前不会改动 SU。";
  for (const id of ["brief", "site-note", "intent"]) $(id).closest(".input-block").hidden = reconstruction;
  $("reference-url").hidden = reconstruction;
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
  const messages = [...(state.project?.context?.conversation || [])];
  if (pendingMessage) messages.push({role: "user", content: pendingMessage, phase: "agent", metadata: {}});
  const history = $("conversation-history");
  if (!messages.length) {
    history.innerHTML = '<div class="welcome"><div class="welcome-symbol">◇</div><h2>把建模交给 AI</h2><p>图片、文字或任务资料都可以。简单说你想做什么，AI 会帮你补充确认。</p><div class="suggestions"><button class="suggestion" data-prompt="按参考图片还原建筑，保留屋顶、窗洞与立面细节。">从图片还原建筑</button><button class="suggestion" data-prompt="没有实测尺寸，请按图像比例估算并标明，允许推断背面。">估算尺寸与补全背面</button><button class="suggestion" data-prompt="请生成可编辑 SketchUp 模型，检查正面、背面和侧面截图。">多角度检查与修改</button></div></div>';
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
      + speaker + "</span><span>" + phase + '</span></header><div class="markdown-content">' + chatText(message.content)
      + "</div>" + (detail ? '<details><summary>本轮记录</summary>' + detail + '</details>' : "") + "</article>";
  }).join("");
  if (pendingMessage) history.insertAdjacentHTML("beforeend", '<article class="chat-message assistant pending-reply"><header><span>建筑 Agent</span></header><p>正在查看参考图片、处理本轮要求，请稍候…</p></article>');
  history.scrollTop = history.scrollHeight;
}

function setStage(stage, complete) {
  const indicator = $(`stage-${stage}`);
  indicator.textContent = complete ? "●" : "○";
  indicator.classList.toggle("complete", complete);
}

function renderArtifacts() {
  const hasGeometry = Object.values(state.project?.agent_session?.ruby_state || {}).some(item => item.revision > 0) || (state.project?.model_state?.objects || []).length > 0;
  const artifacts = allArtifacts().filter(item => item.type !== "skp" || hasGeometry)
    .filter(item => item.type !== "skp" || !state.project?.model_state?.model_path || item.path === state.project.model_state.model_path);
  const unique = [...new Map(artifacts.map((item) => [item.path, item])).values()];
  $("artifact-total").textContent = `${unique.length} 个文件`;
  const container = $("artifact-list");
  if (!unique.length) {
    container.innerHTML = '<div class="artifact-empty">建模后，截图和 SKP 文件会显示在这里。</div>';
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
  const skp = hasGeometry ? artifactByType("skp") : null;
  $("artifact-links").innerHTML = [
    skp ? `<a class="artifact-link" href="${skp.url}" download>↓ 下载 SKP</a>` : "",
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
  if (state.tab === "design" && $("workflow-mode").value === "image_reconstruction") {
    title.textContent = "参考图片与目标";
    caption.textContent = "以图片为外观目标 · 未知尺寸会标记为估算";
    meta.textContent = `${sourceImages().length} 张参考图片`;
    canvas.className = "preview-canvas";
    canvas.innerHTML = sourceImages().length ? `<div class="reference-sheet">${sourceImages().map((ref)=>`<a href="${projectFileUrl(ref.source)}" target="_blank" rel="noreferrer"><img src="${projectFileUrl(ref.source)}" alt="${escapeHtml(ref.source.split('/').at(-1))}"><span>${escapeHtml(ref.source.split('/').at(-1))}</span></a>`).join("")}</div>` : '<div class="reconstruction-empty"><span>IMAGE → SKETCHUP</span><h2>从一张建筑图片开始</h2><p>上传参考图，AI 会先分析并确认建模计划。<br>批准后在独立 SketchUp 模型中执行。</p></div>';
    return;
  }
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
    const views = [...new Map(allArtifacts().filter(item => item.type === "viewport").map(item => [item.path, item])).values()].slice(-12);
    const gallery = views.length > 1 ? `<div class="model-view-gallery" aria-label="历史检查截图">${views.map((item, i) => `<a href="${item.url}" target="_blank" rel="noreferrer" title="查看模型截图 ${i + 1}"><img src="${item.url}" alt="历史检查截图 ${i + 1}" loading="lazy"></a>`).join("")}</div>` : "";
    canvas.innerHTML = `${image}${gallery}${objects.length ? `<div class="model-summary">${chips}</div>` : ""}`;
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
  state.planEditing = false;
  state.projectId = projectId;
  state.project = await api(`/api/projects/${encodeURIComponent(projectId)}`);
  localStorage.setItem("architecture-studio-project", projectId);
  $("project-select").value = projectId;
  $("conversation-input").value = "";
  $("parameter-plan").open = false;
  await loadParameterPlan();
  state.tab = artifactByType("viewport") ? "model" : "design";
  setTab(state.tab);
  updateHeader();
  setStatus(state.project.agent_session?.reconstruction_state === "building" ? "已有模型。可查看截图、下载 SKP 或发送修改要求。" : state.project.design_ir ? "方案和场地图纸已准备完成。" : "工作区已就绪。上传参考图片并分析，确认计划后再开始建模。");
}

async function boot() {
  try {
    const [runtime, projects] = await Promise.all([api("/api/status"), refreshProjects()]);
    state.nativeAgentAvailable = !!runtime.native_agent_available;
    state.modelRouter = runtime.model_router || null;
    refreshTierLabels();
    const economyRoute = routeInfo("economy");
    const premiumRoute = routeInfo("premium");
    const routeStatus = routeAvailable("economy")
      ? `Economy · ${economyRoute.model} · ${(economyRoute.reasoning_effort || "low").toUpperCase()} 已就绪`
      : routeAvailable("premium") ? `Economy 未配置 · 精修 ${premiumRoute.model} 可用` : "本地模型提供方尚未配置";
    $("brain-status").textContent = `建筑 Agent · ${routeStatus}`;
    document.querySelector(".signal-dot").classList.toggle("ready", state.nativeAgentAvailable);
    const savedId = localStorage.getItem("architecture-studio-project");
    if (projects.length) await loadProject(projects.some((p) => p.project_id === savedId) ? savedId : projects[0].project_id);
  } catch (error) {
    showToast(friendlyError(error), true);
  }
}

async function uploadFile(category, file, targetId, manageBusy = true) {
  if (!state.projectId || !file || (manageBusy && state.busy)) return false;
  if (manageBusy) { state.busy = true; updateHeader(); }
  try {
    const url = `/api/projects/${encodeURIComponent(state.projectId)}/inputs/${category}?filename=${encodeURIComponent(file.name)}`;
    const result = await api(url, { method: "POST", headers: { "Content-Type": file.type || "application/octet-stream" }, body: file });
    const chip = document.createElement("span");
    chip.className = "file-chip";
    chip.title = result.path;
    chip.textContent = result.filename;
    $(targetId).append(chip);
    state.project = await api(`/api/projects/${encodeURIComponent(state.projectId)}`);
    showToast(`${result.filename} · ${result.read_status || "已上传"}`);
    return true;
  } catch (error) { showToast(friendlyError(error), true); return false; }
  finally { if (manageBusy) { state.busy = false; updateHeader(); } }
}

async function uploadReferences(files) {
  if (!state.projectId || state.busy || !files.length) return;
  if (files.length + sourceImages().length > 8) { showToast("每个会话最多使用 8 张参考图，避免超出模型的输入范围。请减少本次选择的图片数量。", true); $("reference-file").value = ""; return; }
  state.busy = true;
  let completed = 0;
  beginProgress(`正在上传 ${files.length} 张参考图片`);
  try {
    for (const file of files) {
      const ok = await uploadFile("reference", file, "reference-files", false);
      if (ok) completed++;
      updateHeader();
    }
    showToast(`已上传 ${completed} / ${files.length} 张参考图片${completed < files.length ? "，失败的图片请重新上传" : "。请描述建模要求后发送"}。`, completed < files.length);
  } finally { endProgress(); state.busy = false; $("reference-file").value = ""; updateHeader(); }
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
  if (!state.projectId || state.busy || !routeAvailable("economy")) return;
  state.busy = true;
  const button = $("start-agent-session");
  setBusy(button, true, "正在启动 SketchUp 空白副本…");
  beginProgress("正在打开项目模型并连接 SketchUp");
  setStatus("正在复制 SketchUp Simple 模板，并校验活动模型路径。原始模型不会参与本次会话。");
  try {
    const result = await api(`/api/projects/${encodeURIComponent(state.projectId)}/agent/session`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ confirm_disposable_model: true }),
    });
    state.project = result.project;
    updateHeader();
    setTab("model");
    showResults(false);
    setStatus("项目专属空白副本已校验；现在可以用自然语言要求 Agent 建模。", "ready");
    showToast("Codex Agent 已连接到项目专属 SketchUp 空白副本。", false);
  } catch (error) {
    setStatus(friendlyError(error), "error");
    showToast(friendlyError(error), true);
  } finally {
    endProgress();
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

async function sendConversation(event, agentAction = "auto") {
  event?.preventDefault();
  if (agentAction === "auto" && state.planEditing) agentAction = "plan";
  if (agentAction === "execute" && state.project?.agent_session?.status !== "ready") { $("connect-dialog").showModal(); return; }
  const message = agentAction === "execute" ? ($("conversation-input").value.trim() || "批准执行当前建模计划；完成后按原图视角检查并修正明显差异。") : $("conversation-input").value.trim() || ((state.project?.agent_session?.reconstruction_state || "idle") === "idle" && sourceImages().length ? "请分析这张建筑图片，先确认建模目标与关键未知项。" : "");
  if (!message || state.busy) return;
  pendingMessage = message;
  state.busy = true;
  const button = $("conversation-send");
  const requestedTier = $("conversation-tier").value;
  const route = routeInfo(requestedTier);
  setBusy(button, true, `${requestedTier === "premium" ? "精修" : "Economy"} · ${route.model} 处理中…`);
  const built = state.project?.agent_session?.status === "ready";
  const reconstruction = $("workflow-mode").value === "image_reconstruction";
  const resolvedAction = agentAction;
  const executesModel = agentAction === "execute" || (agentAction === "auto" && state.project?.agent_session?.reconstruction_state === "building");
  if (executesModel) showResults(true);
  beginProgress(executesModel ? "正在建模与检查截图" : "正在分析图片与建模计划");
  $("approve-reconstruction").disabled = true;
  setStatus(reconstruction && !executesModel ? "正在分析图片与建模参数，SketchUp 不会被修改。" : "Agent 正在建模/修改并检查截图。");
  try {
    startLiveProgress();
    const result = await api(`/api/projects/${encodeURIComponent(state.projectId)}/conversation`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        tier: requestedTier,
        workflow_mode: $("workflow-mode").value,
        agent_action: resolvedAction,
      }),
    });
    state.project = result.project;
    pendingMessage = null;
    state.planEditing = false;
    await loadParameterPlan();
    $("conversation-input").value = "";
    $("conversation-tier").value = "economy";
    updateHeader();
    setStatus(result.reply);
    const calls = result.agent?.tool_calls?.length || 0;
    const agent = result.agent || {};
    showToast((agent.tier === "premium" ? "精修" : "Economy") + " · " + (agent.model || "Agent")
      + " 已处理" + (agent.agent_action === "clarify" ? "图片澄清" : agent.agent_action === "plan" ? "建模计划，等待批准" : built ? "当前模型" + (calls ? " · " + (agent.tool_call_count || calls) + " 次工具调用" : "") : "设计讨论") + "。", false);
    if (agent.agent_action === "execute") { setTab("model"); showResults(true); }
  } catch (error) {
    await loadProject(state.projectId).catch(() => {});
    $("conversation-input").value = message;
    setStatus(friendlyError(error), "error");
    showToast(friendlyError(error), true);
  } finally {
    pendingMessage = null;
    endProgress();
    state.busy = false;
    setBusy(button, false);
    updateHeader();
  }
}

document.querySelectorAll("[data-tab]").forEach((button) => button.addEventListener("click", () => setTab(button.dataset.tab)));
$("conversation-form").addEventListener("submit", sendConversation);
$("approve-reconstruction").addEventListener("click", (event) => sendConversation(event, "execute"));
$("revise-reconstruction-plan").addEventListener("click", () => {
  state.planEditing = true;
  updateHeader();
  $("conversation-input").placeholder = "例如：宽度改为 12 米；背面补窗；先只建主体。提交后重新确认计划。";
  $("conversation-input").focus();
  showToast("在对话框填写要修改的参数，然后点击「更新参数计划」。本轮不修改 SketchUp。");
});
$("conversation-input").addEventListener("input", () => {
  updateHeader();
});
$("conversation-tier").addEventListener("change", updateHeader);
$("workflow-mode").addEventListener("change", () => {
  const reconstruction = $("workflow-mode").value === "image_reconstruction";
  $("workflow-help").textContent = reconstruction
    ? "上传参考图片 → 分析并生成计划 → 打开空白副本 → 批准执行。分析阶段不会修改 SketchUp。"
    : "结合任务书、场地与参考资料讨论建筑方案，启动空白模型后继续建模。";
  $("conversation-input").placeholder = reconstruction
    ? "按这张图尽可能还原成可编辑 SketchUp 模型"
    : "输入设计方向或模型修改要求…";
  updateHeader();
});
$("start-agent-session").addEventListener("click", () => $("connect-dialog").showModal());
$("prepare-design").addEventListener("click", prepareDesign);
$("build-model").addEventListener("click", buildModel);
$("disposable-confirm").addEventListener("change", updateHeader);
$("check-connector").addEventListener("click", checkConnector);
$("brief-file").addEventListener("change", (event) => uploadFile("brief", event.target.files[0], "brief-files"));
$("site-file").addEventListener("change", (event) => uploadFile("site", event.target.files[0], "site-files"));
$("reference-file").multiple = true;
$("reference-file").addEventListener("change", (event) => uploadAttachments(Array.from(event.target.files)));
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
$("new-project").addEventListener("click", () => { $("create-project-form").reset(); $("project-dialog").showModal(); });
$("mobile-menu").addEventListener("click", () => {
  const open = document.body.classList.toggle("sidebar-open");
  $("mobile-menu").setAttribute("aria-expanded", String(open));
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    document.body.classList.remove("sidebar-open");
    $("mobile-menu").setAttribute("aria-expanded", "false");
    showResults(false);
  }
});
$("result-toggle").addEventListener("click", () => showResults($("result-panel").hidden));
$("result-close").addEventListener("click", () => { showResults(false); $("result-toggle").focus(); });
$("help-toggle").addEventListener("click", () => $("help-dialog").showModal());
$("help-close").addEventListener("click", () => $("help-dialog").close());
$("conversation-history").addEventListener("click", (event) => {
  const suggestion = event.target.closest("[data-prompt]");
  if (!suggestion || state.busy) return;
  $("conversation-input").value = suggestion.dataset.prompt;
  $("conversation-input").focus();
  updateHeader();
});
$("project-history").addEventListener("click", async (event) => {
  const removal = event.target.closest("[data-delete-project]");
  if (removal) { await deleteProject(removal.dataset.deleteProject); return; }
  const item = event.target.closest("[data-project]");
  if (!item || state.busy || item.dataset.project === state.projectId) return;
  state.busy = true;
  updateHeader();
  try { await loadProject(item.dataset.project); showResults(false); }
  catch (error) { showToast(friendlyError(error), true); }
  finally { state.busy = false; document.body.classList.remove("sidebar-open"); $("mobile-menu").setAttribute("aria-expanded", "false"); updateHeader(); }
});
$("cancel-project").addEventListener("click", () => $("project-dialog").close());
$("project-select").addEventListener("change", async (event) => {
  if (state.busy) return;
  try { await loadProject(event.target.value); setTab(state.tab); }
  catch (error) { showToast(friendlyError(error), true); }
});
$("create-project-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const name = $("new-project-name").value.trim();
  const initialGoal = $("new-project-brief").value.trim();
  if (!name || state.busy) return;
  state.busy = true;
  $("create-project-submit").disabled = true;
  updateHeader();
  try {
    const result = await api("/api/projects", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ project_name: name, brief: initialGoal }),
    });
    $("project-dialog").close();
    document.body.classList.remove("sidebar-open");
    $("mobile-menu").setAttribute("aria-expanded", "false");
    await refreshProjects();
    await loadProject(result.project_id);
    $("conversation-input").value = initialGoal;
    showToast("会话已创建。上传或粘贴资料，直接告诉 AI 你想做什么。");
  } catch (error) { showToast(friendlyError(error), true); }
  finally {
    state.busy = false;
    $("create-project-submit").disabled = false;
    updateHeader();
  }
});

boot();

$("recover-agent-checkpoint").addEventListener("click", async () => {
  if (state.busy) return;
  state.busy = true; updateHeader();
  try {
    const result = await api(`/api/projects/${encodeURIComponent(state.projectId)}/agent/recover`, {method: "POST"});
    state.project = result.project; showToast(result.reply); setStatus(result.reply);
  } catch (error) {
    state.project = await api(`/api/projects/${encodeURIComponent(state.projectId)}`).catch(() => state.project);
    showToast(friendlyError(error), true);
  }
  finally { state.busy = false; updateHeader(); }
});

function renderAttachments() {
  const context = state.project?.context || {};
  const files = [...(context.brief?.source_files || []), ...(context.site?.source_files || []),
    ...(context.references || []).filter(r => r.type === "note").map(r => r.source)];
  $("attachment-list").innerHTML = files.map(path => `<a class="file-chip" href="${projectFileUrl(path)}" target="_blank" rel="noopener">${escapeHtml(path.split("/").pop())}</a>`).join("");
}
async function uploadAttachments(files) {
  if (state.busy || !state.projectId || !files.length) return;
  const images = files.filter(f => f.type.startsWith("image/") || /\.(png|jpe?g|webp|gif|bmp|tiff?)$/i.test(f.name));
  if (images.length) await uploadReferences(images);
  const documents = files.filter(f => !images.includes(f));
  state.busy = true; updateHeader();
  try {
    for (const file of documents) {
      const category = /\.(dxf|dwg)$/i.test(file.name) ? "site" : "brief";
      await uploadFile(category, file, `${category}-files`, false);
    }
  } finally { state.busy = false; $("reference-file").value = ""; updateHeader(); }
}
$("conversation-input").addEventListener("paste", event => {
  const files = Array.from(event.clipboardData?.files || []);
  if (files.length) { event.preventDefault(); uploadAttachments(files); }
});
$("conversation-form").addEventListener("dragover", event => { event.preventDefault(); });
$("conversation-form").addEventListener("drop", event => { event.preventDefault(); uploadAttachments(Array.from(event.dataTransfer?.files || [])); });
$("prepare-plan").addEventListener("click", event => {
  if (!$("conversation-input").value.trim()) $("conversation-input").value = "信息已确认，请整理建模计划，标明估算与需要我确认的内容。";
  sendConversation(event, "plan");
});
$("connect-close").addEventListener("click", () => $("connect-dialog").close());
$("connect-check").addEventListener("click", async () => {
  $("connect-status").textContent = "正在检查本机连接…";
  try {
    const result = await api(`/api/projects/${encodeURIComponent(state.projectId)}/connector`);
    $("connect-status").textContent = result.reachable ? "MCP 已连接。下一步：打开本会话的独立模型。" : "连接未就绪：请在 SketchUp 扩展菜单启动 Kongxing Local Bridge，然后重试。";
  } catch (_) { $("connect-status").textContent = "连接未就绪，请检查 SketchUp 与插件是否已启动。"; }
});
$("connect-open").addEventListener("click", async () => {
  $("connect-dialog").close(); await startAgentSession();
});
function startLiveProgress() {
  const generation = ++progressGeneration;
  clearInterval(progressTimer);
  const refresh = async () => {
    try {
      const p = await api(`/api/projects/${encodeURIComponent(state.projectId)}/agent/progress`);
      if (generation !== progressGeneration || !state.busy || !p.running) return;
      $("operation-progress").textContent = `${p.stage} · ${p.elapsed_seconds} 秒 · 已调用 ${p.tool_calls} 次工具${p.failed_tool_calls ? `（${p.failed_tool_calls} 次失败）` : ""}${p.action !== "execute" ? " · 不改动 SketchUp" : p.committed_revisions.length ? " · SU 已提交实际模型修改" : " · 尚无新的模型提交"}`;
      if (p.preview_url) {
        $("preview-canvas").innerHTML = `<img src="${escapeHtml(p.preview_url)}" alt="建模中的最新 SketchUp 截图">`;
        $("preview-title").textContent = "建模中的真实截图";
      }
    } catch (_) { if (generation === progressGeneration) $("operation-progress").textContent = "进度暂时无法读取，当前回合仍在等待；请勿重复提交。"; }
  };
  refresh(); liveProgressTimer = setInterval(refresh, 3000);
}

$("model-settings-toggle").addEventListener("click", () => $("model-settings-dialog").showModal());
$("model-settings-close").addEventListener("click", () => { $("api-key").value = ""; $("model-settings-dialog").close(); });
$("provider-mode").addEventListener("change", () => $("byok-fields").hidden = $("provider-mode").value !== "byok");
$("model-settings-form").addEventListener("submit", async event => {
  event.preventDefault();
  $("model-settings-status").textContent = "正在设置连接…";
  try {
    state.modelRouter = await api("/api/model-settings", {method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({mode: $("provider-mode").value, model: $("api-model").value, api_base: $("api-base").value, api_key: $("api-key").value})});
    refreshTierLabels(); updateHeader(); $("brain-status").textContent = `建筑 Agent · ${routeInfo("economy").model} · ${routeAvailable("economy") ? "已就绪" : "未配置"}`; $("model-settings-dialog").close();
    showToast("模型连接已设置；尚未发送测试请求。下次交流将使用此模型。");
  } catch (error) { $("model-settings-status").textContent = friendlyError(error); }
  finally { $("api-key").value = ""; }
});

async function deleteProject(id) {
  if (state.busy) return;
  state.busy = true; updateHeader();
  try {
    await api(`/api/projects/${encodeURIComponent(id)}`, {method:"DELETE"});
    const projects = await refreshProjects();
    if (id === state.projectId) {
      if (projects.length) await loadProject(projects[0].project_id);
      else {
        const fresh = await api("/api/projects", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({project_name:"新建模会话"})});
        await refreshProjects(); await loadProject(fresh.project_id);
      }
    }
    showToast("项目已移入回收站，可以恢复。打开的 SU 模型不会被清空。");
  } catch(error) { showToast(friendlyError(error), true); }
  finally { state.busy = false; updateHeader(); }
}
$("reference-gallery").addEventListener("click", async event => {
  const button = event.target.closest("[data-delete-image]");
  if (!button || state.busy) return;
  state.busy = true; updateHeader();
  try {
    await api(`/api/projects/${encodeURIComponent(state.projectId)}/reference-image?path=${encodeURIComponent(button.dataset.deleteImage)}`, {method:"DELETE"});
    state.planEditing = false;
    await loadProject(state.projectId);
    showToast("图片已移入回收站；请重新整理建模计划。已有模型保持不变。");
  } catch(error) { showToast(friendlyError(error), true); }
  finally { state.busy = false; updateHeader(); }
});
async function showTrash() {
  const items = await api("/api/trash");
  $("trash-list").innerHTML = items.map(item => `<div class="trash-row"><span>${item.kind === "image" ? "图片" : "项目"} · ${escapeHtml(item.label)}</span><button class="button-quiet" data-restore="${item.id}">恢复</button></div>`).join("") || "回收站为空";
}
$("trash-open").addEventListener("click", async () => {
  try { await showTrash(); $("trash-dialog").showModal(); }
  catch(error) { showToast(friendlyError(error), true); }
});
$("trash-close").addEventListener("click", () => $("trash-dialog").close());
$("trash-list").addEventListener("click", async event => {
  const button = event.target.closest("[data-restore]");
  if (!button || state.busy) return;
  button.disabled = true; state.busy = true;
  try {
    const result = await api(`/api/trash/${button.dataset.restore}/restore`, {method:"POST"});
    await refreshProjects(); await loadProject(result.project_id); await showTrash();
    showToast("已恢复到原项目。");
  } catch(error) { showToast(friendlyError(error), true); button.disabled = false; }
  finally { state.busy = false; updateHeader(); }
});
