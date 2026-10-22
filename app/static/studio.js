const state = { projectId: null, project: null, tab: "design", busy: false, toastTimer: null, nativeAgentAvailable: false, modelRouter: null, planEditing: false };
const $ = (id) => document.getElementById(id);
let projectList = [];
let pendingMessage = null;
let progressTimer = null;
let liveProgressTimer = null;
let progressGeneration = 0;
let planRequestId = 0;
let projectLoadGeneration = 0;
let pendingExecutionProject = null;
let connectDialogGeneration = 0;
let observingTurn = false;
let observedRunningTurn = false;

function saveDraft() {
  if (!state.projectId) return;
  try {
    localStorage.setItem(`kstudio-draft:${state.projectId}`, JSON.stringify({text: $("conversation-input").value, editing: state.planEditing}));
  } catch (_) { /* Browser storage may be disabled; the server still owns sent messages. */ }
}

function restoreDraft() {
  try {
    const draft = JSON.parse(localStorage.getItem(`kstudio-draft:${state.projectId}`) || "null");
    $("conversation-input").value = typeof draft?.text === "string" ? draft.text : "";
    state.planEditing = !!draft?.editing;
  } catch (_) { $("conversation-input").value = ""; }
}

// This is a USER utterance. Internal execution instructions stay in workflow_context.py.
function executionUserMessage(typed) {
  return typed.trim() ? typed : "确认，按当前计划开始建模。";
}

// Historical compatibility helper only. Live conversation routing belongs to the host.
function isBuildApproval(message) {
  if (/^\s*(?:已)?(?:批准|确认|同意).*(?:执行|开始|建模)/.test(message)) {
    message = message.replace(/不要执行旧(?:整栋)?(?:基线|脚本|计划)/g, "")
      .replace(/不要修改(?:其他|其余|未涉及|未选中)[^，。；\n]*/g, "")
      .replace(/(?:检查|核对|验证)是否/g, "检查");
  }
  if (/不要(?:开始|执行|建模|动|修改|操作)|不要.{0,8}(?:开始建模|执行建模|执行计划|操作)|不执行|不建模|先别|暂不|暂停|停止(?:建模|操作|执行|修改)|禁止.{0,8}(?:建模|操作|执行|修改)|取消|先不|不同意|不批准|未确认|未批准|还没(?:有)?(?:批准|确认)|不想|不希望|如果|假如|能否|是否|怎么|如何|示例|教程|[?？]|改为|修改|调整|改成/.test(message)) return false;
  return /^(?:已)?(?:确认|开始|继续|同意|批准)(?:吧|了|执行|开工)?[。！!\s]*$/.test(message) || /(?:批准|确认|同意).*(?:执行|开始|建模)|(?:开始|继续)(?:按计划)?建模(?:吧|了|。|！|!|$)/.test(message);
}

function renderJourney() {
  const stage = state.project?.agent_session?.reconstruction_state || "idle";
  const available = routeAvailable("economy");
  $("model-connection-notice").hidden = available;
  $("setup-model").hidden = available;
  $("setup-model").disabled = state.busy;
  $("model-connection-hint").textContent = routeInfo("economy").provider === "codex-app-server"
    ? "当前选择的本机 Codex 不可用。请先检查本机安装和配置，或在「模型 / 自带 API」主动选择其他连接。图片和草稿会保留。"
    : "请在「模型 / 自带 API」检查所选供应商的连接。图片和草稿会保留，分析阶段无需 SketchUp。";
  $("clarification-shortcuts").hidden = state.busy || stage !== "clarifying";
  $("use-estimates").disabled = state.busy;
}

function sourceImages() {
  return (state.project?.context?.references || []).filter((ref) => ref.type === "image" && ref.source.startsWith("inputs/reference/"));
}

function referenceSourceMarkup(ref) {
  const filename = ref.source.split('/').at(-1);
  const revisions = Object.entries(ref.evidence_model_revisions || {}).map(([model, revision]) => `${model}: r${revision}`).join("，");
  return `<a class="reference-source" href="${projectFileUrl(ref.source)}" target="_blank" rel="noreferrer"><img src="${projectFileUrl(ref.source)}" alt="${escapeHtml(filename)}" loading="lazy"><span>${escapeHtml(filename)}${revisions ? `<small>记录于 ${escapeHtml(revisions)}</small>` : ""}</span></a>`;
}

function projectFileUrl(path) {
  return `/api/projects/${encodeURIComponent(state.projectId)}/files/${path.split("/").map(encodeURIComponent).join("/")}`;
}

function pendingImages() {
  const submitted = new Set((state.project?.context?.conversation || []).flatMap(message => [
    ...(message.metadata?.attachments || []), ...(message.metadata?.legacy_attachments || []),
  ]));
  return sourceImages().filter(ref => !ref.submitted_at && !submitted.has(ref.source));
}

function pendingAttachmentSources() {
  const context = state.project?.context || {};
  const references = context.references || [];
  const submitted = new Set((context.conversation || []).flatMap(message => [
    ...(message.metadata?.attachments || []), ...(message.metadata?.legacy_attachments || []),
  ]));
  return [...new Set([
    ...pendingImages().map(ref => ref.source),
    ...(context.brief?.source_files || []), ...(context.site?.source_files || []),
    ...references.filter(ref => ref.type === "note").map(ref => ref.source),
  ])].filter(path => !references.find(ref => ref.source === path)?.submitted_at && !submitted.has(path));
}

function renderReferenceComposer() {
  const images = sourceImages();
  const pending = pendingImages();
  const pendingSources = new Set(pending.map(ref => ref.source));
  const submitted = images.filter(ref => !pendingSources.has(ref.source));
  $("reference-gallery").hidden = !!pendingMessage || !pending.length;
  $("reference-gallery").innerHTML = pending.map((ref) => `<div class="image-item"><a href="${projectFileUrl(ref.source)}" title="${escapeHtml(ref.source.split('/').at(-1))}" target="_blank" rel="noreferrer"><img src="${projectFileUrl(ref.source)}" alt="${escapeHtml(ref.source.split('/').at(-1))}"><span>待发送 · 查看原图 ↗</span></a><button class="image-remove" title="移除待发送图片" data-delete-image="${escapeHtml(ref.source)}" aria-label="删除图片 ${escapeHtml(ref.source.split('/').at(-1))}" ${state.busy ? "disabled" : ""}>×</button></div>`).join("");
  const history = $("submitted-reference-history");
  history.hidden = !submitted.length;
  // Keep image history optional. Discuss unclear references in the conversation.
  $("submitted-reference-summary").textContent = `已发送图片 ${submitted.length} 张 · 查看原图`;
  $("submitted-reference-roles").innerHTML = submitted.map(referenceSourceMarkup).join("");

}

function renderWorkflowChecks(progress = null) {
  const agent = state.project?.agent_session || {};
  const blender = agent.modeling_backend === "blender";
  const geometry = blender ? agent.last_model_info?.revision > 0 : Object.values(agent.ruby_state || {}).some(v => v.revision > 0);
  const plan = ["planned", "building"].includes(agent.reconstruction_state);
  const items = progress?.checks || [
    {label:"模型 API", status:routeAvailable("economy") ? "done" : "blocked", detail:routeReadinessLabel("economy")},
    {label:"建模需求", status:sourceImages().length || state.project?.context?.conversation?.length ? "done" : "pending", detail:sourceImages().length ? `${sourceImages().length} 张项目图片；发送后仍保留上下文` : "也可以用文字描述建筑；AI 会先整理假设与计划"},
    {label:"建模计划", status:plan ? "done" : "pending", detail:plan ? "参数已整理" : "回答关键问题后生成计划"},
    {label:blender ? "Blender 连接" : "SketchUp 连接", status:agent.status === "ready" ? "done" : "pending", detail:agent.status === "ready" ? "已绑定独立模型；执行前再核验" : "建模前连接独立模型"},
    {label:"实际模型修改", status:geometry ? "done" : "pending", detail:geometry ? "已有已提交几何" : "尚未提交几何；写脚本不等于已建模"},
    {label:"截图与导出", status:artifactByType(blender ? "blend" : "skp") && geometry ? "done" : "pending", detail:artifactByType(blender ? "blend" : "skp") && geometry ? "已有模型文件；还需检查还原质量" : "等待模型检查与保存"},
    {label:"还原质量验收", status:"pending", detail:geometry ? "模型已执行，质量尚未验收。请对照参考图检查所有立面、屋顶和修改结果；AI 自评不代表通过。" : "实际模型生成后，对照参考图检查"},
  ];
  $("workflow-checklist").innerHTML = items.map(item => `<li class="check-${escapeHtml(item.status)}"><span>${item.status === "done" ? "✓" : item.status === "blocked" ? "!" : item.status === "running" ? "◷" : "○"}</span><div><strong>${escapeHtml(item.label)}</strong><small>${escapeHtml(item.detail || "")}</small></div></li>`).join("");
}

async function refreshProjects() {
  const projects = await api("/api/projects");
  projectList = projects.sort((a, b) => (Number(b.updated_at) || 0) - (Number(a.updated_at) || 0));
  $("project-select").innerHTML = projects.map((project) => `<option value="${escapeHtml(project.project_id)}">${escapeHtml(project.project_name)}</option>`).join("");
  if (state.projectId) $("project-select").value = state.projectId;
  renderProjectHistory();
  return projects;
}

