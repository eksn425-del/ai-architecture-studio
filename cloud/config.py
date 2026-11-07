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
    oidc_token_endpoint_auth_method: str = 'client_secret_post'
    oidc_scope: str = 'openid profile phone email'
    vault_active_key_version: str = ''
    vault_keys_file: str = ''
    payment_provider: str = 'stripe'
    wechatpay_mchid: str = ''
    wechatpay_appid: str = ''
    wechatpay_api_v3_key_file: str = ''
    wechatpay_merchant_private_key_file: str = ''
    wechatpay_merchant_serial: str = ''
    wechatpay_verify_material_file: str = ''
    registration_enabled: bool = True
    payment_enabled: bool = True
    platform_enabled: bool = True
    download_enabled: bool = True
    global_max_concurrency: int = 4
    operator: dict = field(default_factory=dict)
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
        if self.oidc_token_endpoint_auth_method not in ('client_secret_post','client_secret_basic'):
            raise ValueError('OIDC token endpoint requires an authenticated client method')
        if not {'openid','profile'}.issubset(set(self.oidc_scope.split())):
            raise ValueError('OIDC scope must include openid and profile')
        if self.payment_provider not in ('stripe','wechat_native','disabled'):
            raise ValueError('Unknown payment provider')
        if type(self.global_max_concurrency) is not int or not 1<=self.global_max_concurrency<=64:
            raise ValueError('Global concurrency must be between 1 and 64')
        if bool(self.vault_active_key_version) != bool(self.vault_keys_file):
            raise ValueError('Vault key version and key file must be configured together')
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
            oidc_token_endpoint_auth_method=os.getenv('KSTUDIO_OIDC_TOKEN_ENDPOINT_AUTH_METHOD','client_secret_post'),
            oidc_scope=os.getenv('KSTUDIO_OIDC_SCOPE','openid profile phone email'),
            vault_active_key_version=os.getenv('KSTUDIO_VAULT_ACTIVE_KEY_VERSION',''),
            vault_keys_file=os.getenv('KSTUDIO_VAULT_KEYS_FILE',''),
            payment_provider=os.getenv('KSTUDIO_PAYMENT_PROVIDER','disabled'),
            wechatpay_mchid=os.getenv('KSTUDIO_WECHATPAY_MCHID',''),
            wechatpay_appid=os.getenv('KSTUDIO_WECHATPAY_APPID',''),
            wechatpay_api_v3_key_file=os.getenv('KSTUDIO_WECHATPAY_API_V3_KEY_FILE',''),
            wechatpay_merchant_private_key_file=os.getenv('KSTUDIO_WECHATPAY_MERCHANT_PRIVATE_KEY_FILE',''),
            wechatpay_merchant_serial=os.getenv('KSTUDIO_WECHATPAY_MERCHANT_SERIAL',''),
            wechatpay_verify_material_file=os.getenv('KSTUDIO_WECHATPAY_VERIFY_MATERIAL_FILE',''),
            registration_enabled=os.getenv('KSTUDIO_REGISTRATION_ENABLED')=='1',
            payment_enabled=os.getenv('KSTUDIO_PAYMENT_ENABLED')=='1',
            platform_enabled=os.getenv('KSTUDIO_PLATFORM_ENABLED')=='1',
            download_enabled=os.getenv('KSTUDIO_DOWNLOAD_ENABLED')=='1',
            global_max_concurrency=int(os.getenv('KSTUDIO_GLOBAL_MAX_CONCURRENCY','4')),
            operator=obj('KSTUDIO_OPERATOR'),
            stripe_key=os.getenv('KSTUDIO_STRIPE_KEY',''),
            stripe_webhook_secret=os.getenv('KSTUDIO_STRIPE_WEBHOOK_SECRET',''),
            prices_confirmed=os.getenv('KSTUDIO_PRICES_CONFIRMED')=='1',
            prices=obj('KSTUDIO_CLOUD_PRICES'), models=obj('KSTUDIO_CLOUD_MODELS'),
            release=obj('KSTUDIO_CLOUD_RELEASE'),
            website_dir=os.getenv('KSTUDIO_WEBSITE_DIR','website'),
            admin_subjects=tuple(json.loads(os.getenv('KSTUDIO_ADMIN_SUBJECTS','[]')))).validate()
