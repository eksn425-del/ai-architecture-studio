"""Repeatable operator entry; never prints dotenv values or deletes database volumes."""
from __future__ import annotations
import argparse, hashlib, ipaddress, json, os, re, subprocess, sys, tempfile, urllib.request
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parent
RELEASE_SHA = re.compile(r'[a-f0-9]{40}')
SHA256 = re.compile(r'[a-f0-9]{64}')
IMMUTABLE_IMAGE = re.compile(r'(?:[A-Za-z0-9._/:\-]+@)?sha256:[a-f0-9]{64}')
AUDIT_BASE_SHA = '6a8001c5369c323666efa099472ea62f4fbf1c51'
PLATFORM_KEY_ENV = 'KSTUDIO_BAI_PLATFORM_KEY'
LAUNCH_SWITCHES = ('KSTUDIO_REGISTRATION_ENABLED', 'KSTUDIO_PLATFORM_ENABLED',
                   'KSTUDIO_DOWNLOAD_ENABLED', 'KSTUDIO_PAYMENT_ENABLED')
OPERATIVE_ENV_DEFAULTS = {
    **dict.fromkeys(LAUNCH_SWITCHES, '0'),
    'KSTUDIO_PRICES_CONFIRMED': '0',
    'KSTUDIO_CLOUD_PRICES': '{}',
    'KSTUDIO_CLOUD_MODELS': '{}',
    'KSTUDIO_CLOUD_RELEASE': '{}',
    'KSTUDIO_OPERATOR': '{}',
    'KSTUDIO_GLOBAL_MAX_CONCURRENCY': '4',
    'KSTUDIO_PAYMENT_PROVIDER': 'disabled',
    'KSTUDIO_OIDC_METADATA_URL': '',
    'KSTUDIO_OIDC_CLIENT_ID': '',
    'KSTUDIO_OIDC_TOKEN_ENDPOINT_AUTH_METHOD': 'client_secret_post',
    'KSTUDIO_OIDC_SCOPE': 'openid profile phone email',
    'KSTUDIO_WECHATPAY_MCHID': '',
    'KSTUDIO_WECHATPAY_APPID': '',
}
NETWORKS = {
    'staging': ('172.31.91.0/24', '172.31.91.3'),
    'production': ('172.31.92.0/24', '172.31.92.3'),
}


def selected_private_network(environment):
    """Keep volumes and trusted front proxy disjoint across deployment environments."""
    subnet, proxy = NETWORKS[environment]
    return {'KSTUDIO_PRIVATE_SUBNET': subnet, 'KSTUDIO_PROXY_IP': proxy}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file, code, message, headers, new_url):
        return None


def check_health(values, *, release_sha=None):
    release_sha = release_sha or values['KSTUDIO_RELEASE_SHA']
    origin = values['KSTUDIO_CLOUD_PUBLIC_URL']
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    request = urllib.request.Request(origin.rstrip('/') + '/health/ready', headers={'Cache-Control': 'no-cache'})
    with opener.open(request, timeout=20) as response:
        observed = json.loads(response.read(64 * 1024))
    if (observed.get('status') != 'ready' or observed.get('environment') != values['KSTUDIO_CLOUD_ENV']
            or observed.get('release_sha') != release_sha or type(observed.get('schema_version')) is not int):
        raise ValueError('HTTPS endpoint did not prove expected environment, release and schema')
    return {'https_ready': True, 'url': origin, 'release_sha': observed['release_sha'],
            'environment': observed['environment'], 'schema_version': observed['schema_version']}


def _validate_gate_evidence(rows, candidate, evidence_root):
    root = evidence_root.resolve(strict=True)
    for row in rows:
        files = row.get('evidence_files')
        reviewer = row.get('independent_reviewer')
        if (row.get('status') != 'PASS' or row.get('code_sha') != candidate
                or not isinstance(reviewer, str) or not reviewer.strip()
                or row.get('blockers') != [] or not isinstance(files, list) or not files):
            raise ValueError(f"Missing independent acceptance for {row['id']}")
        seen = set()
        for item in files:
            relative = Path(str(item.get('path', ''))) if isinstance(item, dict) else Path()
            expected = item.get('sha256') if isinstance(item, dict) else None
            file = root / relative
            if (relative.is_absolute() or '..' in relative.parts or relative in seen
                    or not SHA256.fullmatch(str(expected)) or file.is_symlink()
                    or not file.resolve().is_relative_to(root) or not file.is_file()):
                raise ValueError(f"Invalid acceptance evidence for {row['id']}")
            with file.open('rb') as stream:
                measured = hashlib.file_digest(stream, 'sha256').hexdigest()
            if measured != expected:
                raise ValueError(f"Acceptance evidence changed for {row['id']}")
            seen.add(relative)


