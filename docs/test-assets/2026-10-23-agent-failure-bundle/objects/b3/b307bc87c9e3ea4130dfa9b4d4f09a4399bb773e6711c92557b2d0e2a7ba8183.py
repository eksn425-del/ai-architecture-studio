from pathlib import Path
import hashlib, json, os, shutil, subprocess, queue, threading, time

ROOT=Path(__file__).resolve().parent
LATEST=Path('E:/K Studio/latest')
SOURCE=Path('C:/CODEXT~1/codex-clipboard-884c6c5d-608c-4169-bc3d-a8f63c65c9cc.png')
RUNTIME=Path('E:/K AI 产品建模网站/runtime')

def dump(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
    backup=ROOT/'before'
    backup.mkdir(parents=True,exist_ok=True)
    for name in ['version.json','Open-KStudio-v2.ps1','Start-KStudioBackend.ps1']:
        dst=backup/name
        if not dst.exists(): shutil.copy2(LATEST/name,dst)
    target=ROOT/'inputs'/'source-target.png'
    target.parent.mkdir(exist_ok=True)
    if not target.exists(): shutil.copy2(SOURCE,target)
    source_sha=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert hashlib.sha256(target.read_bytes()).hexdigest()==source_sha
    inventory=backup/'native-model-manifest.json'
    if not inventory.exists():
        rows=[{'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in RUNTIME.rglob('*.skp')]
        dump(inventory,rows)
    credential=RUNTIME/'local-settings'/'provider.dpapi'
    if not (backup/'credential-fingerprint.json').exists():
        dump(backup/'credential-fingerprint.json',{'exists':credential.exists(),'sha256':hashlib.sha256(credential.read_bytes()).hexdigest() if credential.exists() else None})
    cfg=json.loads((LATEST/'version.json').read_text(encoding='utf-8-sig'))
    cli=Path(cfg['codex_executable'])
    if not cli.is_file():
        candidates=list((Path(os.environ['LOCALAPPDATA'])/'OpenAI'/'Codex'/'bin').glob('*/codex.exe'))
        assert candidates,'Installed Codex executable missing.'
        cli=max(candidates,key=lambda p:p.stat().st_mtime_ns)
    # Query capability metadata only. No turn/start, inference, model writes or Key access.
    env=os.environ.copy()
    for key in ['CODEX_APP_TOOLS_PIPE_PATH','CODEX_SESSION_ID','CODEX_THREAD_ID','CODEX_CI']: env.pop(key,None)
    env['CODEX_HOME']=str(Path(os.environ['LOCALAPPDATA'])/'AI Architecture Studio'/'CodexHome')
    err=(ROOT/'model-list.stderr.log').open('a',encoding='utf-8')
    proc=subprocess.Popen([str(cli),'app-server'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,env=env,cwd=ROOT,bufsize=0)
    events=queue.Queue()
    def reader():
        for line in proc.stdout: events.put(line)
    threading.Thread(target=reader,daemon=True).start()
    def request(n,method,params):
        proc.stdin.write((json.dumps({'id':n,'method':method,'params':params})+'\n').encode());proc.stdin.flush()
        end=time.monotonic()+25
        while time.monotonic()<end:
            message=json.loads(events.get(timeout=max(.1,end-time.monotonic())))
            if message.get('id')==n:
                if 'error' in message:raise RuntimeError(str(message['error']))
                return message['result']
        raise TimeoutError(method)
    try:
        request(1,'initialize',{'clientInfo':{'name':'kstudio-owner-preflight','version':'1'},'capabilities':{'experimentalApi':True}})
        proc.stdin.write(b'{"method":"initialized","params":{}}\n');proc.stdin.flush()
        models=request(2,'model/list',{'includeHidden':True})
        matched=[m for m in models.get('data',[]) if m.get('model')=='gpt-6.1-sol' or m.get('id')=='gpt-6.1-sol']
        dump(ROOT/'model-capabilities.json',{'requested_model':'gpt-6.1-sol','requested_effort':'high','matches':matched,'inference_calls':0})
        assert matched,'Exact model unavailable; no substitution.'
        assert any(e.get('reasoningEffort')=='high' for e in matched[0].get('supportedReasoningEfforts',[])), 'High effort not advertised.'
    finally:
        proc.terminate()
        try:proc.wait(5)
        except subprocess.TimeoutExpired:proc.kill()
        err.close()
    dump(ROOT/'run.json',{'status':'prepared','source':str(target),'source_sha256':source_sha,'requested_model':'gpt-6.1-sol','reasoning_effort':'high','rounds_requested':3,'paid_api_authorized':False,'video':'deferred_by_owner','source_publication_authorized':False,'old_models_manifest':str(inventory)})
    dump(ROOT/'resolved-cli.json',{'path':str(cli)})
    print(json.dumps({'status':'prepared','root':str(ROOT),'source_sha256':source_sha,'exact_model_advertised':True,'effort_high_advertised':True,'paid_calls':0}))

if __name__=='__main__':main()
