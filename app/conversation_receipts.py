"""Host-only per-request replay protection; uncertain turns are never re-executed."""
import hashlib,json,re
from pathlib import Path
from fastapi.encoders import jsonable_encoder


def begin(project:Path,request):
    identity=request.client_request_id
    if not identity:return None,None
    if not re.fullmatch(r'[a-f0-9-]{32,36}',identity):raise ValueError('Invalid request identity.')
    directory=project/'runtime/conversation_requests';directory.mkdir(parents=True,exist_ok=True)
    if directory.is_symlink():raise ValueError('Unsafe request receipt path.')
    path=directory/(identity+'.json')
    if path.is_symlink():raise ValueError('Unsafe request receipt path.')
    digest=hashlib.sha256(json.dumps(request.model_dump(),sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    if path.exists():
        receipt=json.loads(path.read_text(encoding='utf-8'))
        if receipt['request_sha256']!=digest:raise ValueError('Request identity was reused for different content.')
        if receipt['status']=='failed_before_dispatch':
            receipt['status']='running'
            temp=path.with_suffix('.tmp')
            if temp.is_symlink():raise ValueError('Unsafe request receipt temporary path.')
            temp.write_text(json.dumps(receipt,ensure_ascii=False),encoding='utf-8');temp.replace(path)
            return path,None
        if receipt['status']!='completed':raise ValueError('Previous request is unfinished or failed; inspect its actual result before a new request.')
        return path,receipt['response']
    path.write_text(json.dumps({'request_sha256':digest,'status':'running'}),encoding='utf-8')
    return path,None


def finish(path,response=None):
    if path is None:return
    receipt=json.loads(path.read_text(encoding='utf-8'))
    receipt['status']='completed' if response is not None else 'failed_or_uncertain'
    if response is not None:receipt['response']=jsonable_encoder(response)
    temp=path.with_suffix('.tmp')
    if temp.is_symlink():raise ValueError('Unsafe request receipt temporary path.')
    temp.write_text(json.dumps(receipt,ensure_ascii=False),encoding='utf-8');temp.replace(path)

def abort_before_dispatch(path,reason):
    """Only caller-proven absence of model/native dispatch permits same-id retry.

    The cloud may have created a BYOK lease before a transport failure; that lease
    uses the same client request id and is recovered idempotently on the next try.
    """
    if path is None:return
    receipt=json.loads(path.read_text(encoding='utf-8'))
    if receipt.get('status')!='running':raise ValueError('Only an undispatched running request can be released')
    receipt['status']='failed_before_dispatch'
    receipt.setdefault('preflight_failures',[]).append({'reason':str(reason)[:300],'provider_dispatched':False,'native_dispatched':False})
    temp=path.with_suffix('.tmp')
    if temp.is_symlink():raise ValueError('Unsafe request receipt temporary path.')
    temp.write_text(json.dumps(receipt,ensure_ascii=False),encoding='utf-8');temp.replace(path)