function renderProjectHistory() {
  $("session-count").textContent = projectList.length;
  $("project-history").innerHTML = projectList.map((p) => `<div class="history-row"><button class="history-item${p.project_id === state.projectId ? " active" : ""}" data-project="${escapeHtml(p.project_id)}" title="${escapeHtml(p.project_name)}"><span>◷</span><span>${escapeHtml(p.project_name)}${p.project_id === state.runningProjectId ? " · 运行中" : ""}</span></button></div>`).join("");
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
    else if (/^(?:\.\.\/\.\.\/)?outputs\/[a-zA-Z0-9_./-]+$/.test(href) && !href.replace(/^\.\.\/\.\.\//, "").includes("..")) tokens[i].attrSet("href", projectFileUrl(href.replace(/^\.\.\/\.\.\//, "")));
    else if (!/^https?:\/\//i.test(href)) tokens[i].attrSet("href", "#");
    tokens[i].attrSet("target", "_blank"); tokens[i].attrSet("rel", "noopener noreferrer");
    return linkOpen(tokens, i, options, env, self);
  };
  md.renderer.rules.image = (tokens, i) => {
    const src = tokens[i].attrGet("src") || "";
    const alt = escapeHtml(tokens[i].content || "项目草图");
    if (/^(notes|outputs)\/[a-zA-Z0-9_./-]+\.(png|jpe?g|webp)$/i.test(src) && !src.includes("..")) {
      const path = src.startsWith("notes/") ? "runtime/agent_workspace/" + src : src;
      const url = escapeHtml(projectFileUrl(path));
      return `<a href="${url}" target="_blank" rel="noopener noreferrer"><img src="${url}" alt="${alt}" style="max-width:100%;height:auto" loading="lazy"></a>`;
    }
    return alt;
  };
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
  const projectId = state.projectId;
  if (projectId && typeof KStudioActivity !== "undefined") {
    api(`/api/projects/${encodeURIComponent(projectId)}/agent/progress`).then(progress => {
      if (projectId !== state.projectId) return;
      KStudioActivity.remember(projectId, progress.activities);
      KStudioActivity.render(projectId, $("conversation-history"));
    }).catch(() => {});
  }
  clearInterval(progressTimer);
  clearInterval(liveProgressTimer); progressGeneration++;
  $("operation-progress").hidden = true;
  state.activeTurnProgress = null;
  state.turnCancellation = null;
  renderTurnControls();
}

function renderTurnControls(progress = null) {
  if (progress && typeof KStudioActivity !== "undefined") {
    KStudioActivity.remember(state.projectId, progress.activities);
    KStudioActivity.render(state.projectId, $("conversation-history"));
  }
  if (progress) state.activeTurnProgress = {projectId: state.projectId, ...progress};
  const current = state.activeTurnProgress;
  const active = current?.projectId === state.projectId && current.running === true;
  const supported = active && current.cancel_supported === true && typeof current.request_id === "string" && !!current.request_id;
  const cancellation = state.turnCancellation?.projectId === state.projectId && state.turnCancellation.requestId === current?.request_id
    ? state.turnCancellation : null;
  const requested = !!(current?.cancel_requested || cancellation?.attempted);
  const button = $("cancel-agent-turn");
  button.hidden = !supported;
  button.disabled = !supported || requested;
  button.textContent = requested ? "正在等待停止确认…" : "停止本轮";
  const notice = $("cancel-agent-turn-status");
  notice.hidden = !active || !requested;
  renderNativeTurnEvent(active ? current.native_event : null);
  renderLiveActivity(active ? current : null);
  notice.textContent = cancellation?.uncertain
    ? "停止请求的结果尚未确认，正在同步实际状态。已提交的修改不会自动回滚。"
    : "已请求停止，正在等待当前操作结束和服务端确认。已提交的修改不会自动回滚。";
}

function renderLiveActivity(progress, unavailable = false) {
  const card = $("live-activity");
  const viewport = $("conversation-history");
  const followLatest = viewport.scrollHeight - viewport.clientHeight - viewport.scrollTop < 72;
  card.hidden = !progress || progress.running !== true;
  if (card.hidden) return;
  card.setAttribute("data-state", unavailable ? "uncertain" : "running");
  $("live-activity-stage").textContent = unavailable ? "进度连接暂时中断" : progress.stage || "正在等待本轮状态";
  const seconds = Number.isFinite(progress.elapsed_seconds) ? `${progress.elapsed_seconds} 秒` : "耗时同步中";
  $("live-activity-metrics").textContent = `${seconds} · ${Number.isInteger(progress.tool_calls) ? `已调用 ${progress.tool_calls} 次工具` : "工具次数尚未报告"}${progress.failed_tool_calls ? ` · ${progress.failed_tool_calls} 次失败` : ""}`;
  $("live-activity-event").textContent = unavailable ? "暂时无法确认最新进度，正在重连；请勿重复提交。" : $("native-turn-event").textContent || "本轮仍在运行，等待 Agent 返回下一条公开状态；不代表已完成。";
  $("live-activity-model").textContent = progress.cancel_requested ? "已请求停止，等待服务端确认；已有修改不会自动撤销。" : progress.action !== "execute" ? "分析 / 计划阶段 · 不改动模型" : progress.committed_revisions?.length ? `本轮已有 ${progress.committed_revision_count ?? progress.committed_revisions.length} 次模型提交 · 仍需完成检查` : "执行阶段 · 尚无本轮模型提交";
  if (followLatest) viewport.scrollTop = viewport.scrollHeight;
}

function renderNativeTurnEvent(event) {
  const output = $("native-turn-event");
  let text = "";
  if (event && typeof event === "object") {
    const name = event.event;
    if (name === "turn/plan/updated" && Array.isArray(event.plan)) {
      const labels = {pending: "待处理", inProgress: "处理中", in_progress: "处理中", completed: "已完成"};
      text = "当前步骤：" + event.plan.filter(item => typeof item?.step === "string")
        .slice(0, 8).map(item => `${item.step}（${labels[item.status] || "状态未确认"}）`).join("；");
    } else if ((name === "item/agentMessage/delta" || (["item/started", "item/completed"].includes(name) && event.item_type === "agentMessage")) && typeof event.text === "string") {
      text = "Agent 最新消息：" + event.text;
    } else if (typeof event.tool === "string" && ["tool_started", "tool_completed", "tool_cancelled"].includes(name)) {
      text = ({tool_started: "正在调用工具：", tool_completed: event.success === false ? "工具报告失败：" : "工具已返回：", tool_cancelled: "未启动的工具已取消："})[name] + event.tool;
    } else if (name === "turn/completed") {
      text = event.interrupted_confirmed === true ? "本轮已确认中断。已提交的修改不会自动回滚。"
        : event.status === "failed" ? "本轮失败，请查看记录与当前模型。" : "本轮已结束，正在同步结果。";
    } else if (name === "turn_started") text = "本轮已开始处理。";
  }
  // Safe native event allowlist only. Never render reasoning, shell arguments or raw event JSON.
  output.textContent = text.slice(0, 2400);
  output.hidden = !text;
}

async function cancelConversationTurn() {
  const projectId = state.projectId;
  const progress = state.activeTurnProgress;
  if (!projectId || progress?.projectId !== projectId || progress.running !== true || progress.cancel_supported !== true
      || typeof progress.request_id !== "string" || !progress.request_id || progress.cancel_requested
      || (state.turnCancellation?.requestId === progress.request_id && state.turnCancellation.attempted)) return;
  const cancellation = {projectId, requestId: progress.request_id, attempted: true, uncertain: false};
  state.turnCancellation = cancellation;
  renderTurnControls();
  try {
    const result = await api(`/api/projects/${encodeURIComponent(projectId)}/agent/cancel`, {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({expected_request_id: cancellation.requestId}),
    });
    if (projectId !== state.projectId || state.turnCancellation !== cancellation) return;
    // Acknowledgement is not completion. Keep the turn and composer send lock until progress confirms terminal state.
    cancellation.uncertain = result.cancel_requested !== true && result.cancellation_requested !== true;
    renderTurnControls();
  } catch (_) {
    if (projectId !== state.projectId || state.turnCancellation !== cancellation) return;
    cancellation.uncertain = true;
    renderTurnControls();
  }
}

function parameterPlanMarkup(card) {
  const blocks = [...card.matchAll(/<design_scope>\s*([\s\S]*?)\s*<\/design_scope>/g)];
  if (!blocks.length) return chatText(card);
  try {
    if (blocks.length !== 1) throw new Error("ambiguous scope");
    const features = JSON.parse(blocks[0][1]);
    if (!Array.isArray(features) || !features.length || features.some(feature =>
      !feature || typeof feature.feature_id !== "string" || !feature.feature_id.trim()
      || typeof feature.requested_state !== "string" || !feature.requested_state.trim())) throw new Error("invalid scope");
    const scope = '<section class="plan-scoped-features"><strong>本轮功能范围（批准后执行）</strong><ul>'
      + features.map(feature => `<li>${escapeHtml(feature.feature_id)}：${escapeHtml(feature.requested_state)}</li>`).join("") + '</ul></section>';
    // Only this bounded, validated host contract is replaced for presentation.
    // The approval hash covers this card with the host's universal-newline normalization.
    return chatText(card.slice(0, blocks[0].index)) + scope + chatText(card.slice(blocks[0].index + blocks[0][0].length));
  } catch (_) {
    return '<p class="plan-review-note">本轮功能范围格式有误，请先更新计划再批准。</p>' + chatText(card);
  }
}

async function loadParameterPlan() {
  const requestId = ++planRequestId;
  const projectId = state.projectId;
  state.displayedPlan = null;
  $("download-plan").href = projectFileUrl("runtime/agent_workspace/notes/reconstruction_card.md");
  const visible = ["planned", "building"].includes(state.project?.agent_session?.reconstruction_state);
  $("parameter-plan").hidden = !visible;
  $("parameter-plan-content").textContent = "正在读取计划…";
  if (!visible) return;
  try {
    const card = await api(projectFileUrl("runtime/agent_workspace/notes/reconstruction_card.md"));
    // Python reads the approved card with universal newlines on every platform.
    // Canonicalize CRLF/CR before hashing so unchanged Windows plans match.
    const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(card.replace(/\r\n?/g, "\n")));
    if (requestId !== planRequestId || projectId !== state.projectId) return;
    $("parameter-plan-content").innerHTML = '<p class="plan-review-note">请重点核对层数、各立面的门窗数量、尺寸与推断。AI 可能误读图片；有差异时点击「修改参数」纠正后再批准。</p>' + parameterPlanMarkup(card);
    const sha256 = Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, "0")).join("");
    $("parameter-plan").hidden = (state.project?.context?.conversation || []).some(m => m.role === "assistant" && m.metadata?.plan_sha256 === sha256);
    let pendingPlan;
    try { pendingPlan = await api(`/api/projects/${encodeURIComponent(projectId)}/agent/pending-plan`); }
    catch (_) { pendingPlan = null; }
    if (requestId !== planRequestId || projectId !== state.projectId) return;
    if (pendingPlan?.consumed && pendingPlan.plan_sha256 === sha256 && state.project?.agent_session?.reconstruction_state === "building") {
      state.displayedPlan = null;
      $("parameter-plan-content").insertAdjacentHTML("afterbegin", '<p class="plan-review-note">该计划已执行。可在对话中继续提出局部修改。</p>');
      return;
    }
    if (pendingPlan?.consumed && pendingPlan.plan_sha256 === sha256 && state.project?.agent_session?.reconstruction_state === "planned") {
      $("parameter-plan").hidden = false;
      $("parameter-plan-content").insertAdjacentHTML("afterbegin", '<p class="plan-review-note">上次建模中断。可核对空白副本后重新批准同一方案。<button type="button" id="retry-empty-plan">检查副本并恢复批准按钮</button></p>');
      $("retry-empty-plan")?.addEventListener("click", async event => {
        if (state.busy || projectId !== state.projectId) return;
        const control = event.currentTarget;
        control.disabled = true;
        try {
          await api(`/api/projects/${encodeURIComponent(projectId)}/agent/retry-plan`, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({pending_plan_id:pendingPlan.pending_plan_id})});
          if (projectId !== state.projectId) return;
          await loadParameterPlan(); updateHeader();
          showToast("已核对空白副本，请重新批准当前方案。尚未开始建模。", false);
        } catch (error) { showToast(error.message, true); control.disabled = false; }
      });
      return;
    }
    if (!pendingPlan || typeof pendingPlan.pending_plan_id !== "string" || !pendingPlan.pending_plan_id
        || pendingPlan.consumed || pendingPlan.plan_sha256 !== sha256) {
      state.displayedPlan = null;
      // A direct local edit may update working notes after the approved build.
      // Those notes are not a new pending plan and must not appear as a stale
      // approval request below the completed conversation.
      if (state.project?.agent_session?.reconstruction_state === "building") {
        $("parameter-plan").hidden = true;
        return;
      }
      $("parameter-plan-content").insertAdjacentHTML("afterbegin", '<p class="plan-review-note">计划版本尚未核验或已更新，请刷新或重新整理计划后再批准。</p>');
      return;
    }
    state.displayedPlan = {projectId, sha256, pendingPlanId: pendingPlan.pending_plan_id};
  } catch (_) {
    if (requestId === planRequestId && projectId === state.projectId) {
      state.displayedPlan = null;
      $("parameter-plan-content").textContent = "参数文件暂时无法读取或核验，请重新加载计划后再批准。";
    }
  }
}

