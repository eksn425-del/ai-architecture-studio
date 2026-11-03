import urllib.request
import urllib.error
import pytest
from app.desktop_instance import DesktopInstance


def test_repeat_launch_activates_existing_and_clean_exit_releases(tmp_path):
    class Window:
        calls = 0
        def show(self): self.calls += 1
        def restore(self): self.calls += 1
    first = DesktopInstance(tmp_path)
    window = Window()
    assert first.acquire_or_activate()
    first.publish(window)
    try:
        second = DesktopInstance(tmp_path)
        assert not second.acquire_or_activate()
        assert window.calls == 2
        request = urllib.request.Request(f'http://127.0.0.1:{first.server.server_port}/activate', data=b'', method='POST')
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(request)
        assert error.value.code == 403
        assert window.calls == 2
    finally:
        first.close()
    assert not first.receipt.exists()
    third = DesktopInstance(tmp_path)
    assert third.acquire_or_activate()
    third.close()