def _commercial_config(values, key):
    config = json.loads(values.get(key, '{}'))
    if not isinstance(config, dict):
        raise ValueError('Invalid commercial configuration object')
    return config


def _nonempty_label(value):
    return isinstance(value, str) and bool(value.strip())


def _bounded_int(value, lower, upper):
    return type(value) is int and lower <= value <= upper


def _public_https(url):
    if not isinstance(url, str) or not url or any(character.isspace() for character in url):
        return False
    parsed = urlsplit(url)
    return (parsed.scheme == 'https' and bool(parsed.hostname) and parsed.port in (None, 443)
            and parsed.username is None and parsed.password is None and not parsed.query and not parsed.fragment)


def commercial_open(values):
    """BYOK software fees require the same approval as other paid traffic."""
    prices = _commercial_config(values, 'KSTUDIO_CLOUD_PRICES')
    return (any(values.get(name) == '1' for name in LAUNCH_SWITCHES)
            or (values.get('KSTUDIO_PRICES_CONFIRMED') == '1' and bool(prices.get('byok_service_enabled'))))


def commercial_policy_sha256(values, gates):
    """Hash the operative launch policy without any key or secret material."""
    release = gates.get('release', {})
    policy = release.get('commercial_policy') if isinstance(release, dict) else None
    if not isinstance(policy, dict) or set(policy) != {'trial', 'rollout'}:
        raise ValueError('Explicit trial and rollout policies are required')
    # R3 creates new wallets with zero credits and has no promotional grant lane.
    if policy['trial'] != {'mode': 'none'}:
        raise ValueError('Approved trial must match the zero-grant implementation')
    rollout = policy['rollout']
    if (not isinstance(rollout, dict) or set(rollout) != {'mode', 'max_users', 'control_reference'}
            or rollout['mode'] != 'operator_managed' or not _bounded_int(rollout['max_users'], 1, 10**9)
            or not _nonempty_label(rollout['control_reference'])):
        raise ValueError('Verified operator-managed rollout scope is required')
    if 'production' != values.get('KSTUDIO_CLOUD_ENV') or values.get('KSTUDIO_PRICES_CONFIRMED') != '1':
        raise ValueError('Confirmed production policy is required')
    if values.get('KSTUDIO_PAYMENT_PROVIDER') != 'wechat_native':
        raise ValueError('Only the selected WeChat Native route can be approved')
    # Merchant/App identifiers and the IdP authority define who receives money
    # and who can join. These identifiers are distinct from rotating secrets.
    merchant = values.get('KSTUDIO_WECHATPAY_MCHID', '')
    payment_app = values.get('KSTUDIO_WECHATPAY_APPID', '')
    identity_origin = values.get('KSTUDIO_OIDC_METADATA_URL')
    identity_client = values.get('KSTUDIO_OIDC_CLIENT_ID')
    identity_method = values.get('KSTUDIO_OIDC_TOKEN_ENDPOINT_AUTH_METHOD', 'client_secret_post')
    scopes = values.get('KSTUDIO_OIDC_SCOPE', 'openid profile phone email').split()
    if (not re.fullmatch(r'[0-9]{1,32}', merchant) or not re.fullmatch(r'[A-Za-z0-9_-]{1,32}', payment_app)
            or not _public_https(identity_origin) or not re.fullmatch(r'[A-Za-z0-9._-]{1,128}', identity_client or '')
            or identity_method not in ('client_secret_post', 'client_secret_basic')
            or not {'openid', 'profile'}.issubset(scopes)):
        raise ValueError('Approved WeChat merchant and identity authority are required')

    prices = _commercial_config(values, 'KSTUDIO_CLOUD_PRICES')
    if (not _nonempty_label(prices.get('version')) or not isinstance(prices.get('packages'), dict) or not prices['packages']
            or type(prices.get('byok_service_enabled', False)) is not bool):
        raise ValueError('Production packages and software fee settings are required')
    # These fields participate in billing. Separate display metadata remains
    # outside the contract and must never contain confidential values.
    packages = {}
    for package_id, row in prices['packages'].items():
        if (not _nonempty_label(package_id) or not isinstance(row, dict)
                or not _bounded_int(row.get('amount'), 1, 10**12)
                or not _bounded_int(row.get('credits'), 1, 10**12)
                or row.get('currency') not in ('CNY', 'cny')
                or ('amount_minor' in row and (type(row['amount_minor']) is not int or row['amount_minor']!=row['amount']))):
            raise ValueError('Invalid approved WeChat package or inconsistent display pricing')
        packages[package_id] = {key: row[key] for key in ('amount', 'credits', 'currency')}
    byok_enabled = prices.get('byok_service_enabled', False)
    byok_units = prices.get('byok_task_units', 0)
    if not _bounded_int(byok_units, 0, 10**12):
        raise ValueError('Invalid BYOK software fee')

    routes = _commercial_config(values, 'KSTUDIO_CLOUD_MODELS')
    if any(not isinstance(item, dict) for item in routes.values()):
        raise ValueError('Invalid model route')
    active = [(model_id, item) for model_id, item in routes.items() if item.get('enabled') is True]
    if len(active) != 1:
        raise ValueError('Approve exactly one platform model for the initial release')
    model_id, model = active[0]
    if (not _nonempty_label(model_id) or model.get('verified') is not True
            or model.get('protocol') not in ('responses', 'chat-completions')
            or not _nonempty_label(model.get('upstream_model')) or not _public_https(model.get('base_url'))
            or model.get('key_env') != PLATFORM_KEY_ENV):
        raise ValueError('The intended platform model requires explicit route verification')
    tariff = model.get('price')
    price_fields = ('version', 'service_units', 'input_units_per_million', 'output_units_per_million')
    if (not isinstance(tariff, dict) or not _nonempty_label(tariff.get('version'))
            or any(not _bounded_int(tariff.get(key), 0, 10**12) for key in price_fields[1:])):
        raise ValueError('Invalid platform tariff')
    limits = {key: model.get(key) for key in ('max_output_tokens', 'reservation_units', 'daily_units',
                                              'turn_budget_units', 'max_turn_requests', 'turn_timeout_seconds')}
    if (any(not _bounded_int(limits[key], 1, 10**12) for key in
            ('max_output_tokens', 'reservation_units', 'daily_units', 'turn_budget_units'))
            or not _bounded_int(limits['max_turn_requests'], 1, 1000)
            or not _bounded_int(limits['turn_timeout_seconds'], 60, 86400)
            or not tariff['service_units'] <= limits['reservation_units'] <= min(limits['daily_units'], limits['turn_budget_units'])):
        raise ValueError('Explicit server-enforced platform limits are invalid')
    connection_timeout = model.get('timeouts', {})
    if (not isinstance(connection_timeout, dict) or set(connection_timeout) - {'connect', 'read', 'total'}):
        raise ValueError('Invalid platform timeout settings')
    deadlines = {'connect': 10, 'read': 120, 'total': 900, **connection_timeout}
    if (any(type(deadlines[key]) not in (int, float) or not 1 <= deadlines[key] <= limit
            for key, limit in (('connect', 30), ('read', 600), ('total', 1800))) or deadlines['total'] < deadlines['read']):
        raise ValueError('Invalid platform deadlines')
    effort = model.get('reasoning_effort', 'provider-default')
    if effort not in ('provider-default', 'none', 'minimal', 'low', 'medium', 'high', 'xhigh'):
        raise ValueError('Invalid platform reasoning policy')
    global_limit = int(values.get('KSTUDIO_GLOBAL_MAX_CONCURRENCY', '4'))
    refund = _commercial_config(values, 'KSTUDIO_OPERATOR').get('refund_policy')
    if not _bounded_int(global_limit, 1, 64) or not _nonempty_label(refund):
        raise ValueError('Approved concurrency and public refund policy are required')
    description = {
        'schema_version': 1,
        'prices': {'version': prices['version'], 'packages': packages,
                   'byok_service_enabled': byok_enabled, 'byok_task_units': byok_units},
        'platform': {'id': model_id, 'protocol': model['protocol'], 'endpoint': model['base_url'].rstrip('/'),
                     'upstream_model': model['upstream_model'], 'reasoning_effort': effort,
                     'limits': limits, 'timeouts': deadlines, 'price': {key: tariff[key] for key in price_fields}},
        'global_max_concurrency': global_limit,
        'payment': {'provider': values['KSTUDIO_PAYMENT_PROVIDER'], 'merchant': merchant, 'app_id': payment_app},
        'identity': {'metadata_url': identity_origin, 'client_id': identity_client,
                     'token_auth_method': identity_method, 'scopes': scopes},
        'refund_policy': refund,
        'trial': policy['trial'],
        'rollout': rollout,
    }
    return hashlib.sha256(canonical_json(description)).hexdigest()


