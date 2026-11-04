"""One explicit, non-secret connection configuration for every DSH stage.

Capabilities are declarations, not a certificate of provider compatibility.
Unknown endpoints get conservative text-only defaults, never a guessed 128k
vision model. The historical BAI profile is scoped to an exact endpoint/model.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib
import json

EFFORTS = ('provider-default', 'low', 'high')


@dataclass(frozen=True)
class EffectiveConfiguration:
    endpoint: str
    model: str
    protocol: str
    requested_effort: str
    context_window: int
    max_output_tokens: int
    vision: bool
    tools: bool
    streaming: bool
    capability_source: str
    verification_status: str
    request_retries: int = 2

    @property
    def sdk_effort(self):
        # An omitted SDK selector plus a request-local reasoningEfforts:false
        # descriptor omits the wire field in BOTH supported protocols. With
        # off:null alone, Responses unexpectedly sends effort=none. This is
        # absence of a client control, NOT a claim that thinking is disabled.
        return None if self.requested_effort == 'provider-default' else self.requested_effort

    def evidence(self):
        return {'requested': {'model': self.model, 'protocol': self.protocol,
                             'reasoning_effort': self.requested_effort},
                'effective': {**asdict(self), 'sdk_reasoning_effort': self.sdk_effort,
                              'wire_reasoning_effort': None if self.sdk_effort == 'off' else self.sdk_effort},
                'reported': {'model': None, 'reasoning_effort': None, 'context_window': None},
                'supported_efforts': list(EFFORTS),
                'provider': 'bai' if self.endpoint=='https://api.b.ai/v1' else 'deepseek' if self.endpoint.rstrip('/')=='https://api.deepseek.com' else 'user-configured',
                'accepted_runtime_version':'0.2.1-rc.5 (offline wire only)',
                'capability_evidence':{'provider_declaration':None,'user_declaration':self.capability_source=='user_declared_unverified',
                    'offline_contract':'DSH serializer; not this endpoint','live_request':None,'live_modeling':None,
                    'image_formats':['PNG','JPEG','WEBP','GIF frame 0 converted to PNG'],
                    'max_image_bytes':25*1024*1024,'max_decoded_pixels':40000000,
                    'provider_image_limits':None,'parallel_tools':None,'streamed_tool_arguments':None,
                    'usage_semantics':None,'retry_after':'official SDK policy; provider behavior unverified'}}

    def binding(self):
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()

    def model_descriptor(self):
        return {'id': self.model, 'name': self.model, 'contextWindow': self.context_window,
                'maxTokens': self.max_output_tokens, 'input': ['text', 'image'] if self.vision else ['text'],
                'reasoningEfforts': False if self.requested_effort=='provider-default' else {'off': None, 'low': 'low', 'high': 'high'}}

    def compaction(self):
        reserve = min(8192, self.context_window // 8)
        summary = min(4096, self.context_window // 16)
        remaining = self.context_window - self.max_output_tokens - reserve
        return {'headroomTokens': reserve, 'maxTokens': summary,
                'retainTokens': min(16384, max(1024, remaining // 3))}


def resolve_configuration(connection):
    endpoint = connection['api_base'].rstrip('/')
    model = connection['model'].removeprefix('openai/').removeprefix('deepseek/')
    effort = connection.get('reasoning_effort', 'provider-default')
    if effort not in EFFORTS:
        raise ValueError('当前 DeepSeek Harness 接入支持供应商默认、Low、High；该连接档位尚未验证，未自动替换。')
    known = endpoint == 'https://api.b.ai/v1' and model == 'deepseek-v4.1-flash'
    caps = json.loads(connection.get('capabilities_json') or '{}')
    if not isinstance(caps, dict) or set(caps) - {'context_window', 'max_output_tokens', 'vision', 'tools', 'streaming'}:
        raise ValueError('模型能力参数格式不正确。')
    window = caps.get('context_window', 131072 if known else 16384)
    output = caps.get('max_output_tokens', 32768 if known else 4096)
    if type(window) is not int or not 8192 <= window <= 2_000_000:
        raise ValueError('上下文容量需为8192至2000000的整数。')
    if type(output) is not int or not 256 <= output <= min(32768, window // 2):
        raise ValueError('输出上限需为256至32768的整数，且不超过上下文容量的一半。')
    values = [caps.get(k, known) for k in ('vision', 'tools', 'streaming')]
    if any(type(v) is not bool for v in values):
        raise ValueError('图像、工具和流式能力必须明确为true或false。')
    retries=connection.get('request_retries', 2)
    if type(retries) is not int or not 0<=retries<=2:
        raise ValueError('request_retries must be an integer from 0 through 2.')
    return EffectiveConfiguration(endpoint, model,
        'openai-responses' if connection.get('mode') == 'codex-responses' else 'openai-completions',
        effort, window, output, *values,
        'user_declared_unverified' if caps else 'historical_local_configuration' if known else 'conservative_unverified_default',
        'NOT_RUN' if caps or not known else 'HISTORICAL_LOCAL_MODELING_ONLY', retries)