function routeInfo(tier) {
  const fallback = tier === "premium"
    ? { model: "gpt-6-astra", provider: "codex-app-server" }
    : { model: "gpt-6.1-sol", reasoning_effort: "medium", provider: "codex-app-server" };
  return state.modelRouter?.[tier] || fallback;
}

function routeAvailable(tier) {
  const route = routeInfo(tier);
  if (!state.modelRouter) return state.nativeAgentAvailable;
  return !!state.modelRouter.providers?.[route.provider]?.available;
}

function routeReadinessLabel(tier) {
  const route = routeInfo(tier);
  if (!routeAvailable(tier)) return route.provider === "codex-app-server" ? "本机 Codex 不可用" : "模型连接未配置";
  // Only host-recorded assistant responses in this project prove an invocation.
  // Session defaults and connector setup also carry route fields, but are not calls.
  const verified = route.model && state.project?.context?.project_id === state.projectId
    && (state.project.context.conversation || []).some(message => {
      const receipt = message.metadata || {};
      return message.role === "assistant" && !!message.content?.trim()
        && !["failed", "interrupted", "error"].includes(receipt.status) && !receipt.error
        && receipt.provider === route.provider && receipt.model === route.model
        && receipt.reasoning_effort === route.reasoning_effort;
    });
  if (verified) return "本会话已有成功调用";
  return route.provider === "codex-app-server" ? "已检测到本机程序；调用未验证" : "已配置；调用未验证";
}

function refreshTierLabels() {
  const select = $("conversation-tier");
  if (!select) return;
  const economy = select.querySelector('option[value="economy"]');
  const premium = select.querySelector('option[value="premium"]');
  const economyRoute = routeInfo("economy");
  $("model-settings-toggle").textContent = economyRoute.provider === "managed-responses" ? "K Studio 模型服务" : "模型 / 自带 API";
  const premiumRoute = routeInfo("premium");
  const economyLabel = economyRoute.model === "deepseek/deepseek-flash"
    ? "DeepSeek V4.1 Flash · 官方"
    : economyRoute.model === "openai/deepseek-v4.1-flash" && state.modelRouter?.providers?.litellm?.api_base === "https://api.b.ai/v1"
    ? "DeepSeek V4.1 Flash · B.AI"
    : `${economyRoute.model} · ${(economyRoute.reasoning_effort || "provider-default").toUpperCase()}`;
  economy.textContent = economyRoute.provider === "managed-responses"
    ? `K Studio · ${economyRoute.model} · ${routeReadinessLabel("economy")} · 内部测试中`
    : `${economyLabel} · ${routeReadinessLabel("economy")}`;
  premium.textContent = `精修 · ${premiumRoute.model}（仅本轮 · ${routeReadinessLabel("premium")}）`;
  $("brain-status").textContent = `建筑 Agent · ${economyLabel} · ${routeReadinessLabel("economy")}`;
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
  if (!response.ok) {
    const detail = body?.detail || body?.error;
    throw new Error(Array.isArray(detail) ? "输入内容不符合要求，请检查文件或消息长度后重试。" : detail || `请求失败（${response.status}）`);
  }
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
  if (/dynamic tools must use either canonical or legacy format consistently/i.test(message)) return "建模未启动：本机 Agent 的工具注册格式不一致。项目、图片和计划已保留，需要更新 K Studio 后重新检查并批准计划。";
  if (/pending plan was already consumed or replaced/i.test(message)) return "这份计划的批准记录已使用或已更新，本次未开始建模。请重新检查当前计划；若上一轮启动失败，请先恢复批准记录。";
  if (/Connection file not found:/i.test(message)) return "本机连接程序已就绪，但还没收到 SketchUp 插件的连接信息。请完成插件安装，在所选 SketchUp 的「扩展程序 → Kongxing AI → Start Local Bridge」启动桥接，再检查 MCP。";
  if (/existing SketchUp MCP.*not configured|standalone SketchUp connector configuration is unavailable|kongxing_sketchup MCP server is not enabled/i.test(message)) return "SketchUp 连接器尚未配置。请在连接窗口打开「安装 K Studio 连接器」，完成插件和本机连接程序安装，再检查 MCP。";
  if (/Codex config\.toml was not found|local native agent is not configured/i.test(message)) return "本机 Codex 尚未配置。请先在运行 K Studio 的电脑上完成 Codex 配置，再回到本会话重试。已上传的图片和对话仍在，无需新建项目；这不是 DeepSeek Key 错误。";
  if (/Codex CLI is unavailable|local Codex App Server is unavailable/i.test(message)) return "未找到可用的本机 Codex 程序。请检查 K Studio 所在电脑的程序安装和启动路径，再回到本会话重试；图片和对话仍保留。";
  if (/Selected model is at capacity|model.*capacity/i.test(message)) return "当前模型服务繁忙，暂时无法继续。图片和已保存的计划仍在；请稍后在本会话重试，无需重新上传，也无需重新填写 Key。";
  if (/workspace routing discovery unauthorized|refresh token was already used/i.test(message)) return "Codex 本机登录缓存已失效，需要刷新 Codex 登录；这不是 DeepSeek API Key 问题。图片、计划和模型已保留。";
  if (/Failed to fetch|NetworkError|Load failed/i.test(message)) return "工作台连接暂时中断。草稿已保留；恢复连接后先同步已有模型，请勿重复发送修改请求。";
  if (/Project input-token budget|project budget cannot be verified/i.test(message)) return "本项目累计建模预算已达到上限，或历史用量尚未核实。已提交的模型不会因此删除；请先查看现有成果和恢复状态，不要重复建模。";
  if (/Native Builder exceeded|Native Builder reached|tool-call budget/i.test(message)) return "本轮 Agent 达到执行上限。已提交部分可能仍保留，请先检查当前模型并恢复，勿直接重复整轮修改。";
  if (/Codex agent turn exceeded|app-server communication failed/i.test(message)) return "建模处理被中断，但 SketchUp 可能已经写入。请先恢复/同步确认当前模型版本，避免重复执行同一修改。";
  // Ruby backtrace line numbers (e.g. geometry_tools.rb:401) are not HTTP codes.
  const httpStatus = code => new RegExp(`请求失败\\s*[（(]${code}[）)]|\\bHTTP(?:\\s+(?:error|status))?\\s*[:=]?\\s*${code}\\b|\\bstatus(?:_code)?["']?\\s*[:=]\\s*${code}\\b`, "i").test(message);
  if (/AuthenticationError|invalid.*api.?key|Incorrect API key|Unauthorized/i.test(message) || httpStatus(401)) return "API Key 无效或已失效，请打开「模型 / 自带 API」检查供应商和 Key。图片、计划和草稿都已保留。";
  if (/Insufficient Balance|insufficient_quota|余额不足/i.test(message) || httpStatus(402)) return "模型账户余额或额度不足，请检查供应商账户；项目资料与计划已保留。";
  if (/RateLimitError|rate.limit/i.test(message) || httpStatus(429)) return "模型供应商暂时限流，请稍后重试；无需重新上传资料。";
  if (/WinError 10061|Server disconnected without sending a response|ConnectError|ProxyError/i.test(message)) return "模型 API 连接中断；已保留图片、计划和脚本。请重试执行，当前无需恢复或重新创建模型。";
  if (/本轮 API 小额测试预算已到安全边界/.test(message)) return "本轮 API 测试已到预算安全边界，未继续调用。现有图片、方案和用量记录已保留；请先核实超时费用或调整测试上限。";
  if (/API 意图理解[\s\S]*timed out/i.test(message)) return "模型 API 在理解请求时等待响应超时，尚未开始建模；这不是 MCP 连接失败。图片和草稿已保留。请检查服务商状态，不要连续重复发送。";
  if (/APITimeoutError|LiteLLM request failed[\s\S]*(?:Timeout|timed out)|Request timed out/i.test(message)) {
    return "模型 API 请求超时，本轮未完成；这不代表 MCP 断开。项目记录已保留，请分阶段重试，先建主体并截图，再补细节。";
  }
  if (/active model path and GUID|active model could not be verified/i.test(message)) {
    return "SketchUp 插件已响应，但当前模型尚不能绑定。若是未保存的无标题模型，请先保存当前工作并关闭它，再由网站打开独立副本；不要直接在原模型上建模。";
  }
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
  // Recovery can make an older checkpoint current. Manifest insertion order
  // is not the identity of the model the user is looking at.
  const modelPath = state.project?.model_state?.model_path;
  return all.filter((item) => item.type === type &&
    (type !== "viewport" || state.project?.agent_session?.modeling_backend !== "blender" || !modelPath || item.path.startsWith(modelPath.slice(0, modelPath.lastIndexOf("/") + 1))) &&
    (!["skp", "blend"].includes(type) || !modelPath || item.path === modelPath)).at(-1) || null;
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
  $("agent-error").textContent = agent.error ? friendlyError(new Error(agent.error)) : "";
  const agentReady = agent.status === "ready" && !!agent.model_path;
  const reconstructionMode = $("workflow-mode").value === "image_reconstruction";
  document.body.classList.toggle("reconstruction-mode", reconstructionMode);
  document.querySelector('.tab-button[data-tab="design"]').childNodes[0].textContent = reconstructionMode ? "图片与计划 " : "方案设计 ";
  $("project-select").disabled = !!state.switchingProject;
  $("new-project").disabled = state.busy;
  $("conversation-input").disabled = false;
  $("conversation-input").setAttribute("aria-description", state.busy ? "可以记录下一条要求；本轮结束前不会发送。" : "输入建模要求");
  $("recover-agent-checkpoint").hidden = state.project?.agent_session?.reconstruction_state !== "building" || agent.modeling_backend === "blender";
  $("recover-agent-checkpoint").disabled = state.busy;
  renderProjectHistory();
  renderTurnControls();
  for (const id of ["workflow-mode", "conversation-tier", "reference-file", "brief-file", "site-file", "project-name"]) $(id).disabled = state.busy;
  $("reference-status").hidden = reconstructionMode;
  $("reconstruction-guide").hidden = !reconstructionMode;
  $("reference-files").innerHTML = sourceImages().map((ref) => `<span class="file-chip">${escapeHtml(ref.source.split("/").at(-1))}</span>`).join("");
  renderReferenceComposer();
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
  $("start-agent-session").hidden = agent.modeling_backend === "blender";
  $("start-agent-session").disabled = state.busy || agent.modeling_backend === "blender";
  $("start-blender-session").disabled = state.busy || agent.modeling_backend === "blender";
  $("start-blender-session").textContent = agent.modeling_backend === "blender" ? "Blender 已连接" : "连接 Blender（测试）";
  if (agent.modeling_backend === "blender") $("agent-session-state").textContent = "Blender 有限体块后端 · 原生保存/重开核验 · 非完整建筑复原";
  if (!state.busy) $("start-agent-session").querySelector("span:first-child").textContent = agentReady ? "重连 SketchUp" : "连接 SketchUp";
  const hasAgentTurn = agent.status === "conversation" || agent.status === "ready";
  const activeModel = hasAgentTurn && agent.model ? agent.model : routeInfo("economy").model;
  $("model-tier-status").textContent = activeModel;
  $("conversation-input").placeholder = $("workflow-mode").value === "image_reconstruction"
    ? sourceImages().length ? "根据这些图片还原建筑，或继续描述修改要求" : "描述你想建的建筑，也可粘贴一张或多个视角图片"
    : agentReady ? "描述设计修改；Agent 会自行调用工具、查看结果并继续修正…" : "先讨论设计方向；启动空白模型后，Agent 可直接建模并继续修改…";
  $("conversation-send").disabled = state.busy || !routeAvailable($("conversation-tier").value) || !$("conversation-input").value.trim();
  const reconstruction = $("workflow-mode").value === "image_reconstruction";
  const reconstructionState = agent.reconstruction_state || "idle";
  $("reconstruction-state").hidden = !reconstruction;
  $("reconstruction-state").textContent = state.busy ? "正在处理，请等待" : {idle: "待分析", clarifying: "等待补充信息", planned: "等待批准", building: "已有模型 · 可继续修改"}[reconstructionState] || "待分析";
  const detailContext = `${state.projectId}:${reconstructionState}`;
  const taskDetails = $("task-details");
  if (taskDetails.dataset.context !== detailContext) {
    taskDetails.open = reconstructionState === "planned";
    taskDetails.dataset.context = detailContext;
  }
  const hasImages = sourceImages().length > 0;
  $("prepare-plan").hidden = state.busy || reconstructionState !== "clarifying";
  $("prepare-plan").disabled = state.busy;
  $("model-settings-toggle").disabled = state.busy;
  renderAttachments();
  $("conversation-send").disabled = state.busy || !routeAvailable($("conversation-tier").value) || (!$("conversation-input").value.trim() && !(reconstruction && reconstructionState === "idle" && hasImages));
  $("next-step").textContent = {idle: hasImages ? "下一步：描述目标或直接点击「分析图片」。" : "下一步：描述建筑，或上传一张/多个视角参考图。", clarifying: "下一步：回答关键问题；信息齐全后整理计划。", planned: agentReady ? "下一步：查看估算，批准并开始建模。" : "下一步：查看计划，连接 SketchUp 后批准建模。", building: "下一步：查看截图或下载 SKP；继续输入修改要求。"}[reconstructionState];
  $("revise-reconstruction-plan").hidden = !reconstruction || !["planned", "building"].includes(reconstructionState);
  $("revise-reconstruction-plan").disabled = state.busy;
  $("approve-reconstruction").hidden = !reconstruction || reconstructionState !== "planned";
  const hasDraft = !!$("conversation-input").value.trim();
  const approvalReady = state.displayedPlan?.projectId === state.projectId && !!state.displayedPlan?.pendingPlanId
    && !state.planEditing && !pendingAttachmentSources().length;
  $("approve-reconstruction").disabled = state.busy || !routeAvailable($("conversation-tier").value) || (!hasDraft && !approvalReady);
  $("approve-reconstruction").querySelector("span:first-child").textContent = $("conversation-input").value.trim()
    ? "发送草稿后再批准" : "批准计划并开始建模";
  if (!state.busy) $("conversation-send").querySelector("span:first-child").textContent = state.planEditing ? "更新参数计划" : !reconstruction ? "发送消息" : {idle: "发送", clarifying: "继续交流", planned: "继续交流 / 更新计划", building: "发送修改要求"}[reconstructionState];
  $("conversation-send").setAttribute("aria-label", $("conversation-send").querySelector("span:first-child").textContent);
  $("conversation-send").title = $("conversation-send").getAttribute("aria-label");
  const isBlender = agent.modeling_backend === "blender";
  $("start-blender-session").title = "Blender 体块测试：支持有界网格、材质、局部修改和原生保存重开；外观质量尚未验收。";
  document.querySelector(".eyebrow").textContent = isBlender ? "BLENDER ASSISTANT" : "SKETCHUP ASSISTANT";
  document.querySelector(".mode-label small").textContent = isBlender ? "Blender" : "SketchUp";
  if (isBlender) {
    $("start-agent-session").hidden = true;
    $("next-step").textContent = reconstructionState === "building" ? "继续修改同一模型，或在模型与文件中下载 .blend。" : reconstructionState === "planned" ? "查看计划后批准执行 Blender 体块测试。" : "先描述要求，再整理计划。";
    $("prepare-plan").hidden = state.busy || reconstructionState === "planned" || reconstructionState === "building";
  }
  for (const id of ["brief", "site-note", "intent"]) $(id).closest(".input-block").hidden = reconstruction;
  $("reference-url").hidden = reconstruction;
  setStage("design", true);
  setStage("model", prepared);
  setStage("drawing", !!artifactByType("dxf"));
  setStage("render", !!artifactByType("viewport"));
  setStage("present", !!artifactByType("presentation"));
  renderArtifacts();
  renderConversation();
  renderWorkflowChecks();
  renderJourney();
  renderPreview();
}

