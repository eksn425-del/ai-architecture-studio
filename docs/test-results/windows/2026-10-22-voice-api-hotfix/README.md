# Voice and first-message API hotfix

The installed 8296cde first-readonly shortcut omitted user_message_id. main.py indexed this field before inference and raised KeyError, causing HTTP 500 with either B.AI or compatible providers. This was our regression. The shortcut now provides the same message ID and actual utterance fields as other receipts, preserving execution_granted=false.

Validation: 37 focused Python tests passed; two existing symbolic-link tests require missing Windows privilege (WinError1314). Full UI node suite passed. New full FastAPI conversation tests cover first image/message and idempotent retry for both B.AI and compatible routes with mocked inference. No paid/native modeling acceptance is claimed.

Voice now captures microphone PCM in the app, stops tracks, sends at most 60 seconds to the loopback transcription endpoint, and inserts recognized text without submitting. Windows Win+H and browser remote recognition removed. Local Vosk 0.3.45 plus official Chinese small model 0.22 (Apache-2.0) used. Audio is processed in memory, not saved or uploaded. Changed drafts/projects are protected from late results. A synthetic Chinese WAV actually recognized as 请把建筑改成十层保留屋顶; human microphone/accent acceptance remains pending.

Install optional requirements-speech.txt using the application's Python. Download the model from https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip and extract to an ASCII-only directory on Windows (native Vosk cannot open this host's Chinese path). runtime/speech-models/location.json may contain a local model_path; otherwise runtime/speech-models/vosk-model-small-cn-0.22 is used. Current owner install uses E:/K Studio/speech-models/vosk-model-small-cn-0.22. Public installer automation/clean-PC voice verification is not complete. Source: https://alphacephei.com/vosk/models .

Historical gateway stalls awaiting headers are separate unresolved evidence. This hotfix does not establish that every API supports images/tools, or that paid model building succeeds. No new paid inference, no SU geometry changes, no cloud deployment. Saved credentials and historical budget reservations are preserved.
