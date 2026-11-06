import {installTestBudget} from './dsh_test_budget.mjs';
import {toolDenial} from './dsh_tool_policy.mjs';
// Thin official DSH plugin: forward the host's fixed tool catalog, never run code.
export const name = 'kstudio-host-tools';
export const inject = ['tools', 'attachments', 'systemPrompt'];
export async function apply(ctx) {
  const url = process.env.KSTUDIO_TOOLS_URL;
  const token = process.env.KSTUDIO_TOOLS_TOKEN;
  if (!url || !/^http:\/\/127\.0\.0\.1:\d+$/.test(url) || !token) throw new Error('Missing loopback tool binding');
  async function call(path, body) {
    const response = await fetch(url + path, {method: body ? 'POST':'GET',headers:{'Authorization':'Bearer '+token,'Content-Type':'application/json'}, ...(body ? {body:JSON.stringify(body)}:{})});
    if (!response.ok) throw new Error('Host tool refused: '+response.status);
    return response.json();
  }
  const specs = await call('/tools');
  const task = await call('/task');
  if(task.test_budget_enabled) installTestBudget(ctx,call);
  if (task.instructions) ctx.systemPrompt.section({
    name:'kstudio:architecture', order:10200, text:task.instructions, interpolate:false,
  });
  if (task.text) ctx.systemPrompt.section({
    name:'kstudio:host-task-record', order:10300, text:task.text, interpolate:false,
  });
  for (const spec of specs) {
    ctx.tools.register({
      name:spec.name, description:spec.description, parameters:spec.inputSchema,
      output:{schema:{type:'object'},render:(_args,value)=>value.blocks},
      async execute(args) {
        const result = await call('/call',{name:spec.name,arguments:args});
        const blocks=[];
        for(const item of result.contentItems ?? [{type:'inputText',text:JSON.stringify(result)}]) {
          if(item.type==='inputText') blocks.push({type:'text',text:item.text});
          else if(item.type==='inputImage') {
            const match=/^data:image\/png;base64,([A-Za-z0-9+/=]+)$/.exec(item.imageUrl);
            if(!match) throw new Error('Invalid host image');
            const attachment=await ctx.attachments.saveImage({data:Buffer.from(match[1],'base64'),mediaType:'image/png',name:'sketchup-viewport.png'});
            blocks.push({type:'image',attachment});
          }
        }
        return {blocks};
      }
    });
  }
  const actual=ctx.tools.schemas().map(tool=>tool.name);
  if(process.env.KSTUDIO_DSH_CAPABILITIES !== 'full' && actual.some(n=>!specs.some(s=>s.name===n))) throw new Error('Unexpected model-visible tools: '+actual.join(', '));
  await call('/inventory',{names:actual});
  if(process.env.KSTUDIO_DSH_CAPABILITIES === 'full') {
    let rootAgentId;
    async function interaction(kind, request) {
      const row=await call('/interaction',kind==='approval'
        ? {kind,tool:request.toolName,reason:request.reason||'',callId:request.callId}
        : {kind,questions:request.questions,callId:request.wait?.callId});
      try {
        for (;;) {
          if(request.signal?.aborted) throw new Error('Interaction cancelled');
          const state=await call('/interaction/'+row.id);
          if(state.status==='answered') return state.answer;
          if(state.status==='cancelled') throw new Error('Interaction cancelled');
          await new Promise(resolve=>setTimeout(resolve,300));
        }
      } finally { await call('/interaction/cancel',{id:row.id}).catch(()=>{}); }
    }
    ctx.on('user-questions/request',(request)=>interaction('question',request));
    ctx.on('approval/request',async(request)=>{
      try {return await interaction('approval',request);}
      catch {return request.signal?.aborted?'cancelled':'unavailable';}
    });
    ctx.on('tools/pre-execute',async(exec,next)=>{
      const control=await call('/control');
      if(control.cancelled) return {kind:'cancel'};
      const denial=toolDenial(exec,{rootAgentId,hostNames:new Set(specs.map(s=>s.name)),policy:process.env.KSTUDIO_DSH_EXECUTION_POLICY});
      if(denial) return {kind:'deny',reason:denial};
      return next();
    });
    ctx.on('tools/execute',async(exec,next)=>{
      const start=Date.now();
      await call('/native-event',{event:'tool_started',tool:exec.name,call_id:exec.callId});
      let result;
      try { result=await next(); }
      catch (error) {
        await call('/native-event',{event:'tool_result',tool:exec.name,call_id:exec.callId,
          success:false,elapsed_ms:Date.now()-start}).catch(()=>{});
        throw error;
      }
      // Results stay in the official durable session. Public progress carries
      // names and outcomes only, never shell arguments or reasoning.
      await call('/native-event',{event:'tool_result',tool:exec.name,call_id:exec.callId,
        success:!result.isError,elapsed_ms:Date.now()-start}).catch(()=>console.error('K Studio progress delivery failed; the native tool result is preserved.'));
      return result;
    });
    const agents=new Set();
    ctx.on('agent/created',({agent})=>{agents.add(agent);rootAgentId ??= agent.id;});
    ctx.on('agent/disposed',({agent})=>{agents.delete(agent);});
    let checking=false;
    const timer=setInterval(async()=>{
      if(checking)return; checking=true;
      try {if((await call('/control')).cancelled) for(const agent of agents) agent.cancel({kind:'user'});}
      catch { /* shutdown closes the host before the plugin disposer */ }
      finally {checking=false;}
    },500);
    timer.unref();
    ctx.on('dispose',()=>clearInterval(timer));
    // MCP discovery is asynchronous; the initial plugin snapshot is not the
    // completed runtime inventory. Keep later generations observable as well.
    let inventoryQueue=Promise.resolve();
    ctx.on('tools/change', () => {
      inventoryQueue=inventoryQueue.then(()=>call('/inventory', {names:ctx.tools.schemas().map(tool=>tool.name)}))
        .catch(()=>{ console.error('K Studio inventory observer disconnected; tools remain owned by DSH.'); });
    });
  }
}
