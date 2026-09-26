from __future__ import annotations

import http.client
import ipaddress
import re
import socket
import ssl
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import Message
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, urlunsplit


MAX_RESPONSE_BYTES = 1_000_000
MAX_EXCERPT_CHARS = 4_000
MAX_REDIRECTS = 3
USER_AGENT = "AIArchitectureStudio/0.2 (local reference reader)"
SKIP_TAGS = {"script", "style", "noscript", "svg", "nav", "footer", "header", "form", "button"}


@dataclass(frozen=True)
class FetchResult:
    status: int
    content_type: str
    body: bytes
    location: str = ""


class _PageText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self._title_depth = 0
        self._skip_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        style = (attributes.get("style") or "").replace(" ", "").lower()
        hidden = "hidden" in attributes or (attributes.get("aria-hidden") or "").lower() == "true" or "display:none" in style or "visibility:hidden" in style
        if tag in SKIP_TAGS or hidden:
            self._skip_stack.append(tag)
        if tag == "title":
            self._title_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self._title_depth:
            self._title_depth -= 1
        if tag in self._skip_stack:
            index = len(self._skip_stack) - 1 - self._skip_stack[::-1].index(tag)
            del self._skip_stack[index:]

    def handle_data(self, data: str) -> None:
        value = " ".join(data.split())
        if not value:
            return
        if self._title_depth:
            self.title_parts.append(value)
        elif not self._skip_stack:
            self.text_parts.append(value)


class _PinnedHTTPConnection(http.client.HTTPConnection):
    def __init__(self, host: str, port: int, address: str, timeout: float):
        super().__init__(host, port, timeout=timeout)
        self.address = address

    def connect(self) -> None:
        self.sock = socket.create_connection((self.address, self.port), self.timeout, self.source_address)


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host: str, port: int, address: str, timeout: float):
        super().__init__(host, port, timeout=timeout, context=ssl.create_default_context())
        self.address = address

    def connect(self) -> None:
        raw_socket = socket.create_connection((self.address, self.port), self.timeout, self.source_address)
        self.sock = self._context.wrap_socket(raw_socket, server_hostname=self.host)


class _UnreadableReference(ValueError):
    pass