def validate_launch(values, gates, approval, *, commercial, evidence_root):
    """Bind the owner approval to independently reviewed release and policy evidence."""
    if not commercial or not isinstance(gates, dict) or not isinstance(approval, dict):
        raise ValueError('Independent READY release and matching owner launch approval are required')
    expected_gates = {f'G{i:02d}' for i in range(11)}
    rows = gates.get('gates')
    if not isinstance(rows, list) or any(not isinstance(row, dict) or not isinstance(row.get('id'), str) for row in rows):
        raise ValueError('Invalid release gates')
    statuses = {row['id']: row for row in rows}
    candidate = values['KSTUDIO_RELEASE_SHA']
    release = _commercial_config(values, 'KSTUDIO_CLOUD_RELEASE')
    prices = _commercial_config(values, 'KSTUDIO_CLOUD_PRICES')
    requested = {name for name in LAUNCH_SWITCHES if values.get(name) == '1'}
    approved_switches = approval.get('switches', [])
    gate_hash = hashlib.sha256(canonical_json(gates)).hexdigest()
    artifact = gates.get('release', {})
    if (type(gates.get('schema_version')) is not int or gates['schema_version'] != 1
            or gates.get('audit_base_sha') != AUDIT_BASE_SHA
            or gates.get('implementation_sha') != candidate
            or gates.get('status') != 'READY_FOR_OWNER_LAUNCH_APPROVAL'
            or not expected_gates.issubset(statuses) or len(statuses) != len(rows)
            or not set(statuses).issubset(expected_gates | {'G11'})
            or not isinstance(artifact, dict) or not SHA256.fullmatch(str(release.get('sha256', '')))
            or artifact.get('signed_installer_sha256') != release['sha256']
            or artifact.get('version') != release.get('version') or not str(artifact.get('version') or '').strip()
            or type(release.get('size_bytes')) is not int or release['size_bytes'] <= 0
            or artifact.get('installer_size_bytes') != release['size_bytes']
            or artifact.get('download_url') != release.get('url') or not _public_https(release.get('url'))
            or approval.get('release_sha') != candidate or approval.get('gate_sha256') != gate_hash
            or approval.get('signed_installer_sha256') != release.get('sha256')
            or approval.get('origin') != values['KSTUDIO_CLOUD_PUBLIC_URL']
            or approval.get('approved') is not True or not _nonempty_label(approval.get('owner_reference'))
            or not isinstance(approved_switches, list) or any(name not in LAUNCH_SWITCHES for name in approved_switches)
            or not requested.issubset(approved_switches)
            or (prices.get('byok_service_enabled') is True and approval.get('byok_service_approved') is not True)
            or not all(release.get(key) is True for key in (
                'verified', 'public_distribution_authorized', 'signing_verified', 'clean_windows_verified'))
            or release.get('license_clearance') != 'CLEARED'):
        raise ValueError('Independent READY release and matching owner launch approval are required')
    policy_digest = commercial_policy_sha256(values, gates)
    if (artifact.get('commercial_policy_sha256') != policy_digest
            or approval.get('commercial_policy_sha256') != policy_digest):
        raise ValueError('Effective commercial policy differs from accepted and approved policy')
    _validate_gate_evidence([statuses[gate] for gate in sorted(expected_gates)], candidate, evidence_root)


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')


