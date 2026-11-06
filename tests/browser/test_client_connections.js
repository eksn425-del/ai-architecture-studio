// Opt-in real browser + actual client JS with an explicitly synthetic HTTP fixture.
// No provider/native SDK, user credentials, or user models are touched.
const {test}=require('node:test');const assert=require('node:assert/strict');
const fs=require('node:fs');const path=require('node:path');const http=require('node:http');
const enabled=process.env.KSTUDIO_RUN_BROWSER_TESTS==='1' && process.env.KSTUDIO_PLAYWRIGHT_CORE;
async function screenshot(page, name){if(process.env.KSTUDIO_BROWSER_EVIDENCE){fs.mkdirSync(process.env.KSTUDIO_BROWSER_EVIDENCE,{recursive:true});await page.screenshot({path:path.join(process.env.KSTUDIO_BROWSER_EVIDENCE,name)});}}
test('real client preserves missing-API draft and synchronizes configuration across tabs', {skip:!enabled}, async()=>{
  const {chromium}=require(process.env.KSTUDIO_PLAYWRIGHT_CORE);
  const root=path.resolve(__dirname,'../../app/static');
  const project={project_id:'fixture-p',project_name:'客户端工程验收（无真实模型）',
    context:{project_id:'fixture-p',project_name:'客户端工程验收（无真实模型）',conversation:[],references:[{type:'image',source:'inputs/reference/fixture.svg'}],brief:{text:'',source_files:[]},site:{text:'',source_files:[]}},
    agent_session:{status:'conversation',modeling_backend:'sketchup',reconstruction_state:'idle'},artifacts:[],model_state:{objects:[]}};
  let model='obsolete-fixture-model',configured=false,connection=null;const requests=[];
  let selectedId=null,instanceLive=true;
  let recoveryCase=false,pendingConsumed=true;
  const recoveryCard='# 既有方案\n此处仅验证用户界面，没有真实建筑模型。';
  const recoveryHash=require('node:crypto').createHash('sha256').update(recoveryCard).digest('hex');
  const instances=()=>({selected_instance_id:selectedId,selection_status:!selectedId?'none':instanceLive?'selected':'stale',
    detail:instanceLive?'请明确选择本会话安全副本。':'所选窗口已退出，未自动切换到其他窗口。',instances:[
      {instance_id:'owned-2024-boot1',pid:1001,sketchup_version:'2024',model_name:'本会话副本.skp',model_path:'E:/fixture/blank-disposable.skp',model_guid:'fixture-guid',selectable:instanceLive,status:instanceLive?'live':'stale',reason:instanceLive?'':'所选窗口已退出'},
      {instance_id:'foreign-2026-boot2',pid:1002,sketchup_version:'2026',model_name:'用户原模型.skp',model_path:'E:/fixture/other.skp',model_guid:'foreign-guid',selectable:false,status:'live',reason:'此模型属于其他会话，未授权切换。'}]});
  const router=()=>({economy:{provider:'deepseek-harness',model,reasoning_effort:'provider-default'},premium:{provider:'none',model:'disabled'},providers:{'deepseek-harness':{available:configured,credential_configured:configured,dependency_installed:true}}});
  const server=http.createServer(async(req,res)=>{
    const url=new URL(req.url,'http://fixture');const route=url.pathname;
    const reply=(body,status=200)=>{res.writeHead(status,{'Content-Type':'application/json'});res.end(JSON.stringify(body));};
    requests.push({method:req.method,path:route});
    if(route==='/'||route.startsWith('/static/')){
      const file=route==='/'?path.join(root,'index.html'):path.resolve(root,decodeURIComponent(route.slice(8)));
      if(!file.startsWith(root+path.sep)||!fs.existsSync(file)){res.writeHead(404);res.end();return;}
      res.writeHead(200,{'Content-Type':file.endsWith('.js')?'application/javascript':file.endsWith('.css')?'text/css':file.endsWith('.svg')?'image/svg+xml':'text/html'});fs.createReadStream(file).pipe(res);return;
    }
    if(route.endsWith('/reconstruction_card.md')){res.writeHead(200,{'Content-Type':'text/plain;charset=utf-8'});res.end(recoveryCard);return;}
    if(route.endsWith('/agent/pending-plan'))return reply(recoveryCase?{pending_plan_id:pendingConsumed?'used-fixture-plan':'renewed-fixture-plan',plan_sha256:recoveryHash,consumed:pendingConsumed}:{});
    if(route.endsWith('/agent/retry-plan')){pendingConsumed=false;return reply({status:'awaiting_new_approval',execution_started:false,model_changed:false});}
    if(route.includes('/files/')){res.writeHead(200,{'Content-Type':'image/svg+xml'});res.end('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect width="100" height="100" fill="#e7e3d7"/></svg>');return;}
    if(route==='/api/status')return reply({model_router:router(),personal_desktop:true,native_agent_available:configured,active_project_id:'fixture-p'});
    if(route==='/api/projects')return reply([{project_id:project.project_id,project_name:project.project_name}]);
    if(route==='/api/projects/fixture-p')return reply(project);
    if(route.endsWith('/agent/progress'))return reply({running:false,activities:[]});
    if(route.endsWith('/connector'))return reply({reachable:!!selectedId&&instanceLive,project_bound:!!selectedId&&instanceLive});
    if(route==='/api/connectors/sketchup/instances')return reply(instances());
    if(route.endsWith('/connector/instance')&&req.method==='POST'){
      const chunks=[];for await(const chunk of req)chunks.push(chunk);const body=JSON.parse(Buffer.concat(chunks));
      assert.deepEqual(body,{instance_id:'owned-2024-boot1',expected_model_path:'E:/fixture/blank-disposable.skp',expected_model_guid:'fixture-guid'});
      selectedId=body.instance_id;return reply({selected_instance_id:selectedId});
    }
    if(route==='/api/cloud-account-config')return reply({available:false,source_mode:'byok'});
    if(route==='/api/model-connections'&&req.method==='POST'){
      const chunks=[];for await(const chunk of req)chunks.push(chunk);const body=JSON.parse(Buffer.concat(chunks));
      assert.equal(body.api_key,'synthetic-fixture-key');model=body.model;configured=true;
      connection={id:'fixture-connection',name:body.name,mode:body.mode,model,api_base:body.api_base,reasoning_effort:body.reasoning_effort,capabilities_json:body.capabilities_json};
      return reply({connections:[connection],active_id:connection.id,model_router:router()});
    }
    if(route==='/api/model-connections')return reply({connections:connection?[connection]:[],active_id:connection?.id||null,model_router:router()});
    if(route.endsWith('/conversation')){
      // Deliberately return 200 with a retained old reply and explicit failure.
      // This is a client error-rendering fixture, never an inference result.
      project.agent_session.error='PI_AI_ERROR: Response incomplete: length';
      project.agent_session.last_reply='上一轮计划，不是本轮结果';
      return reply({project,reply:project.agent_session.last_reply,agent:{status:'failed'}});
    }
    return reply({});
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const browser=await chromium.launch({executablePath:process.env.KSTUDIO_TEST_BROWSER,headless:true});
  const errors=[];
  try{
    const context=await browser.newContext({viewport:{width:1440,height:960}});const a=await context.newPage();
    a.on('pageerror',e=>errors.push(String(e)));await a.goto(`http://127.0.0.1:${server.address().port}`);
    await a.locator('#project-title').filter({hasText:'客户端工程验收'}).waitFor();
    await a.locator('#conversation-input').fill('  请分析这张图片，先不要建模。\n');
    await a.locator('#conversation-send').click();
    await a.locator('#toast').filter({hasText:'尚未配置或启用模型 API'}).waitFor();
    assert.equal(await a.locator('#conversation-input').inputValue(),'  请分析这张图片，先不要建模。\n');
    assert.ok(await a.locator('a[href*="fixture.svg"]').count()>0);
    assert.equal(requests.filter(r=>r.path.endsWith('/conversation')).length,0);
    await screenshot(a,'client-no-api-draft-fixture.png');
    const b=await context.newPage();b.on('pageerror',e=>errors.push(String(e)));await b.goto(a.url());
    await b.locator('#model-connection-notice #setup-model').click();
    await b.locator('#connections-dialog').waitFor();
    await b.locator('#connection-name').fill('合成连接 · 仅 UI 验收');
    await b.locator('#connection-base').fill('https://fixture.invalid/v1');
    await b.locator('#connection-model').fill('fresh-fixture-model');
    await b.locator('#connection-key').fill('synthetic-fixture-key');
    await b.locator('#connection-form button[type="submit"]').click();
    await b.locator('#connection-status').filter({hasText:'当前使用此配置'}).waitFor();
    await a.waitForFunction(()=>document.querySelector('#brain-status').textContent.includes('fresh-fixture-model'));
    assert.equal(await a.locator('#conversation-input').inputValue(),'  请分析这张图片，先不要建模。\n');
    await a.locator('#modeling-plugins summary').click();
    await a.locator('#modeling-connection-status').filter({hasText:'本地桥接未响应'}).waitFor();
    assert.match(await a.locator('#brain-status').textContent(),/调用未验证/);
    await a.locator('#sketchup-instance-select option[value="owned-2024-boot1"]').waitFor({state:'attached'});
    assert.equal(await a.locator('#sketchup-instance-select').inputValue(),'');
    assert.ok(await a.locator('#sketchup-instance-connect').isDisabled());
    await a.locator('#sketchup-instance-select').selectOption('foreign-2026-boot2');
    assert.ok(await a.locator('#sketchup-instance-connect').isDisabled());
    assert.match(await a.locator('#sketchup-instance-note').textContent(),/未授权/);
    await a.locator('#sketchup-instance-select').selectOption('owned-2024-boot1');
    await a.locator('#sketchup-instance-connect').click();
    await a.locator('#modeling-connection-status').filter({hasText:'本会话模型已核验'}).waitFor();
    await screenshot(a,'client-selected-window-fixture.png');
    assert.equal(requests.filter(r=>r.method==='POST'&&r.path.endsWith('/connector/instance')).length,1);
    instanceLive=false;await a.locator('#sketchup-instances-refresh').click();
    await a.locator('#sketchup-instance-note').filter({hasText:'所选窗口已退出'}).waitFor();
    assert.equal(await a.locator('#sketchup-instance-select').inputValue(),'owned-2024-boot1');
    assert.ok(await a.locator('#sketchup-instance-connect').isDisabled());
    assert.equal(requests.filter(r=>r.method==='POST'&&r.path.endsWith('/connector/instance')).length,1);
    assert.equal(requests.filter(r=>r.path.endsWith('/conversation')).length,0);
    assert.deepEqual(errors,[]);
    await screenshot(a,'client-api-sync-fixture.png');
    for(const width of [800,390]){
      await a.setViewportSize({width,height:960});
      assert.ok(await a.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
      const box=await a.locator('.modeling-plugin-popover').boundingBox();assert.ok(box.x>=0&&box.y>=0&&box.x+box.width<=width+1);
    }
    await a.setViewportSize({width:1440,height:960});
    await a.locator('#conversation-input').fill('请继续检查当前模型。');
    await a.locator('#conversation-send').click();
    await a.locator('#agent-error').filter({hasText:'模型单次输出达到上限'}).waitFor();
    assert.equal(await a.locator('#conversation-input').inputValue(),'请继续检查当前模型。');
    assert.match(await a.locator('#agent-error').textContent(),/不会自动重试或重建/);
    assert.ok(!(await a.locator('#status-line').textContent()).includes('上一轮计划'));
    assert.ok(!(await a.locator('#toast').textContent()).includes('已处理'));
    assert.equal(requests.filter(r=>r.path.endsWith('/conversation')).length,1);
    await screenshot(a,'client-output-limit-fixture.png');
    recoveryCase=true;project.agent_session.reconstruction_state='planned';
    project.agent_session.error='This pending plan was already consumed or replaced.';
    await a.reload();
    await a.locator('#plan-recovery-notice').waitFor();
    assert.equal(requests.filter(r=>r.path.endsWith('/agent/retry-plan')).length,0);
    assert.equal(await a.locator('#conversation-input').inputValue(),'请继续检查当前模型。');
    await screenshot(a,'client-consumed-plan-recovery-fixture.png');
    await a.locator('#recover-plan-before-send').click();
    await a.locator('#toast').filter({hasText:'已核对空白副本'}).waitFor();
    assert.ok(await a.locator('#plan-recovery-notice').isHidden());
    assert.equal(requests.filter(r=>r.path.endsWith('/agent/retry-plan')).length,1);
    assert.equal(requests.filter(r=>r.path.endsWith('/conversation')).length,1);
    assert.equal(await a.locator('#conversation-input').inputValue(),'请继续检查当前模型。');
    if(process.env.KSTUDIO_BROWSER_EVIDENCE){
      const {createHash}=require('node:crypto');
      const hashes=Object.fromEntries(['studio.js','connections.js','modeling-plugins.js','modeling-plugins.css','cloud-account.js','index.html'].map(file=>[file,createHash('sha256').update(fs.readFileSync(path.join(root,file))).digest('hex')]));
      fs.writeFileSync(path.join(process.env.KSTUDIO_BROWSER_EVIDENCE,'client-connection-ui-fixture.json'),JSON.stringify({
        status:'PASS',scope:'REAL_EDGE_CLIENT_UI_SYNTHETIC_SERVER',missing_api_preserved_draft_and_image:true,
        configuration_changed_in_second_tab_synced:true,explicit_window_selection:true,foreign_model_blocked:true,
        selected_instance_exit_no_fallback:true,viewports:[1440,800,390],preflight_conversation_post_count:0,
        synthetic_failed_conversation_post_count:1,output_limit_recovery_guidance:true,old_reply_not_promoted_to_new_success:true,
        consumed_recovery_visible_by_composer:true,explicit_recovery_post_count:1,recovery_never_dispatches_conversation:true,
        instance_selection_post_count:1,page_errors:errors,source_sha256:hashes,
        real_provider:'NOT_RUN',native_sketchup:'NOT_RUN',paid_inference:false,user_models_touched:false
      },null,2));
    }
  }finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
});
