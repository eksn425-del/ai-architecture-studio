"""Windows prerequisites, no silent runtime download or global environment edit."""
import os

WEBVIEW_DOWNLOAD = 'https://developer.microsoft.com/microsoft-edge/webview2/#download-section'


def inspect_prerequisites():
    if os.name != 'nt':
        return {'supported': False, 'missing': ['Windows 10/11 x64'], 'webview2': None}
    import winreg
    versions = []
    product = '{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}'
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for prefix in ('SOFTWARE', r'SOFTWARE\WOW6432Node'):
            try:
                with winreg.OpenKey(hive, rf'{prefix}\Microsoft\EdgeUpdate\Clients\{product}') as key:
                    value = str(winreg.QueryValueEx(key, 'pv')[0])
                    if value and value != '0.0.0.0':
                        versions.append(value)
            except OSError:
                pass
    net = 0
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full') as key:
            net = int(winreg.QueryValueEx(key, 'Release')[0])
    except OSError:
        pass
    missing = ([] if versions else ['Microsoft Edge WebView2 Evergreen Runtime'])
    if net < 394802:
        missing.append('Microsoft .NET Framework 4.6.2 或更新版本')
    return {'supported': not missing, 'missing': missing, 'webview2': versions[0] if versions else None,
            'net_release': net, 'download_url': WEBVIEW_DOWNLOAD}


def require_desktop_prerequisites():
    result = inspect_prerequisites()
    if not result['supported']:
        message = 'K Studio 需要以下 Windows 组件：\n' + '\n'.join(result['missing'])
        message += '\n\n请从微软官方安装页面补齐后再打开，项目和 API 配置会保留。\n' + WEBVIEW_DOWNLOAD
        if os.name == 'nt':
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, message, 'K Studio 安装检查', 0x10)
        raise RuntimeError(message)
    return result