def rollback_image(compose, env, previous_image, expected_sha):
    """Probe the exact old image against the current database before changing services."""
    if (not IMMUTABLE_IMAGE.fullmatch(previous_image or '')
            or not RELEASE_SHA.fullmatch(expected_sha or '')):
        raise ValueError('Rollback requires a verified immutable image digest and its exact release SHA')
    image_label = subprocess.check_output(['docker', 'image', 'inspect', '--format',
        '{{index .Config.Labels "org.opencontainers.image.revision"}}', previous_image], text=True).strip()
    if image_label != expected_sha:
        raise ValueError('Rollback image revision does not match verified release')
    rollback_env = {**env, 'KSTUDIO_IMAGE': previous_image, 'KSTUDIO_RELEASE_SHA': expected_sha}
    if env.get('KSTUDIO_CLOUD_ENV') == 'production':
        rollback_env.update(dict.fromkeys(LAUNCH_SWITCHES, '0'))
        # Prevent new BYOK software fees as well. Merchant settings remain
        # available for existing orders, callbacks, refunds and reconciliation.
        rollback_env['KSTUDIO_PRICES_CONFIRMED'] = '0'
    # Run the old code with the existing mounted environment and read-only
    # audit before changing a service. No db migration or volume operation.
    probe = subprocess.run([*compose, 'run', '--no-deps', '--rm', '-T', 'app',
        'python', '-m', 'cloud.cli', 'rollback-check'], env=rollback_env, cwd=ROOT, check=True, capture_output=True)
    evidence = json.loads(probe.stdout)
    if (evidence.get('consistent') is not True or evidence.get('rollback_read_only') is not True
            or type(evidence.get('schema_version')) is not int):
        raise ValueError('Rollback image could not audit the current ledger')
    subprocess.run([*compose, 'up', '-d', '--no-build', '--no-deps', 'app', 'maintenance'],
        env=rollback_env, cwd=ROOT, check=True)