function renderConversation() {
  const messages = [...(state.project?.context?.conversation || [])];
  const pendingHere = pendingMessage && (!state.pendingMessageProjectId || state.pendingMessageProjectId === state.projectId);
  // Loading the running project can already include the server-persisted user
  // message. Keep the pending reply, but do not append its optimistic echo twice.
  // Only compare messages added after submission; an older identical instruction
  // is still a distinct user turn.
  const pendingStored = Number.isInteger(state.pendingConversationLength)
    && messages.slice(state.pendingConversationLength).some(message => message.role === "user" && message.content === pendingMessage);
  if (pendingHere && !pendingStored) messages.push({role: "user", content: pendingMessage, phase: "agent", metadata: {attachments: pendingAttachmentSources()}});
  const viewport = $("conversation-history");
  const previousScrollTop = viewport.scrollTop;
  const followLatest = state.conversationViewportProject !== state.projectId
    || viewport.scrollHeight - viewport.clientHeight - viewport.scrollTop < 72;
  state.conversationViewportProject = state.projectId;
  const history = $("conversation-messages");
  if (!messages.length) {
    history.innerHTML = `<div class="welcome">
      <div class="welcome-symbol"><img src="/static/k-monogram.svg" alt="K Studio 几何 K 标志" width="180" height="180"></div>
      <div class="welcome-kicker">K STUDIO / FORM &amp; SPACE</div>
      <h2>把想象，<em>构筑成形。</em></h2>
      <p>从一张参考图、一段描述开始。<br>与你一起推敲空间，让灵感成为可编辑的建筑。</p>
      <div class="suggestions">
        <button class="suggestion" data-prompt="按参考图片还原建筑，保留屋顶、窗洞与立面细节。"><small aria-hidden="true">01 / RECONSTRUCT</small><span>从图片还原建筑</span><span class="suggestion-arrow" aria-hidden="true">↗</span></button>
        <button class="suggestion" data-prompt="没有实测尺寸，请按图像比例估算并标明，允许推断背面。"><small aria-hidden="true">02 / EXPLORE</small><span>估算尺寸与补全背面</span><span class="suggestion-arrow" aria-hidden="true">↗</span></button>
        <button class="suggestion" data-prompt="请生成可编辑 SketchUp 模型，检查正面、背面和侧面截图。"><small aria-hidden="true">03 / REFINE</small><span>多角度检查与修改</span><span class="suggestion-arrow" aria-hidden="true">↗</span></button>
      </div>
    </div>`;
    return;
  }
  history.innerHTML = messages.map((message) => {
    const isUser = message.role === "user";
    const speaker = isUser ? "你" : "建筑 Agent";
    const phase = message.phase === "agent" ? "Agent 对话 / 建模" : message.phase === "after_build" ? "模型修改" : "方案讨论";
    const meta = message.metadata || {};
    const attachments = [...(meta.attachments || []), ...(meta.legacy_attachments || [])];
    const media = attachments.map(path => {
      const ref = (state.project.context.references || []).find(r => r.source === path);
      if (!ref) return `<small class="removed-attachment">已移除附件</small>`;
      const url = projectFileUrl(path);
      return ref.type === "image" ? `<div class="sent-image"><a href="${url}" target="_blank" rel="noreferrer"><img src="${url}" alt="已发送参考图 ${escapeHtml(path.split('/').at(-1))}"></a><button class="image-remove" data-delete-image="${escapeHtml(path)}" aria-label="删除已发送图片 ${escapeHtml(path.split('/').at(-1))}" ${state.busy ? "disabled" : ""}>×</button></div>` : `<a href="${url}" target="_blank" rel="noreferrer">${escapeHtml(path.split('/').at(-1))}</a>`;
    }).join("");
    const detail = !isUser && meta.model
      ? '<small class="chat-metadata">' + escapeHtml("建筑 Agent")
        + " · " + escapeHtml(meta.model)
        + (Number.isInteger(meta.input_tokens) ? " · " + meta.input_tokens + " 输入 token" : "")
        + (Number.isInteger(meta.output_tokens) ? " · " + meta.output_tokens + " 输出 token" : "")
        + (Number.isFinite(meta.latency_ms) ? " · " + meta.latency_ms + " ms" : " · 耗时未报告")
        + "</small>"
      : "";
    return '<article class="chat-message ' + (isUser ? "user" : "assistant") + '" data-created-ms="' + (Date.parse(message.created_at) || 0) + '" data-activity-anchor="' + escapeHtml(meta.activity_id || "") + '"><header><span>'
      + speaker + "</span><span>" + phase + '</span></header><div class="markdown-content">' + chatText(message.content)
      + "</div>" + (!isUser && meta.plan_text ? `<section class="inline-plan markdown-content"><h3>本轮计划与参数</h3>${parameterPlanMarkup(meta.plan_text)}</section>` : "") + (media ? `<div class="message-attachments">${media}</div>` : "") + (detail ? '<details><summary>本轮记录</summary>' + detail + '</details>' : "") + "</article>";
  }).join("");
  if (typeof KStudioActivity !== "undefined") {
    if (pendingHere) history.insertAdjacentHTML("beforeend", '<article class="chat-message assistant pending-reply"><p>正在处理本轮要求…</p></article>');
    KStudioActivity.render(state.projectId, viewport);
    KStudioActivity.bind(viewport, document.querySelector(".composer-area"));
  }
  viewport.scrollTop = followLatest ? viewport.scrollHeight : previousScrollTop;
}

