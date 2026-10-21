// User-initiated dictation only. Never sends a message or starts modeling.
(() => {
  const button = document.getElementById('conversation-voice');
  const input = document.getElementById('conversation-input');
  if (!button || !input) return;
  let recognition = null;
  button.addEventListener('click', async () => {
    input.focus();
    if (recognition) { recognition.stop(); return; }
    if (window.pywebview?.api?.start_dictation) {
      if (await window.pywebview.api.start_dictation()) return;
    }
    const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Speech) {
      showToast('此窗口不支持浏览器语音识别。光标已移到输入框；Windows 请按 Win + H 使用系统语音输入，完成后手动发送。', false);
      return;
    }
    if (!window.confirm('使用浏览器语音识别？浏览器可能将音频发送到其语音服务。识别文字只填入输入框，由你确认后发送。')) return;
    const before = input.value, projectId = state.projectId;
    const current = new Speech(); recognition = current;
    current.lang = 'zh-CN'; current.continuous = false; current.interimResults = false;
    button.textContent = '停止'; button.setAttribute('aria-pressed', 'true');
    current.onresult = event => {
      if (state.projectId !== projectId || input.value !== before) {
        showToast('输入内容或项目已改变，本次识别未覆盖你的文字。', false); return;
      }
      const words = Array.from(event.results).filter(item => item.isFinal).map(item => item[0].transcript).join('');
      input.value = before + (before && words ? ' ' : '') + words;
      input.dispatchEvent(new Event('input', {bubbles:true}));
    };
    current.onerror = () => showToast('语音识别未完成，请检查麦克风权限和网络；也可在输入框按 Win + H。', true);
    current.onend = () => { recognition = null; button.textContent = '🎙'; button.setAttribute('aria-pressed', 'false'); };
    try { current.start(); } catch (_) { current.onend(); current.onerror(); }
  });
})();