def restore_target(value):
    if not isinstance(value,str) or not re.fullmatch(r'kstudio_restore_[a-z0-9_]{1,45}',value):
        raise ValueError('Restore requires an explicit new kstudio_restore_* database')
    return value

def encrypted_backup(compose,env,output):
    """pg_dump runs inside the private DB container; no host port is needed."""
    target=Path(output).resolve()
    if target.exists() or target.is_symlink():raise ValueError('Refusing existing backup destination')
    if not target.parent.is_dir():raise ValueError('Create the private backup directory first')
    recipient=env.get('KSTUDIO_BACKUP_RECIPIENT','')
    if not recipient:raise ValueError('Backup public recipient is missing')
    age=env.get('KSTUDIO_AGE_EXECUTABLE','age')
    with tempfile.TemporaryDirectory(prefix='.kstudio-backup-',dir=target.parent) as temporary:
        temporary=Path(temporary);os.chmod(temporary,0o700)
        encrypted=temporary/'database.age'
        with (temporary/'private-errors.log').open('wb') as errors:
            producer=subprocess.Popen([*compose,'exec','-T','db','pg_dump','-U','kstudio','-d','kstudio',
                '--format=custom','--no-owner','--no-acl'],env=env,stdout=subprocess.PIPE,stderr=errors)
            consumer=None
            try:
                consumer=subprocess.Popen([age,'--recipient',recipient,'--output',str(encrypted)],
                    env=env,stdin=producer.stdout,stdout=subprocess.DEVNULL,stderr=errors)
                producer.stdout.close()
                c=consumer.wait(timeout=1800);p=producer.wait(timeout=1800)
                if p or c:raise RuntimeError('Encrypted database backup failed')
            finally:
                for child in (producer,consumer):
                    if child is not None and child.poll() is None:child.kill();child.wait()
        os.chmod(encrypted,0o600)
        # Same-filesystem exclusive publication cannot replace an earlier archive.
        os.link(encrypted,target)
    with target.open('rb') as source:sha=hashlib.file_digest(source,'sha256').hexdigest()
    return {'status':'ENCRYPTED_BACKUP_CREATED','database':'kstudio','bytes':target.stat().st_size,
        'sha256':sha,
        'transport':'docker compose exec private db; no host database port',
        'keys_in_archive':False,'scope':'single-database logical snapshot; not WAL/PITR'}

