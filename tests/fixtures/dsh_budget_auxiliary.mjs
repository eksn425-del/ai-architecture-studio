// Test-only local control: invoke the REAL installed compaction backend with
// the REAL SDK-created agent. This is not a production tool or release plugin.
import {createServer} from 'node:http';
import {writeFileSync} from 'node:fs';
export const name='budget-auxiliary-fixture';
export const inject=['compaction'];
export function apply(ctx,config){
 let root;
 ctx.on('agent/created',({agent})=>{root??=agent;});
 const server=createServer(async(req,res)=>{
  try{
   if(!root)throw new Error('No real SDK agent yet');
   await ctx.compaction.summarize({messages:[{role:'user',content:[{type:'text',text:'Summarize the local synthetic fixture.'}]}]},root);
   res.writeHead(200);res.end('completed');
  }catch(error){res.writeHead(409);res.end(String(error));}
 });
 server.listen(0,'127.0.0.1',()=>writeFileSync(config.receipt,JSON.stringify({port:server.address().port})));
 ctx.on('dispose',()=>server.close());
}
