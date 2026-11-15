"""Server-owned whitelist only. No customer Base URL or Key is accepted."""
import asyncio, hashlib, hmac, ipaddress, json, os, re, socket
from urllib.parse import urlparse
import httpx
from .ledger import BillingError, claim, remember_provider_receipt, settle

MAX_UPSTREAM_TOTAL_SECONDS=1800

def timeout_policy(model):
    """Operator-only bounded connection/header/idle/whole-request deadlines."""
    configured=model.get('timeouts',{})
    if not isinstance(configured,dict) or set(configured)-{'connect','read','total'}:raise BillingError('Invalid upstream timeout configuration')
    result={**{'connect':10,'read':120,'total':900},**configured}
    for key,maximum in (('connect',30),('read',600),('total',MAX_UPSTREAM_TOTAL_SECONDS)):
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

def request_fingerprint(account_id, turn_id, model_id, payload):
    # Account IDs are random allocation identifiers. Key the digest by account
    # so the same prompt cannot be linked across users, and the same request
    # remains identifiable across session-secret rotation and process restart.
    try:
        canonical = json.dumps([turn_id, model_id, payload], sort_keys=True,
                               separators=(',', ':'), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise BillingError('Invalid model request fields') from exc
    return hmac.new(account_id.encode(), canonical.encode(), hashlib.sha256).hexdigest()


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

def sse_data(frame):
    fields = [line[5:].removeprefix(' ') for line in frame.splitlines() if line.startswith('data:')]
    return '\n'.join(fields).strip()


async def frames(lines):
    """Yield complete SSE events only. EOF with a partial event is not completion."""
    buffered = []
    size = 0
    async for line in lines:
        if line:
            size += len(line)
            if size > 8_000_000:
                raise BillingError('Upstream event exceeds supported size')
            buffered.append(line)
        elif buffered:
            yield '\n'.join(buffered) + '\n\n'
            buffered.clear()
            size = 0


def json_data(data):
    try:
        value = json.loads(data)
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}


def safe_provider_id(value):
    return value if isinstance(value, str) and re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._:-]{0,127}', value) else None


def provider_receipt(response, usage, request_id):
    """Store minimized pairing data for supplier reconciliation, without content."""
    receipt = {}
    for field, value in (
        ('provider_request_id', request_id),
        ('provider_response_id', response.get('id')),
        ('reported_model', response.get('model')),
    ):
        value = safe_provider_id(value)
        if value is not None:
            receipt[field] = value
    if isinstance(usage, dict):
        incoming = usage.get('input_tokens', usage.get('prompt_tokens'))
        outgoing = usage.get('output_tokens', usage.get('completion_tokens'))
        details = usage.get('input_tokens_details', usage.get('prompt_tokens_details'))
        cached = details.get('cached_tokens') if isinstance(details, dict) else None
        for field, value in (('input_tokens', incoming), ('output_tokens', outgoing), ('cached_input_tokens', cached)):
            if type(value) is int and 0 <= value <= 10**12:
                receipt[field] = value
    return receipt


def response_error(frame, item):
    return item.get('error') or item.get('type') in (
        'error', 'response.failed', 'response.incomplete', 'response.cancelled'
    ) or 'event: error' in frame.splitlines()


async def collect(stream,protocol):
    """Non-streaming SDK compatibility still uses the same metered upstream path."""
    content=[];tools={};usage=None;model=None;finish='stop';response=None;complete=False
    async for frame in stream:
        raw=sse_data(frame)
        if raw=='[DONE]' and protocol=='chat-completions':
            complete=True
            continue
        item=json_data(raw)
        if response_error(frame,item):
            raise BillingError('平台模型请求未完成，费用状态请查看待对账记录。')
        if protocol=='responses' and item.get('type')=='response.completed':
            response=item.get('response')
            complete=True
            continue
        model=item.get('model',model);usage=item.get('usage') or usage
        for choice in item.get('choices',[]):
            delta=choice.get('delta',{})
            if delta.get('content'):content.append(delta['content'])
            finish=choice.get('finish_reason') or finish
            for fragment in delta.get('tool_calls',[]):
                call=tools.setdefault(fragment['index'],{'id':'','type':'function','function':{'name':'','arguments':''}})
                if fragment.get('id'):call['id']=fragment['id']
                for key in ('name','arguments'):call['function'][key]+=fragment.get('function',{}).get(key,'')
    if not complete:raise BillingError('平台模型请求未完成，费用状态请查看待对账记录。')
    if protocol=='responses':
        if not isinstance(response,dict):raise BillingError('平台响应未完成；未将未知费用标记为零。')
        return response
    message={'role':'assistant','content':''.join(content) or None}
    if tools:message['tool_calls']=[tools[k] for k in sorted(tools)]
    return {'id':'kstudio-metered','object':'chat.completion','model':model,'choices':[{'index':0,'message':message,'finish_reason':finish}],'usage':usage}


