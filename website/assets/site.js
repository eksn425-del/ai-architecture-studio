/* Public control-plane UI. No provider keys, mock identities, or client-side settlement. */
(() => {
  'use strict';
  const main = document.getElementById('main');
  let config = {}, identity = {authenticated: false};
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const safeUrl = value => { if(!value)return ''; try { const u = new URL(value, location.origin); return !u.username && !u.password && (u.protocol === 'https:' || (u.origin === location.origin && u.protocol === location.protocol)) ? u.href : ''; } catch { return ''; } };
  async function api(path, options = {}) {
    const res = await fetch(path, {credentials:'same-origin', ...options, headers:{'Content-Type':'application/json', ...(identity.csrf_token ? {'X-CSRF-Token':identity.csrf_token} : {}), ...options.headers}});
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : data.error?.message || `服务暂时不可用（${res.status}）`);
    return data;
  }
  const page = (title, lead, body, kicker = 'K STUDIO / FORM & SPACE') => `<div class="wrap content-page"><header class="page-hero"><div class="breadcrumb"><a href="/">首页</a><span>/</span><span>${esc(title)}</span></div><div class="kicker">${kicker}</div><h1>${title}</h1><p>${lead}</p></header>${body}</div>`;
  const notice = text => `<div class="notice" role="status">${esc(text)}</div>`;
  const nav = '<nav class="account-tabs" aria-label="账户导航"><a href="/account/usage">额度与用量</a><a href="/account/orders">订单与充值</a><a href="/account/devices">设备与会话</a><button class="btn light small-btn" id="logout">退出账户</button></nav>';
  const statusLabel = value => ({reserved:'已预占',running:'执行中',settled:'已结算',pending_reconciliation:'费用待确认',created:'已创建',paid:'已支付',refunded:'已退款',refund_pending_reconciliation:'退款待核对',failed:'失败',cancelled:'已取消',pending:'处理中',checkout_pending:'等待支付',credit:'充值',reserve:'预占',settle:'结算',refund:'退款'}[value] || value || '待确认');
  const amount = value => value === null || value === undefined ? '待确认' : esc(value);
  function table(headers, rows) { return `<div class="table-overflow"><table class="compat-table"><thead><tr>${headers.map(x=>`<th scope="col">${esc(x)}</th>`).join('')}</tr></thead><tbody>${rows.length ? rows.map(row=>`<tr>${row.map(x=>`<td>${x}</td>`).join('')}</tr>`).join('') : `<tr><td colspan="${headers.length}">暂无记录。</td></tr>`}</tbody></table></div>`; }
  const authEnabled = () => config.auth?.available === true;
  const pricing = () => config.pricing || {confirmed:config.prices_confirmed, packages:config.packages || []};
  function authPage(kind) {
    const title = kind === 'register' ? '开始你的创作账户。' : kind === 'recover' ? '找回你的账户。' : '欢迎回来。';
    const custom = kind === 'register' ? config.auth?.registration_url : kind === 'recover' ? config.auth?.recovery_url : '';
    const returnTo=location.pathname==='/account/device' ? location.pathname+location.search : '';
    const url = custom && safeUrl(custom) || '/api/auth/login'+(returnTo?'?next='+encodeURIComponent(returnTo):'');
    return page(title, '登录用于云端账户、额度与设备。本机自带 API 模式不要求创建账户。', `<div class="auth-panel"><img src="/assets/k-monogram.svg" width="72" height="72" alt="K Studio"><h2>连接你的创作。</h2><p>使用已配置的身份服务完成验证。密码和验证码在认证服务处理，本站不模拟登录。</p>${authEnabled() ? `<a class="btn" href="${esc(url)}">${kind === 'recover' ? '前往身份服务恢复账户' : kind === 'register' ? '前往身份服务注册' : '安全登录'} ↗</a>` : '<button class="btn" disabled>账户服务尚未开放</button><p class="notice">认证服务尚未配置。不会创建演示账户或跳转为已登录。</p>'}<div class="auth-links"><a href="/auth/login">登录</a><a href="/auth/register">注册账户</a><a href="/auth/recover">恢复账户</a></div><p class="small">继续前请阅读 <a class="text-link" href="/privacy">隐私说明</a> 与 <a class="text-link" href="/terms">使用条款</a>。</p></div>`);
  }
  function downloadPage() {
    const r = config.release || {}, url = safeUrl(r.url || r.download_url || '');
    const ready = (r.download_available === true) && url && /^[a-f0-9]{64}$/i.test(r.sha256 || '') && r.version && r.size_bytes;
    return page('把工作台，带回你的电脑。', '下载前先确认发行状态、系统要求与已验证的软件版本。', `<div class="download-grid"><article class="download-card"><div class="kicker">WINDOWS DESKTOP</div><h2>K Studio</h2><p>${esc(r.channel || '候选版本 · 尚未公开发行')}</p>${ready ? `<a class="btn" href="${esc(url)}">下载 ${esc(r.version)} ↗</a>` : '<button class="btn" disabled>公开下载尚未开放</button>'}${notice(ready ? '请核对 SHA-256 与发布者；保留项目和旧版本后再更新。' : '尚无已验证且获准公开分发的安装包。此页不会提供占位下载链接。')}<dl class="metadata"><dt>版本</dt><dd>${esc(r.version || '未公布')}</dd><dt>大小</dt><dd>${r.size_bytes ? esc((r.size_bytes/1048576).toFixed(1))+' MiB' : '未公布'}</dd><dt>发布日期</dt><dd>${esc(r.published_at || r.date || '未公布')}</dd><dt>签名发布者</dt><dd>${esc(r.publisher || '未验证')}</dd><dt>签名状态</dt><dd>${esc(r.signing_status || '未验证')}</dd><dt>SHA-256</dt><dd class="hash">${esc(r.sha256 || '未提供')}</dd></dl></article><aside><h3>开始前，准备好三件事。</h3><ol class="steps"><li>Windows 电脑与合法安装的 SketchUp。</li><li>平台服务或你自己的兼容 API。</li><li>独立的项目副本与参考资料。</li></ol><a class="text-link" href="/docs/start">查看安装与连接指南 ↗</a><p class="notice">${esc(Array.isArray(r.limitations) ? r.limitations.join('；') : r.limitations || '目前主要验证环境为 SketchUp 2024。其他版本须逐项测试，不因检测到安装而视为支持。')}</p></aside></div><section class="subsection"><h2>版本与兼容范围</h2>${table(['软件','证据','状态'], (r.compatibility || [{name:'SketchUp',evidence:'本版逐版本验收清单尚未公布',status:'候选范围不代表已支持'},{name:'Blender / Rhino / Unity',evidence:'规划或实验',status:'不属当前正式支持'}]).map(x=>[esc(x.name),esc(x.evidence),esc(x.status)]))}<h3>系统要求</h3><p>${esc(Array.isArray(r.system_requirements) ? r.system_requirements.join('；') : r.system_requirements || '完整系统要求随验收发行公布；当前本机候选不证明所有 Windows / SketchUp 环境兼容。')}</p><h3>版本记录</h3>${Array.isArray(r.changelog) && r.changelog.length ? '<ul>'+r.changelog.map(x=>'<li>'+esc(typeof x==='string'?x:x.version+' · '+x.summary)+'</li>').join('')+'</ul>' : '<p>尚无已公布的公开发行记录。</p>'}<h3>更新与回退</h3><p>安装更新前退出运行中的建模任务、保存原生文件并备份项目。只接受匹配发行清单的安装包；失败后保留旧版及数据，不自动迁移或删除模型。</p></section>`);
  }
  function docsPage() {
    return page('连接好，再开始建模。','每一步都核对真实状态；模型服务、桥接和项目文件是三个独立环节。', `<div class="reading"><ol class="guide"><li><h2>安装与打开</h2><p>从下载页核对版本、签名和 SHA-256。安装桌面客户端后从桌面图标打开。本机工作台不作为公网服务器。</p><a class="text-link" href="/download">查看发行信息</a></li><li><h2>配置模型服务</h2><p>在输入框工具行打开“模型设置 → 模型 / 自带 API”。填入服务商给出的 API 地址、准确模型标识和 Key。保存表示配置已保存；图片、工具调用、流式与 usage 需要分别验证。</p><p>第三方 API Key 在本机配置，网站不收集。选择供应商实际支持的推理档位；未知能力应明确声明并保留未验证状态。</p></li><li><h2>连接 SketchUp</h2><p>在“建模工具”选择 SketchUp，打开连接向导。先在向导配置本机配对，再下载 .rbz，打开所选 SketchUp 的扩展程序管理器安装 K Studio Connector 并重启；插件会尝试自动启动。未响应时从 K Studio Connector 菜单启动。已有其他连接配置按原说明启用并保留。检测到软件不等于插件可用，桥接可达也不等于目标项目已绑定。</p></li><li><h2>绑定项目副本</h2><p>保存独立的空白或现有模型副本，再在连接向导核对文档路径、项目及只读检测结果。不要默认授权修改原件。显示已连接的必须是当前目标文档。</p></li><li><h2>讨论、批准与修改</h2><p>上传参考图并用自然语言讨论需求。检查尺寸估计、主体关系及保留范围，批准当前方案后开始建模。停止会阻止后续步骤，已完成的修改仍存在；恢复检查点是独立操作。</p></li><li><h2>保存与交付核对</h2><p>从“模型与文件”查看回传截图及版本、保存原生 SKP，下载后在 SketchUp 重新打开。保存成功不代表外观和构件质量已全部通过。</p></li></ol><h2>连接失败时</h2>${table(['现象','下一步'],[['软件未找到','确认已合法安装，当前版本在验证范围内。'],['桥接不可达','在 SketchUp 中检查插件加载与桥接服务，使用连接向导重新只读检测。'],['文档不匹配','核对当前打开副本的完整路径与项目绑定，不直接重试写入。'],['API 鉴权失败','核对服务商、地址与 Key；不要将 Key 发给反馈或截图。'],['执行状态未知','先检查最近成功提交、当前模型版本和保存文件，再决定继续；不要整轮重复建模。']])}</div>`);
  }
  function pricingPage() {
    const p=pricing();
    return page('每一次消耗，都有来处。','模型调用与 K Studio 服务费用分别记录，不用 Token 数冒充账单。', `<div class="mode-grid"><article class="mode-explanation"><h2>平台模型</h2><p>平台提供模型连接，账本分别记录模型费用、K 服务费用、预占与实际结算。</p></article><article class="mode-explanation"><h2>自带 API</h2><p>模型费用由你的服务商收取；K 服务费用仅按已公布并确认的规则收取。上游未知 usage 标为待确认，不当作零费用。</p></article></div>${notice(p.confirmed ? '以下套餐来自当前服务端价格版本。订单与支付回调决定入账状态。' : '正式价格、兑换率与失败结算规则尚未确认；暂不开放充值。测试单位不代表正式售价。')}<div id="packages"></div><a class="btn light" href="/account/orders">查看我的订单 ↗</a>`);
  }
  async function accountPage(path) {
    if (!identity.authenticated) return authPage('login');
    let body='';
    if (path === '/account/device') {
      const code=new URLSearchParams(location.search).get('user_code') || '';
      if(!code) return page('授权这台电脑。','请从桌面客户端发起登录，并打开它提供的授权链接。',notice('链接缺少验证码；本站不会猜测或自动绑定设备。'));
      const d=await api('/api/auth/device/details?user_code='+encodeURIComponent(code));
      body=`<div class="auth-panel"><h2>确认设备授权</h2><p>设备：${esc(d.device_name || '未命名设备')}</p><p>验证码：<strong>${esc(code)}</strong></p><p>只有当这个验证码与你正在使用的 K Studio 桌面一致时才确认。授权后，该电脑可按你的选择访问账户和模型服务；你可以在设备列表撤销。</p><p>有效期：${esc(d.expires ? new Date(d.expires*1000).toLocaleString() : '以服务器校验为准')}</p><button class="btn" id="approve-device" data-user-code="${esc(code)}">确认授权这台电脑</button><p id="device-approval-status" role="status" aria-live="polite"></p><a class="text-link" href="/account/devices">管理已授权设备</a></div>`;
    } else if (path.includes('/devices')) {
      const d=await api('/api/account/devices');
      body='<h2>已连接设备</h2>'+table(['设备','最近活动','操作'],(d.devices||[]).map(x=>[esc(x.device_name||x.name||x.id),esc(x.revoked ? '已撤销' : '有效至 '+ new Date(x.expires*1000).toLocaleString()),`<button class="btn light small-btn" data-revoke="${esc(x.id)}" ${x.revoked?'disabled':''}>撤销设备</button>`]));
    } else if(path.includes('/orders') || path.includes('payment-return')) {
      const d=await api('/api/account/orders'), orders=d.orders||[];
      const orderId=path.startsWith('/account/orders/') ? decodeURIComponent(path.split('/').pop()) : null;
      const chosen=orderId ? orders.filter(x=>x.id===orderId) : orders;
      body=`<h2>${path.includes('payment-return') ? '正在核对支付结果' : orderId ? '订单详情' : '订单与充值'}</h2><p>支付页面返回不代表入账。以下结果来自服务端；等待签名回调时可刷新本页。</p>${table(['订单','金额 / 单位','状态','创建时间'],chosen.map(x=>[`<a class="text-link" href="/account/orders/${encodeURIComponent(x.id)}">${esc(x.id)}</a>`,`${amount(x.amount_minor ?? x.amount)} ${esc(x.currency || '')}`,esc(statusLabel(x.state||x.status)),esc(x.created_at||new Date(x.created*1000).toLocaleString())]))}${orderId&&!chosen.length ? notice('未找到属于当前账户的订单。') : ''}<button class="btn light" id="refresh-page">刷新服务端状态</button><h3 class="subsection">充值套餐</h3><div id="packages"></div><p class="small">退款和结算以订单记录与已公布条款为准。需要协助可在反馈页提交订单号，不要提交支付凭据或密码。</p>`;
    } else {
      const d=await api('/api/account/usage'),b=d.balance||{};
      body=`<div class="wallet-grid">${[['可用',b.available],['预占',b.reserved],['待结算',b.pending]].map(([n,v])=>`<article class="wallet-card"><div class="label">${n}额度</div><div class="amount">${amount(v)}</div><p>${esc(b.currency||'未确认单位')}</p></article>`).join('')}</div><p class="plain-note">价格版本：${esc(b.price_version||'待确认')}。未知模型费用保持待确认，上游 BYOK 费用不等同本平台余额。</p><h2>任务与费用</h2>${table(['任务','模型费用','K 服务费用','状态'],(d.tasks||[]).map(x=>[esc(x.name||x.task_id||x.id),amount(x.model_units ?? x.model_cost),amount(x.service_units ?? x.service_cost),esc(statusLabel(x.state||x.status))]))}<h3>账本记录</h3>${table(['事件','金额','状态','时间'],(d.events||[]).map(x=>[esc(statusLabel(x.type||x.kind)),amount(x.amount),esc(x.status||'已记录'),esc(x.created_at||new Date(x.created*1000).toLocaleString())]))}`;
    }
    return page('你的创作账户。',`当前账户：${esc(identity.user?.display_name||identity.user?.id)}`,nav+body);
  }
  const legal = {
    '/privacy':['隐私与数据流','本机项目、参考图、原生模型与 API 配置用于你发起的任务。向模型服务发送资料前，应确认该服务的隐私条款；本机运行不代表图片不会发送给所选模型。','本网站的账户会话、订单与账本存于云端服务。自带 API Key 不在此网站输入或保存。反馈只提交必要的脱敏信息；不要上传密钥、私人模型或第三方个人信息。','正式运营主体、联系渠道、数据保留期限与权利请求流程须在公开运营前配置并公布；当前页面不虚构该信息。'],
    '/terms':['使用条款与边界','K Studio 用于辅助建筑设计与可编辑建模。生成的尺寸、构件、规范判断与外观需要设计者核对，不构成施工、结构安全或法规合规证明。','使用合法模型服务、软件与有权使用的素材。执行前核对方案、文档和修改范围；保留原件与恢复副本。支持版本、价格和退款规则以当前发行及运营配置为准。','公开服务尚未开放时，不接受付款或承诺未验收兼容性。正式服务主体、争议处理与退款规则将在开放前公布。'],
    '/licenses':['开源与素材归属','K Studio 建立在所采用的开源软件与其许可之上。发布安装包应随附第三方许可、NOTICE 与组件版本清单；上游开源不等于可取消署名或许可义务。','官网 K 标志、绿金品牌与建筑示意沿用用户提供的 R2 设计资产。首页建筑图与工作台局部是产品示意，不作为真实模型质量证据。','DSH、连接器与其他依赖的具体版本和许可以对应发行包的 SBOM / THIRD_PARTY_NOTICES 为准。历史展示中的来源说明继续保留。']
  };
  async function packages() {
    const target=document.getElementById('packages'); if(!target)return;
    const p=pricing(), list=Array.isArray(p.packages)?p.packages:Object.entries(p.packages||{}).map(([id,v])=>({id,...v}));
    target.innerHTML=list.length ? list.map(x=>`<article class="package"><h3>${esc(x.name||x.label||x.id)}</h3><p>${amount(x.credits)} 额度 · ${amount(x.amount_minor ?? x.amount)} ${esc(x.currency||'测试单位')}（最小货币单位）</p><button class="btn" data-buy="${esc(x.id)}" ${!p.confirmed||!identity.authenticated||!config.payment?.available?'disabled':''}>${!identity.authenticated?'登录后查看购买':p.confirmed&&config.payment?.available?'创建支付订单':'充值尚未开放'}</button></article>`).join('') : notice('暂无已公布的充值套餐。');
  }
  async function render() {
    const path=location.pathname.replace(/\/$/,'')||'/';
    if(path==='/') { const res=await fetch('/assets/home.html'); if(!res.ok)throw new Error('首页资源加载失败'); main.innerHTML=await res.text(); }
    else if(path==='/download') main.innerHTML=downloadPage();
    else if(path.startsWith('/docs/'))main.innerHTML=docsPage();
    else if(path==='/pricing')main.innerHTML=pricingPage();
    else if(path.startsWith('/auth/'))main.innerHTML=authPage(path.split('/').pop());
    else if(path.startsWith('/account/'))main.innerHTML=await accountPage(path);
    else if(path==='/status'){const d=await api('/api/status'); main.innerHTML=page('服务状态。','以下为当前服务实际响应；不以页面打开代替模型或软件可用。', `<div class="notice">${esc(['ok','ready'].includes(d.database?.status) ? '数据库可用 · 其他组件独立检查' : '存在待配置或异常组件')}</div>${table(['组件','状态'],Object.entries(d.components||{database:d.database?.status,model_service:d.model_service,payment_service:d.payment_service}).map(([k,v])=>[esc(k),esc(typeof v==='object'?v.status:v)]))}<p>检查时间：${esc(d.checked_at||new Date().toISOString())}</p>${(d.known_issues||[]).map(x=>notice(x)).join('')}<p>本机 SketchUp 与 API 的状态请在客户端连接向导检查。</p>`);}
    else if(path==='/feedback')main.innerHTML=page('把遇到的问题，告诉我们。','只提交必要的脱敏信息。请勿提交 API Key、验证码或私人模型。',`<form id="feedback-form" class="public-form"><label for="feedback-email">联系邮箱（可选）</label><input id="feedback-email" type="email" maxlength="254" autocomplete="email"><label for="feedback-message">问题说明</label><textarea id="feedback-message" required minlength="10" maxlength="4000" rows="7" placeholder="出现在哪个入口？期望和实际结果是什么？"></textarea><button class="btn" type="submit">提交反馈</button><p id="form-status" role="status" aria-live="polite"></p></form>`);
    else if(legal[path]) { const [title,...paras]=legal[path];main.innerHTML=page(title,'公开说明 · 以实际开放服务为准',`<div class="reading">${paras.map(t=>`<p>${esc(t)}</p>`).join('')}</div>`);}
    else main.innerHTML=page('这一页暂不存在。','请确认地址或返回首页。','<a class="btn" href="/">返回首页</a>');
    const compatibilityNote=document.getElementById('home-compatibility-status');
    if(compatibilityNote && Array.isArray(config.release?.compatibility) && config.release.compatibility.length) compatibilityNote.textContent=config.release.compatibility.map(x=>`${x.name}：${x.status}`).join(' · ');
    document.title=`${main.querySelector('h1')?.textContent||'K Studio'} · K Studio`;
    document.querySelectorAll('#main-nav a').forEach(a=>{if(a.pathname===path)a.setAttribute('aria-current','page');});
    await packages();
    if(location.hash)document.getElementById(location.hash.slice(1))?.scrollIntoView();
  }
  document.getElementById('menu-toggle').addEventListener('click', e=>{const b=e.currentTarget, open=b.getAttribute('aria-expanded')!=='true';b.setAttribute('aria-expanded',String(open));document.getElementById('main-nav').classList.toggle('mobile-open',open);});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'){document.getElementById('main-nav').classList.remove('mobile-open');document.getElementById('menu-toggle').setAttribute('aria-expanded','false');}});
  main.addEventListener('submit', async e=>{if(e.target.id!=='feedback-form')return;e.preventDefault();const b=e.target.querySelector('button'),s=document.getElementById('form-status');b.disabled=true;s.textContent='正在提交…';try{const d=await api('/api/feedback',{method:'POST',body:JSON.stringify({message:document.getElementById('feedback-message').value,email:document.getElementById('feedback-email').value||undefined})});s.textContent=`反馈已接收${d.receipt_id?'，编号 '+d.receipt_id:''}。`;e.target.reset();}catch(error){s.textContent=error.message;}finally{b.disabled=false;}});
  main.addEventListener('click',async e=>{const b=e.target.closest('button');if(!b)return;try{if(b.id==='approve-device'){b.disabled=true;await api('/api/auth/device/approve',{method:'POST',body:JSON.stringify({user_code:b.dataset.userCode})});document.getElementById('device-approval-status').textContent='设备授权已确认。请返回 K Studio，客户端会同步真实授权状态。';}else if(b.id==='logout'){await api('/api/auth/logout',{method:'POST'});location.assign('/auth/login');}else if(b.id==='refresh-page')await render();else if(b.dataset.revoke){b.disabled=true;await api('/api/account/devices/'+encodeURIComponent(b.dataset.revoke),{method:'DELETE'});await render();}else if(b.dataset.buy){b.disabled=true;const keyName=`kstudio-order:${identity.user.id}:${b.dataset.buy}`;let key;try{key=sessionStorage.getItem(keyName);}catch(_){}if(!key){key=crypto.randomUUID();try{sessionStorage.setItem(keyName,key);}catch(_){}}const d=await api('/api/account/orders',{method:'POST',body:JSON.stringify({package_id:b.dataset.buy,idempotency_key:key})});try{sessionStorage.removeItem(keyName);}catch(_){}const u=safeUrl(d.checkout_url);if(u)location.assign(u);else location.assign('/account/orders/'+encodeURIComponent(d.order_id||d.order?.id||d.id));}}catch(error){let s=document.getElementById('action-error');if(!s){s=document.createElement('p');s.id='action-error';s.className='notice';s.setAttribute('role','alert');b.after(s);}s.textContent=error.message;b.disabled=false;}});
  Promise.allSettled([api('/api/public/config'),api('/api/auth/me')]).then(async results=>{if(results[0].status==='fulfilled')config=results[0].value;if(results[1].status==='fulfilled')identity=results[1].value;if(identity.authenticated){const a=document.getElementById('account-link');a.textContent='我的账户';a.href='/account/usage';}await render();if(results[0].status==='rejected'){const d=document.createElement('p');d.className='wrap notice';d.setAttribute('role','status');d.textContent='服务配置暂时无法取得，下载与充值保持关闭。请稍后重试。';main.prepend(d);}}).catch(error=>{main.innerHTML=page('服务暂时不可用。',esc(error.message),'<a class="btn light" href="/">返回首页重试</a>');});
})();
