from dataclasses import dataclass, field
import json, os
from urllib.parse import urlparse

@dataclass
class Settings:
    database_url: str
    session_secret: str
    public_url: str = 'http://127.0.0.1:8920'
    environment: str = 'local'
    oidc_metadata_url: str = ''
    oidc_client_id: str = ''
    oidc_client_secret: str = ''
    stripe_key: str = ''
    stripe_webhook_secret: str = ''
    prices_confirmed: bool = False
    prices: dict = field(default_factory=dict)
    models: dict = field(default_factory=dict)
    release: dict = field(default_factory=dict)
    session_seconds: int = 3600
    max_request_bytes: int = 8_000_000
    website_dir: str = 'website'
    admin_subjects: tuple = ()

    def validate(self):
        if len(self.session_secret) < 32:
            raise ValueError('KSTUDIO_CLOUD_SESSION_SECRET must contain at least 32 characters')
        if self.environment not in ('local', 'test', 'staging', 'production'):
            raise ValueError('Unknown cloud environment')
        if self.environment in ('staging', 'production'):
            if not self.database_url.startswith('postgresql'):
                raise ValueError('Deployed control plane requires PostgreSQL')
            if urlparse(self.public_url).scheme != 'https':
                raise ValueError('Deployed control plane requires HTTPS public URL')
        if self.stripe_key and self.environment != 'production' and not self.stripe_key.startswith('sk_test_'):
            raise ValueError('Non-production environment refuses live payment key')
        if self.stripe_key and not self.prices_confirmed:
            raise ValueError('Payment requests require explicitly confirmed price configuration')
        return self

    @classmethod
    def from_env(cls):
        def obj(name):
            return json.loads(os.environ.get(name, '{}'))
        return cls(database_url=os.environ['KSTUDIO_CLOUD_DATABASE_URL'],
            session_secret=os.environ['KSTUDIO_CLOUD_SESSION_SECRET'],
            public_url=os.getenv('KSTUDIO_CLOUD_PUBLIC_URL','http://127.0.0.1:8920'),
            environment=os.getenv('KSTUDIO_CLOUD_ENV','local'),
            oidc_metadata_url=os.getenv('KSTUDIO_OIDC_METADATA_URL',''),
            oidc_client_id=os.getenv('KSTUDIO_OIDC_CLIENT_ID',''),
            oidc_client_secret=os.getenv('KSTUDIO_OIDC_CLIENT_SECRET',''),
            stripe_key=os.getenv('KSTUDIO_STRIPE_KEY',''),
            stripe_webhook_secret=os.getenv('KSTUDIO_STRIPE_WEBHOOK_SECRET',''),
            prices_confirmed=os.getenv('KSTUDIO_PRICES_CONFIRMED')=='1',
            prices=obj('KSTUDIO_CLOUD_PRICES'), models=obj('KSTUDIO_CLOUD_MODELS'),
            release=obj('KSTUDIO_CLOUD_RELEASE'),
            website_dir=os.getenv('KSTUDIO_WEBSITE_DIR','website'),
            admin_subjects=tuple(json.loads(os.getenv('KSTUDIO_ADMIN_SUBJECTS','[]')))).validate()