function setStage(stage, complete) {
  const indicator = $(`stage-${stage}`);
  indicator.textContent = complete ? "●" : "○";
  indicator.classList.toggle("complete", complete);
}

function renderArtifacts() {
  const hasGeometry = Object.values(state.project?.agent_session?.ruby_state || {}).some(item => item.revision > 0) || (state.project?.model_state?.objects || []).length > 0;
  const artifacts = allArtifacts().filter(item => item.type !== "skp" || hasGeometry)
    .filter(item => !["skp", "blend"].includes(item.type) || !state.project?.model_state?.model_path || item.path === state.project.model_state.model_path);
  const unique = [...new Map(artifacts.map((item) => [item.path, item])).values()];
  $("artifact-total").textContent = `${unique.length} 个文件`;
  const container = $("artifact-list");
  if (!unique.length) {
    container.innerHTML = '<div class="artifact-empty">建模后，可用预览和模型文件会显示在这里。</div>';
    $("artifact-links").innerHTML = "";
    return;
  }
  container.innerHTML = unique.slice(-6).map((item) => {
    const extension = item.path.split(".").at(-1).toUpperCase();
    const name = item.path.split("/").at(-1);
    const typeLabel = artifactTypeLabels[item.type] || item.type.replaceAll("-", " ").toUpperCase();
    return `<a class="artifact-card" href="${item.url}" target="_blank" rel="noreferrer"><span class="artifact-glyph">${extension.slice(0, 4)}</span><span class="artifact-copy"><strong>${escapeHtml(name)}</strong><small>${escapeHtml(typeLabel)}</small></span></a>`;
  }).join("");
  const blend = artifactByType("blend");
  const dxf = artifactByType("dxf");
  const board = artifactByType("presentation");
  const skp = hasGeometry ? artifactByType("skp") : null;
  const deliveryUnverified = state.project?.model_state?.last_operation?.delivery_status === "UNVERIFIED_NATIVE_REOPEN";
  // A recovery/legacy operation may have no delivery_status at all. Absence
  // is not a verified native reopen receipt, so retain an explicit warning.
  const deliveryNote = deliveryUnverified
    ? "候选模型：尚未通过 SketchUp 原生重开及深层几何一致性验收"
    : "已保存的模型文件：保存不等于原生重开验收，请查看与本文件对应的原生重开核验记录。";
  $("artifact-links").innerHTML = [
    blend ? `<a class="artifact-link" href="${blend.url}" download>↓ 下载 BLEND</a>` : "",
    skp ? `<a class="artifact-link" href="${skp.url}" download>↓ 下载 SKP</a><small class="artifact-delivery-note">${deliveryNote}</small>` : "",
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
  } else if (state.tab === "model" && project.agent_session?.modeling_backend === "blender") {
    title.textContent = "可编辑 Blender 模型";
    caption.textContent = "真实几何保存并重开；外观仍需对照参考图验收";
    const receipt = project.agent_session.last_model_info || {};
    meta.textContent = `版本 ${receipt.revision || 0} · ${Object.keys(receipt.objects || {}).length} 个命名构件`;
    canvas.className = "preview-canvas";
    canvas.innerHTML = capture ? `<img class="preview-image" src="${capture.url}" alt="Blender 模型渲染">` : '<div class="reconstruction-empty"><h2>模型已保存</h2><p>从下方下载 .blend；尚未生成本轮可视化预览，不以参考图替代模型结果。</p></div>';
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
  const generation = ++projectLoadGeneration;
  if (projectId !== state.projectId) { saveDraft(); state.displayedPlan = null; }
  // Commit identity and data together. A failed read must not send the old
  // visible conversation (or its draft) to a different project.
  const project = await api(`/api/projects/${encodeURIComponent(projectId)}`);
  if (generation !== projectLoadGeneration) return;
  state.planEditing = false;
  state.projectId = projectId;
  state.project = project;
  try { localStorage.setItem("architecture-studio-project", projectId); } catch (_) { /* Optional storage. */ }
  $("project-select").value = projectId;
  restoreDraft();
  $("parameter-plan").open = false;
  await loadParameterPlan();
  if (generation !== projectLoadGeneration) return;
  state.tab = artifactByType("viewport") ? "model" : "design";
  setTab(state.tab);
  updateHeader();
  setStatus(state.project.agent_session?.reconstruction_state === "building" ? "已有模型。可查看可用预览、下载模型或发送修改要求。" : state.project.design_ir ? "方案和场地图纸已准备完成。" : "工作区已就绪。上传参考图片并分析，确认计划后再开始建模。");
  if (typeof KStudioActivity !== "undefined") {
    try {
      const progress = await api(`/api/projects/${encodeURIComponent(projectId)}/agent/progress`);
      if (generation !== projectLoadGeneration || projectId !== state.projectId) return;
      KStudioActivity.remember(projectId, progress.activities);
      KStudioActivity.render(projectId, $("conversation-history"));
    } catch (_) { /* History remains available when progress is temporarily unavailable. */ }
  }
}

async function boot() {
  try {
    const [runtime, projects] = await Promise.all([api("/api/status"), refreshProjects()]);
    state.nativeAgentAvailable = !!runtime.native_agent_available;
    state.modelRouter = runtime.model_router || null;
    if (runtime.credential_restore_error) showToast("本机加密连接无法恢复，请重新填写 API Key；旧文件没有被发送或显示。", true);
    refreshTierLabels();
    const economyRoute = routeInfo("economy");
    const premiumRoute = routeInfo("premium");
    const routeStatus = routeAvailable("economy")
      ? `${economyRoute.model} · ${(economyRoute.reasoning_effort || "模型默认").toUpperCase()} · ${routeReadinessLabel("economy")}`
      : routeReadinessLabel("economy");
    $("brain-status").textContent = `建筑 Agent · ${routeStatus}`;
    document.querySelector(".signal-dot").classList.toggle("ready", state.nativeAgentAvailable);
    const savedId = localStorage.getItem("architecture-studio-project");
    if (projects.length) await loadProject(runtime.active_project_id || (projects.some((p) => p.project_id === savedId) ? savedId : projects[0].project_id));
    if (state.projectId) await observeRunningTurn();
    if (!state.projectId) { $("project-title").textContent = "点击「新建建模会话」开始"; $("conversation-send").disabled = true; }
  } catch (error) {
    showToast(friendlyError(error), true);
  }
}

async function uploadFile(category, file, targetId, manageBusy = true, referenceOptions = null) {
  if (!state.projectId || !file || (manageBusy && state.busy)) return false;
  if (manageBusy) { state.busy = true; updateHeader(); }
  try {
    const reference = referenceOptions || {evidence_role: "auto", role_context: $("conversation-input").value, batch_image_count: 1};
    const roleQuery = category === "reference" ? `&evidence_role=${encodeURIComponent(reference.evidence_role || "auto")}&role_context=${encodeURIComponent(reference.role_context || "")}&batch_image_count=${encodeURIComponent(reference.batch_image_count || 1)}` : "";
    const url = `/api/projects/${encodeURIComponent(state.projectId)}/inputs/${category}?filename=${encodeURIComponent(file.name)}${roleQuery}`;
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
  if (!state.projectId || state.busy) return false;
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
    showToast("已连接到本会话的 SketchUp 独立模型。", false);
    return true;
  } catch (error) {
    setStatus(friendlyError(error), "error");
    showToast(friendlyError(error), true);
    throw error;
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
  if (state.busy) return;
  // The composer never classifies natural language as approval, denial or plan editing.
  // Only a clean explicit button gesture is sent separately; the host validates context.
  const typed = $("conversation-input").value;
  const approvalButton = agentAction === "execute";
  if (approvalButton && typed.trim()) agentAction = "auto";
  const approvalGesture = approvalButton && !typed.trim() ? "plan_button" : undefined;
  if (approvalGesture && (state.planEditing || pendingAttachmentSources().length)) {
    showToast("还有未提交的参数或资料，请先发送并检查更新后的计划，再批准建模。");
    return;
  }
  const submittedProjectId = state.projectId;
  const approvedPlanSha256 = state.displayedPlan && state.displayedPlan.projectId === submittedProjectId
    ? state.displayedPlan.sha256 : undefined;
  const approvedPendingPlanId = approvedPlanSha256 ? state.displayedPlan.pendingPlanId : undefined;
  if (approvalGesture && (!approvedPlanSha256 || !approvedPendingPlanId)) {
    showToast("当前计划尚未读取或已失效，请重新检查计划后再批准。", true);
    return;
  }
  if (approvalGesture && state.project?.agent_session?.status !== "ready" && state.project?.agent_session?.modeling_backend !== "blender") {
    openConnectDialog(true);
    return;
  }
  // Preserve the human's exact text, including whitespace. Never replace a draft with approval.
  const message = approvalGesture ? executionUserMessage(typed)
    : typed.trim() ? typed
    : pendingAttachmentSources().length ? "请结合新上传的资料继续分析，整理需要我确认的内容。"
    : ((state.project?.agent_session?.reconstruction_state || "idle") === "idle" && sourceImages().length ? "请分析这张建筑图片，先确认建模目标与关键未知项。" : "");
  if (!message || state.busy) return;
  if (agentAction === "plan") state.displayedPlan = null;
  $("conversation-input").value = "";
  state.planEditing = false;
  saveDraft();
  pendingMessage = message;
  state.pendingConversationLength = (state.project?.context?.conversation || []).length;
  state.pendingMessageProjectId = submittedProjectId;
  state.runningProjectId = submittedProjectId;
  state.busy = true;
  const button = $("conversation-send");
  const requestedTier = $("conversation-tier").value;
  const clientRequestId = globalThis.crypto?.randomUUID?.();
  const route = routeInfo(requestedTier);
  setBusy(button, true, `${route.model} 处理中…`);
  const built = state.project?.agent_session?.status === "ready";
  const reconstruction = $("workflow-mode").value === "image_reconstruction";
  const resolvedAction = agentAction;
  const executesModel = !!approvalGesture;
  showResults(false);
  beginProgress(executesModel ? "正在校验批准并处理计划" : "正在处理本轮要求");
  // Keep the conversation visible while the approved plan is executing.
  if (executesModel) $("parameter-plan").open = false;
  $("workflow-progress").open = false;
  $("approve-reconstruction").disabled = true;
  setStatus("正在结合对话、资料与当前计划核对本轮要求；实际执行状态以实时进度为准。");
  try {
    startLiveProgress();
    const result = await api(`/api/projects/${encodeURIComponent(submittedProjectId)}/conversation`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        tier: requestedTier,
        workflow_mode: $("workflow-mode").value,
        agent_action: resolvedAction,
        ...(clientRequestId ? {client_request_id: clientRequestId} : {}),
        ...(approvedPlanSha256 && approvedPendingPlanId ? {approved_plan_sha256: approvedPlanSha256, approved_pending_plan_id: approvedPendingPlanId} : {}),
        ...(approvalGesture ? {approval_gesture: approvalGesture} : {}),
      }),
    });
    if (state.projectId !== submittedProjectId) return;
    state.project = result.project;
    pendingMessage = null;
    state.planEditing = false;
    await loadParameterPlan();
    if (result.agent?.agent_action === "plan") $("parameter-plan").open = true;
    saveDraft();
    $("conversation-tier").value = "economy";
    updateHeader();
    setStatus(result.reply);
    const calls = result.agent?.tool_calls?.length || 0;
    const agent = result.agent || {};
    showToast((agent.model || "建筑 Agent")
      + " 已处理" + (agent.agent_action === "clarify" ? "图片澄清" : agent.agent_action === "plan" ? "建模计划，等待批准" : built ? "当前模型" + (calls ? " · " + (agent.tool_call_count || calls) + " 次工具调用" : "") : "设计讨论") + "。", false);
    // Executing or inspecting an existing model is not a new result. Only the
    // host's current-turn commit/checkpoint receipts may open the result panel.
    if (agent.geometry_committed === true || agent.checkpoint_saved === true) { setTab("model"); showResults(true); }
  } catch (error) {
    try { localStorage.setItem(`kstudio-failed-message:${submittedProjectId}`, message); } catch (_) {}
    if (state.projectId !== submittedProjectId) return;
    saveDraft();
    await loadProject(submittedProjectId).catch(() => {});
    if (state.projectId !== submittedProjectId) return;
    if (!$("conversation-input").value.trim()) $("conversation-input").value = message;
    saveDraft();
    setStatus(friendlyError(error), "error");
    showToast(friendlyError(error), true);
  } finally {
    pendingMessage = null;
    state.pendingMessageProjectId = null;
    state.pendingConversationLength = null;
    state.runningProjectId = null;
    endProgress();
    state.busy = !!state.switchingProject;
    setBusy(button, false);
    updateHeader();
    await observeRunningTurn();
  }
}

