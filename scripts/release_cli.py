"""Signed release installer CLI. Distribution must ship pinned trust, never remote trust."""
from __future__ import annotations
import argparse,base64,hashlib,ipaddress,json,os,secrets,socket,sys,tempfile,subprocess,re
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request,build_opener,ProxyHandler,HTTPRedirectHandler
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.release_channel import verify_manifest,stage_archive,activate,rollback,installation_guard,atomic_json,canonical,safe_root,verify_installed

def approved_url(url,hosts):
    parsed=urlparse(url)
    if parsed.scheme!='https' or parsed.hostname not in hosts or parsed.username or parsed.password or parsed.port not in (None,443) or parsed.fragment:
        raise ValueError('Download URL/redirect is outside the pinned HTTPS hosts')
    if any(not ipaddress.ip_address(x[4][0]).is_global for x in socket.getaddrinfo(parsed.hostname,443,type=socket.SOCK_STREAM)):
        raise ValueError('Download destination must be public')
    return url

class SafeRedirect(HTTPRedirectHandler):
    def __init__(self,hosts):self.hosts=hosts
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        approved_url(newurl,self.hosts)
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def download(url,path,hosts,max_bytes,expected_sha=None):
    approved_url(url,hosts)
    opener=build_opener(ProxyHandler({}),SafeRedirect(hosts))
    digest=hashlib.sha256();size=0
    # Caller owns this fresh temporary directory. Never overwrite an artifact.
    with opener.open(Request(url,headers={'Accept-Encoding':'identity','User-Agent':'KStudioUpdater/1'}),timeout=30) as response,path.open('xb') as out:
        approved_url(response.url,hosts)
        while chunk:=response.read(1024*1024):
            size+=len(chunk)
            if size>max_bytes:raise ValueError('Download exceeded signed size')
            digest.update(chunk);out.write(chunk)
        out.flush();os.fsync(out.fileno())
    if expected_sha and (size!=max_bytes or digest.hexdigest()!=expected_sha):raise ValueError('Downloaded digest/size mismatch')
    return path

def download_resume(url,cache,hosts,size,sha):
    """Keep interrupted bytes, but activate only the signed full-file hash."""
    cache=safe_root(cache);cache.mkdir(parents=True,exist_ok=True)
    path=cache/(sha+'.part')
    if path.is_symlink():raise ValueError('Download cache redirect rejected')
    approved_url(url,hosts)
    offset=path.stat().st_size if path.exists() else 0
    if offset==size:
        with path.open('rb') as f:
            if hashlib.file_digest(f,'sha256').hexdigest()==sha:return path
        offset=0
    if offset>size:offset=0
    headers={'Accept-Encoding':'identity','User-Agent':'KStudioUpdater/1'}
    if offset:headers['Range']='bytes='+str(offset)+'-'
    opener=build_opener(ProxyHandler({}),SafeRedirect(hosts))
    with opener.open(Request(url,headers=headers),timeout=30) as response:
        approved_url(response.url,hosts)
        if response.status==206:
            match=re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)',response.headers.get('Content-Range',''))
            if not match or int(match[1])!=offset or int(match[3])!=size:raise ValueError('Invalid download resume range')
        elif response.status==200:offset=0
        else:raise ValueError('Unexpected download response')
        with path.open('ab' if offset else 'wb') as out:
            while chunk:=response.read(1024*1024):
                offset+=len(chunk)
                if offset>size:raise ValueError('Download exceeded signed size')
                out.write(chunk)
            out.flush();os.fsync(out.fileno())
    with path.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
    if offset!=size or actual!=sha:
        if offset==size:path.unlink() # exact updater-owned corrupt cache only
        raise ValueError('Incomplete or mismatched release download; original version unchanged')
    return path

