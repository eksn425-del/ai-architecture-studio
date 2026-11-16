"""Bounded, local-only Chinese dictation. No audio files or provider credentials."""
import importlib.util
import io
import json
import threading
import wave
from pathlib import Path

from fastapi import HTTPException, Request
from starlette.concurrency import run_in_threadpool

MAX_BYTES = 1920044  # 60 seconds, mono 16 kHz PCM16 + WAV header


class LocalSpeech:
    def __init__(self, runtime: Path):
        self.path = runtime / 'speech-models/vosk-model-small-cn-0.22'
        location = runtime / 'speech-models/location.json'
        if location.is_file():
            self.path = Path(json.loads(location.read_text(encoding='utf-8'))['model_path'])
        self.model = None
        self.lock = threading.Lock()

    def ready(self):
        return (self.path / 'am/final.mdl').is_file() and importlib.util.find_spec('vosk') is not None

    def transcribe(self, audio: bytes):
        if not self.ready():
            raise HTTPException(503, '本机语音识别组件尚未安装，请更新完整安装包。')
        try:
            with wave.open(io.BytesIO(audio), 'rb') as wav:
                if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) != (1, 2, 16000):
                    raise ValueError('format')
                if not 1 <= wav.getnframes() <= 960000:
                    raise ValueError('duration')
                pcm = wav.readframes(wav.getnframes())
                if len(pcm) != wav.getnframes() * 2:
                    raise ValueError('truncated')
        except (ValueError, wave.Error, EOFError):
            raise HTTPException(400, '录音格式无效；请重新录制不超过 60 秒的语音。') from None
        if not self.lock.acquire(blocking=False):
            raise HTTPException(409, '上一段语音还在识别，请稍候。')
        try:
            from vosk import Model, KaldiRecognizer, SetLogLevel
            SetLogLevel(-1)
            if self.model is None:
                self.model = Model(str(self.path))
            recognizer = KaldiRecognizer(self.model, 16000)
            parts = []
            for offset in range(0, len(pcm), 8000):
                if recognizer.AcceptWaveform(pcm[offset:offset + 8000]):
                    parts.append(json.loads(recognizer.Result()).get('text', ''))
            parts.append(json.loads(recognizer.FinalResult()).get('text', ''))
            import re
            text = ' '.join(filter(None, parts))
            text = re.sub(r'(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])', '', text)
            return {'text': text, 'engine': 'local-vosk', 'audio_saved': False}
        except Exception:
            raise HTTPException(503, '本机语音识别暂时不可用，请检查语音组件或重新录制。') from None
        finally:
            self.lock.release()


def register_routes(app, runtime: Path):
    speech = LocalSpeech(runtime)

    @app.get('/api/speech/status')
    def status():
        return {'ready': speech.ready(), 'local_only': True, 'max_seconds': 60}

    @app.post('/api/speech/transcribe')
    async def transcribe(request: Request):
        origin = request.headers.get('origin')
        if origin and origin != str(request.base_url).rstrip('/'):
            raise HTTPException(403, '录音只能由当前工作台提交。')
        chunks = bytearray()
        async for chunk in request.stream():
            if len(chunks) + len(chunk) > MAX_BYTES:
                raise HTTPException(413, '录音不能超过 60 秒。')
            chunks.extend(chunk)
        return await run_in_threadpool(speech.transcribe, bytes(chunks))
