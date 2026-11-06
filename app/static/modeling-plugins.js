// Choosing a destination never opens software or starts inference.
(() => {
  const picker = document.getElementById('modeling-plugins');
  if (!picker) return;
  let connection = null;
  let checkGeneration = 0;
  let refreshTimer = null;
  let currentController = null;
  let viewedProject = null;
  let viewedBackend = null;
  let instances = null;
  let instanceError = '';
  let selectingInstance = false;
  let checkingInstances = false;
  const names = {sketchup: 'SketchUp', blender: 'Blender'};
  const backendForProject = () => state.project?.agent_session?.modeling_backend || 'sketchup';
  const instanceSelect = document.getElementById('sketchup-instance-select');
  const selectedInstance = () => instances?.instances?.find(row => row.instance_id === instanceSelect.value);
  function renderInstances() {
    document.getElementById('sketchup-instance-picker').hidden = backendForProject() !== 'sketchup';
    const previous = instanceSelect.value;
    const rows = instances?.instances || [];
    instanceSelect.replaceChildren(new Option(rows.length ? '请选择已打开的窗口' : '没有可用窗口', ''));
    for (const row of rows) {
      const filename = row.model_name || row.title || row.model_path?.split(/[\\/]/).pop() || '未保存模型';
      instanceSelect.add(new Option(`SketchUp ${row.sketchup_version || '?'} · ${filename} · PID ${row.pid}${row.selectable !== true ? ' · 不可连接' : ''}`, row.instance_id));
    }
    instanceSelect.value = rows.some(row => row.instance_id === previous) ? previous : instances?.selected_instance_id || '';
    instanceSelect.disabled = state.busy || selectingInstance || checkingInstances || !rows.length;
    document.getElementById('sketchup-instances-refresh').disabled = state.busy || selectingInstance || checkingInstances;
    const selected = selectedInstance();
    document.getElementById('sketchup-instance-connect').disabled = state.busy || selectingInstance || checkingInstances || selected?.selectable !== true;
    document.getElementById('sketchup-instance-note').textContent = selectingInstance ? '正在核验所选窗口与本会话模型…'
      : checkingInstances ? '正在读取活跃窗口…' : instanceError || (selected?.selectable === false ? (selected.reason || '此窗口不是本会话已授权的模型。请使用下方连接入口打开本会话副本。')
      : instances?.detail || (rows.length ? '核对版本和模型后选择连接。不会修改窗口内模型，也不会开始建模。' : '未发现当前连接器的活跃窗口。请打开 SketchUp 并启用 K Studio 插件，再刷新；可在下方打开本会话副本。'));
  }
  const stopCheck = () => {
    checkGeneration++;
    checkingInstances = false;
    if (refreshTimer !== null) clearTimeout(refreshTimer);
    refreshTimer = null;
    currentController?.abort();
    currentController = null;
  };
  const scheduleCheck = () => {
    if (refreshTimer !== null) clearTimeout(refreshTimer);
    if (picker.open && state.projectId && backendForProject() === 'sketchup') {
      refreshTimer = setTimeout(() => { refreshTimer = null; void refreshSketchUpConnection(); }, 10000);
    }
  };
  async function refreshSketchUpConnection() {
    stopCheck();
    const projectId = state.projectId;
    if (!picker.open || !projectId || backendForProject() !== 'sketchup') return;
    const generation = checkGeneration;
    checkingInstances = !state.busy;
    connection = {projectId, backend:'sketchup', message:state.busy ? '连接状态待核验' : '正在检查 SketchUp 连接…'};
    window.renderModelingPlugins();
    if (state.busy) { scheduleCheck(); return; }
    const controller = new AbortController();
    currentController = controller;
    const timeout = setTimeout(() => controller.abort(), 5000);
    try {
      const [health, discovery] = await Promise.allSettled([
        api(`/api/projects/${encodeURIComponent(projectId)}/connector`, {signal:controller.signal}),
        api(`/api/connectors/sketchup/instances?project_id=${encodeURIComponent(projectId)}`, {signal:controller.signal})
      ]);
      if (generation !== checkGeneration || !picker.open || projectId !== state.projectId || backendForProject() !== 'sketchup') return;
      instances = discovery.status === 'fulfilled' ? discovery.value : null;
      instanceError = discovery.status === 'fulfilled' ? '' : '暂时无法读取 SketchUp 窗口。请检查连接器版本后刷新；未自动选择其他窗口。';
      if (health.status === 'rejected') throw health.reason;
      const result = health.value;
      connection = {projectId, backend:'sketchup', message:result.reachable === true && result.project_bound === true
        ? '已连接 · 本会话模型已核验' : result.reachable === true ? 'MCP 可达 · 本会话尚未绑定' : '本地桥接未响应'};
    } catch (_) {
      if (generation !== checkGeneration || !picker.open || projectId !== state.projectId || backendForProject() !== 'sketchup') return;
      connection = {projectId, backend:'sketchup', message:'连接检查失败 · 请重试'};
    } finally {
      clearTimeout(timeout);
      if (generation === checkGeneration) {
        checkingInstances = false;
        currentController = null;
        window.renderModelingPlugins();
        scheduleCheck();
      }
    }
  }
  window.setModelingConnection = (backend, message) => {
    stopCheck();
    connection = {projectId: state.projectId, backend, message};
    window.renderModelingPlugins();
    scheduleCheck();
  };
  window.renderModelingPlugins = () => {
    const session = state.project?.agent_session || {};
    const backend = session.modeling_backend || 'sketchup';
    const changed = viewedProject !== state.projectId || viewedBackend !== backend;
    if (changed) {
      stopCheck();
      connection = null;
      instances = null; instanceError = ''; instanceSelect.value = '';
      viewedProject = state.projectId;
      viewedBackend = backend;
    }
    document.getElementById('modeling-selected-label').textContent = names[backend];
    for (const button of picker.querySelectorAll('[data-modeling-backend]')) {
      const selected = button.dataset.modelingBackend === backend;
      button.setAttribute('aria-checked', String(selected));
      button.classList.toggle('selected', selected);
      button.disabled = state.busy || !state.projectId;
    }
    const checked = connection?.projectId === state.projectId && connection.backend === backend;
    document.getElementById('modeling-connection-status').textContent = checked ? connection.message
      : session.model_path ? '已保留项目模型 · 连接待核验' : '尚未连接项目模型';
    document.getElementById('modeling-plugin-note').textContent = backend === 'sketchup'
      ? 'MCP 负责连接建模软件；模型 API 在左侧“模型设置”单独配置。'
      : '使用 K Studio 本机 Blender 连接器，当前不是外部 MCP 服务。选择后仍需批准计划才能建模。';
    renderInstances();
    if (changed && picker.open && backend === 'sketchup' && state.projectId) void refreshSketchUpConnection();
  };
  instanceSelect.addEventListener('change', renderInstances);
  document.getElementById('sketchup-instances-refresh').addEventListener('click', () => {
    if (!state.busy && !selectingInstance) void refreshSketchUpConnection();
  });
  document.getElementById('sketchup-instance-connect').addEventListener('click', async () => {
    const selected = selectedInstance();
    if (state.busy || selectingInstance || checkingInstances || selected?.selectable !== true || !state.projectId) return;
    const projectId = state.projectId;
    stopCheck(); selectingInstance = true; state.busy = true; updateHeader();
    try {
      await api(`/api/projects/${encodeURIComponent(projectId)}/connector/instance`, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({instance_id:selected.instance_id, expected_model_path:selected.model_path, expected_model_guid:selected.model_guid})
      });
      if (projectId !== state.projectId) return;
      const project = await api(`/api/projects/${encodeURIComponent(projectId)}`);
      if (projectId !== state.projectId) return;
      state.project = project;
      showToast('窗口选择已保存，正在检查本会话绑定。尚未开始建模。');
    } catch (error) {
      if (projectId === state.projectId) { instanceError = friendlyError(error); showToast(instanceError, true); }
    } finally {
      selectingInstance = false; state.busy = false; updateHeader();
      if (projectId === state.projectId && picker.open) await refreshSketchUpConnection();
    }
  });
  picker.addEventListener('toggle', () => {
    if (picker.open) void refreshSketchUpConnection();
    else stopCheck();
  });
  picker.addEventListener('click', async event => {
    // Invalidate the previous result before the details element opens; its
    // toggle event is delivered asynchronously by the browser.
    if (!picker.open && event.target.closest('summary')) {
      stopCheck();
      connection = null;
      window.renderModelingPlugins();
      return;
    }
    const button = event.target.closest('[data-modeling-backend]');
    if (!button || state.busy || !state.projectId) return;
    const backend = button.dataset.modelingBackend;
    if (backend === (state.project?.agent_session?.modeling_backend || 'sketchup')) return;
    const projectId = state.projectId;
    state.busy = true;
    updateHeader();
    try {
      const result = await api(`/api/projects/${encodeURIComponent(projectId)}/modeling/backend`, {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({backend})
      });
      if (state.projectId !== projectId) return;
      state.project = result.project;
      state.displayedPlan = null;
      state.planEditing = false;
      connection = null;
      await loadParameterPlan();
      showToast(`已选择 ${names[backend]}。对话和原模型已保留，请连接后更新执行计划。`, false);
    } catch (error) {
      showToast(friendlyError(error), true);
    } finally {
      state.busy = false;
      updateHeader();
    }
  });
  document.addEventListener('pointerdown', event => {
    if (!picker.contains(event.target)) picker.open = false;
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && picker.open) {
      picker.open = false;
      picker.querySelector('summary').focus();
    }
  });
  window.renderModelingPlugins();
})();