def main():
    parser=argparse.ArgumentParser(description='K Studio signed candidate installer; never changes user data.')
    sub=parser.add_subparsers(dest='action',required=True)
    for name in ('install','rollback'):
        p=sub.add_parser(name);p.add_argument('--install-root',type=Path,required=True);p.add_argument('--data-dir',type=Path,required=True);p.add_argument('--runtime-dir',type=Path)
        if name=='install':
            p.add_argument('--manifest',required=True,help='Local signed envelope or approved HTTPS URL')
            p.add_argument('--trusted-keys',type=Path,required=True,help='Independently supplied pinned public key/host JSON')
            p.add_argument('--archive',type=Path,help='Offline artifact; signed digest still required')
            p.add_argument('--channel',choices=['candidate','stable'],default='candidate')
            p.add_argument('--desktop-shortcut',action='store_true',help='Install a user desktop shortcut, preserving an existing link')
    p=sub.add_parser('test-sign');p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--version',required=True);p.add_argument('--sequence',type=int,required=True)
    args=parser.parse_args()
    if args.action=='test-sign':
        from datetime import datetime,timedelta,timezone
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat,PrivateFormat,NoEncryption
        args.output.mkdir(parents=True,exist_ok=False);key=Ed25519PrivateKey.generate()
        payload={'schema':1,'channel':'candidate','platform':'windows-x64','version':args.version,'sequence':args.sequence,'expires_at':(datetime.now(timezone.utc)+timedelta(days=14)).isoformat(),'sha256':hashlib.sha256(args.archive.read_bytes()).hexdigest(),'bytes':args.archive.stat().st_size,'url':'https://test-artifact.invalid/'+args.archive.name,'data_schema':1,'acceptance':'local-test-only','authenticode':'unsigned'}
        envelope={'payload':payload,'key_id':'LOCAL_TEST_ONLY','signature':base64.b64encode(key.sign(canonical(payload))).decode()}
        atomic_json(args.output/'manifest.json',envelope)
        atomic_json(args.output/'trust-test-only.json',{'keys':{'LOCAL_TEST_ONLY':base64.b64encode(key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode()},'download_hosts':['test-artifact.invalid'],'scope':'LOCAL_TEST_ONLY_NOT_PRODUCTION_TRUST'})
        (args.output/'private-test-key.pem').write_bytes(key.private_bytes(Encoding.PEM,PrivateFormat.PKCS8,NoEncryption()))
        print(json.dumps({'status':'local_test_signed_only','authenticode':'unsigned','production_trust':False}));return
    root=safe_root(args.install_root);root.mkdir(parents=True,exist_ok=True)
    with installation_guard(root,args.data_dir,args.runtime_dir):
        if args.action=='rollback':result=rollback(root)
        else:
            trust=json.loads(args.trusted_keys.read_text(encoding='utf-8'));hosts=trust['download_hosts']
            if args.channel=='stable' and trust.get('scope','').startswith('LOCAL_TEST'):raise ValueError('Test trust cannot authorize stable releases')
            with tempfile.TemporaryDirectory(prefix='download-',dir=root) as directory:
                temp=Path(directory)
                manifest_path=download(args.manifest,temp/'envelope.json',hosts,1_000_000) if args.manifest.startswith(('https:','http:')) else Path(args.manifest)
                if manifest_path.stat().st_size>1_000_000:raise ValueError('Manifest too large')
                envelope=json.loads(manifest_path.read_text(encoding='utf-8'))
                verified=verify_manifest(envelope,trust['keys'],channel=args.channel)
                artifact=args.archive or download_resume(verified['url'],root/'download-cache',hosts,verified['bytes'],verified['sha256'])
                staged=root/'versions'/verified['version']
                if staged.exists():
                    if verify_installed(root,verified['version'])!=verified:raise ValueError('Existing immutable version differs from signed release')
                else:staged=stage_archive(artifact,root,verified)
                if args.channel=='stable':
                    if os.name!='nt':raise ValueError('Stable Authenticode verification requires Windows')
                    certificate=trust.get('authenticode_thumbprint','')
                    verifier=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent))/'verify_authenticode.ps1'
                    subprocess.run([str(Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'),'-NoProfile','-NonInteractive','-File',str(verifier),'-Path',str(staged/'KStudio.exe'),'-Thumbprint',certificate],check=True,capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
                current_path=root/'current.json'
                current=json.loads(current_path.read_text()) if current_path.exists() else None
                result={'status':'already_current','version':verified['version'],'user_data_changed':False} if current and current['version']==verified['version'] and current['sequence']==verified['sequence'] else activate(root,verified)
                resources=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent))
                launcher=root/'launch_installed.ps1'
                temporary=root/('.launcher-'+secrets.token_hex(8)+'.tmp')
                temporary.write_bytes((resources/'launch_installed.ps1').read_bytes());os.replace(temporary,launcher)
                if args.desktop_shortcut:
                    if os.name!='nt':raise ValueError('Desktop shortcut requires Windows')
                    subprocess.run([str(Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'),'-NoProfile','-NonInteractive','-File',str(resources/'install_shortcut.ps1'),'-InstallRoot',str(root),'-DataDir',str(args.data_dir.resolve())],check=True,capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
        print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,OSError) as exc:
        print(json.dumps({'status':'refused','reason':str(exc)},ensure_ascii=False),file=sys.stderr);raise SystemExit(2)
