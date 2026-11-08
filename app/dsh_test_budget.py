"""Opt-in finite experiment ledger; never changes ordinary production BYOK.

The request ceiling is exact at the official adapter boundary. Token amounts
are conservative reservations, NOT a provider billing guarantee. No key stored.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import time
import uuid
from contextlib import contextmanager
from .runtime_safety import LocalRuntimeLease


class TestBatchBudget:
    __test__=False

    @classmethod
    def configured(cls, configuration, workspace=None):
        path=os.environ.get('KSTUDIO_TEST_BATCH_CONFIG','').strip()
        return cls(Path(path),configuration,run_id=(Path(workspace).parent.parent.name if workspace is not None else None)) if path else None

    def __init__(self,path,configuration,run_id=None):
        self.path=path.resolve();self.config=json.loads(self.path.read_text(encoding='utf-8-sig'))
        c=self.config
        from urllib.parse import urlparse
        authorization=c.get('authorization',{})
        fixture=authorization.get('status')=='local_fixture' and urlparse(c.get('api_base','')).hostname in ('127.0.0.1','::1','localhost')
        if not fixture and not (authorization.get('status')=='granted' and authorization.get('reference')):
            raise ValueError('Finite test batch has no recorded authorization; no request dispatched')
        if c.get('schema_version')!=1 or not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}',c.get('batch_id','')):
            raise ValueError('Invalid finite test batch identity')
        for key in ('max_requests','max_reserved_tokens','reserved_tokens_per_request','max_output_tokens'):
            if type(c.get(key)) is not int or c[key]<=0:raise ValueError('Invalid test batch ceiling')
        if (c['api_base'].rstrip('/')!=configuration.endpoint or c['model']!=configuration.model
            or c['protocol']!=configuration.protocol or c['max_output_tokens']<configuration.max_output_tokens):
            raise ValueError('Test batch route/output differs from effective configuration')
        if c.get('effective_configuration_sha256') and c['effective_configuration_sha256']!=configuration.binding():
            raise ValueError('Effective model configuration differs from the finite test registration')
        if c['reserved_tokens_per_request']<configuration.context_window+configuration.max_output_tokens:
            raise ValueError('Test token reservation must cover declared context plus output')
        self.run_id=run_id
        if 'allowed_run_ids' in c:
            runs=c['allowed_run_ids']
            if not isinstance(runs,list) or not runs or len(runs)!=len(set(runs)) or any(not isinstance(r,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,100}',r) for r in runs):raise ValueError('Invalid preregistered run IDs')
            if run_id not in runs:raise ValueError('Project is not a preregistered finite test run')
            if type(c.get('per_run_max_requests')) is not int or c['per_run_max_requests']<=0:raise ValueError('Invalid per-run request ceiling')
        self.batch=c['batch_id'];self.owner=uuid.uuid4().hex
        self.digest=hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        self.database=self.path.parent/'dsh-test-batches.sqlite3'
        self.recovery=self._recovery_policy(configuration.request_retries)
        self.lease_root=self.path.parent/'.dsh-test-owners'
        self.lease=LocalRuntimeLease(self.lease_root/self.owner).acquire()
        try:
            with self.connect() as db:
                db.executescript('CREATE TABLE IF NOT EXISTS batches(id TEXT PRIMARY KEY,config_hash TEXT NOT NULL); CREATE TABLE IF NOT EXISTS runs(batch TEXT,id TEXT,requests INTEGER NOT NULL,PRIMARY KEY(batch,id)); CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY,batch TEXT NOT NULL,owner TEXT NOT NULL,session TEXT,status TEXT NOT NULL,reservation INTEGER NOT NULL,usage_json TEXT,created REAL NOT NULL);')
                db.execute('BEGIN IMMEDIATE')
                old=db.execute('SELECT config_hash FROM batches WHERE id=?',(self.batch,)).fetchone()
                if old and old[0]!=self.digest:raise ValueError('Test batch configuration changed; existing ledger preserved')
                db.execute('INSERT OR IGNORE INTO batches VALUES (?,?)',(self.batch,self.digest));db.commit()
                if self.recovery is not None:
                    db.execute('BEGIN IMMEDIATE')
                    db.execute('CREATE TABLE IF NOT EXISTS recovery_authorizations(batch TEXT PRIMARY KEY,policy_hash TEXT NOT NULL,policy_json TEXT NOT NULL,created REAL NOT NULL)')
                    policy_hash=hashlib.sha256(json.dumps(self.recovery,sort_keys=True,separators=(',',':')).encode()).hexdigest()
                    previous=db.execute('SELECT policy_hash FROM recovery_authorizations WHERE batch=?',(self.batch,)).fetchone()
                    if previous and previous[0]!=policy_hash:raise ValueError('Test recovery authorization changed; existing ledger preserved')
                    for attempt in self.recovery['acknowledged_unknown_attempts']:
                        row=db.execute('SELECT status FROM attempts WHERE batch=? AND id=?',(self.batch,attempt)).fetchone()
                        if row!=('unknown',):raise ValueError('Recovery acknowledgement must name an existing unknown attempt in this batch')
                    db.execute('INSERT OR IGNORE INTO recovery_authorizations VALUES (?,?,?,?)',(self.batch,policy_hash,json.dumps(self.recovery),time.time()));db.commit()
        except BaseException:self.lease.release();raise

    def _recovery_policy(self,configured_retries):
        """An additive owner decision, never a rewritten budget or usage receipt.

        Only transport/timeouts can continue. Cancellation, crashed owners and
        other unknowns still require investigation. The SDK owns actual retry
        execution; this ledger counts every dispatch, including failed retries.
        """
        path=self.path.with_name(self.path.stem+'.recovery.json')
        if not path.exists():return None
        if path.is_symlink() or path.stat().st_size>16384:raise ValueError('Invalid test recovery authorization')
        policy=json.loads(path.read_text(encoding='utf-8-sig'))
        if not isinstance(policy,dict):raise ValueError('Invalid test recovery authorization')
        auth=policy.get('authorization',{})
        if (policy.get('schema_version')!=1 or policy.get('batch_id')!=self.batch
            or policy.get('configuration_sha256')!=self.digest
            or policy.get('mode')!='bounded-network-retry'
            or not isinstance(auth,dict) or auth.get('status')!='granted'
            or not isinstance(auth.get('reference'),str) or not auth['reference'].strip()
            or type(policy.get('max_consecutive_retries')) is not int
            or not 1<=policy['max_consecutive_retries']<=min(2,configured_retries)):
            raise ValueError('Invalid test recovery authorization')
        acknowledged=policy.get('acknowledged_unknown_attempts')
        if (not isinstance(acknowledged,list) or len(acknowledged)>self.config['max_requests']
            or any(not isinstance(a,str) or not re.fullmatch(r'[a-f0-9-]{36}',a) for a in acknowledged)
            or len(set(acknowledged))!=len(acknowledged)):
            raise ValueError('Invalid test recovery acknowledgement')
        return policy

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.database,timeout=20)
        db.execute('PRAGMA synchronous=FULL')
        try:yield db
        finally:db.close()

    def reserve(self,data):
        c=self.config;attempt=data.get('attempt_id')
        if not isinstance(attempt,str) or not re.fullmatch(r'[a-f0-9-]{36}',attempt):raise ValueError('Invalid test attempt identity')
        if data.get('provider')!='kstudio-bai' or data.get('model')!=c['model']:raise ValueError('Test batch provider/model substitution denied')
        output=data.get('max_output_tokens')
        if type(output) is not int or not 1<=output<=c['max_output_tokens']:raise ValueError('Test batch output limit exceeded')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            # A crashed SDK owner leaves its reservation durable. Its OS lease
            # disappears; detecting that transitions the attempt to UNKNOWN.
            owners=db.execute("SELECT DISTINCT owner FROM attempts WHERE batch=? AND status='reserved'",(self.batch,)).fetchall()
            for (owner,) in owners:
                if owner==self.owner:continue
                probe=LocalRuntimeLease(self.lease_root/owner)
                try:probe.acquire()
                except RuntimeError:continue
                else:
                    probe.release();db.execute("UPDATE attempts SET status='unknown' WHERE batch=? AND owner=? AND status='reserved'",(self.batch,owner))
            unknown=db.execute("SELECT id,usage_json FROM attempts WHERE batch=? AND status='unknown'",(self.batch,)).fetchall()
            if unknown:
                policy=self.recovery
                acknowledged=set(policy['acknowledged_unknown_attempts']) if policy else set()
                if not policy or any(a not in acknowledged and json.loads(raw or '{}').get('error_code') not in ('TRANSPORT','TIMEOUT') for a,raw in unknown):
                    db.commit();raise ValueError('Test batch has unknown provider liability; no new request dispatched')
                # Success starts a new network-recovery sequence. A maximum of
                # two further dispatches can follow its first failure, across
                # process restarts AND concurrent subagents. Unknowns remain.
                last_success=db.execute("SELECT COALESCE(MAX(created),0) FROM attempts WHERE batch=? AND status='settled'",(self.batch,)).fetchone()[0]
                outstanding=db.execute("SELECT COUNT(*) FROM attempts WHERE batch=? AND status IN ('unknown','reserved') AND created>?",(self.batch,last_success)).fetchone()[0]
                if outstanding>policy['max_consecutive_retries']:
                    db.commit();raise ValueError('Test network retry limit reached; unknown usage preserved; no new request dispatched')
            if db.execute('SELECT 1 FROM attempts WHERE id=?',(attempt,)).fetchone():raise ValueError('Attempt already reserved; do not replay')
            count,total=db.execute('SELECT COUNT(*),COALESCE(SUM(reservation),0) FROM attempts WHERE batch=?',(self.batch,)).fetchone()
            if count>=c['max_requests'] or total+c['reserved_tokens_per_request']>c['max_reserved_tokens']:
                raise ValueError('Finite test batch ceiling reached; no new request dispatched')
            if 'allowed_run_ids' in c:
                run=db.execute('SELECT requests FROM runs WHERE batch=? AND id=?',(self.batch,self.run_id)).fetchone()
                if run and run[0]>=c['per_run_max_requests']:raise ValueError('Finite test run ceiling reached; no new request dispatched')
                db.execute('INSERT INTO runs VALUES (?,?,1) ON CONFLICT(batch,id) DO UPDATE SET requests=requests+1',(self.batch,self.run_id))
            # Keep the full conservative token charge even after known usage:
            # this cannot silently buy more attempts using uncertain accounting.
            db.execute('INSERT INTO attempts VALUES (?,?,?,?,?,?,?,?)',(attempt,self.batch,self.owner,str(data.get('session_id') or ''),'reserved',c['reserved_tokens_per_request'],json.dumps({'request_purpose':data.get('request_purpose','conversation'),'run_id':self.run_id}),time.time()));db.commit()
        return {'attempt_id':attempt,'batch_id':self.batch,'reserved_tokens':c['reserved_tokens_per_request']}

    def settle(self,data):
        attempt=data.get('attempt_id');usage=data.get('usage');reason=data.get('finish_reason')
        error_code=data.get('error_code') if data.get('error_code') in ('TRANSPORT','TIMEOUT','RATE_LIMIT','SERVER','AUTHENTICATION','QUOTA') else None
        known=(reason in ('stop','tool-calls','max-tokens') and isinstance(usage,dict)
               and all(type(usage.get(k)) is int and usage[k]>=0 for k in ('inputTokens','outputTokens')))
        if known and type(usage.get('totalTokens')) is int and usage['totalTokens']>self.config['reserved_tokens_per_request']:known=False
        if known and (usage['outputTokens']>self.config['max_output_tokens'] or usage['inputTokens']+usage['outputTokens']>self.config['reserved_tokens_per_request']):known=False
        state='settled' if known else 'unknown'
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT status,usage_json FROM attempts WHERE id=? AND batch=? AND owner=?',(attempt,self.batch,self.owner)).fetchone()
            if not row:raise ValueError('Unknown test reservation')
            if row[0]!='reserved':raise ValueError('Test reservation already finalized; no replay')
            db.execute('UPDATE attempts SET status=?,usage_json=? WHERE id=?',(state,json.dumps({**json.loads(row[1] or '{}'),'usage':usage,'finish_reason':reason,'error_code':error_code}),attempt));db.commit()
        return {'status':state}

    def close(self):
        try:
            with self.connect() as db:
                db.execute("UPDATE attempts SET status='unknown' WHERE batch=? AND owner=? AND status='reserved'",(self.batch,self.owner));db.commit()
        finally:self.lease.release()
