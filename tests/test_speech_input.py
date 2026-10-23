import io,wave
import pytest
from fastapi import FastAPI,HTTPException
from fastapi.testclient import TestClient
from app.speech_input import LocalSpeech,register_routes,MAX_BYTES

def wav(frames=160,rate=16000):
    data=io.BytesIO()
    with wave.open(data,'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(b'\0\0'*frames)
    return data.getvalue()

@pytest.mark.parametrize('audio',[b'bad',wav(rate=8000),wav(frames=960001),wav()[:-10]], ids=['invalid','sample-rate','duration','truncated'])
def test_reject_invalid_audio_before_engine(tmp_path,monkeypatch,audio):
    speech=LocalSpeech(tmp_path);monkeypatch.setattr(speech,'ready',lambda:True)
    with pytest.raises(HTTPException) as e:speech.transcribe(audio)
    assert e.value.status_code==400

def test_local_origin_and_upload_size_boundary(tmp_path,monkeypatch):
    calls=[];monkeypatch.setattr(LocalSpeech,'transcribe',lambda _,data:calls.append(data) or {'text':'测试','audio_saved':False})
    app=FastAPI();register_routes(app,tmp_path);client=TestClient(app)
    assert client.post('/api/speech/transcribe',content=wav(),headers={'origin':'https://evil.invalid'}).status_code==403
    assert client.post('/api/speech/transcribe',content=b'x'*(MAX_BYTES+1)).status_code==413
    assert not calls
    result=client.post('/api/speech/transcribe',content=wav(),headers={'origin':'http://testserver'})
    assert result.status_code==200 and result.json()['text']=='测试' and len(calls)==1

def test_missing_model_is_explicit_not_fake_transcription(tmp_path):
    speech=LocalSpeech(tmp_path)
    assert not speech.ready()
    with pytest.raises(HTTPException) as e:speech.transcribe(wav())
    assert e.value.status_code==503
