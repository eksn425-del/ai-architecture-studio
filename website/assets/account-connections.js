/* Account-owned opt-in vault UI. Secrets never enter URL/storage or list markup. */
window.KStudioAccountExtras = (() => {
  let api, esc, refresh;
  const say = text => { const e=document.getElementById('connection-status');if(e)e.textContent=text; };
  async function page(path, helpers) {
    ({api,esc,refresh}=helpers);
    if(path==='/account/privacy')return `<h2>你的数据</h2><p>项目、原图和模型默认留在电脑。账户API仅在你选择云保存后加密存储。导出不包含密钥；删除云端API并撤销设备不会删除本机模型。已恢复到电脑的Key不能远程彻底抹除，请在供应商处撤销不再信任的Key。</p><button class="btn light" id="export-private">导出账户元数据</button><label><input type="checkbox" id="confirm-private-delete">我确认删除云端API并撤销所有设备</label><button class="btn light" id="delete-private">删除云端私人配置</button><p>财务、订单、审计和稳定账户标识仍保留用于核账；这不是彻底删除全部账户数据。完整注销请联系已公布的支持渠道。</p><p id="connection-status" role="status"></p><p>导出或删除需要最近10分钟内重新登录。</p><a class="text-link" href="/api/auth/login?return_to=%2Faccount%2Fprivacy">重新验证身份</a><p><a class="text-link" href="/account/usage">返回账户</a></p>`;
    if(path!=='/account/connections')return null;
    const [data,devices]=await Promise.all([api('/api/account/connections'),api('/api/account/devices')]);
    const options=(devices.devices||[]).filter(d=>!d.revoked&&d.can_restore_credentials).map(d=>`<option value="${esc(d.id)}">${esc(d.device_name)} · ${esc(d.id.slice(0,8))}</option>`).join('');
    return `<h2>我的 API</h2><p>可以只在客户端本机保存。选择下面的云保存后，Key加密归属当前账户；只有你明确授权的电脑可恢复。保存成功不代表模型能力验证通过。</p><form id="connection-form" class="public-form" autocomplete="off"><input name="id" type="hidden"><label>连接名称<input name="label" required maxlength="80" value="我的 BAI"></label><label>服务商<input name="provider" required maxlength="40" value="BAI"></label><label>API 地址<input name="base_url" type="url" required value="https://api.b.ai/v1"></label><label>协议<select name="protocol"><option value="responses">Responses</option><option value="chat-completions">Chat Completions</option></select></label><label>模型名称<input name="model_id" required value="deepseek-v4.1-flash"></label><label>推理档位<select name="reasoning_effort"><option value="low">Low（当前 BAI 实测配置）</option><option value="provider-default">服务商默认</option><option value="medium">Medium（需供应商支持）</option><option value="high">High（需供应商支持）</option></select></label><label>API Key<input name="api_key" type="password" autocomplete="new-password" maxlength="4096" required></label><label><input name="cloud_storage_consent" type="checkbox" required>我同意加密保存到当前 K Studio 账户</label><button class="btn" type="submit">加密保存</button><button class="btn light" type="reset">取消编辑</button></form><p id="connection-status" role="status"></p><section class="subsection">${(data.connections||[]).map(c=>`<article class="package"><h3>${esc(c.label)}</h3><p>${esc(c.provider)} · ${esc(c.model_id)} · ${esc(c.protocol)} · ${esc(c.reasoning_effort)}</p><p>${esc(c.base_url)} · ${esc(c.secret_mask)} · ${esc(c.verification_status==='verified'?'已验证':'尚未验证')}</p><button class="btn light" data-edit-connection="${esc(c.id)}">修改配置</button><button class="btn light" data-delete-connection="${esc(c.id)}">删除连接</button><label>恢复到已授权电脑<select id="device-for-${esc(c.id)}"><option value="">选择设备</option>${options}</select></label><button class="btn" data-sync-connection="${esc(c.id)}">授权这台电脑恢复</button></article>`).join('')||'<p>尚未保存账户 API。</p>'}</section><p>恢复前需在客户端登录并授权设备。恢复码只对所选设备有效，120秒过期且只能使用一次。近期登录过期时，请重新登录后继续。</p><output id="restore-grant"></output><a class="text-link" href="/api/auth/login?return_to=%2Faccount%2Fconnections">重新验证身份</a>`;
  }
  document.addEventListener('submit',async e=>{
    if(e.target.id!=='connection-form')return;e.preventDefault();e.stopImmediatePropagation();
    const form=e.target,button=form.querySelector('[type=submit]');button.disabled=true;
    try{
      const d=Object.fromEntries(new FormData(form));const id=d.id;delete d.id;d.cloud_storage_consent=d.cloud_storage_consent==='on';if(!d.api_key)delete d.api_key;
      await api('/api/account/connections'+(id?'/'+encodeURIComponent(id):''),{method:id?'PATCH':'POST',body:JSON.stringify(d)});
      form.elements.api_key.value='';await refresh();say('连接已加密保存；没有进行付费调用。');
    }catch(error){say(error.message);}finally{button.disabled=false;}
  });
  document.addEventListener('reset',e=>{if(e.target.id==='connection-form')e.target.elements.api_key.required=true;});
  document.addEventListener('click',async e=>{
    const b=e.target.closest('button');if(!b)return;
    const matched=b.dataset.editConnection||b.dataset.deleteConnection||b.dataset.syncConnection||['export-private','delete-private'].includes(b.id);if(!matched)return;
    e.stopImmediatePropagation();b.disabled=true;
    try{
      if(b.dataset.editConnection){
        const d=await api('/api/account/connections');const c=d.connections.find(x=>x.id===b.dataset.editConnection);if(!c)throw new Error('连接已删除，请刷新。');
        const f=document.getElementById('connection-form');for(const k of ['id','label','provider','base_url','protocol','model_id','reasoning_effort'])f.elements[k].value=c[k];f.elements.api_key.value='';f.elements.api_key.required=false;f.elements.cloud_storage_consent.checked=false;f.scrollIntoView({block:'center'});
      }else if(b.dataset.deleteConnection){if(!confirm('删除此云端连接并取消未使用的恢复授权？'))return;await api('/api/account/connections/'+encodeURIComponent(b.dataset.deleteConnection),{method:'DELETE'});await refresh();}
      else if(b.dataset.syncConnection){const id=b.dataset.syncConnection,device=document.getElementById('device-for-'+id).value;if(!device)throw new Error('请先选择你已授权的电脑。');if(!confirm('允许选定电脑取得此API Key并加密保存在该账户的本机空间？'))return;const d=await api('/api/account/connections/'+encodeURIComponent(id)+'/sync-grants',{method:'POST',body:JSON.stringify({device_id:device,confirm_device_restore:true})});const output=document.getElementById('restore-grant');output.textContent='一次性恢复码（请粘贴到该电脑客户端的账户面板）：'+d.sync_token;setTimeout(()=>{output.textContent='恢复码已过期，请重新授权。';},120000);}
      else if(b.id==='export-private'){const d=await api('/api/account/export');const url=URL.createObjectURL(new Blob([JSON.stringify(d,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='kstudio-account-metadata.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
      else{if(!document.getElementById('confirm-private-delete').checked)throw new Error('请先勾选删除确认。');await api('/api/account/private-data',{method:'DELETE',body:JSON.stringify({confirm_delete_private_data:true})});location.assign('/auth/login');}
    }catch(error){say(error.message);}finally{b.disabled=false;}
  });
  return {page};
})();
