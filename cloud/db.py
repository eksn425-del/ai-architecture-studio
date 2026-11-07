"""Versioned schema; explicit migrations only, never boot-time production mutation."""
import time, uuid
from sqlalchemy import (MetaData, Table, Column, String, Integer, BigInteger, Text,
                        ForeignKey, UniqueConstraint, CheckConstraint, create_engine, event,inspect,text,Index)
SCHEMA_VERSION=3
metadata=MetaData()
schema_version=Table('schema_version',metadata,Column('version',Integer,primary_key=True))
users=Table('users',metadata,Column('id',String(64),primary_key=True),Column('subject',String(512),unique=True,nullable=False),Column('display_name',String(128),nullable=False),Column('created',BigInteger,nullable=False))
sessions=Table('sessions',metadata,Column('id',String(64),primary_key=True),Column('user_id',ForeignKey('users.id'),nullable=False),Column('token_hash',String(64),unique=True,nullable=False),Column('csrf',String(128),nullable=False),Column('device_name',String(128),nullable=False),Column('expires',BigInteger,nullable=False),Column('revoked',Integer,nullable=False,default=0),Column('refresh_hash',String(64)),Column('refresh_expires',BigInteger),Column('authenticated_at',BigInteger,nullable=False,server_default='0'))
device_authorizations=Table('device_authorizations',metadata,Column('id',String(64),primary_key=True),Column('device_hash',String(64),unique=True,nullable=False),Column('user_code_hash',String(64),unique=True,nullable=False),Column('challenge',String(128),nullable=False),Column('device_name',String(128),nullable=False),Column('state',String(32),nullable=False),Column('user_id',ForeignKey('users.id')),Column('expires',BigInteger,nullable=False),Column('last_poll',BigInteger,nullable=False))
wallets=Table('wallets',metadata,Column('user_id',ForeignKey('users.id'),primary_key=True),Column('balance',BigInteger,nullable=False,default=0),Column('reserved',BigInteger,nullable=False,default=0),CheckConstraint('balance >= 0 AND reserved >= 0 AND balance >= reserved'))
ledger=Table('ledger_events',metadata,Column('id',String(64),primary_key=True),Column('user_id',ForeignKey('users.id'),nullable=False),Column('kind',String(32),nullable=False),Column('amount',BigInteger,nullable=False),Column('reservation_delta',BigInteger,nullable=False),Column('reference',String(128),nullable=False),Column('idempotency_key',String(256),unique=True,nullable=False),Column('price_version',String(64),nullable=False),Column('reason',String(256),nullable=False),Column('created',BigInteger,nullable=False))
tasks=Table('tasks',metadata,Column('id',String(64),primary_key=True),Column('user_id',ForeignKey('users.id'),nullable=False),Column('key',String(128),nullable=False),Column('mode',String(16),nullable=False),Column('model',String(128),nullable=False),Column('state',String(32),nullable=False),Column('reserve',BigInteger,nullable=False),Column('charged',BigInteger),Column('price_version',String(64),nullable=False),Column('price_json',Text,nullable=False),Column('created',BigInteger,nullable=False),Column('updated',BigInteger,nullable=False),UniqueConstraint('user_id','key'))
orders=Table('orders',metadata,Column('id',String(64),primary_key=True),Column('user_id',ForeignKey('users.id'),nullable=False),Column('key',String(128),nullable=False),Column('package',String(64),nullable=False),Column('amount',BigInteger,nullable=False),Column('currency',String(8),nullable=False),Column('credits',BigInteger,nullable=False),Column('state',String(32),nullable=False),Column('provider_session',String(128),unique=True),Column('payment_id',String(128),unique=True),Column('checkout_url',Text),Column('created',BigInteger,nullable=False),UniqueConstraint('user_id','key'))
payment_events=Table('payment_events',metadata,Column('id',String(128),primary_key=True),Column('order_id',ForeignKey('orders.id'),nullable=False),Column('created',BigInteger,nullable=False))
payment_reconciliation=Table('payment_reconciliation',metadata,Column('event_id',String(128),primary_key=True),Column('order_id',ForeignKey('orders.id'),nullable=False),Column('amount',BigInteger,nullable=False),Column('reason',String(256),nullable=False),Column('state',String(32),nullable=False),Column('created',BigInteger,nullable=False))
outbox=Table('outbox',metadata,Column('id',String(64),primary_key=True),Column('topic',String(64),nullable=False),Column('reference',String(128),nullable=False),Column('state',String(32),nullable=False),Column('created',BigInteger,nullable=False))
feedback=Table('feedback',metadata,Column('id',String(64),primary_key=True),Column('user_id',ForeignKey('users.id')),Column('message',Text,nullable=False),Column('email',String(256)),Column('created',BigInteger,nullable=False))
indexes=(Index('ix_ledger_user_created',ledger.c.user_id,ledger.c.created),Index('ix_tasks_user_state',tasks.c.user_id,tasks.c.state,tasks.c.updated),Index('ix_orders_user_created',orders.c.user_id,orders.c.created),Index('ix_sessions_user',sessions.c.user_id),Index('ix_sessions_refresh',sessions.c.refresh_hash,unique=True))
def now(): return int(time.time())
def uid(): return uuid.uuid4().hex
def engine_for(url):
    engine=create_engine(url,pool_pre_ping=True,connect_args={'check_same_thread':False,'timeout':30} if url.startswith('sqlite') else {})
    if url.startswith('sqlite'):
        @event.listens_for(engine,'connect')
        def sqlite_settings(dbapi,record):
            dbapi.execute('PRAGMA foreign_keys=ON')
            dbapi.execute('PRAGMA journal_mode=WAL')
    return engine
def migrate(engine):
    # Refuse unknown future versions BEFORE touching their schema.
    if inspect(engine).has_table('schema_version'):
        with engine.connect() as c:
            versions=c.execute(schema_version.select()).scalars().all()
            if len(versions)>1 or any(v not in (1,2,SCHEMA_VERSION) for v in versions):
                raise ValueError('Unsupported database schema version')
    from . import provider_connections, wechat_payments  # registers tables on shared metadata
    metadata.create_all(engine)
    with engine.begin() as c:
        columns={x['name'] for x in inspect(c).get_columns('sessions')}
        if 'refresh_hash' not in columns:c.execute(text('ALTER TABLE sessions ADD COLUMN refresh_hash VARCHAR(64)'))
        if 'refresh_expires' not in columns:c.execute(text('ALTER TABLE sessions ADD COLUMN refresh_expires BIGINT'))
        if 'authenticated_at' not in columns:c.execute(text('ALTER TABLE sessions ADD COLUMN authenticated_at BIGINT NOT NULL DEFAULT 0'))
        for index in indexes:index.create(c,checkfirst=True)
        current=c.execute(schema_version.select()).scalar()
        if current is None:c.execute(schema_version.insert().values(version=SCHEMA_VERSION))
        elif current in (1,2):c.execute(schema_version.update().values(version=SCHEMA_VERSION))
        elif current!=SCHEMA_VERSION:raise ValueError('Unsupported database schema version')
