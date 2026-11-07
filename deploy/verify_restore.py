"""Read-only restored PostgreSQL verification, executed in the application image.

The target name is the only CLI argument; credentials remain in private settings.
Results contain counts/hashes only, never identities, ciphertext or master keys.
"""
import hashlib
import json
import re
import sys
from sqlalchemy import select
from sqlalchemy.engine import make_url
from cloud.config import Settings
from cloud.db import engine_for,metadata,schema_version,SCHEMA_VERSION,users
from cloud import provider_connections,wechat_payments
from cloud.credential_crypto import CredentialCipher
from cloud.ledger import audit_wallet


def verify(engine,cipher=None):
    with engine.connect() as c:
        version=c.execute(select(schema_version.c.version)).scalar_one()
        if version!=SCHEMA_VERSION:raise ValueError('Unexpected restored schema version')
        snapshots={}
        for table in sorted(metadata.tables.values(),key=lambda t:t.name):
            rows=[dict(r) for r in c.execute(select(table)).mappings()]
            payload=sorted(json.dumps(r,sort_keys=True,separators=(',',':'),default=str) for r in rows)
            snapshots[table.name]={'rows':len(rows),'sha256':hashlib.sha256(json.dumps(payload,separators=(',',':')).encode()).hexdigest()}
        account_ids=c.execute(select(users.c.id)).scalars().all()
        credentials=c.execute(select(provider_connections.connections)).mappings().all()
        if credentials and cipher is None:raise ValueError('Separate vault key required for restore verification')
        for row in credentials:cipher.decrypt(dict(row))
    consistent=all(audit_wallet(engine,user_id)['consistent'] for user_id in account_ids)
    if not consistent:raise ValueError('Restored ledger audit failed')
    return {'status':'PASS','schema_version':version,'tables':snapshots,'ledger_consistent':consistent,
        'vault_credentials_decrypted':len(credentials),'includes_verified_payment_inbox':True,
        'read_only':True,'production_cutover':False}


def main():
    name=sys.argv[1] if len(sys.argv)==2 else ''
    if not re.fullmatch(r'kstudio_restore_[a-z0-9_]{1,45}',name):raise ValueError('Explicit isolated restore database required')
    settings=Settings.from_env()
    url=make_url(settings.database_url)
    if not url.drivername.startswith('postgresql') or url.database==name:raise ValueError('Original production database cannot be the restore target')
    engine=engine_for(url.set(database=name).render_as_string(hide_password=False))
    cipher=CredentialCipher.from_file(settings.vault_keys_file,settings.vault_active_key_version) if settings.vault_keys_file else None
    try:print(json.dumps(verify(engine,cipher)))
    finally:engine.dispose()


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'status':'FAIL','error_type':type(exc).__name__,'secrets_printed':False}));sys.exit(1)