document.querySelectorAll("[data-tab]").forEach((button) => button.addEventListener("click", () => setTab(button.dataset.tab)));
$("conversation-form").addEventListener("submit", sendConversation);
$("cancel-agent-turn").addEventListener("click", cancelConversationTurn);
$("conversation-input").addEventListener("focus", () => {
  if (window.innerWidth <= 1050) showResults(false);
});
$("approve-reconstruction").addEventListener("click", (event) => sendConversation(event, "execute"));
$("revise-reconstruction-plan").addEventListener("click", () => {
  state.displayedPlan = null;
  state.planEditing = true;
  saveDraft();
  updateHeader();
  $("conversation-input").placeholder = "例如：宽度改为 12 米；背面补窗；先只建主体。提交后重新确认计划。";
  $("conversation-input").focus();
  showToast("在对话框填写要修改的参数，然后点击「更新参数计划」。本轮不会修改模型。");
});
$("conversation-input").addEventListener("input", () => {
  saveDraft();
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
$("start-agent-session").addEventListener("click", () => openConnectDialog());
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
  saveDraft();
  $("conversation-input").focus();
  updateHeader();
});
async function browseProject(projectId) {
  if (!projectId || projectId === state.projectId || state.switchingProject || (state.busy && !state.runningProjectId)) return;
  state.switchingProject = true;
  const running = state.runningProjectId;
  state.busy = true;
  try { await loadProject(projectId); showResults(false); }
  catch (error) { showToast(friendlyError(error), true); }
  finally {
    state.switchingProject = false;
    state.busy = !!state.runningProjectId;
    document.body.classList.remove("sidebar-open"); $("mobile-menu").setAttribute("aria-expanded", "false");
    updateHeader();
    if (!running) await observeRunningTurn();
  }
}

$("project-history").addEventListener("click", async (event) => {
  const removal = event.target.closest("[data-delete-project]");
  if (removal) { await deleteProject(removal.dataset.deleteProject); return; }
  const item = event.target.closest("[data-project]");
  if (item) await browseProject(item.dataset.project);
});
$("cancel-project").addEventListener("click", () => $("project-dialog").close());
$("project-select").addEventListener("change", async (event) => {
  await browseProject(event.target.value);
  event.target.value = state.projectId;
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
    saveDraft();
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
  const images = new Set(sourceImages().map(ref => ref.source));
  const files = pendingAttachmentSources().filter(path => !images.has(path));
  $("attachment-list").hidden = !!pendingMessage || !files.length;
  $("attachment-list").innerHTML = files.map(path => `<a class="file-chip" href="${projectFileUrl(path)}" target="_blank" rel="noopener">${escapeHtml(path.split("/").pop())}</a>`).join("");
}
async function uploadAttachments(files) {
  if (!files.length) return;
  if (!state.projectId) { showToast("请先新建或选择建模会话，再上传资料。", true); return; }
  if (state.busy) { showToast("本轮正在处理，请结束后再上传资料。", true); return; }
  if (files.some(f => f.size > 25 * 1024 * 1024)) { showToast("单个文件不能超过 25 MiB，请压缩或拆分后上传。", true); $("reference-file").value = ""; return; }
  const images = files.filter(f => f.type.startsWith("image/") || /\.(png|jpe?g|webp|gif|bmp|tiff?)$/i.test(f.name));
  if (images.length + sourceImages().length > 8) {
    showToast("每个会话最多使用 8 张参考图。请减少选择的图片数量；完整多视图整图可直接上传。", true);
    $("reference-file").value = "";
    return;
  }
  // Capture one context for the batch, even if the user keeps typing during upload.
  const referenceOptions = {evidence_role: "auto", role_context: $("conversation-input").value, batch_image_count: images.length};
  // Hold one busy state across a mixed batch; sending/switching cannot race
  // the transition from images to documents.
  state.busy = true;
  let completed = 0;
  beginProgress(`正在上传 ${files.length} 个资料文件`);
  try {
    for (const file of files) {
      const category = images.includes(file) ? "reference" : /\.(dxf|dwg)$/i.test(file.name) ? "site" : "brief";
      if (await uploadFile(category, file, `${category}-files`, false, referenceOptions)) completed++;
      updateHeader();
    }
    showToast(`已上传 ${completed} / ${files.length} 个文件${completed < files.length ? "，失败的文件请重新上传" : "。请描述建模要求后发送"}。`, completed < files.length);
  } finally { endProgress(); state.busy = false; $("reference-file").value = ""; updateHeader(); }
}
$("conversation-input").addEventListener("paste", event => {
  const files = Array.from(event.clipboardData?.files || []);
  if (files.length) {
    event.preventDefault();
    const text = event.clipboardData.getData("text/plain");
    if (text) {
      event.target.setRangeText(text, event.target.selectionStart, event.target.selectionEnd, "end");
      saveDraft();
      updateHeader();
    }
    uploadAttachments(files);
  }
});
$("conversation-form").addEventListener("dragover", event => {
  if (Array.from(event.dataTransfer?.types || []).includes("Files")) event.preventDefault();
});
$("conversation-form").addEventListener("drop", event => {
  const files = Array.from(event.dataTransfer?.files || []);
  if (files.length) { event.preventDefault(); uploadAttachments(files); }
});
$("prepare-plan").addEventListener("click", event => {
  if (!$("conversation-input").value.trim()) $("conversation-input").value = "信息已确认，请整理建模计划，标明估算与需要我确认的内容。";
  sendConversation(event, "plan");
});
$("setup-model").addEventListener("click", openModelSettings);
$("use-estimates").addEventListener("click", () => {
  $("conversation-input").value = ($("conversation-input").value.trim() ? $("conversation-input").value.trim() + "\n" : "") + "没有实测尺寸，请保留我已说明的要求，对未知尺寸提出合理估算并标明；未说明的范围先以外部建筑为主，背面可合理推断并标明，支持多角度查看。先整理计划供我检查，不要开始建模。";
  saveDraft(); updateHeader(); $("conversation-input").focus();
});
$("conversation-input").addEventListener("keydown", event => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter" && !event.isComposing && !$("conversation-send").disabled) sendConversation(event);
});
window.addEventListener("beforeunload", saveDraft);
function openConnectDialog(executeAfterConnect = false) {
  if (state.busy || !state.projectId) return;
  connectDialogGeneration++;
  pendingExecutionProject = executeAfterConnect ? state.projectId : null;
  $("connect-status").textContent = executeAfterConnect
    ? "计划和资料已保留。连接本会话的独立模型后才会开始建模；也可以稍后再连接。"
    : "交流与分析无需连接；开始建模前才需要连接。";
  $("connect-check").disabled = false;
  $("connect-open").disabled = false;
  $("connect-open").textContent = executeAfterConnect ? "连接并执行已批准计划" : "打开项目模型并连接";
  $("connect-manual").open = false;
  if (!$("connect-dialog").open) $("connect-dialog").showModal();
}

function closeConnectDialog() {
  connectDialogGeneration++;
  pendingExecutionProject = null;
  $("connect-dialog").close();
}

function isCurrentConnectDialog(generation, projectId) {
  return generation === connectDialogGeneration && projectId === state.projectId && $("connect-dialog").open;
}

async function checkConnectDialog() {
  if (state.busy || !$("connect-dialog").open || $("connect-check").disabled || $("connect-open").disabled) return;
  const generation = connectDialogGeneration;
  const projectId = state.projectId;
  $("connect-check").disabled = true;
  $("connect-status").textContent = "正在检查本机连接…";
  try {
    const result = await api(`/api/projects/${encodeURIComponent(projectId)}/connector`);
    if (!isCurrentConnectDialog(generation, projectId)) return;
    $("connect-status").textContent = result.reachable ? "MCP 桥接已响应。本次仅检查连接，未打开或绑定项目模型。需要建模时，请使用下方的项目连接按钮。" : friendlyError(new Error(result.detail || "请在 SketchUp 扩展菜单启动 Kongxing Local Bridge，然后重试。"));
  } catch (_) {
    if (isCurrentConnectDialog(generation, projectId)) $("connect-status").textContent = "连接未就绪，请检查 SketchUp 与插件是否已启动。";
  } finally { if (isCurrentConnectDialog(generation, projectId)) $("connect-check").disabled = false; }
}

async function connectCurrentProject() {
  if (state.busy || !$("connect-dialog").open || $("connect-open").disabled || $("connect-check").disabled) return;
  const generation = connectDialogGeneration;
  const projectId = state.projectId;
  $("connect-open").disabled = true;
  $("connect-status").textContent = "正在自动检查连接；成功后打开本会话独立模型…";
  try {
    const result = await api(`/api/projects/${encodeURIComponent(projectId)}/connector`);
    if (!isCurrentConnectDialog(generation, projectId)) return;
    $("connect-status").textContent = result.reachable ? "MCP 已连接，正在打开并校验项目副本…" : "正在启动 SketchUp，并尝试连接已安装的插件…";
    if (await startAgentSession()) {
      if (!isCurrentConnectDialog(generation, projectId)) return;
      const executeAfterConnect = pendingExecutionProject === projectId;
      closeConnectDialog();
      if (executeAfterConnect) await sendConversation(null, "execute");
    }
  } catch (error) {
    if (isCurrentConnectDialog(generation, projectId)) $("connect-status").textContent = friendlyError(error);
  } finally { if (isCurrentConnectDialog(generation, projectId)) $("connect-open").disabled = false; }
}

