/* Desktop account controls; opaque tokens remain in the native DPAPI store. */
(() => {
  const el = id => document.getElementById(`cloud-account-${id}`);
  const dialog = el('dialog'), opener = el('open');
  let account = null, working = false, generation = 0, timer = null, deviceDeadline = 0;
  const taskRunning = () => typeof state !== 'undefined' && state.busy === true;
  const known = value => value === null || value === undefined ? '待同步' : String(value);
  function secureUrl(value) {
    const url = new URL(value);
    if (url.protocol !== 'https:' || url.username || url.password) throw new Error('账户服务地址未通过 HTTPS 校验。');
    return url;
  }
  async function request(path, body) {
    const response = await fetch('/api/cloud-account' + path, body === undefined ? {} : {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : `账户服务暂时不可用（${response.status}）`);
    return data;
  }
  function controls() {
    for (const id of ['device-start','logout','apply']) el(id).disabled = working || taskRunning();
    el('refresh').disabled = working;
    el('mode').disabled = working || taskRunning();
    el('model').disabled = working || taskRunning();
    el('fee-ack').disabled = working || taskRunning();
    if (el('mode').value === 'platform' && ![...el('model').options].some(o => o.value && o.selected && !o.disabled)) el('apply').disabled = true;
  }
  function showSource() {
    const platform = el('mode').value === 'platform';
    el('model').hidden = el('model-label').hidden = !platform;
    const fee = account?.byok;
    const paidByok = !platform && fee?.service_enabled === true && Number(fee.service_units) > 0;
    el('fee-label').hidden = !paidByok;
    el('fee-label-text').textContent = paidByok ? `我确认每次任务授权的 K 服务费为 ${fee.service_units} 额度；模型费用另由我的 API 服务商收取。` : '';
    el('cost-note').textContent = platform
      ? '平台任务从账户预占并按服务端价格结算，模型费与 K 服务费分列；未知供应商用量保持待核对，不显示为零。'
      : paidByok ? '自带 API 直接连接你的供应商；本平台只收取上方明确列出的任务服务费。价格变更需要重新确认。'
      : '自带 API 直接连接你的供应商，Key 留在本机。当前 K 服务费未启用，不发起云端收费请求。';
    controls();
  }
  function render(next) {
    account = next;
    el('auth').hidden = !next.configured;
    el('details').hidden = !next.authenticated && !next.account_restore_required;
    el('device-start').hidden = !!next.authenticated;
    el('logout').hidden = !next.authenticated;
    el('links').hidden = true;
    if (next.url) {
      const base = secureUrl(next.url);
      el('usage').href = new URL('/account/usage', base).href;
      el('login').href = new URL('/account/devices', base).href;
      el('links').hidden = false;
    }
    el('status').textContent = next.error || (!next.configured
      ? '云端账户服务尚未配置。本机项目和自带 API 仍可使用；当前没有可显示的云端余额。'
      : next.authenticated ? '本机账户已授权。余额来自云端；退出会撤销本机令牌，已完成模型不会被删除。'
      : '尚未授权这台电脑。点击登录后，在安全的账户网站核对设备验证码；本站登录本身不会自动授权桌面。');
    if (next.authenticated || next.account_restore_required) {
      el('user').textContent = next.user?.display_name || next.user?.id || (next.authenticated ? '已授权账户' : '账户需要恢复 · 尚未重新授权');
      const b = next.balance;
      el('balance').textContent = b ? `可用 ${known(b.available)} · 预占 ${known(b.reserved)} · 待结算 ${known(b.pending)} ${b.currency || '额度'}。价格版本：${b.price_version || '待确认'}` : '额度暂未取得，等待同步；不以零余额代替未知值。';
      el('mode').value = next.source_mode === 'platform' ? 'platform' : 'byok';
      el('model').replaceChildren(new Option('选择已开放的平台模型', ''));
      for (const model of next.models || []) {
        const option = new Option(`${model.name || model.id} · ${model.verified ? '已有验证记录' : '尚未验证'}`, model.id);
        option.disabled = model.enabled !== true;
        el('model').add(option);
      }
      el('model').value = next.selected_model || '';
      el('fee-ack').checked = false;
    }
    showSource();
  }
  async function refresh() {
    const current = generation;
    const next = await request('');
    if (current === generation && dialog.open) render(next);
    return next;
  }
  async function refreshModelRoute() {
    if (typeof api !== 'function' || typeof state === 'undefined') return;
    const runtime = await api('/api/status');
    state.modelRouter = runtime.model_router || null;
    state.nativeAgentAvailable = routeAvailable('economy');
    refreshTierLabels(); updateHeader();
    document.querySelector('.signal-dot')?.classList.toggle('ready', state.nativeAgentAvailable);
  }
  async function run(operation) {
    if (working || taskRunning()) { el('status').textContent = '请先等待当前建模回合结束，再变更账户或模型方式。'; return; }
    const current = generation;
    working = true; controls();
    try { await operation(); }
    catch (error) { if(current===generation && dialog.open) el('status').textContent = error.message; }
    finally { working = false; controls(); }
  }
  async function pollDevice(current, interval, failures = 0) {
    if (current !== generation || !dialog.open) return;
    if (Date.now() >= deviceDeadline) { el('device-status').textContent = '验证码已到期，请重新发起登录。'; return; }
    try {
      const result = await request('/device/poll', {});
      if (current !== generation || !dialog.open) return;
      if (result.status === 'authorized') {
        el('device').hidden = true;
        await refresh(); await refreshModelRoute();
        return;
      }
      if (result.status === 'expired_token' || result.status === 'access_denied') {
        el('device-status').textContent = result.status === 'access_denied' ? '账户网站未授权此设备，请核对后重新发起。' : '验证码已到期，请重新发起登录。';
        return;
      }
      el('device-status').textContent = '等待你在账户网站确认授权；尚未登录本机。';
      timer = setTimeout(() => pollDevice(current, interval), interval);
    } catch (error) {
      if (current !== generation || !dialog.open) return;
      el('device-status').textContent = `授权状态暂未同步：${error.message}`;
      if (failures < 2) timer = setTimeout(() => pollDevice(current, interval * 2, failures + 1), interval * 2);
    }
  }
  opener.addEventListener('click', async () => {
    generation++; dialog.showModal(); el('device').hidden = true;
    const current = generation;
    el('auth').hidden = el('details').hidden = el('links').hidden = true;
    el('status').textContent = '正在读取账户状态…';
    try { await refresh(); } catch (error) { if(current===generation && dialog.open) el('status').textContent = error.message; }
  });
  el('device-start').addEventListener('click', () => run(async () => {
    const current = generation;
    clearTimeout(timer);
    const result = await request('/device/start', {});
    if(current!==generation || !dialog.open)return;
    const uri = secureUrl(result.verification_uri);
    if(account?.url && uri.origin !== secureUrl(account.url).origin) throw new Error('授权地址与已配置账户服务不匹配。');
    el('user-code').textContent = result.user_code;
    el('verify').href = uri.href;
    el('device').hidden = false;
    el('device-status').textContent = '请打开授权页，核对上方验证码并确认设备。';
    deviceDeadline = Date.now() + Math.min(Number(result.expires_in) || 300, 900) * 1000;
    const interval = Math.max(Number(result.interval) || 5, 5) * 1000;
    timer = setTimeout(() => pollDevice(current, interval), interval);
  }));
  el('logout').addEventListener('click', () => run(async () => {
    await request('/logout', {}); await refresh(); await refreshModelRoute();
  }));
  el('apply').addEventListener('click', () => run(async () => {
    const current = generation;
    const mode = el('mode').value;
    const paid = mode === 'byok' && account?.byok?.service_enabled === true && Number(account.byok.service_units) > 0;
    if (paid && !el('fee-ack').checked) throw new Error('请先确认当前按任务收取的 K 服务费。');
    await request('/source', {mode, ...(mode === 'platform' ? {model_id:el('model').value} : {}), ...(paid ? {service_fee_acknowledged:true} : {})});
    await refresh(); await refreshModelRoute();
    if(current!==generation || !dialog.open)return;
    el('status').textContent = '模型方式已保存并同步。账户授权不代表供应商或建模软件已通过能力验收。';
  }));
  el('refresh').addEventListener('click', async () => { if (working) return; const current=generation;working=true;controls();try{await refresh();}catch(error){if(current===generation && dialog.open)el('status').textContent=error.message;}finally{working=false;controls();} });
  el('mode').addEventListener('change', () => {el('fee-ack').checked=false;showSource();});
  el('model').addEventListener('change', controls);
  el('close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => {generation++;clearTimeout(timer);opener.focus();});
})();
