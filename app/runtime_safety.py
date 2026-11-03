"""One local service per JSON project store; not a distributed tenant lock."""
from __future__ import annotations

import os
from pathlib import Path


class LocalRuntimeLease:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.handle = None

    def acquire(self):
        if self.handle is not None:
            raise RuntimeError('This local runtime lease is already held.')
        if os.environ.get('K_STUDIO_DEPLOYMENT_MODE', 'local') != 'local':
            raise RuntimeError('This build is local and single-user. Public managed deployment requires the separate authenticated control plane.')
        try:
            workers = int(os.environ.get('WEB_CONCURRENCY', '1'))
        except ValueError:
            raise RuntimeError('WEB_CONCURRENCY must be 1 for the local JSON store.') from None
        if workers != 1:
            raise RuntimeError('Use one worker for the local JSON store; multiple workers cannot share the native writer.')
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / '.kstudio-runtime.lock'
        if path.is_symlink():
            raise RuntimeError('Unsafe runtime lease path.')
        handle = path.open('a+b')
        try:
            if path.stat().st_size == 0:
                handle.write(b'\0'); handle.flush()
            handle.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            handle.close()
            raise RuntimeError('Another K Studio service owns this runtime. Stop that service normally or use an independent runtime; project files were not changed.') from None
        self.handle = handle
        return self

    def release(self):
        handle, self.handle = self.handle, None
        if handle is None:
            return
        try:
            handle.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()

    def __enter__(self):
        return self.acquire()

    def __exit__(self, *exc):
        self.release()


def release_readiness() -> dict:
    """Report implemented boundaries, never infer a commercial PASS from flags."""
    return {
        'schema_version': 1,
        'deployment_mode': 'local_single_user',
        'paid_multi_user_release_ready': False,
        'project_storage': 'local_json_files',
        'local_service_lease': 'os_advisory_lock_at_application_lifespan',
        'existing_uninstrumented_services': 'must_be_stopped_before_adoption',
        'cloud_capabilities': {
            name: 'not_implemented' for name in (
                'tenant_auth_and_authorization', 'postgres_atomic_credit_ledger',
                'durable_job_queue_and_recovery', 'authenticated_remote_connector_pairing',
                'private_object_storage', 'payment_webhook_idempotency')
        },
        'release_evidence_required': [
            'approved_provider_real_image_tool_loop_and_cancel',
            'native_source_fidelity_local_edit_keep_save_download_reopen',
            'tenant_isolation_and_quota_race_tests',
            'mainland_network_load_and_failure_drills',
            'backup_restore_and_release_rollback_drills',
            'commercial_privacy_licensing_and_mainland_launch_review',
        ],
    }