$("connect-close").addEventListener("click", closeConnectDialog);
$("connect-dismiss").addEventListener("click", closeConnectDialog);
$("connect-dialog").addEventListener("cancel", event => { event.preventDefault(); closeConnectDialog(); });
$("connect-check").addEventListener("click", checkConnectDialog);
$("connect-open").addEventListener("click", connectCurrentProject);
let copyOwnershipPreview = null;
async function copyOwnership(action) {
  if (state.busy || !$("connect-dialog").open) return;
  const projectId = state.projectId;
  const generation = connectDialogGeneration;
  if (action === "confirm" && (!copyOwnershipPreview || copyOwnershipPreview.target_project_id !== projectId)) return;
  state.busy = true;
  $("copy-ownership-preview").disabled = true;
  $("copy-ownership-confirm").disabled = true;
  $("copy-ownership-status").textContent = action === "preview" ? "正在只读核对来源与副本…" : "正在校验并迁移独立副本归属…";
  try {
    const result = await api(`/api/projects/${encodeURIComponent(projectId)}/model-copy-ownership`, {
      method: "POST", headers: {"Content-Type":"application/json"},
      body: JSON.stringify({action, receipt_id: action === "confirm" ? copyOwnershipPreview.receipt_id : undefined}),
    });
    if (!isCurrentConnectDialog(generation, projectId)) return;
    if (action === "preview") {
      copyOwnershipPreview = result;
      $("copy-ownership-status").textContent = `来源：${result.source_project_name}（${result.source_project_id}）；目标：${result.target_project_name}（${result.target_project_id}）。独立副本、根对象与版本已核对。请确认仅迁移归属。`;
      $("copy-ownership-confirm").disabled = false;
    } else {
      copyOwnershipPreview = null;
      $("copy-ownership-status").textContent = "副本归属已迁移并保存，几何、层级与材质指纹一致。请重新连接并检查模型；尚未执行局部修改。";
      showToast("副本归属已恢复；原件未变。", false);
    }
  } catch (error) {
    copyOwnershipPreview = null;
    if (isCurrentConnectDialog(generation, projectId)) $("copy-ownership-status").textContent = friendlyError(error);
  } finally {
    state.busy = false;
    $("copy-ownership-preview").disabled = false;
    updateHeader();
  }
}
$("copy-ownership-preview").addEventListener("click", () => copyOwnership("preview"));
$("copy-ownership-confirm").addEventListener("click", () => copyOwnership("confirm"));
let connectorSetupGeneration = 0;
let connectorSetupInfo = null;
let connectorSetupBusy = false;
function closeConnectorSetup() {
  connectorSetupGeneration++;
  $("connector-setup-dialog").close();
}
function renderConnectorSetup() {
  const info = connectorSetupInfo || {};
  const year = Number($("connector-sketchup-version").value);
  const selected = (info.installations || []).find(item => item.year === year) || ((info.compatibility_policy?.candidate_years || []).includes(year) ? {year, name: `SketchUp ${year}`, manual:true} : null);
  const existing = info.configuration_kind === "existing";
  const legacyPlugin = selected?.plugin_kind === "existing";
  const available = info.platform_supported && info.package_available && !!selected && selected.year >= 2019 && selected.year <= 2026;
  const download = $("connector-plugin-download");
  if (available) download.href = "/api/connectors/sketchup/plugin";
  else download.removeAttribute("href");
  download.setAttribute("aria-disabled", String(!available));
  $("connector-runtime-install").disabled = !available || info.configured || connectorSetupBusy;
  $("connector-runtime-install").textContent = info.configured ? "已有连接配置 · 已保留" : "安装本机连接程序";
  $("connector-setup-check").disabled = connectorSetupBusy;
  download.textContent = existing || legacyPlugin ? "重新下载插件 (.rbz) · 不自动覆盖" : "下载 SketchUp 插件 (.rbz) ↓";
  $("connector-version-note").textContent = selected?.manual ? "手动选择：本机未检测到此版本。仅配置通用桥接，插件须在你自己的 SketchUp 中安装并检查连接。" : selected
    ? `${selected.name}（本机检测结果，不代表仅支持此版本） · ${selected.plugin_present ? "检测到插件文件；仍需检查实际连接" : "尚未检测到插件"} · 兼容性尚未验证`
    : info.installations?.length ? "请选择你要连接的 SketchUp 版本，不会自动替换。" : "没有识别到 SketchUp。请先安装或注册你已有的软件，本窗口不会替你安装其他版本。";
  $("connector-package-note").textContent = existing || legacyPlugin
    ? "已有配置已保留，可先检查连接。重新下载不会安装或覆盖现有插件；请勿在原插件可用时重复安装。"
    : !info.platform_supported ? "当前安装程序仅适用于 Windows。"
    : !info.package_available ? "安装包尚未准备好；下载与安装暂不可用。"
    : info.publication === "private_local_trial" ? "本机试用包：尚未完成公开分发许可审查和新电脑原生验收，不作为正式发行版。"
    : "安装包已就绪；仍需在所选软件版本中检查原生连接。";
}
async function openConnectorSetup() {
  if (state.busy || connectorSetupBusy) return;
  const generation = ++connectorSetupGeneration;
  connectorSetupInfo = null;
  $("connector-setup-status").textContent = "正在读取本机安装状态…";
  $("connector-runtime-install").disabled = true;
  $("connector-plugin-download").removeAttribute("href");
  $("connector-setup-check").disabled = true;
  $("connector-sketchup-version").innerHTML = "";
  if (!$("connector-setup-dialog").open) $("connector-setup-dialog").showModal();
  try {
    const info = await api("/api/connectors/sketchup/setup");
    if (generation !== connectorSetupGeneration || !$("connector-setup-dialog").open) return;
    connectorSetupInfo = info;
    $("connector-sketchup-version").innerHTML = '<option value="">请选择你使用的版本</option>' + (info.installations || []).map(item => `<option value="${item.year}">${escapeHtml(item.name)} · 已检测</option>`).join("") + (info.compatibility_policy?.candidate_years || []).filter(year => !(info.installations || []).some(item => item.year === year)).map(year => `<option value="${year}">SketchUp ${year} · 手动选择 / 待验证</option>`).join("");
    if (info.installations?.length === 1) $("connector-sketchup-version").value = String(info.installations[0].year);
    renderConnectorSetup();
    $("connector-setup-status").textContent = info.configured ? "已发现连接配置；尚未检查实际 MCP 连通性。" : "请选择软件版本，按顺序完成插件和本机连接程序安装。";
  } catch (error) {
    if (generation === connectorSetupGeneration) $("connector-setup-status").textContent = friendlyError(error);
  }
}
async function installConnectorRuntime() {
  if (connectorSetupBusy || state.busy || $("connector-runtime-install").disabled) return;
  const generation = connectorSetupGeneration;
  connectorSetupBusy = true; renderConnectorSetup();
  $("connector-setup-status").textContent = "正在校验安装文件并配置本机连接程序；不会修改模型…";
  try {
    const result = await api("/api/connectors/sketchup/install", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({confirm_install:true, year:Number($("connector-sketchup-version").value), manual_version:!(connectorSetupInfo?.installations || []).some(item => item.year === Number($("connector-sketchup-version").value))})});
    if (generation !== connectorSetupGeneration) return;
    connectorSetupInfo = await api("/api/connectors/sketchup/setup");
    $("connector-setup-status").textContent = result.status === "runtime_installed" ? "本机连接程序已安装并通过启动自检。请在 SketchUp 启动插件，然后检查 MCP；尚未验证原生连接。" : "已有连接配置已保留，未覆盖文件。请继续检查 MCP。";
  } catch (error) {
    if (generation === connectorSetupGeneration) $("connector-setup-status").textContent = friendlyError(error);
  } finally {
    connectorSetupBusy = false;
    if (generation === connectorSetupGeneration) renderConnectorSetup();
  }
}
async function checkConnectorSetup() {
  if (state.busy || connectorSetupBusy || !state.projectId || $("connector-setup-check").disabled) return;
  const generation = connectorSetupGeneration, projectId = state.projectId;
  $("connector-setup-check").disabled = true;
  $("connector-setup-status").textContent = "正在只读检查 MCP 与 SketchUp…";
  try {
    const result = await api(`/api/projects/${encodeURIComponent(projectId)}/connector`);
    if (generation !== connectorSetupGeneration || projectId !== state.projectId) return;
    $("connector-setup-status").textContent = result.reachable ? "MCP 桥接已响应。尚未打开或绑定项目模型，也未修改几何。" : friendlyError(new Error(result.detail || "插件尚未响应，请在 SketchUp 启动 Local Bridge 后重试。"));
  } catch (error) {
    if (generation === connectorSetupGeneration) $("connector-setup-status").textContent = friendlyError(error);
  } finally {
    if (generation === connectorSetupGeneration) $("connector-setup-check").disabled = false;
  }
}
$("connector-setup-open").addEventListener("click", openConnectorSetup);
$("connector-setup-close").addEventListener("click", closeConnectorSetup);
$("connector-setup-dialog").addEventListener("cancel", event => {event.preventDefault();closeConnectorSetup();});
$("connector-sketchup-version").addEventListener("change", renderConnectorSetup);
$("connector-runtime-install").addEventListener("click", installConnectorRuntime);
$("connector-setup-check").addEventListener("click", checkConnectorSetup);
async function observeRunningTurn() {
  if (!state.projectId || state.busy) return;
  const projectId = state.projectId;
  const generation = progressGeneration;
  observedRunningTurn = false;
  // A reload/switch can find a still-running turn. Do not open a repeat-send
  // window while its status request is in flight.
  state.busy = true; updateHeader();
  try {
    const progress = await api(`/api/projects/${encodeURIComponent(projectId)}/agent/progress`);
    if (projectId !== state.projectId || generation !== progressGeneration) return;
    renderTurnControls(progress);
    if (!progress.running) return;
    state.runningProjectId = projectId;
    observingTurn = true; observedRunningTurn = true;
    beginProgress("已恢复正在处理的回合");
    startLiveProgress();
  } catch (_) {
    if (projectId === state.projectId && generation === progressGeneration) {
      // Unknown is not idle. Keep sending locked and retry read-only status
      // checks until the server can confirm whether this turn has finished.
      observingTurn = true;
      state.runningProjectId = projectId;
      beginProgress("连接暂时中断，正在同步本轮状态");
      startLiveProgress();
    }
  }
  finally {
    if (projectId === state.projectId && !observingTurn) { state.busy = false; updateHeader(); }
  }
}

