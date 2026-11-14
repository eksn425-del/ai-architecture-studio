"""Explicit migration, audit and encrypted SQLite local restore drill tools."""
import argparse, json, os, sqlite3, tempfile, time
from pathlib import Path
from cryptography.fernet import Fernet
from sqlalchemy import select
from .config import Settings
from .db import engine_for,migrate,users,SCHEMA_VERSION
from .ledger import audit_wallet

def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['migrate','audit','recover-stale','backup-sqlite','restore-sqlite']);parser.add_argument('--path');parser.add_argument('--target');args=parser.parse_args()
    settings=Settings.from_env();engine=engine_for(settings.database_url)
    if args.action=='migrate':migrate(engine);print(f'schema_version={SCHEMA_VERSION}');return
    if args.action=='recover-stale':
        from .recovery import recover_stale
        print(json.dumps(recover_stale(engine)));return
    if args.action=='audit':
        with engine.connect() as c:ids=c.execute(select(users.c.id)).scalars().all()
        results=[audit_wallet(engine,u) for u in ids];print(json.dumps({'accounts':len(ids),'consistent':all(r['consistent'] for r in results)}));return
    if not settings.database_url.startswith('sqlite:///'):raise ValueError('Use deploy/backup.sh with pg_dump for PostgreSQL')
    key=os.environ['KSTUDIO_BACKUP_KEY'].encode();cipher=Fernet(key);destination=Path(args.path)
    if args.action=='backup-sqlite':
        if destination.exists():raise ValueError('Refuse to overwrite backup')
        source=settings.database_url.removeprefix('sqlite:///')
        with tempfile.TemporaryDirectory(dir=destination.parent) as d:
            plain=Path(d)/'backup.sqlite'
            with sqlite3.connect(source) as src,sqlite3.connect(plain) as dst:src.backup(dst)
            destination.write_bytes(cipher.encrypt(plain.read_bytes()))
        print(json.dumps({'encrypted_backup':str(destination),'snapshot_completed_at':int(time.time())}))
    else:
        target=Path(args.target)
        if target.exists():raise ValueError('Restore target must be new isolated path')
        data=cipher.decrypt(destination.read_bytes());target.write_bytes(data)
        with sqlite3.connect(target) as db:
            if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Restored database corrupt')
        print('isolated_restore_integrity=ok')
if __name__=='__main__':main()