def encrypted_restore(compose,env,archive,target_database):
    """Authenticate the archive first, create a NEW DB, restore atomically, verify."""
    target_database=restore_target(target_database)
    archive=Path(archive).resolve()
    identity=env.get('KSTUDIO_BACKUP_IDENTITY','')
    if not archive.is_file() or not identity or not Path(identity).is_file():
        raise ValueError('Encrypted archive and separate private backup identity required')
    age=env.get('KSTUDIO_AGE_EXECUTABLE','age')
    with tempfile.TemporaryDirectory(prefix='.kstudio-restore-',dir=archive.parent) as temporary:
        temporary=Path(temporary);os.chmod(temporary,0o700)
        plain=temporary/'database.dump'
        # Decrypt completely before any SQL; authenticated EOF is required.
        subprocess.run([age,'--decrypt','--identity',identity,'--output',str(plain),str(archive)],
            env=env,check=True,capture_output=True,timeout=1800)
        os.chmod(plain,0o600)
        # createdb refuses an existing name. Never DROP or clear an old database.
        subprocess.run([*compose,'exec','-T','db','createdb','-U','kstudio','--',target_database],
            env=env,check=True,capture_output=True,timeout=60)
        with plain.open('rb') as incoming:
            subprocess.run([*compose,'exec','-T','db','pg_restore','-U','kstudio','--dbname',target_database,
                '--exit-on-error','--single-transaction','--no-owner','--no-acl'],
                env=env,stdin=incoming,check=True,capture_output=True,timeout=1800)
    # Read-only verify in the normal application image using its mounted vault keys.
    result=subprocess.run([*compose,'--profile','maintenance','run','--rm','-T','migrate',
        'python','-',target_database],env=env,input=(ROOT/'verify_restore.py').read_bytes(),
        check=True,capture_output=True,timeout=180)
    receipt=json.loads(result.stdout)
    if receipt.get('status')!='PASS':raise RuntimeError('Restored database validation failed')
    return receipt
def load_env(path):
    values={}
    for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
        line=line.strip()
        if not line or line.startswith('#'):continue
        key,sep,value=line.partition('=')
        if not sep or not re.fullmatch(r'[A-Z][A-Z0-9_]*',key):raise ValueError('Invalid private environment file syntax')
        values[key]=value.strip().strip('"') if not value.lstrip().startswith(('{','[')) else value.strip()
    return values

