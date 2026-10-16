"""Isolated MCP JSON-RPC adapter, supporting the repository's legacy framed stdio.
No network listener, credentials, model endpoint or arbitrary-code tool.
"""
import sys,json,os,subprocess,math,re,fcntl
from pathlib import Path
ROOT=Path(os.environ['DOT_BLENDER_LAB_ROOT']).resolve(); ROOT.mkdir(parents=True,exist_ok=True)
from backend_contract import TOOLS
def call(name,a):
    if name not in {x['name'] for x in TOOLS}: raise ValueError('Unknown tool')
    if not isinstance(a,dict): raise ValueError('Arguments must be object')
    def validate_box(box):
        if not isinstance(box,dict) or set(box)!={'name','dimensions','location'}: raise ValueError('Exact box keys required')
        if not isinstance(box['name'],str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,63}',box['name']): raise ValueError('Invalid name')
        for key in ['dimensions','location']:
            values=box[key]
            if not isinstance(values,list) or len(values)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) or abs(v)>1000 for v in values): raise ValueError('Invalid bounded coordinates')
        if min(box['dimensions'])<=0: raise ValueError('Dimensions must be positive')
    if name=='blender_create_box': validate_box(a)
    elif name in ('blender_create_assembly','blender_edit_parts'):
        if set(a)!={'expected_geometry_sha256','parts'}: raise ValueError('Exact assembly keys required')
        digest=a['expected_geometry_sha256']
        if not isinstance(digest,str) or (digest and not re.fullmatch('[a-f0-9]{64}',digest)): raise ValueError('Invalid geometry digest')
        if not isinstance(a['parts'],list) or not 1<=len(a['parts'])<=64: raise ValueError('Part count out of range')
        for part in a['parts']: validate_box(part)
        if len({p['name'] for p in a['parts']})!=len(a['parts']): raise ValueError('Duplicate part names')
        if name=='blender_edit_parts':
            allowed=set(json.loads(os.environ.get('DOT_BLENDER_ALLOWED_EDIT_NAMES','[]')))
            if not {p['name'] for p in a['parts']} <= allowed: raise ValueError('Target not in host-approved edit scope')
    elif a: raise ValueError('No arguments allowed')
    if name=='blender_health':
        p=subprocess.run(['blender','--version'],capture_output=True,text=True,timeout=15,check=True)
        return {'version':p.stdout.splitlines()[0],'model_runtime':'NOT_CONNECTED','scope':'DISPOSABLE_TRANSPORT_TEST'}
    lock=(ROOT/'writer.lock').open('a')
    try: fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError: raise ValueError('Another operation is active')
    if name=='blender_inspect' and not (ROOT/'scene.blend').exists(): raise ValueError('No saved scene')
    (ROOT/'job_result.json').unlink(missing_ok=True)
    (ROOT/'candidate.blend').unlink(missing_ok=True)
    (ROOT/'job.json').write_text(json.dumps({'method':name,'arguments':a}))
    p=subprocess.run(['blender','--background','--factory-startup','--python',str(Path(__file__).with_name('blender_job.py')),'--',str(ROOT/'job.json')],capture_output=True,text=True,timeout=120)
    with (ROOT/'blender.log').open('a') as f: f.write('\n'+name+'\n'+p.stdout+'\n'+p.stderr)
    # Blender can return 0 despite Python exception; reject explicit traceback and stale result.
    if p.returncode or 'Traceback (most recent call last)' in p.stdout+p.stderr: raise ValueError('Blender operation failed; see local log')
    result=json.loads((ROOT/'job_result.json').read_text())
    if (ROOT/'candidate.blend').exists():
        (ROOT/'candidate.blend').replace(ROOT/'scene.blend')
    return result
def reply(message):
    body=json.dumps(message,ensure_ascii=False).encode(); sys.stdout.buffer.write(f'Content-Length: {len(body)}\r\n\r\n'.encode()+body); sys.stdout.buffer.flush()
while True:
    line=sys.stdin.buffer.readline()
    if not line: break
    if not line.lower().startswith(b'content-length:'): continue
    size=int(line.split(b':')[1]);
    while sys.stdin.buffer.readline().strip(): pass
    msg=json.loads(sys.stdin.buffer.read(size)); ident=msg.get('id'); method=msg.get('method')
    if ident is None: continue
    try:
        if method=='initialize': result={'protocolVersion':'2024-11-05','capabilities':{'tools':{}},'serverInfo':{'name':'dot-blender-lab','version':'0.1.0'}}
        elif method=='tools/list': result={'tools':TOOLS}
        elif method=='tools/call':
            p=msg['params']; data=call(p['name'],p.get('arguments',{})); result={'content':[{'type':'text','text':json.dumps(data)}],'isError':False}
        else: raise ValueError('Unsupported method')
        reply({'jsonrpc':'2.0','id':ident,'result':result})
    except Exception as e:
        reply({'jsonrpc':'2.0','id':ident,'error':{'code':-32602,'message':str(e)}})