class ReferenceIngestor:
    """Fetches one public page without proxies, private targets, or unbounded bodies."""

    def __init__(self, timeout_seconds: float = 8.0, max_bytes: int = MAX_RESPONSE_BYTES):
        self.timeout_seconds = timeout_seconds
        self.max_bytes = max_bytes

    def ingest(self, source: str) -> dict[str, str | list[str]]:
        original = source.strip()[:1200]
        base: dict[str, str | list[str]] = {
            "type": "url", "source": original, "status": "unreadable", "title": "",
            "excerpt": "", "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "error": "暂时无法安全读取此网页，请上传网页截图或参考图片。", "observed_principles": [],
        }
        try:
            final_url, result = self._fetch_public(original)
            media_type, charset = self._content_type(result.content_type)
            if media_type not in {"text/html", "application/xhtml+xml", "text/plain"}:
                raise _UnreadableReference("网页没有可读取的 HTML 或纯文本内容，请上传网页截图或参考图片。")
            encoding = charset or "utf-8"
            try:
                document = result.body.decode(encoding, errors="replace")
            except LookupError:
                document = result.body.decode("utf-8", errors="replace")
            if media_type == "text/plain":
                title, text = "", " ".join(document.split())
            else:
                parser = _PageText()
                parser.feed(document)
                title = " ".join(" ".join(parser.title_parts).split())[:300]
                text = " ".join(" ".join(parser.text_parts).split())
            if len(text) < 40:
                raise _UnreadableReference("网页可见正文太少或需要浏览器脚本才能显示，请上传网页截图或参考图片。")
            base.update({
                "source": final_url,
                "status": "readable",
                "title": title,
                "excerpt": text[:MAX_EXCERPT_CHARS],
                "error": "",
            })
        except (OSError, ValueError, http.client.HTTPException, ssl.SSLError, TimeoutError) as error:
            message = str(error).strip()
            base["error"] = message if message else "网页读取失败，请上传网页截图或参考图片。"
        return base

    def _fetch_public(self, source: str) -> tuple[str, FetchResult]:
        current = source
        for redirect_count in range(MAX_REDIRECTS + 1):
            parts, addresses, port = self._validate_and_resolve(current)
            path = urlunsplit(("", "", parts.path or "/", parts.query, ""))
            result = self._request_once(parts, port, addresses[0], path)
            if result.status in {301, 302, 303, 307, 308}:
                if not result.location or redirect_count >= MAX_REDIRECTS:
                    raise _UnreadableReference("网页跳转次数过多，请上传网页截图或参考图片。")
                current = urljoin(current, result.location)
                continue
            if result.status < 200 or result.status >= 300:
                raise _UnreadableReference(f"网页返回 HTTP {result.status}，请上传网页截图或参考图片。")
            return current, result
        raise _UnreadableReference("网页跳转次数过多，请上传网页截图或参考图片。")

    def _validate_and_resolve(self, raw_url: str):
        parts = urlsplit(raw_url)
        if parts.scheme.lower() not in {"http", "https"}:
            raise _UnreadableReference("仅支持公开 HTTP 或 HTTPS 网页，请上传网页截图或参考图片。")
        if not parts.hostname or parts.username is not None or parts.password is not None:
            raise _UnreadableReference("网址格式不安全，请检查网址或上传网页截图。")
        host = parts.hostname.rstrip(".").encode("idna").decode("ascii").lower()
        if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
            raise _UnreadableReference("不允许读取本机或局域网网址，请上传网页截图或参考图片。")
        try:
            port = parts.port or (443 if parts.scheme.lower() == "https" else 80)
        except ValueError as error:
            raise _UnreadableReference("网址端口无效，请上传网页截图或参考图片。") from error
        if port not in {80, 443}:
            raise _UnreadableReference("仅允许标准 HTTP/HTTPS 端口，请上传网页截图或参考图片。")
        try:
            literal = ipaddress.ip_address(host)
        except ValueError:
            literal = None
        if literal is not None:
            addresses = [str(literal)]
        else:
            try:
                answers = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
            except OSError as error:
                raise _UnreadableReference("无法解析该公开网址，请检查链接或上传网页截图。") from error
            addresses = list(dict.fromkeys(answer[4][0] for answer in answers))
        if not addresses:
            raise _UnreadableReference("网址没有可用的网络地址，请上传网页截图或参考图片。")
        for address in addresses:
            try:
                parsed_ip = ipaddress.ip_address(address.split("%", 1)[0])
            except ValueError as error:
                raise _UnreadableReference("网址解析到无效网络地址，请上传网页截图。") from error
            if not parsed_ip.is_global:
                raise _UnreadableReference("不允许读取本机或局域网网址，请上传网页截图或参考图片。")
        return parts, addresses, port

    def _request_once(self, parts, port: int, address: str, path: str) -> FetchResult:
        connection_type = _PinnedHTTPSConnection if parts.scheme.lower() == "https" else _PinnedHTTPConnection
        connection = connection_type(parts.hostname, port, address, self.timeout_seconds)
        try:
            connection.request("GET", path, headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9",
                "Accept-Encoding": "identity",
                "Connection": "close",
            })
            response = connection.getresponse()
            location = response.getheader("Location", "")
            if response.status in {301, 302, 303, 307, 308}:
                return FetchResult(response.status, response.getheader("Content-Type", ""), b"", location)
            length = response.getheader("Content-Length")
            if length:
                try:
                    content_length = int(length)
                except ValueError:
                    content_length = None
                if content_length is not None and content_length > self.max_bytes:
                    raise _UnreadableReference("网页超过 1 MB 读取上限，请上传网页截图或参考图片。")
            content_encoding = (response.getheader("Content-Encoding") or "identity").lower()
            if content_encoding not in {"", "identity"}:
                raise _UnreadableReference("网页使用了暂不支持的压缩格式，请上传网页截图或参考图片。")
            chunks: list[bytes] = []
            total = 0
            deadline = time.monotonic() + self.timeout_seconds
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("读取网页超时，请上传网页截图或参考图片。")
                if connection.sock is not None:
                    connection.sock.settimeout(min(self.timeout_seconds, remaining))
                chunk = response.read(min(64 * 1024, self.max_bytes - total + 1))
                if not chunk:
                    break
                total += len(chunk)
                if total > self.max_bytes:
                    raise _UnreadableReference("网页超过 1 MB 读取上限，请上传网页截图或参考图片。")
                chunks.append(chunk)
            return FetchResult(response.status, response.getheader("Content-Type", ""), b"".join(chunks))
        finally:
            connection.close()

    @staticmethod
    def _content_type(value: str) -> tuple[str, str | None]:
        header = Message()
        header["content-type"] = value or "application/octet-stream"
        return header.get_content_type().lower(), header.get_content_charset()
