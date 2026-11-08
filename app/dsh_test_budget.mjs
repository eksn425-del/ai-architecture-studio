// Optional official request middleware. Never replaces the agent loop.
import {randomUUID} from 'node:crypto';
export function installTestBudget(ctx,call,{enabled=true}={}) {
  ctx.on('llm/stream',(options,next)=>(async function*(){
    // This host gate also covers ordinary BYOK and official child/compaction
    // requests. An uncertain native write must stop before another dispatch.
    await call('/provider-ready');
    if(!enabled){yield* next();return;}
    const attempt=randomUUID();let usage=null,finish=null,errorCode=null,settled=false;
    await call('/test-budget/reserve',{attempt_id:attempt,session_id:options.sessionId,
      provider:options.provider,model:options.model,request_purpose:options.purpose||'conversation',max_output_tokens:options.maxTokens});
    try {
      for await(const chunk of next()) {
        if(chunk.type==='usage')usage=chunk.usage;
        if(chunk.type==='finish'){finish=chunk.reason?.kind;errorCode=chunk.reason?.failure?.code;}
        yield chunk;
      }
      await call('/test-budget/settle',{attempt_id:attempt,usage,finish_reason:finish,error_code:errorCode});settled=true;
    } finally {
      if(!settled)await call('/test-budget/settle',{attempt_id:attempt,usage:null,finish_reason:'aborted-or-unknown'}).catch(()=>{});
    }
  })());
}
