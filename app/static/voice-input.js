// App-owned microphone capture; PCM goes only to this loopback server.
(() => {
  const button = document.getElementById('conversation-voice');
  const input = document.getElementById('conversation-input');
  if (!button || !input) return;
  let job = null;
  const reset = () => { button.textContent = '🎙'; button.setAttribute('aria-pressed', 'false'); button.title = '点击讲话，本机识别；再次点击结束'; };
  function wavBuffer(chunks, rate) {
    const size = chunks.reduce((n, a) => n + a.length, 0);
    const samples = new Float32Array(size); let offset = 0;
    for (const chunk of chunks) { samples.set(chunk, offset); offset += chunk.length; }
    const length = Math.floor(size * 16000 / rate), buffer = new ArrayBuffer(44 + length * 2), view = new DataView(buffer);
    const ascii = (at, text) => { for (let i=0;i<text.length;i++) view.setUint8(at+i,text.charCodeAt(i)); };
    ascii(0,'RIFF'); view.setUint32(4,36+length*2,true); ascii(8,'WAVE'); ascii(12,'fmt ');
    view.setUint32(16,16,true); view.setUint16(20,1,true); view.setUint16(22,1,true);
    view.setUint32(24,16000,true); view.setUint32(28,32000,true); view.setUint16(32,2,true); view.setUint16(34,16,true);
    ascii(36,'data'); view.setUint32(40,length*2,true);
    for (let i=0;i<length;i++) {
      const start=Math.floor(i*rate/16000), end=Math.min(size,Math.max(start+1,Math.floor((i+1)*rate/16000)));
      let sum=0; for(let k=start;k<end;k++) sum+=samples[k];
      const value=Math.max(-1,Math.min(1,sum/(end-start)));
      view.setInt16(44+i*2,value<0?value*32768:value*32767,true);
    }
    return buffer;
  }
  async function finish(current, cancel=false) {
    if (current.finished) return;
    current.finished = true; current.cancelled ||= cancel;
    clearTimeout(current.timer);
    current.processor?.disconnect(); current.source?.disconnect(); current.gain?.disconnect();
    current.stream?.getTracks().forEach(track => track.stop());
    if (current.audio) await current.audio.close().catch(()=>{});
    if (current.cancelled || !current.chunks.length) { if(job===current){job=null;reset();} return; }
    button.textContent='识别中'; button.disabled=true;
    const controller=new AbortController(), timer=setTimeout(()=>controller.abort(),60000);
    try {
      const response=await fetch('/api/speech/transcribe',{method:'POST',headers:{'Content-Type':'audio/wav'},body:wavBuffer(current.chunks,current.rate),signal:controller.signal});
      const result=await response.json();
      if(!response.ok) throw new Error(result.detail || '语音识别失败');
      if (current.cancelled || state.projectId!==current.projectId || input.value!==current.before) {
        showToast('项目或输入内容已改变，识别结果未覆盖你的文字。',false); return;
      }
      if(!result.text?.trim()){showToast('没有识别到清晰语音，请靠近麦克风重新录制。',false);return;}
      input.value=current.before+(current.before?' ':'')+result.text.trim();
      input.dispatchEvent(new Event('input',{bubbles:true})); input.focus();
    } catch(error) { if(!current.cancelled)showToast(error.name==='AbortError'?'语音识别超时，请录制短一些。':error.message,true); }
    finally { clearTimeout(timer); current.chunks=[]; if(job===current){job=null;button.disabled=false;reset();} }
  }
  button.addEventListener('click',async()=>{
    if(job){await finish(job);return;}
    const current={before:input.value,projectId:state.projectId,chunks:[],frames:0,cancelled:false,finished:false}; job=current;
    button.textContent='准备中';
    try {
      const status=await fetch('/api/speech/status').then(r=>r.json());
      if(!status.ready)throw new Error('本机语音组件尚未安装，请更新完整安装包。');
      if(current.finished)return;
      if(!navigator.mediaDevices?.getUserMedia)throw new Error('当前窗口无法使用麦克风，请在本机浏览器打开 K Studio。');
      current.stream=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:true,noiseSuppression:true},video:false});
      if(current.finished){current.stream.getTracks().forEach(t=>t.stop());return;}
      current.audio=new (window.AudioContext || window.webkitAudioContext)({sampleRate:16000});
      current.rate=current.audio.sampleRate;
      current.source=current.audio.createMediaStreamSource(current.stream);
      current.processor=current.audio.createScriptProcessor(4096,1,1);
      current.gain=current.audio.createGain(); current.gain.gain.value=0;
      current.processor.onaudioprocess=event=>{
        if(current.finished)return;
        const data=event.inputBuffer.getChannelData(0), remaining=current.rate*60-current.frames;
        const chunk=data.slice(0,Math.min(data.length,remaining));current.chunks.push(chunk);current.frames+=chunk.length;
        if(current.frames>=current.rate*60)finish(current);
      };
      current.source.connect(current.processor);current.processor.connect(current.gain);current.gain.connect(current.audio.destination);
      await current.audio.resume();
      button.textContent='停止';button.setAttribute('aria-pressed','true');button.title='正在录音，点击结束并识别';
      current.timer=setTimeout(()=>finish(current),60000);
      showToast('正在录音，再点麦克风结束；仅在本机识别，最多 60 秒。',false);
    } catch(error) {
      await finish(current,true);
      showToast(error.name==='NotAllowedError'?'麦克风权限未允许，请允许后再试。':error.message,true);
    }
  });
  document.addEventListener('visibilitychange',()=>{if(document.hidden&&job){job.cancelled=true;finish(job,true);}});
  window.addEventListener('beforeunload',()=>{if(job){job.cancelled=true;finish(job,true);}});
  reset();
})();
