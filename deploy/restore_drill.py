"""Disposable PostgreSQL drill. No production URL accepted; preserves receipts on E."""
import argparse,json,subprocess,time,hashlib,os
from pathlib import Path
from cryptography.fernet import Fernet
from sqlalchemy import select,update
from cloud.db import engine_for,migrate,orders,tasks,ledger,users,sessions,device_authorizations
from cloud.auth import create_identity
from cloud.ledger import create_order,payment_paid,reserve,claim,settle,audit_wallet

def main():
    p=argparse.ArgumentParser();p.add_argument('--bin',required=True);p.add_argument('--output',required=True);p.add_argument('--port',default='55439');a=p.parse_args()
    output=Path(a.output).resolve();output.mkdir(parents=True,exist_ok=False)
    bindir=Path(a.bin);stamp=str(time.time_ns());source='kstudio_drill_'+stamp;target='kstudio_restore_'+stamp
    def command(name,*args):
        subprocess.run([str(bindir/(name+'.exe')),'-h','127.0.0.1','-p',a.port,'-U','kstudio_test',*map(str,args)],check=True,capture_output=True)
    def url(db):return 'postgresql+psycopg://kstudio_test@127.0.0.1:'+a.port+'/'+db
    command('createdb',source);engine=engine_for(url(source));migrate(engine)
    user=create_identity(engine,'restore-fixture|alice','Restore fixture')
    order=create_order(engine,user['id'],'fixture-order','fixture',{'amount':100,'currency':'usd','credits':1000})
    with engine.begin() as c:c.execute(update(orders).where(orders.c.id==order['id']).values(provider_session='cs_restore_fixture'))
    payment_paid(engine,'evt_restore',order['id'],'pi_restore',100,'usd','cs_restore_fixture')
    price={'version':'drill-fixture','service_units':5,'input_units_per_million':1,'output_units_per_million':1}
    task=reserve(engine,user['id'],'fixture-task','platform','fixture',100,price);claim(engine,user['id'],task['id']);settle(engine,user['id'],task['id'],35)
    from cloud import device_auth
    verifier='restore-fixture-verifier-'+('x'*40)
    device=device_auth.start(engine,'Restore test device',device_auth.challenge(verifier));device_auth.approve(engine,user['id'],device['user_code']);device_auth.poll(engine,device['device_code'],verifier,3600)
    def snapshot(e):
        with e.connect() as c:
            tables={t.name:[dict(r) for r in c.execute(select(t).order_by(t.c.id)).mappings().all()] for t in (users,tasks,orders,ledger,sessions,device_authorizations)}
        return {'tables':tables,'wallet':audit_wallet(e,user['id'])}
    before=snapshot(engine);plain=output/'snapshot.dump';encrypted=output/'snapshot.dump.fernet'
    backup_start=time.monotonic();command('pg_dump','-Fc','--no-owner','--file',plain,source)
    key=Fernet.generate_key();cipher=Fernet(key);encrypted.write_bytes(cipher.encrypt(plain.read_bytes()));(output/'backup-private.key').write_bytes(key)
    snapshot_completed=time.time();backup_seconds=time.monotonic()-backup_start
    # Preserve plaintext dump only inside this private local drill directory; the
    # deployment backup.sh removes its protected temporary plaintext automatically.
    restored=output/'decrypted.dump';restore_start=time.monotonic();restored.write_bytes(cipher.decrypt(encrypted.read_bytes()))
    command('createdb',target);command('pg_restore','--exit-on-error','--single-transaction','--no-owner','-d',target,restored)
    restored_engine=engine_for(url(target));after=snapshot(restored_engine)
    receipt={'scope':'LOCAL_POSTGRESQL_FIXTURE_NOT_PRODUCTION','postgresql':'17.11','source_database':source,'restored_database':target,'records_equal':before==after,'ledger_consistent':after['wallet']['consistent'],'backup_seconds':round(backup_seconds,3),'restore_seconds':round(time.monotonic()-restore_start,3),'snapshot_completed_at':snapshot_completed,'rpo':'snapshot point; production schedule not configured','encrypted_sha256':hashlib.sha256(encrypted.read_bytes()).hexdigest(),'counts':{k:len(v) for k,v in after['tables'].items()},'no_real_payments':True}
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print(json.dumps(receipt));engine.dispose();restored_engine.dispose()
    if before!=after:raise SystemExit(1)
if __name__=='__main__':main()
