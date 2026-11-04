/* Personal desktop connection manager. Keys never enter browser storage. */
const KStudioConnections = (() => {
  const dialog = document.getElementById("connections-dialog");
  const form = document.getElementById("connection-form");
  const node = id => document.getElementById(`connection-${id}`);
  let snapshot = {connections: [], active_id: null}, editingId = null, working = false, capabilitiesChanged = false, sourceMode = 'byok';
  const selected = () => snapshot.connections.find(item => item.id === editingId);
  function setWorking(value) {
    working = value;
    for (const control of dialog.querySelectorAll("button, input, select")) control.disabled = value;
    if (!value) {
      node("use").disabled = !editingId || editingId === snapshot.active_id;
      node("remove").disabled = !editingId;
      node("disconnect").disabled = !snapshot.active_id;
      effortOptions();
    }
  }
  function effortOptions() {
    const config = selected()?.effective_configuration;
    const supported = config?.supported_efforts || ["provider-default", "low", "high"];
    for (const option of node("effort").options) option.disabled = !supported.includes(option.value);
  }
  function protocol() {
    const mode = node("mode").value;
    const responses = mode === "codex-responses";
    node("ack-label").hidden = !responses;
    node("effort").value = "provider-default";
    effortOptions();
    node("base").readOnly = mode === "deepseek" || mode === "bai";
    node("model").readOnly = mode === "deepseek";
    node("base").value = mode === "deepseek" ? "https://api.deepseek.com" : mode === "bai" ? "https://api.b.ai/v1" : "";
    node("model").value = mode === "deepseek" ? "deepseek-flash" : "";
    node("ack").checked = false;
    node("key").value = "";
    node("protocol-note").textContent = responses
      ? "高级连接：服务商须支持 Responses、流式 SSE、图片和函数工具。使用本机 Agent 运行时，鉴权只用你填写的 Key；不调用 Codex 账号。供应商兼容性需实际验证。"
      : "支持 Chat Completions 兼容接口。建模需要模型支持图片和工具调用；保存配置不会发送测试请求。";
    keyHint();
  }
  function keyHint() {
    const old = selected();
    const model = node("model").value.trim().replace(/^(openai|deepseek)\//, "");
    const same = old && old.mode === node("mode").value && old.api_base === node("base").value.trim().replace(/\/+$/, "") && old.model.replace(/^(openai|deepseek)\//, "") === model;
    node("key").placeholder = same ? "已加密保存；不更换模型和地址可留空" : "粘贴此服务商的 API Key";
  }
  function edit(id) {
    editingId = id || null;
    const item = selected();
    node("saved").value = editingId || "";
    node("name").value = item?.name || "";
    node("mode").value = item?.mode || "compatible";
    protocol();
    if (item) {
      node("base").value = item.api_base;
      node("model").value = item.mode === "codex-responses" ? item.model : item.model.replace(/^(openai|deepseek)\//, "");
      node("effort").value = item.reasoning_effort;
      node("ack").checked = item.mode === "codex-responses";
    }
    let capability = {}; try { capability = JSON.parse(item?.capabilities_json || "{}"); } catch (_) {}
    node("context").value = capability.context_window || "";
    node("output").value = capability.max_output_tokens || "";
    for (const field of ["vision", "tools", "streaming"]) node(field).checked = (capability[field] ?? item?.effective_configuration?.effective?.[field]) === true;
    capabilitiesChanged = false;
    const effective = item?.effective_configuration;
    node("effective").textContent = effective?.status === "unsupported" ? `当前配置不支持：${effective.reason}` : effective?.effective ? `实际协议：${effective.effective.protocol} · 推理：${effective.effective.requested_effort} · 上下文：${effective.effective.context_window} · 能力来源：${effective.effective.capability_source} · 验证：${effective.effective.verification_status || "NOT_RUN"}。供应商回报模型：${effective.reported?.model || "unknown"}` : "保存后读取实际配置；尚未调用供应商。";
    node("status").textContent = sourceMode === 'unavailable' ? '云账户配置需要恢复。请先在侧栏“账户与额度”重新登录或明确选择自带 API；未替换连接。' : sourceMode === 'platform' ? '当前选择平台模型。请先在侧栏“账户与额度”明确切换为自带 API，再变更本机连接；已有 Key 保留。' : item ? (item.id === snapshot.active_id ? "当前使用此配置；建模能力仍需验证，Key 不会回显。" : "此连接已保存；能力仍需验证。") : "新连接默认没有 Key，请自行填写。";
    keyHint(); setWorking(false);
  }
  function render(next) {
    snapshot = next;
    if (next.model_router) {
      state.modelRouter = next.model_router;
      state.nativeAgentAvailable = routeAvailable("economy");
      refreshTierLabels(); updateHeader();
      document.querySelector(".signal-dot").classList.toggle("ready", state.nativeAgentAvailable);
    }
    node("saved").replaceChildren(new Option("＋ 添加 API 连接", ""));
    for (const item of snapshot.connections) node("saved").add(new Option(`${sourceMode === 'byok' && item.id === snapshot.active_id ? "当前 · " : ""}${item.name}`, item.id));
    node("summary").textContent = sourceMode === 'unavailable' ? '账户配置未恢复 · 尚未启用模型方式' : sourceMode === 'platform' ? '当前使用平台模型 · 下面是本机保存的自带 API 配置' : snapshot.active_id
      ? `已保存 ${snapshot.connections.length} 个连接 · 重启自动恢复当前连接`
      : "尚未启用 API · 可以打开项目和连接建模软件";
  }
  async function run(operation, done) {
    if (working || state.busy) return;
    setWorking(true); node("status").textContent = "正在保存本机设置…";
    try {
      sourceMode = (await api('/api/cloud-account-config')).source_mode || 'byok';
      if (sourceMode === 'unavailable') throw new Error('云账户配置需要恢复。请先在侧栏“账户与额度”重新登录或明确选择自带 API；未更改连接或模型。');
      if (sourceMode === 'platform') throw new Error('当前选择平台模型。请先关闭此面板，在侧栏“账户与额度”明确选择自带 API；未更改连接或模型。');
      const next = await operation(); render(next); edit(done?.(next) || editingId);
    }
    catch (error) { node("status").textContent = friendlyError(error); }
    finally { node("key").value = ""; setWorking(false); }
  }
  async function open() {
    if (state.busy) { showToast("请等当前回合结束后再更换 API。"); return; }
    try {
      sourceMode = (await api('/api/cloud-account-config')).source_mode || 'byok';
      render(await api("/api/model-connections")); edit(snapshot.active_id);
      dialog.showModal();
    } catch (error) { showToast(friendlyError(error), true); }
  }
  form.addEventListener("submit", event => {
    event.preventDefault();
    const capabilities = {};
    if (node("context").value) capabilities.context_window = Number(node("context").value);
    if (node("output").value) capabilities.max_output_tokens = Number(node("output").value);
    for (const field of ["vision", "tools", "streaming"]) capabilities[field] = node(field).checked;
    const body = {capabilities_json: capabilitiesChanged ? JSON.stringify(capabilities) : selected()?.capabilities_json || "{}", id: editingId, name: node("name").value, mode: node("mode").value,
      model: node("model").value, api_base: node("base").value, api_key: node("key").value,
      reasoning_effort: node("effort").value, compatibility_acknowledged: node("ack").checked};
    run(() => api("/api/model-connections", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)}), next => next.active_id);
  });
  for (const field of ["context", "output", "vision", "tools", "streaming"]) node(field).addEventListener("input", () => { capabilitiesChanged = true; });
  node("saved").addEventListener("change", () => edit(node("saved").value));
  node("mode").addEventListener("change", protocol);
  for (const field of ["base", "model"]) node(field).addEventListener("input", keyHint);
  node("use").addEventListener("click", () => run(() => api("/api/model-connections/active", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({id:editingId})})));
  node("disconnect").addEventListener("click", () => run(() => api("/api/model-connections/active", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({id:null})})));
  node("remove").addEventListener("click", () => {
    if (!editingId) return;
    run(() => api(`/api/model-connections/${encodeURIComponent(editingId)}`, {method:"DELETE"}), () => { editingId = null; return null; });
  });
  node("close").addEventListener("click", () => { if (!working) dialog.close(); });
  dialog.addEventListener("cancel", event => { if (working) event.preventDefault(); });
  dialog.addEventListener("close", () => { node("key").value = ""; });
  return {open};
})();
