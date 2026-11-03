import threading
from app.desktop_lifecycle import notify_busy_close


def test_busy_close_returns_without_waiting_for_ui_script():
    entered = threading.Event()
    release = threading.Event()
    completed = threading.Event()
    caller_thread = threading.get_ident()
    class Window:
        def evaluate_js(self, script):
            assert threading.get_ident() != caller_thread
            entered.set()
            release.wait(3)
            completed.set()
    try:
        notify_busy_close(Window())
        assert entered.wait(1)
        assert not completed.is_set()
    finally:
        release.set()
    assert completed.wait(1)
