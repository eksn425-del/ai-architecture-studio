"""Nonblocking notifications for synchronous native window callbacks."""
import logging
import threading


def notify_busy_close(window):
    # FormClosing runs on the UI thread. evaluate_js waits for WebView's UI
    # callback, so calling it inline deadlocks that same message pump.
    def notify():
        try:
            window.evaluate_js("showToast('当前任务尚未结束，请先点击停止本轮，等待模型保存后再退出。', true)")
        except Exception:
            logging.getLogger(__name__).exception('Could not display busy-close notification')
    threading.Thread(target=notify, daemon=True, name='desktop-close-notification').start()
