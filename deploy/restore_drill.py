"""Independent loopback PostgreSQL/age/vault/payment-inbox restore acceptance.

Always creates an owned cluster and new fixture databases; never accepts a
production URL. Synthetic identities/payment receipts are explicitly labeled.
"""
import argparse,base64,json,subprocess,time,hashlib,os,secrets,socket,tempfile
from pathlib import Path
from sqlalchemy import update,select
from cloud.db import engine_for,migrate,orders,now
from cloud.auth import create_identity
from cloud.ledger import create_order,payment_paid,reserve,claim,settle,audit_wallet
from cloud.credential_crypto import CredentialCipher
from cloud.provider_connections import ConnectionService
from cloud import device_auth,wechat_payments
from cloud.maintenance import cycle
from deploy.verify_restore import verify


def main():
    p=argparse.ArgumentParser();p.add_argument('--bin',required=True);p.add_argument('--age-bin',required=True)
    p.add_argument('--output',required=True);p.add_argument('--port',default='55448');p.add_argument('--keep-server',action='store_true');a=p.parse_args()
    output=Path(a.output).absolute();output.mkdir(parents=True,exist_ok=False)
    bindir=Path(a.bin);agedir=Path(a.age_bin);stamp=str(time.time_ns())
    source='kstudio_drill_'+stamp;target='kstudio_restore_'+stamp
    if not a.port.isdigit() or not 1024<=int(a.port)<=65535:raise ValueError('Invalid isolated test port')
    with socket.socket() as probe:
        probe.settimeout(.5)
        if probe.connect_ex(('127.0.0.1',int(a.port)))==0:raise ValueError('Test port already occupied; no existing server touched')
    ext='.exe' if os.name=='nt' else ''
    flags={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}
    def native_path(value):
        if os.name!='nt' or not isinstance(value,Path):return str(value)
        # PostgreSQL Windows CRT tools interpret some bootstrap paths in the
        # ANSI codepage. Use the verified existing-parent short name, not a data move.
        import ctypes
        parent=value.absolute();tail=[]
        while not parent.exists():tail.insert(0,parent.name);parent=parent.parent
        buffer=ctypes.create_unicode_buffer(32768)
        length=ctypes.windll.kernel32.GetShortPathNameW(str(parent),buffer,len(buffer))
        if not length or length>=len(buffer):raise ValueError('Cannot resolve Windows PostgreSQL compatible path')
        return str(Path(buffer.value).joinpath(*tail))
    def run(binary,*args):
        cmd=[native_path(binary),*[native_path(x) for x in args]]
        if binary.stem=='pg_ctl':
            # A Windows server can inherit pg_ctl's pipe handles. A file avoids
            # waiting for EOF until the long-lived server itself exits.
            with (output/'private-pgctl.log').open('ab') as log:
                return subprocess.run(cmd,check=True,stdout=log,stderr=log,timeout=120,**flags)
        return subprocess.run(cmd,check=True,capture_output=True,timeout=120,**flags)
    def command(name,*args):return run(bindir/(name+ext),'-h','127.0.0.1','-p',a.port,'-U','kstudio_test',*args)
    def url(db):return 'postgresql+psycopg://kstudio_test@127.0.0.1:'+a.port+'/'+db
    cluster=output/'private-postgres-cluster';engine=None;restored_engine=None;started=False;successful=False
    try:
        run(bindir/('initdb'+ext),'-D',cluster,'-U','kstudio_test','--auth=trust','--encoding=UTF8','--locale=C')
        run(bindir/('pg_ctl'+ext),'-D',cluster,'-l',output/'private-postgres.log','-o','-p '+a.port+' -h 127.0.0.1','-w','start');started=True
        command('createdb',source);engine=engine_for(url(source));migrate(engine)
        user=create_identity(engine,'restore-fixture|alice','Restore fixture')
        order=create_order(engine,user['id'],'fixture-order','fixture',{'amount':100,'currency':'usd','credits':1000})
        with engine.begin() as c:c.execute(update(orders).where(orders.c.id==order['id']).values(provider_session='cs_restore_fixture'))
        payment_paid(engine,'evt_restore',order['id'],'pi_restore',100,'usd','cs_restore_fixture')
        price={'version':'drill-fixture','service_units':5,'input_units_per_million':1,'output_units_per_million':1}
        task=reserve(engine,user['id'],'fixture-task','platform','fixture',100,price);claim(engine,user['id'],task['id']);settle(engine,user['id'],task['id'],35)
        verifier='restore-fixture-verifier-'+('x'*40)
        device=device_auth.start(engine,'Restore test device',device_auth.challenge(verifier))
        device_auth.approve(engine,user['id'],device['user_code']);device_auth.poll(engine,device['device_code'],verifier,3600)
        # Separate encryption keys, both private; never bundled into the .age archive.
        master=secrets.token_bytes(32);cipher=CredentialCipher({'drill':master},'drill')
        (output/'private-vault-keys.json').write_text(json.dumps({'drill':base64.b64encode(master).decode()}),encoding='utf8')
        vault=ConnectionService(engine,cipher)
        vault.save(user['id'],{'label':'Restore fixture','provider':'fixture','protocol':'responses',
            'base_url':'https://provider.example.invalid/v1','model_id':'fixture-model','reasoning_effort':'low',
            'api_key':'synthetic-restore-secret-not-a-real-key','cloud_storage_consent':True})
        pending=create_order(engine,user['id'],'inbox-order','fixture-cny',{'amount':75,'currency':'cny','credits':100})
        with engine.begin() as c:c.execute(update(orders).where(orders.c.id==pending['id']).values(state='checkout',provider_session=wechat_payments._session(pending)))
        # Fixture enters the *already verified* inbox; no real webhook/signature or payment claim.
        payload={'out_trade_no':pending['id'],'transaction_id':'fixture-wechat-transaction','trade_state':'SUCCESS',
            'amount':{'total':75,'currency':'CNY'},'appid':'fixture-app','mchid':'fixture-merchant'}
        wechat_payments._store_inbox(engine,'fixture-inbox-event','TRANSACTION.SUCCESS',pending,payload)
        before=verify(engine,cipher)
        identity=output/'private-backup-identity.txt'
        run(agedir/('age-keygen'+ext),'-o',identity)
        recipient=run(agedir/('age-keygen'+ext),'-y',identity).stdout.decode().strip()
        encrypted=output/'snapshot.age';backup_start=time.monotonic()
        with tempfile.TemporaryDirectory(prefix='private-plain-',dir=output) as temp:
            plain=Path(temp)/'database.dump';restored=Path(temp)/'restored.dump'
            command('pg_dump','-Fc','--no-owner','--no-acl','--file',plain,source)
            run(agedir/('age'+ext),'-r',recipient,'-o',encrypted,plain)
            backup_seconds=time.monotonic()-backup_start;restore_start=time.monotonic()
            run(agedir/('age'+ext),'-d','-i',identity,'-o',restored,encrypted)
            if hashlib.sha256(plain.read_bytes()).digest()!=hashlib.sha256(restored.read_bytes()).digest():raise ValueError('Decrypted snapshot differs')
            command('createdb',target)
            command('pg_restore','--exit-on-error','--single-transaction','--no-owner','--no-acl','-d',target,restored)
        restored_engine=engine_for(url(target));after=verify(restored_engine,cipher)
        restore_seconds=time.monotonic()-restore_start
        if before!=after:raise ValueError('Restored table fingerprints differ')
        wallet_before=audit_wallet(restored_engine,user['id'])
        first=cycle(restored_engine);second=cycle(restored_engine)
        wallet_after=audit_wallet(restored_engine,user['id'])
        if wallet_after['balance']-wallet_before['balance']!=100 or len(first['payment_recovery'])!=1 or second['payment_recovery']:
            raise ValueError('Verified inbox was not recovered exactly once')
        with restored_engine.connect() as c:
            if c.execute(select(wechat_payments.verified_payment_inbox.c.state)).scalar_one()!='applied':raise ValueError('Inbox state not persisted')
        receipt={'scope':'LOCAL_POSTGRESQL_FIXTURE_NOT_PRODUCTION','postgresql':command('psql','--version').stdout.decode().strip(),
            'source_database':source,'restored_database':target,'records_equal':True,'ledger_consistent':wallet_after['consistent'],
            'vault_credentials_decrypted':after['vault_credentials_decrypted'],'pending_payment_inbox_recovered_once':True,
            'maintenance_cycles':2,'backup_seconds':round(backup_seconds,3),'restore_seconds':round(restore_seconds,3),
            'encrypted_sha256':hashlib.sha256(encrypted.read_bytes()).hexdigest(),'tables':after['tables'],
            'no_real_payments':True,'no_real_provider_calls':True,'docker_execution':'NOT_RUN',
            'encryption':'official age CLI, separate backup identity and vault master key',
            'plaintext_dump_retained':False,'cluster_left_running_for_other_disposable_tests':a.keep_server}
        (output/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
        (output/'private-test-server.json').write_text(json.dumps({'url':url('postgres'),'data_directory':str(cluster),'port':int(a.port),'user':'kstudio_test','owned':True}),encoding='utf8')
        print(json.dumps(receipt));successful=True
    finally:
        if engine:engine.dispose()
        if restored_engine:restored_engine.dispose()
        if started and not (a.keep_server and successful):run(bindir/('pg_ctl'+ext),'-D',cluster,'-m','fast','-w','stop')


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'status':'FAIL','error_type':type(exc).__name__,'secrets_printed':False}));raise SystemExit(1)
