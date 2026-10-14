from types import SimpleNamespace
import pytest
from windows_mcp.desktop import service
from windows_mcp.desktop.service import Desktop


def bind(monkeypatch, process='SketchUp.exe', foreground=42, window_class='#32770'):
    monkeypatch.setattr(service.win32gui, 'WindowFromPoint', lambda point: 10)
    monkeypatch.setattr(service.win32gui, 'GetAncestor', lambda hwnd, flag: 42)
    monkeypatch.setattr(service.win32gui, 'GetClassName', lambda hwnd: window_class)
    monkeypatch.setattr(service.win32gui, 'GetForegroundWindow', lambda: foreground)
    monkeypatch.setattr(service.win32process, 'GetWindowThreadProcessId', lambda hwnd: (1, 2))
    monkeypatch.setattr(service, 'Process', lambda pid: SimpleNamespace(name=lambda: process))


def test_codex_chat_path_rejected_before_any_input(monkeypatch):
    bind(monkeypatch, process='Codex.exe', window_class='Chrome_WidgetWin_1')
    instance=Desktop.__new__(Desktop)
    monkeypatch.setattr(instance, '_validate_screen_point', lambda x,y: None)
    monkeypatch.setattr(service.uia, 'Click', lambda *a: pytest.fail('No click allowed'))
    with pytest.raises(ValueError, match='Codex/ChatGPT chat'):
        instance.type((100,100), 'E:/private/model.skp', press_enter=True)


def test_native_file_dialog_stable_target(monkeypatch):
    bind(monkeypatch)
    root=Desktop._path_input_window((100,100), 'E:/private/model.skp')
    assert root==42
    Desktop._assert_path_input_window(root)


def test_foreground_switch_after_click_prevents_text_and_enter(monkeypatch):
    bind(monkeypatch, foreground=99)
    instance=Desktop.__new__(Desktop)
    monkeypatch.setattr(instance, '_validate_screen_point', lambda x,y: None)
    monkeypatch.setattr(service.uia, 'Click', lambda *a: None)
    monkeypatch.setattr(service.uia, 'SendKeys', lambda *a,**k: pytest.fail('No keys allowed'))
    with pytest.raises(ValueError, match='foreground window changed'):
        instance.type((100,100), 'E:/private/model.skp', clear=True, press_enter=True)


def test_intentional_codex_path_requires_explicit_opt_in(monkeypatch):
    bind(monkeypatch, process='Codex.exe', window_class='Chrome_WidgetWin_1')
    assert Desktop._path_input_window((100,100), 'E:/private/model.skp', True)==42
    assert Desktop._path_input_window((100,100), '普通文字') is None
