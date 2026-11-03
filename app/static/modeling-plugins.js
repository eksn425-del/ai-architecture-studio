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
  const names = {sketchup: 'SketchUp', blender: 'Blender'};
  const backendForProject = () => state.project?.agent_session?.modeling_backend || 'sketchup';
  const stopCheck = () => {
    checkGeneration++;
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
    connection = {projectId, backend:'sketchup', message:state.busy ? '连接状态待核验' : '正在检查 SketchUp 连接…'};
    window.renderModelingPlugins();
    if (state.busy) { scheduleCheck(); return; }
    const controller = new AbortController();
    currentController = controller;
    const timeout = setTimeout(() => controller.abort(), 5000);
    try {
      const result = await api(`/api/projects/${encodeURIComponent(projectId)}/connector`, {signal:controller.signal});
      if (generation !== checkGeneration || !picker.open || projectId !== state.projectId || backendForProject() !== 'sketchup') return;
      connection = {projectId, backend:'sketchup', message:result.reachable === true && result.project_bound === true
        ? '已连接 · 本会话模型已核验' : result.reachable === true ? 'MCP 可达 · 本会话尚未绑定' : '本地桥接未响应'};
    } catch (_) {
      if (generation !== checkGeneration || !picker.open || projectId !== state.projectId || backendForProject() !== 'sketchup') return;
      connection = {projectId, backend:'sketchup', message:'连接检查失败 · 请重试'};
    } finally {
      clearTimeout(timeout);
      if (generation === checkGeneration) {
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
      ? '通过 SketchUp MCP 连接本会话独立模型。选择工具后，再点击连接。'
      : '使用 K Studio 本机 Blender 连接器，当前不是外部 MCP 服务。选择后仍需批准计划才能建模。';
    if (changed && picker.open && backend === 'sketchup' && state.projectId) void refreshSketchUpConnection();
  };
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
