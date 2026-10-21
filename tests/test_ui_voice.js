const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const source=fs.readFileSync('app/static/voice-input.js','utf8');
function fixture(){
 let click,processor,stopped=0,transcribe;
 const button={addEventListener(_,f){click=f},setAttribute(){}};
 const input={value:'原文',focus(){},dispatchEvent(){}};
 const state={projectId:'p'};const messages=[],requests=[];
 const node=()=>({connect(){},disconnect(){}});
 const window={addEventListener(){},AudioContext:class{constructor(){this.sampleRate=16000;this.destination={}}createMediaStreamSource(){return node()}createScriptProcessor(){processor=node();return processor}createGain(){return {...node(),gain:{value:1}}}async resume(){}async close(){}}};
 const navigator={mediaDevices:{async getUserMedia(){return {getTracks:()=>[{stop(){stopped++}}]}}}};
 const fetch=async(url,options)=>{requests.push([url,options]);return url.endsWith('status')?{json:async()=>({ready:true})}:new Promise(resolve=>transcribe=()=>resolve({ok:true,json:async()=>({text:'新文字'})}));};
 vm.runInNewContext(source,{document:{getElementById:id=>id==='conversation-voice'?button:input,addEventListener(){}},window,navigator,state,fetch,showToast:m=>messages.push(m),Event:class{},AbortController,setTimeout,clearTimeout});
 return {click,input,state,messages,requests,get processor(){return processor},get stopped(){return stopped},complete:()=>transcribe()};
}
test('app records PCM locally, stops tracks before recognition, never submits',async()=>{
 const f=fixture();await f.click();f.processor.onaudioprocess({inputBuffer:{getChannelData:()=>new Float32Array(4096)}});
 const ending=f.click();await new Promise(r=>setImmediate(r));assert.equal(f.stopped,1);assert.equal(f.requests[1][0],'/api/speech/transcribe');
 assert.equal(new DataView(f.requests[1][1].body).getUint32(24,true),16000);f.complete();await ending;assert.equal(f.input.value,'原文 新文字');
});
test('late transcript does not overwrite changed project or draft',async()=>{for(const change of ['draft','project']){
 const f=fixture();await f.click();f.processor.onaudioprocess({inputBuffer:{getChannelData:()=>new Float32Array(4096)}});
 const ending=f.click();await new Promise(r=>setImmediate(r));if(change==='draft')f.input.value='新草稿';else f.state.projectId='q';f.complete();await ending;assert.doesNotMatch(f.input.value,/新文字/);
}});
test('voice contains no system hotkey or remote browser recognizer',()=>{assert.doesNotMatch(source,/start_dictation|Win \+ H|SpeechRecognition|webkitSpeechRecognition/);});