function startLiveProgress() {
  const generation = ++progressGeneration;
  const runningProjectId = state.runningProjectId || state.projectId;
  clearInterval(progressTimer);
  let refreshing = false;
  const refresh = async () => {
    if (refreshing || generation !== progressGeneration) return;
    refreshing = true;
    try {
      const p = await api(`/api/projects/${encodeURIComponent(runningProjectId)}/agent/progress`);
      if (generation !== progressGeneration || !state.busy) return;
      const viewingRunning = state.projectId === runningProjectId;
      if (viewingRunning) renderTurnControls(p);
      else {
        renderTurnControls();
        $("operation-progress").textContent = "正在浏览历史会话；原任务继续在后台运行，可从左侧返回。";
      }
      if (!p.running) {
        if (observingTurn) {
          // Keep the observer and busy lock until the completed project has
          // loaded. On a read failure, the next poll retries synchronization.
          if (viewingRunning) await loadProject(runningProjectId);
          if (generation !== progressGeneration) return;
          const completedObservedTurn = observedRunningTurn;
          observingTurn = false; observedRunningTurn = false; endProgress(); state.busy = false; state.runningProjectId = null;
          const lastUser = [...(state.project.context.conversation || [])].reverse().find(m => m.role === "user");
          if (viewingRunning && completedObservedTurn && !state.project.agent_session?.error && lastUser?.content === $("conversation-input").value.trim()) {
            $("conversation-input").value = ""; saveDraft();
          }
          if (viewingRunning && state.project.agent_session?.reconstruction_state === "planned") $("parameter-plan").open = true;
          updateHeader(); showToast(!viewingRunning ? "后台任务已结束，可从左侧返回查看结果。" : state.project.agent_session?.error ? "本轮未完成，请查看原因；资料与草稿已保留。" : "本轮结果已同步，可以继续交流。", viewingRunning && !!state.project.agent_session?.error);
        }
        return;
      }
      if (observingTurn) observedRunningTurn = true;
      if (!viewingRunning) return;
      renderWorkflowChecks(p);
      $("operation-progress").textContent = `${p.stage} · ${p.elapsed_seconds} 秒${p.tool_calls == null ? "" : ` · 已调用 ${p.tool_calls} 次工具`}${p.failed_tool_calls ? `（${p.failed_tool_calls} 次失败）` : ""}${p.action !== "execute" ? " · 不改动模型" : p.committed_revisions.length ? " · 已提交实际模型修改" : " · 尚无新的模型提交"}`;
      if (p.preview_url) {
        $("preview-canvas").innerHTML = `<img src="${escapeHtml(p.preview_url)}" alt="建模中的最新 SketchUp 截图">`;
        $("preview-title").textContent = "建模中的真实截图";
      }
    } catch (_) { if (generation === progressGeneration && state.projectId === runningProjectId) {
      $("operation-progress").textContent = "进度暂时无法读取，当前回合仍在等待；请勿重复提交。";
      renderLiveActivity({running: true, ...state.activeTurnProgress}, true);
    } }
    finally { refreshing = false; }
  };
  refresh(); liveProgressTimer = setInterval(refresh, 3000);
}

function sameSavedApiConnection() {
  const saved = state.modelRouter?.providers?.litellm;
  const wire = $("api-model").value.trim();
  const model = $("provider-mode").value !== "deepseek" ? "openai/" + wire.replace(/^openai\//, "") : "deepseek/deepseek-flash";
  return !!saved?.credential_configured && saved.model === model && saved.api_base === $("api-base").value.trim().replace(/\/+$/, "");
}
function applyApiProvider() {
  const bai = $("provider-mode").value === "bai";
  const compatible = $("provider-mode").value === "compatible";
  $("api-model").value = compatible ? "" : bai ? "deepseek-v4.1-flash" : "deepseek-flash";
  $("api-model").readOnly = !bai && !compatible;
  $("api-base").value = compatible ? "" : bai ? "https://api.b.ai/v1" : "https://api.deepseek.com";
  $("api-base").readOnly = !compatible;
  $("api-base").placeholder = "https://服务商地址/v1";
  $("api-effort").value = "provider-default";
  $("api-key").value = "";
  $("api-key").placeholder = compatible ? "粘贴该服务商的 API Key" : bai ? "粘贴 B.AI API Key" : "粘贴 DeepSeek 官方 API Key";
  $("provider-address-note").textContent = compatible ? "填写服务商提供的 HTTPS Base URL（通常以 /v1 结尾，不要包含 /chat/completions）。此入口需要兼容 Chat Completions、支持图片和工具调用的模型；保存配置后仍需实际建模验证。" : bai ? "模型请求将发送到 B.AI。模型名称请使用 B.AI 模型列表中的标识。" : "模型请求将发送到 DeepSeek 官方。B.AI 等第三方平台的 Key 不能用于此地址。";
  $("provider-key-link").hidden = compatible;
  $("provider-key-link").href = bai ? "https://chat.b.ai/key" : "https://platform.deepseek.com/api_keys";
  $("saved-key-status").textContent = sameSavedApiConnection() ? "已保存此连接；保持原模型和地址可留空 Key。" : "请填写所选服务商的 Key；不会把其他连接的 Key 自动发往此地址。";
}
function openModelSettings() {
  if (routeInfo("economy").provider === "managed-responses") {
    showToast("模型由 K Studio 服务端配置。当前为托管 Agent 内部测试，供应商质量尚未验收；普通用户无需填写 API Key。");
    return;
  }
  const saved = state.modelRouter?.providers?.litellm;
  $("provider-mode").value = saved?.api_base === "https://api.b.ai/v1" ? "bai" : saved?.api_base && saved.api_base !== "https://api.deepseek.com" ? "compatible" : "deepseek";
  applyApiProvider();
  if (saved?.api_base === "https://api.b.ai/v1" && saved.model?.startsWith("openai/")) $("api-model").value = saved.model.slice(7);
  if ($("provider-mode").value === "compatible") {
    $("api-base").value = saved.api_base;
    $("api-model").value = (saved.model || "").replace(/^openai\//, "");
  }
  $("forget-api-key").disabled = !saved?.credential_configured;
  $("api-effort").value = sameSavedApiConnection() ? routeInfo("economy").reasoning_effort : "provider-default";
  $("saved-key-status").textContent = sameSavedApiConnection() ? "已保存此连接；保持原模型和地址可留空 Key。" : "请填写所选服务商的 Key；不会把其他连接的 Key 自动发往此地址。";
  $("model-settings-status").textContent = "";
  $("model-settings-dialog").showModal();
}
$("provider-mode").addEventListener("change", applyApiProvider);
$("model-settings-toggle").addEventListener("click", openModelSettings);
$("forget-api-key").addEventListener("click", async () => {
  try {
    state.modelRouter = await api("/api/model-settings/credential", {method:"DELETE"});
    $("api-key").value = ""; refreshTierLabels(); updateHeader();
    $("saved-key-status").textContent = "本机已移除保存的 Key。";
    $("api-key").placeholder = "粘贴所选服务商的 API Key";
    $("forget-api-key").disabled = true;
    $("model-settings-status").textContent = "已移除本机保存的 Key；再次使用需重新填写。";
  } catch (error) { $("model-settings-status").textContent = friendlyError(error); }
});
$("model-settings-close").addEventListener("click", () => { $("api-key").value = ""; $("model-settings-dialog").close(); });
$("model-settings-form").addEventListener("submit", async event => {
  event.preventDefault();
  const button = $("model-settings-form").querySelector('button[type="submit"]');
  if (button.disabled) return;
  if (!$("api-key").value.trim() && !sameSavedApiConnection()) {
    $("model-settings-status").textContent = "请先填写所选服务商的 API Key，再保存为默认。";
    $("api-key").focus();
    return;
  }
  button.disabled = true;
  $("model-settings-status").textContent = "正在设置连接…";
  try {
    state.modelRouter = await api("/api/model-settings", {method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({mode: $("provider-mode").value, model: $("api-model").value, api_base: $("api-base").value, api_key: $("api-key").value, reasoning_effort: $("api-effort").value})});
    refreshTierLabels(); updateHeader(); $("brain-status").textContent = `建筑 Agent · ${routeInfo("economy").model} · ${routeReadinessLabel("economy")}`; $("model-settings-dialog").close();
    showToast(state.modelRouter.credential_storage === "windows-dpapi" ? "模型连接已加密保存在本机；重启自动恢复。尚未发送测试请求。" : "模型连接已设置；本机仅支持内存保存，重启需重新填写。");
  } catch (error) { $("model-settings-status").textContent = friendlyError(error); }
  finally { $("api-key").value = ""; button.disabled = false; }
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
async function removeReferenceImage(event) {
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
}
$("reference-gallery").addEventListener("click", removeReferenceImage);
$("conversation-history").addEventListener("click", removeReferenceImage);
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

let menuProjectId = null;
function closeProjectMenu() { $("project-context-menu").hidden = true; menuProjectId = null; }
$("project-history").addEventListener("contextmenu", event => {
  const item = event.target.closest("[data-project]");
  if (!item) return;
  event.preventDefault(); if (state.busy) return;
  menuProjectId = item.dataset.project;
  const menu = $("project-context-menu"); menu.hidden = false;
  menu.style.left = `${Math.max(0, Math.min(event.clientX, innerWidth - menu.offsetWidth - 8))}px`;
  menu.style.top = `${Math.max(0, Math.min(event.clientY, innerHeight - menu.offsetHeight - 8))}px`;
  $("project-context-delete").focus();
});
$("project-context-delete").addEventListener("click", async () => {
  const id = menuProjectId; closeProjectMenu(); if (id) await deleteProject(id);
});
document.addEventListener("pointerdown", event => { if (!event.target.closest("#project-context-menu")) closeProjectMenu(); });
document.addEventListener("keydown", event => { if (event.key === "Escape") closeProjectMenu(); });
window.addEventListener("resize", closeProjectMenu);
document.addEventListener("scroll", closeProjectMenu, true);

// Explicit opt-in keeps existing SketchUp sessions and defaults unchanged.
$("start-blender-session")?.addEventListener("click", async () => {
  if (!state.projectId || state.busy) return;
  state.busy = true;
  const button = $("start-blender-session");
  setBusy(button, true, "检查 Blender…");
  try {
    const result = await api(`/api/projects/${encodeURIComponent(state.projectId)}/blender/session`, { method: "POST" });
    state.project = result.project;
    updateHeader();
    setStatus("Blender 体块后端已连接。先制定计划，再执行；当前仅支持命名方盒及局部尺寸修改，尚非完整建筑复原。", "ready");
  } catch (error) {
    setStatus(friendlyError(error), "error");
  } finally {
    state.busy = false;
    setBusy(button, false);
    updateHeader();
  }
});

$("check-software-update").addEventListener("click", async () => {
  const button = $("check-software-update"); if (button.disabled) return;
  button.disabled = true; $("software-update-status").textContent = "正在检查正式版本…";
  try { const result = await api("/api/software-update"); $("software-update-status").textContent = result.message + (result.latest_tag ? ` 版本：${result.latest_tag}` : ""); }
  catch (_) { $("software-update-status").textContent = "暂时无法检查更新，当前版本和项目保持不变。"; }
  finally { button.disabled = false; }
});