async def stream(engine, user, task, payload, model, already_claimed=False):
    if not already_claimed:
        claim(engine,user,task['id'])
    price=json.loads(task['price_json'])
    dispatched=False
    receipt_saved=False
    upstream_id=None
    reported={}
    usage=None
    ledger_failure=False
    chat_finished=False

    def record(actual, reason):
        nonlocal receipt_saved
        result=settle(engine, user, task['id'], actual, reason,
                      provider_receipt=provider_receipt(reported, usage, upstream_id))
        receipt_saved=True
        return result['state']

    try:
        base=await asyncio.wait_for(asyncio.to_thread(validate_upstream,model['base_url']),timeout=10)
        key=os.environ.get(model['key_env'])
        if not key:
            raise BillingError('Configured platform credential unavailable')
        protocol=model['protocol']
        if protocol not in ('responses','chat-completions'):
            raise BillingError('Unsupported configured upstream protocol')
        endpoint='/responses' if protocol=='responses' else '/chat/completions'
        body={**payload,'model':model['upstream_model'],'stream':True}
        if protocol=='chat-completions':
            body['stream_options']={'include_usage':True}
        deadlines=timeout_policy(model)
        async with asyncio.timeout(deadlines['total']),httpx.AsyncClient(timeout=httpx.Timeout(deadlines['read'],connect=deadlines['connect']),follow_redirects=False,trust_env=False) as client:
            dispatched=True
            async with client.stream('POST',base+endpoint,json=body,headers={'Authorization':'Bearer '+key}) as response:
                upstream_id=response.headers.get('x-request-id')
                if upstream_id:
                    remember_provider_receipt(engine,user,task['id'],provider_receipt({},None,upstream_id))
                if response.status_code!=200:
                    code='UPSTREAM_'+str(response.status_code)
                    category,message={401:('authentication','平台供应商认证失败，请联系运营方。'),403:('authentication','平台供应商拒绝授权，请联系运营方。'),402:('balance','平台供应商额度不足，请联系运营方。'),429:('rate_limit','平台供应商暂时限流。')}.get(response.status_code,('provider_failure','平台供应商请求失败。'))
                    record(None,'upstream HTTP failure; awaiting reconciliation')
                    yield upstream_error(task['id'],code,category,message+'请在账单查看此次费用状态。')
                    return
                async for frame in frames(response.aiter_lines()):
                    raw=sse_data(frame)
                    obj=json_data(raw)
                    event_type=obj.get('type')
                    if protocol=='responses':
                        response_object=obj.get('response')
                        if isinstance(response_object,dict):
                            reported=response_object
                        terminal=event_type=='response.completed'
                        if terminal:
                            # Only the terminal response is an authoritative usage
                            # receipt. Never pick up usage from an earlier delta.
                            usage=response_object.get('usage') if isinstance(response_object,dict) else None
                    else:
                        if obj:
                            reported={**reported,**obj}
                        choices=obj.get('choices')
                        if isinstance(choices,list):
                            chat_finished=chat_finished or any(
                                isinstance(one,dict) and one.get('finish_reason') in
                                ('stop','length','tool_calls','content_filter','function_call') for one in choices
                            )
                            if not choices and obj.get('usage') is not None:
                                usage=obj['usage']
                        terminal=raw=='[DONE]'
                    if response_error(frame,obj):
                        if protocol=='responses' and isinstance(response_object,dict):
                            usage=response_object.get('usage')
                        incomplete=reported.get('incomplete_details')
                        output_limit=event_type=='response.incomplete' and isinstance(incomplete,dict) and incomplete.get('reason')=='max_output_tokens'
                        category='output_limit' if output_limit else 'provider_failure'
                        message='平台模型提前停止，请缩小本次操作范围。' if category=='output_limit' else '平台模型没有完成。'
                        record(None,'upstream terminal failure; awaiting reconciliation')
                        yield upstream_error(task['id'],'UPSTREAM_FAILED',category,message+'请在账单查看此次费用状态。')
                        return
                    if terminal:
                        valid_response=(chat_finished if protocol=='chat-completions' else
                                        isinstance(response_object,dict) and response_object.get('status')=='completed')
                        model_matches=(safe_provider_id(reported.get('model')) or '').casefold()==model['upstream_model'].casefold()
                        actual=cost(price,usage) if valid_response and model_matches else None
                        state=record(actual,'gateway metered usage' if actual is not None else 'unknown or unverified provider usage')
                        if state=='settled':
                            yield frame
                        else:
                            yield upstream_error(task['id'],'UPSTREAM_USAGE_UNVERIFIED','billing','平台费用尚未核实，请在账单查看待对账记录。')
                        return
                    if raw!='[DONE]':
                        yield frame
        record(None,'upstream stream disconnected; awaiting reconciliation')
        yield upstream_error(task['id'],'UPSTREAM_UNAVAILABLE','connection','平台供应商响应提前结束。请在账单查看此次费用状态。')
    except asyncio.CancelledError:
        raise
    except (TimeoutError,httpx.TimeoutException):
        record(None if dispatched else 0,'upstream response timed out')
        yield upstream_error(task['id'],'UPSTREAM_UNAVAILABLE','timeout','平台供应商响应超时。请在账单查看此次费用状态。')
    except Exception:
        if not receipt_saved:
            # If the write failed, keep the running reservation until recovery.
            # A failed or ambiguous settlement may not produce a success event.
            try:
                record(None if dispatched else 0,'upstream connection, configuration or settlement failed')
            except Exception:
                ledger_failure=True
        yield upstream_error(task['id'],'UPSTREAM_UNAVAILABLE','connection_or_configuration','平台供应商连接中断、配置或结算暂不可用。请在账单查看此次费用状态。')
    finally:
        if not receipt_saved and not ledger_failure:
            # Includes disconnect and generator closure between streamed events.
            record(None if dispatched else 0,'request stopped before terminal receipt')
