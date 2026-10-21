const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const source=fs.readFileSync('app/static/voice-input.js','utf8');
function fixture(native=false){
 let click, speech;
 const button={addEventListener(_,f){click=f},setAttribute(){}};
 const input={value:'原文',focus(){},dispatchEvent(){}};
 const state={projectId:'p'};const messages=[];
 const window={confirm:()=>true,SpeechRecognition:class{constructor(){speech=this}start(){}stop(){this.onend()}}};
 if(native)window.pywebview={api:{start_dictation:async()=>true}};
 vm.runInNewContext(source,{document:{getElementById:id=>id==='conversation-voice'?button:input},window,state,showToast:m=>messages.push(m),Event:class{}});
 return {click, input, state, messages,get speech(){return speech}};
}
test('dictation appends final words but never submits',async()=>{const f=fixture();await f.click();f.speech.onresult({results:[Object.assign([{transcript:'新文字'}],{isFinal:true})]});assert.equal(f.input.value,'原文 新文字');});
test('late speech cannot overwrite new draft or another project',async()=>{for(const change of ['draft','project']){const f=fixture();await f.click();if(change==='draft')f.input.value='新草稿';else f.state.projectId='q';f.speech.onresult({results:[Object.assign([{transcript:'不应写入'}],{isFinal:true})]});assert.doesNotMatch(f.input.value,/不应写入/);assert.equal(f.messages.length,1);}});
test('desktop uses system dictation without starting browser recording',async()=>{const f=fixture(true);await f.click();assert.equal(f.speech,undefined);assert.equal(f.input.value,'原文');});
