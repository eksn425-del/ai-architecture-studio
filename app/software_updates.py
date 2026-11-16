"""Read-only public release discovery; never downloads or executes an update."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPOSITORY = "https://github.com/eksn425-del/ai-architecture-studio"
RELEASE_API = "https://api.github.com/repos/eksn425-del/ai-architecture-studio/releases/latest"


def check_release(root: Path) -> dict:
    current = "development"
    try:
        current = json.loads((root / "release-source.json").read_text(encoding="utf-8-sig"))["commit"]
    except (OSError, ValueError, KeyError, TypeError):
        pass
    result = {"current_commit": current, "automatic_install": False,
              "release_url": REPOSITORY + "/releases", "skills_auto_update": False}
    try:
        request = Request(RELEASE_API, headers={"Accept": "application/vnd.github+json", "User-Agent": "K-Studio-release-check"})
        with urlopen(request, timeout=5) as response:
            raw = response.read(262145)
        if len(raw) > 262144:
            raise ValueError("Oversize release response")
        release = json.loads(raw)
        tag = release.get("tag_name")
        if (release.get("draft") is not False or release.get("prerelease") is not False
                or not isinstance(tag, str) or not tag.strip() or len(tag) > 120):
            raise ValueError("No stable release")
        return {**result, "status": "release_available", "latest_tag": tag,
                "message": "发现正式发布记录。请查看版本说明；当前不会自动下载、替换连接器或更新技能。"}
    except HTTPError as error:
        if error.code == 404:
            return {**result, "status": "no_release", "message": "仓库尚无正式发布版；本机试用版可继续使用。"}
    except (OSError, ValueError, TypeError, AttributeError, URLError):
        pass
    return {**result, "status": "check_failed", "message": "暂时无法检查更新。当前版本和项目保持不变，可稍后重试。"}


def register_routes(app) -> None:
    @app.get("/api/software-update")
    def status():
        return check_release(Path(__file__).resolve().parents[1])