def check(values, *, commercial=False):
    required=['KSTUDIO_DOMAIN','KSTUDIO_DATABASE_PASSWORD','KSTUDIO_CLOUD_DATABASE_URL','KSTUDIO_CLOUD_SESSION_SECRET','KSTUDIO_CLOUD_PUBLIC_URL','KSTUDIO_IMAGE','KSTUDIO_RELEASE_SHA','KSTUDIO_SECRET_DIR','KSTUDIO_CLOUD_ENV']
    if commercial:required+=['KSTUDIO_OIDC_METADATA_URL','KSTUDIO_OIDC_CLIENT_ID','KSTUDIO_OIDC_CLIENT_SECRET','KSTUDIO_VAULT_ACTIVE_KEY_VERSION','KSTUDIO_VAULT_KEYS_FILE','KSTUDIO_WECHATPAY_MCHID','KSTUDIO_WECHATPAY_APPID','KSTUDIO_WECHATPAY_API_V3_KEY_FILE','KSTUDIO_WECHATPAY_MERCHANT_PRIVATE_KEY_FILE','KSTUDIO_WECHATPAY_MERCHANT_SERIAL','KSTUDIO_WECHATPAY_VERIFY_MATERIAL_FILE','KSTUDIO_BAI_PLATFORM_KEY','KSTUDIO_BACKUP_RECIPIENT']
    missing=[k for k in required if not values.get(k) or any(x in values[k] for x in ('REPLACE','example.invalid','URL_ENCODED'))]
    errors=[]
    if values.get('KSTUDIO_CLOUD_ENV') not in NETWORKS:errors.append('invalid_deployment_environment')
    try:
        public=urlsplit(values.get('KSTUDIO_CLOUD_PUBLIC_URL',''))
        if public.hostname!=values.get('KSTUDIO_DOMAIN'):errors.append('public_domain_mismatch')
        if (public.scheme!='https' or not public.hostname or '.' not in public.hostname
                or public.username is not None or public.password is not None or public.port not in (None,443)
                or public.path not in ('','/') or public.query or public.fragment):
            errors.append('invalid_https_origin')
        if public.hostname:
            try:ipaddress.ip_address(public.hostname)
            except ValueError:pass
            else:errors.append('public_origin_requires_dns_name')
    except ValueError:errors.append('invalid_https_origin')
    try:
        database=urlsplit(values.get('KSTUDIO_CLOUD_DATABASE_URL',''))
        if (database.scheme!='postgresql+psycopg' or database.netloc is None or database.hostname!='db'
                or database.port!=5432 or database.path!='/kstudio' or database.username!='kstudio'
                or not database.password or database.query or database.fragment):
            errors.append('database_outside_private_compose_contract')
    except ValueError:errors.append('database_outside_private_compose_contract')
    image=values.get('KSTUDIO_IMAGE','')
    sha=values.get('KSTUDIO_RELEASE_SHA','')
    if image and sha and image != 'kstudio-cloud:'+sha and not IMMUTABLE_IMAGE.fullmatch(image):errors.append('image_outside_release_contract')
    if values.get('KSTUDIO_RELEASE_SHA') and not RELEASE_SHA.fullmatch(values['KSTUDIO_RELEASE_SHA']):errors.append('invalid_release_sha')
    if len(values.get('KSTUDIO_CLOUD_SESSION_SECRET',''))<32:errors.append('session_secret_too_short')
    if any(values.get(name,'0') not in ('0','1') for name in LAUNCH_SWITCHES):errors.append('invalid_launch_switch')
    if commercial and values.get('KSTUDIO_PRICES_CONFIRMED')!='1':errors.append('prices_not_confirmed')
    if commercial and values.get('KSTUDIO_PAYMENT_PROVIDER')!='wechat_native':errors.append('wechat_native_not_selected')
    if commercial:
        try:
            operator=json.loads(values.get('KSTUDIO_OPERATOR','{}'))
            if not isinstance(operator,dict) or not all(operator.get(k) for k in ('name','icp','privacy_contact','data_retention','refund_policy')) or not (operator.get('support_email') or operator.get('support_url')):errors.append('operator_identity_contact_or_icp_missing')
            release=json.loads(values.get('KSTUDIO_CLOUD_RELEASE','{}'))
            if (not isinstance(release,dict) or not all(release.get(k) is True for k in ('verified','public_distribution_authorized','signing_verified','clean_windows_verified'))
                    or release.get('license_clearance')!='CLEARED' or not re.fullmatch(r'[a-f0-9]{64}',str(release.get('sha256','')))):
                errors.append('release_acceptance_missing')
        except ValueError:errors.append('invalid_public_metadata_json')
    return {'status':'READY_FOR_OPERATOR_EXECUTION' if not missing and not errors else 'BLOCKED_CONFIGURATION','missing_names':missing,'errors':errors,'production_acceptance':'NOT_PROVEN_BY_PREFLIGHT'}

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['check','commercial-policy','deploy','health','audit','recover-stale','backup','restore-drill','rollback']);p.add_argument('--env-file',required=True);p.add_argument('--commercial',action='store_true');p.add_argument('--output');p.add_argument('--archive');p.add_argument('--target-db');p.add_argument('--previous-image');p.add_argument('--previous-release-sha');p.add_argument('--permit-closed-production',action='store_true');p.add_argument('--gate-state',type=Path);p.add_argument('--launch-approval',type=Path);a=p.parse_args()
    envfile=Path(a.env_file).resolve();values=load_env(envfile)
    if a.action=='commercial-policy':
        if not a.gate_state:raise ValueError('A gate state with rollout and trial policies is required')
        gates=json.loads(a.gate_state.read_bytes())
        print(json.dumps({'commercial_policy_sha256':commercial_policy_sha256(values,gates)}))
        return 0
    # Recovery remains available even when new commercial credentials or
    # pricing have been withdrawn. The immutable old image performs its probe.
    result=check(values,commercial=a.commercial and a.action!='rollback')
    if a.action=='check':print(json.dumps(result));return 0 if result['status']=='READY_FOR_OPERATOR_EXECUTION' else 2
    if result['status']!='READY_FOR_OPERATOR_EXECUTION':print(json.dumps(result));return 2
    environment=values['KSTUDIO_CLOUD_ENV']
    env={**os.environ,**values,'KSTUDIO_ENV_FILE':str(envfile),**selected_private_network(environment)}
    # Give Compose exactly the operative values validated above. The shell
    # cannot inject a switch or a policy absent from the private dotenv.
    env.update({name:values.get(name,default) for name,default in OPERATIVE_ENV_DEFAULTS.items()})
    compose=['docker','compose','--project-name','kstudio-cloud-'+environment,
        '--env-file',str(envfile),'-f',str(ROOT/'compose.yml')]
    def docker(*args):subprocess.run([*compose,*args],env=env,cwd=ROOT,check=True)
    if a.action in ('deploy','rollback') and (os.environ.get('DOCKER_HOST') or os.environ.get('DOCKER_CONTEXT')):
        raise ValueError('Use the local authorized Docker context on the deployment host')
    if a.action=='deploy':
        if environment=='production':
            if commercial_open(values):
                if not a.gate_state or not a.launch_approval:
                    raise ValueError('Opening production requires verified release and private owner approval receipts')
                validate_launch(values,json.loads(a.gate_state.read_bytes()),json.loads(a.launch_approval.read_bytes()),
                    commercial=a.commercial,evidence_root=a.gate_state.resolve().parent)
            elif not a.permit_closed_production:
                raise ValueError('Explicit closed production deployment authorization is required')
        actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT.parent,text=True).strip()
        if actual!=values['KSTUDIO_RELEASE_SHA']:raise ValueError('Deploy checkout differs from pinned release SHA')
        if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT.parent,text=True).strip():raise ValueError('Deploy requires a clean source checkout')
        docker('config','--quiet')
        if IMMUTABLE_IMAGE.fullmatch(values['KSTUDIO_IMAGE']):
            image_label = subprocess.check_output(['docker','image','inspect','--format',
                '{{index .Config.Labels "org.opencontainers.image.revision"}}',values['KSTUDIO_IMAGE']],text=True).strip()
            if image_label!=actual:raise ValueError('Pinned image revision does not match pinned source')
        else:
            docker('build','app')
        docker('up','-d','db')
        docker('--profile','maintenance','run','--rm','migrate')
        docker('up','-d','--no-build','app','proxy','maintenance')
        docker('exec','-T','app','python','-m','cloud.cli','audit')
    elif a.action=='health':
        print(json.dumps(check_health(values)))
    elif a.action in ('audit','recover-stale'):docker('exec','-T','app','python','-m','cloud.cli',a.action)
    elif a.action=='rollback':
        rollback_image(compose,env,a.previous_image,a.previous_release_sha)
        if environment=='production':
            print('Production admission and new charges are closed. Verify HTTPS, existing order access and ledger before restoring traffic.')
        else:
            print('Application image changed. Verify HTTPS readiness against the previous release and audit.')
    elif a.action=='backup':
        if not a.output:raise ValueError('New private encrypted backup output required')
        print(json.dumps(encrypted_backup(compose,env,a.output)))
    elif a.action=='restore-drill':
        if not a.archive:raise ValueError('Encrypted archive required')
        print(json.dumps(encrypted_restore(compose,env,a.archive,a.target_db)))
    return 0
if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:
        # Library messages can include URLs/passwords. Report only type at boundary.
        print(json.dumps({'status':'FAILED','error_type':type(exc).__name__,'secrets_printed':False}));sys.exit(1)
