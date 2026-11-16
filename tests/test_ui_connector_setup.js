const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../app/static/studio.js'), 'utf8');
function production(...names) {
  return names.map(name => {
    const start = source.search(new RegExp(`^(?:async )?function ${name}\\(`, 'm'));
    assert.notEqual(start, -1);
    return source.slice(start, source.indexOf('\n}', start) + 2);
  }).join('\n');
}
const ready = {platform_supported:true, package_available:true, configured:false, configuration_kind:'missing', publication:'private_local_trial', installations:[{year:2022,name:'SketchUp 2022',plugin_present:false,plugin_kind:'missing'}]};
function fixture(info=ready, api=async()=>({})) {
  const nodes={};
  const $=id=>nodes[id]||=( {value:id==='connector-sketchup-version'?'2022':'',open:true,disabled:false,
    close(){this.open=false;},showModal(){this.open=true;},setAttribute(k,v){this[k]=v;},removeAttribute(k){delete this[k];}} );
  const sandbox=vm.createContext({$,state:{busy:false,projectId:'p'}, api, escapeHtml:x=>x});
  vm.runInContext(`let connectorSetupGeneration=1,connectorSetupInfo=${JSON.stringify(info)},connectorSetupBusy=false;\n`+
    production('renderConnectorSetup','closeConnectorSetup','installConnectorRuntime','checkConnectorSetup','openConnectorSetup','friendlyError'),sandbox);
  return {sandbox,$,nodes};
}
test('verified trial package gives real download only after selecting a discovered year',()=>{
  const {sandbox,$}=fixture(); $('connector-sketchup-version').value='';sandbox.renderConnectorSetup();
  assert.equal($('connector-plugin-download').href,undefined);assert.equal($('connector-runtime-install').disabled,true);
  $('connector-sketchup-version').value='2022';sandbox.renderConnectorSetup();
  assert.equal($('connector-plugin-download').href,'/api/connectors/sketchup/plugin');
  assert.equal($('connector-runtime-install').disabled,false);
  assert.match($('connector-package-note').textContent,/本机试用包/);
});
for(const [name,patch] of [['missing package',{package_available:false}],['unsupported platform',{platform_supported:false}]]){
  test(`${name} cannot offer an install or fake download`,()=>{
    const {sandbox,$}=fixture({...ready,...patch});sandbox.renderConnectorSetup();
    assert.equal($('connector-runtime-install').disabled,true);assert.equal($('connector-plugin-download').href,undefined);
  });
}
test('existing plugin cannot be overwritten through trial wizard',()=>{
  const {sandbox,$}=fixture({...ready,installations:[{year:2022,name:'SU',plugin_present:true,plugin_kind:'existing'}]});
  sandbox.renderConnectorSetup();assert.equal($('connector-runtime-install').disabled,false);assert.equal($('connector-plugin-download').href,'/api/connectors/sketchup/plugin');
});
test('installation posts explicit selected version, ignores repeat clicks, and never calls model tools',async()=>{
  const calls=[];let respond;
  const {sandbox,$}=fixture(ready,async(url,options)=>{calls.push([url,options]);return options?new Promise(resolve=>respond=resolve):{...ready,configured:true,configuration_kind:'managed'};});
  const pending=sandbox.installConnectorRuntime();await sandbox.installConnectorRuntime();
  assert.equal(calls.length,1);assert.deepEqual(JSON.parse(calls[0][1].body),{confirm_install:true,year:2022,manual_version:false});
  respond({status:'runtime_installed'});await pending;
  assert.equal(calls.length,2);assert.match($('connector-setup-status').textContent,/尚未验证原生连接/);
  assert.equal($('connector-runtime-install').disabled,true);
});
test('closed wizard does not render a late installer success',async()=>{
  let respond;const {sandbox,$}=fixture(ready,async()=>new Promise(resolve=>respond=resolve));
  const pending=sandbox.installConnectorRuntime();sandbox.closeConnectorSetup();respond({status:'runtime_installed'});await pending;
  assert.equal($('connector-setup-dialog').open,false);
  assert.doesNotMatch($('connector-setup-status').textContent,/已安装并通过/);
});
test('failed MCP check is actionable and never suggests manual credential copying',async()=>{
  const {sandbox,$}=fixture(ready,async()=>({reachable:false,detail:'Connection file not found: private-path\nRun tools/save_kongxing_connection.ps1'}));
  await sandbox.checkConnectorSetup();assert.match($('connector-setup-status').textContent,/Start Local Bridge/);
  assert.doesNotMatch($('connector-setup-status').textContent,/private-path|save_kongxing|已响应/);
});
test('fresh MCP configuration error directs users to installer, not to Codex installation',()=>{
  const {sandbox}=fixture();const text=sandbox.friendlyError(new Error('Codex config.toml was not found; the existing SketchUp MCP is not configured.'));
  assert.match(text,/安装 K Studio 连接器/);assert.doesNotMatch(text,/完成 Codex 配置/);
});
