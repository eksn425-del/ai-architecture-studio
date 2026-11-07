// Real pinned DSH provider serializer and real loopback HTTP, no paid provider.
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {pathToFileURL} from 'node:url';
import {readFileSync} from 'node:fs';
import path from 'node:path';
const root=process.env.KSTUDIO_TEST_DSH_NODE_MODULES;
if(!root) throw new Error('Set KSTUDIO_TEST_DSH_NODE_MODULES to the pinned official installation');
const {apply}=await import(pathToFileURL(path.join(root,'@deepseek-ai/dsh-llm-pi-ai/lib/index.js')));
const fixture=JSON.parse(readFileSync(process.env.KSTUDIO_TEST_EFFECTIVE_CONFIG,'utf8'));

function adapterFor(provider){
 let adapter;
 const ctx={fiber:{entry:{options:{id:'wire-test'}}},inject(){},on(){},
  logger:{error(error){throw error},warn(){}},
  get(name){if(name==='credentials')return {resolve:async()=>({value:'local-test-not-a-key'})}},
  llm:{registerConfigurableProviders(){return {replace(){}}},registerModelDiscovery(){},
   registerAdapter(_routes,value){adapter=value;return {replace(){}}}}};
 apply(ctx,{providers:{get:()=>({'kstudio-bai':provider})}});
 // Use the actual adapter's durable image seam, with deterministic test bytes.
 adapter.config.resolveAttachments=()=>({readImageRequest:async(ref)=>{
  const source=fixture.images.find(image=>image.id===ref.attachmentId);
  return {data:Buffer.from(source.data,'base64'),mediaType:source.mimeType,bytes:Buffer.from(source.data,'base64').length,width:12,height:8};
 }});
 adapter.config.resolveImageAccess=()=>undefined;
 return adapter;
}

for(const protocol of ['openai-completions','openai-responses']){
 for(const effort of ['provider-default','low','high']){
  test(`${protocol} ${effort}: official wire preserves model, effort, output, images and tool schema`,async()=>{
   const seen=[];
   const server=createServer(async(req,res)=>{
    let raw='';for await(const chunk of req)raw+=chunk;
    seen.push({url:req.url,body:JSON.parse(raw),headers:req.headers});
    res.writeHead(200,{'content-type':'text/event-stream'});
    const send=(value)=>res.write(`data: ${JSON.stringify(value)}\n\n`);
    if(protocol==='openai-completions'){
     send({id:'local-chat',object:'chat.completion.chunk',created:0,model:'fixture-model',choices:[{index:0,delta:{role:'assistant',content:'verified'},finish_reason:null}]});
     send({id:'local-chat',object:'chat.completion.chunk',created:0,model:'fixture-model',choices:[{index:0,delta:{},finish_reason:'stop'}],usage:{prompt_tokens:7,completion_tokens:2,total_tokens:9}});
     res.end('data: [DONE]\n\n');
    }else{
     const item={id:'m1',type:'message',role:'assistant',status:'in_progress',content:[]};
     send({type:'response.created',response:{id:'local-response',model:'fixture-model',status:'in_progress',output:[]}});
     send({type:'response.output_item.added',output_index:0,item});
     send({type:'response.content_part.added',output_index:0,content_index:0,item_id:'m1',part:{type:'output_text',text:'',annotations:[]}});
     send({type:'response.output_text.delta',output_index:0,content_index:0,item_id:'m1',delta:'verified'});
     const done={...item,status:'completed',content:[{type:'output_text',text:'verified',annotations:[]}]};
     send({type:'response.output_item.done',output_index:0,item:done});
     send({type:'response.completed',response:{id:'local-response',model:'fixture-model',status:'completed',output:[done],usage:{input_tokens:7,output_tokens:2,total_tokens:9}}});res.end();
    }
   });
   await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
   try{
    const provider={api:protocol,baseURL:`http://127.0.0.1:${server.address().port}/v1`,apiKeyEnv:'TEST_ONLY',headers:{'X-KStudio-Turn-ID':'test-platform-turn-001'},models:[fixture.models[effort]]};
    const adapter=adapterFor(provider);
    const content=[{type:'text',text:'use original image order'},...fixture.images.map(image=>({type:'image',attachment:{attachmentId:image.id,width:12,height:8,mediaType:image.mimeType,bytes:Buffer.from(image.data,'base64').length}}))];
    const chunks=[];
    for await(const chunk of adapter.stream({provider:'kstudio-bai',model:'fixture-model',
      reasoningEffort:effort==='provider-default'?undefined:effort,maxTokens:4096,
      messages:[{role:'user',content}],tools:[{name:'readonly_probe',description:'test read',parameters:{type:'object',properties:{},additionalProperties:false}}]}))chunks.push(chunk);
    assert.equal(seen.length,1);
    assert.equal(seen[0].headers['x-kstudio-turn-id'],'test-platform-turn-001');
    const body=seen[0].body;assert.equal(body.model,'fixture-model');assert.equal(body.stream,true);
    if(protocol==='openai-completions'){
     assert.equal(seen[0].url,'/v1/chat/completions');
     assert.equal(body.reasoning_effort,effort==='provider-default'?undefined:effort);
     assert.equal(body.max_completion_tokens??body.max_tokens,4096);
     assert.equal(body.tools[0].function.name,'readonly_probe');
    }else{
     assert.equal(seen[0].url,'/v1/responses');
     assert.equal(body.reasoning?.effort,effort==='provider-default'?undefined:effort);
     assert.equal(body.max_output_tokens,4096);assert.equal(body.tools[0].name,'readonly_probe');
    }
    const all=JSON.stringify(body);let previous=-1;
    for(const image of fixture.images){const index=all.indexOf(`data:${image.mimeType};base64,${image.data}`);assert.ok(index>previous,`image ${image.id} bytes and order`);previous=index}
    assert.ok(chunks.some(chunk=>chunk.type==='usage'),'actual SDK parsed usage');
    assert.ok(chunks.some(chunk=>chunk.type==='finish'),'actual SDK parsed terminal event');
   }finally{await new Promise(resolve=>server.close(resolve))}
  });
 }
}
