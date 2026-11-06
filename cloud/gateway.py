"""Server-owned whitelist only. No customer Base URL or Key is accepted."""
import asyncio, ipaddress, json, os, socket
from urllib.parse import urlparse
import httpx
from .ledger import BillingError, reserve, claim, settle

def validate_upstream(url):
    parsed=urlparse(url)
    if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.fragment or parsed.query:raise BillingError('Invalid upstream URL')
    addresses=socket.getaddrinfo(parsed.hostname,parsed.port or 443,type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(row[4][0]).is_global for row in addresses):raise BillingError('Private upstream destination forbidden')
    # DNS is defense in depth; production additionally enforces outbound firewall.
    return url.rstrip('/')

def cost(price,usage):
    if not isinstance(usage,dict):return None
    incoming=usage.get('input_tokens',usage.get('prompt_tokens'))
    outgoing=usage.get('output_tokens',usage.get('completion_tokens'))
    if type(incoming) is not int or type(outgoing) is not int or incoming<0 or outgoing<0:return None
    return price['service_units']+(incoming*price['input_units_per_million']+outgoing*price['output_units_per_million']+999999)//1000000

async def collect(stream,protocol):
    """Non-streaming SDK compatibility still uses the same metered upstream path."""
    content=[];tools={};usage=None;model=None;finish='stop';response=None;error=None;complete=False
    async for chunk in stream:
        for line in chunk.splitlines():
            if not line.startswith('data:'):continue
            raw=line[5:].strip()
            if raw=='[DONE]':complete=True;continue
            if not raw:continue
            try:item=json.loads(raw)
            except ValueError:continue
            if item.get('code') or item.get('error'):error=item
            if item.get('type')=='response.completed':response=item['response'];complete=True
            model=item.get('model',model);usage=item.get('usage') or usage
            for choice in item.get('choices',[]):
                delta=choice.get('delta',{})
                if delta.get('content'):content.append(delta['content'])
                finish=choice.get('finish_reason') or finish
                for fragment in delta.get('tool_calls',[]):
                    call=tools.setdefault(fragment['index'],{'id':'','type':'function','function':{'name':'','arguments':''}})
                    if fragment.get('id'):call['id']=fragment['id']
                    for key in ('name','arguments'):call['function'][key]+=fragment.get('function',{}).get(key,'')
    if error or not complete:raise BillingError('平台模型请求未完成，费用状态请查看待对账记录。')
    if protocol=='responses':
        if response is None:raise BillingError('平台响应未完成；未将未知费用标记为零。')
        return response
    message={'role':'assistant','content':''.join(content) or None}
    if tools:message['tool_calls']=[tools[k] for k in sorted(tools)]
    return {'id':'kstudio-metered','object':'chat.completion','model':model,'choices':[{'index':0,'message':message,'finish_reason':finish}],'usage':usage}

async def stream(engine,user,task,payload,model,already_claimed=False):
    if not already_claimed:claim(engine,user,task['id'])
    usage=None;started=False;completed=False
    try:
        base=validate_upstream(model['base_url'])
        key=os.environ.get(model['key_env'])
        if not key:raise BillingError('Configured platform credential unavailable')
        protocol=model['protocol']
        endpoint='/responses' if protocol=='responses' else '/chat/completions'
        body={**payload,'model':model['upstream_model'],'stream':True}
        if protocol=='chat-completions':body['stream_options']={'include_usage':True}
        async with asyncio.timeout(120),httpx.AsyncClient(timeout=httpx.Timeout(120,connect=10),follow_redirects=False,trust_env=False) as client:
            # Never retry the whole task or after any streamed event.
            started=True
            async with client.stream('POST',base+endpoint,json=body,headers={'Authorization':'Bearer '+key}) as response:
                if response.status_code!=200:
                    code='UPSTREAM_'+str(response.status_code)
                    yield 'event: error\ndata: '+json.dumps({'error':{'code':code,'type':'upstream_error','message':'平台上游请求失败，费用状态请查看待对账记录。'},'code':code,'task_id':task['id']})+'\n\n'
                    return
                async for line in response.aiter_lines():
                    if line.startswith('data:'):
                        data=line[5:].strip()
                        if data=='[DONE]':completed=True
                        if data and data!='[DONE]':
                            try:
                                obj=json.loads(data)
                                if obj.get('type')=='response.completed':completed=True
                                reported=obj.get('usage') or obj.get('response',{}).get('usage')
                                if reported:usage=reported
                            except (ValueError,AttributeError):pass
                    yield line+'\n'
    except asyncio.CancelledError:
        raise
    except Exception:
        yield 'event: error\ndata: '+json.dumps({'error':{'code':'UPSTREAM_UNAVAILABLE','type':'upstream_error','message':'平台上游连接中断，费用状态请查看待对账记录。'},'code':'UPSTREAM_UNAVAILABLE','task_id':task['id']})+'\n\n'
    finally:
        price=json.loads(task['price_json'])
        actual=cost(price,usage) if completed else None
        # Even connection failures can be ambiguous; only provably not dispatched
        # requests release their reservation automatically.
        settle(engine,user,task['id'],actual if started else 0,'gateway usage' if actual is not None else 'unknown provider usage')
