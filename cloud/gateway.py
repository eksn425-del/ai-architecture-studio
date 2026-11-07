"""Server-owned whitelist only. No customer Base URL or Key is accepted."""
import asyncio, ipaddress, json, os, socket
from urllib.parse import urlparse
import httpx
from .ledger import BillingError, reserve, claim, settle

def timeout_policy(model):
    """Operator-only bounded connection/header/idle/whole-request deadlines."""
    configured=model.get('timeouts',{})
    if not isinstance(configured,dict) or set(configured)-{'connect','read','total'}:raise BillingError('Invalid upstream timeout configuration')
    result={**{'connect':10,'read':120,'total':900},**configured}
    for key,maximum in (('connect',30),('read',600),('total',1800)):
        value=result[key]
        if type(value) not in (int,float) or not 1<=value<=maximum:raise BillingError('Invalid upstream timeout configuration')
    if result['total']<result['read']:raise BillingError('Total deadline is shorter than stream idle deadline')
    return result


def apply_reasoning_policy(payload, model):
    """A verified platform route owns its effort; never silently lower it."""
    if 'thinking' in payload:raise BillingError('Thinking override is not supported by the verified platform route')
    effort=model.get('reasoning_effort','provider-default')
    if effort not in ('provider-default','none','minimal','low','medium','high','xhigh'):
        raise BillingError('Invalid verified reasoning configuration')
    supplied=payload.get('reasoning_effort')
    reasoning=payload.get('reasoning')
    if reasoning is not None:
        if not isinstance(reasoning,dict):raise BillingError('Invalid reasoning request')
        if set(reasoning)-{'effort','summary','generate_summary'}:raise BillingError('Unsupported reasoning override')
        nested=reasoning.get('effort')
        if supplied is not None and nested is not None and supplied!=nested:
            raise BillingError('Conflicting reasoning request')
        supplied=nested if nested is not None else supplied
    expected=None if effort=='provider-default' else effort
    if supplied is not None and supplied!=expected:
        raise BillingError('Reasoning effort differs from the verified platform route')
    payload.pop('reasoning_effort',None)
    if model['protocol']=='responses':
        if expected is not None:payload['reasoning']={**(reasoning or {}),'effort':expected}
    else:
        payload.pop('reasoning',None)
        if expected is not None:payload['reasoning_effort']=expected
    return payload

def upstream_error(task_id,code,category,message):
    return 'event: error\ndata: '+json.dumps({'error':{'code':code,'type':'upstream_error','category':category,'message':message},'code':code,'task_id':task_id},ensure_ascii=False)+'\n\n'

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
    fields=('service_units','input_units_per_million','output_units_per_million')
    if any(type(price.get(k)) is not int or not 0<=price[k]<=10**12 for k in fields):return None
    result=price['service_units']+(incoming*price['input_units_per_million']+outgoing*price['output_units_per_million']+999999)//1000000
    return result if result<=10**12 else None

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
    usage=None;started=False;completed=False;failed=False
    try:
        base=validate_upstream(model['base_url'])
        key=os.environ.get(model['key_env'])
        if not key:raise BillingError('Configured platform credential unavailable')
        protocol=model['protocol']
        if protocol not in ('responses','chat-completions'):raise BillingError('Unsupported configured upstream protocol')
        endpoint='/responses' if protocol=='responses' else '/chat/completions'
        body={**payload,'model':model['upstream_model'],'stream':True}
        if protocol=='chat-completions':body['stream_options']={'include_usage':True}
        deadlines=timeout_policy(model)
        async with asyncio.timeout(deadlines['total']),httpx.AsyncClient(timeout=httpx.Timeout(deadlines['read'],connect=deadlines['connect']),follow_redirects=False,trust_env=False) as client:
            # Never retry the whole task or after any streamed event.
            started=True
            async with client.stream('POST',base+endpoint,json=body,headers={'Authorization':'Bearer '+key}) as response:
                if response.status_code!=200:
                    code='UPSTREAM_'+str(response.status_code)
                    category,message={401:('authentication','平台供应商认证失败，请联系运营方。'),403:('authentication','平台供应商拒绝授权，请联系运营方。'),402:('balance','平台供应商额度不足，请联系运营方。'),429:('rate_limit','平台供应商暂时限流，请稍后明确重试。')}.get(response.status_code,('provider_failure','平台供应商请求失败。'))
                    yield upstream_error(task['id'],code,category,message+'本次不自动重放；费用状态请查看待对账记录。')
                    return
                async for line in response.aiter_lines():
                    if line.startswith('data:'):
                        data=line[5:].strip()
                        if data=='[DONE]':completed=True
                        if data and data!='[DONE]':
                            try:
                                obj=json.loads(data)
                                if obj.get('type')=='response.completed':completed=True
                                if obj.get('error') or obj.get('type') in ('error','response.failed','response.incomplete'):failed=True
                                reported=obj.get('usage') or obj.get('response',{}).get('usage')
                                if reported:usage=reported
                            except (ValueError,AttributeError):pass
                    yield line+'\n'
    except asyncio.CancelledError:
        raise
    except (TimeoutError,httpx.TimeoutException):
        yield upstream_error(task['id'],'UPSTREAM_UNAVAILABLE','timeout','平台供应商响应超时；没有自动重放，费用状态请查看待对账记录。')
    except Exception:
        yield upstream_error(task['id'],'UPSTREAM_UNAVAILABLE','connection_or_configuration','平台供应商连接中断或配置未就绪；没有自动重放，费用状态请查看待对账记录。')
    finally:
        price=json.loads(task['price_json'])
        actual=cost(price,usage) if completed and not failed else None
        # Even connection failures can be ambiguous; only provably not dispatched
        # requests release their reservation automatically.
        settle(engine,user,task['id'],actual if started else 0,'gateway usage' if actual is not None else 'unknown provider usage')
