#!/usr/bin/env python3
"""Enter/exit YouTube HTML Picture-in-Picture.

Prefers Chromium DevTools with userGesture=true so PiP can be requested
after every workspace switch, not only after a fresh play click.
Falls back to the extension native-messaging socket.
"""

from __future__ import annotations

import base64
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

SOCK_NAME = "webtom-auto-pip.sock"
CDP_PORT = int(os.environ.get("WEBTM_AUTOPIP_CDP_PORT", "19222"))
CDP_HOST = "127.0.0.1"

ENTER_JS = r"""
(async () => {
  const video = document.querySelector("video.html5-main-video") || document.querySelector("video");
  if (!video) return { ok: false, error: "no-video" };
  if (document.pictureInPictureElement && document.pictureInPictureElement !== video) {
    try { await document.exitPictureInPicture(); } catch (e) {}
  }
  if (document.pictureInPictureElement === video) return { ok: true, already: true };
  if (video.paused) {
    try { await video.play(); } catch (e) {}
  }
  await video.requestPictureInPicture();
  return { ok: true };
})()
"""

EXIT_JS = r"""
(async () => {
  if (!document.pictureInPictureElement) return { ok: true, already: true };
  await document.exitPictureInPicture();
  return { ok: true };
})()
"""


def recvall(sock: socket.socket, length: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < length:
        piece = sock.recv(length - len(chunks))
        if not piece:
            raise ConnectionError("cdp socket closed")
        chunks.extend(piece)
    return bytes(chunks)


def ws_connect(url: str, timeout: float = 2.0) -> socket.socket:
    parsed = urlparse(url)
    host = parsed.hostname or CDP_HOST
    port = parsed.port or 80
    sock = socket.create_connection((host, port), timeout=timeout)
    key_b64 = base64.b64encode(os.urandom(16)).decode("ascii")
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key_b64}\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        "\r\n"
    )
    sock.sendall(request.encode("ascii"))
    header = b""
    while b"\r\n\r\n" not in header:
        piece = sock.recv(4096)
        if not piece:
            raise ConnectionError("cdp websocket handshake failed")
        header += piece
    status_line = header.split(b"\r\n", 1)[0].decode("ascii", "replace")
    if "101" not in status_line:
        raise ConnectionError(f"cdp handshake: {status_line}")
    leftover = header.split(b"\r\n\r\n", 1)[1]
    if leftover:
        sock.settimeout(timeout)
    return sock


def ws_send_text(sock: socket.socket, text: str) -> None:
    payload = text.encode("utf-8")
    header = bytearray()
    header.append(0x81)
    length = len(payload)
    mask_bit = 0x80
    if length < 126:
        header.append(mask_bit | length)
    elif length < 65536:
        header.append(mask_bit | 126)
        header.extend(length.to_bytes(2, "big"))
    else:
        header.append(mask_bit | 127)
        header.extend(length.to_bytes(8, "big"))
    mask = os.urandom(4)
    header.extend(mask)
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    sock.sendall(header + masked)


def ws_recv_text(sock: socket.socket) -> str:
    while True:
        hdr = recvall(sock, 2)
        opcode = hdr[0] & 0x0F
        masked = bool(hdr[1] & 0x80)
        length = hdr[1] & 0x7F
        if length == 126:
            length = int.from_bytes(recvall(sock, 2), "big")
        elif length == 127:
            length = int.from_bytes(recvall(sock, 8), "big")
        mask = recvall(sock, 4) if masked else b""
        data = recvall(sock, length)
        if masked:
            data = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
        if opcode == 0x9:
            # ping -> pong
            pong = bytearray([0x8A, 0x80 | len(data)])
            pong_mask = os.urandom(4)
            pong.extend(pong_mask)
            pong.extend(bytes(b ^ pong_mask[i % 4] for i, b in enumerate(data)))
            sock.sendall(pong)
            continue
        if opcode == 0x8:
            raise ConnectionError("cdp websocket closed")
        if opcode in (0x1, 0x2, 0x0):
            return data.decode("utf-8")


def cdp_targets() -> list[dict]:
    headers = {
        "Host": f"{CDP_HOST}:{CDP_PORT}",
        "Origin": f"http://{CDP_HOST}:{CDP_PORT}",
    }
    for path in ("/json/list", "/json"):
        request = urllib.request.Request(
            f"http://{CDP_HOST}:{CDP_PORT}{path}",
            headers=headers,
        )
        try:
            with urllib.request.urlopen(request, timeout=1.2) as response:
                payload = json.load(response)
            if isinstance(payload, list):
                return payload
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            continue
    return []


def youtube_targets(targets: list[dict]) -> list[dict]:
    pages = []
    for target in targets:
        kind = str(target.get("type") or "")
        page_url = str(target.get("url") or "")
        if kind not in ("page", "app"):
            continue
        if "youtube.com" not in page_url:
            continue
        if target.get("webSocketDebuggerUrl"):
            pages.append(target)
    return pages


def cdp_evaluate(ws_url: str, expression: str) -> dict:
    sock = ws_connect(ws_url)
    try:
        msg_id = 1
        ws_send_text(
            sock,
            json.dumps(
                {
                    "id": msg_id,
                    "method": "Runtime.evaluate",
                    "params": {
                        "expression": expression,
                        "awaitPromise": True,
                        "returnByValue": True,
                        "userGesture": True,
                    },
                }
            ),
        )
        deadline = time.time() + 2.5
        while time.time() < deadline:
            payload = json.loads(ws_recv_text(sock))
            if payload.get("id") != msg_id:
                continue
            if payload.get("error"):
                return {"ok": False, "error": payload["error"]}
            result = (payload.get("result") or {}).get("result") or {}
            value = result.get("value")
            if isinstance(value, dict):
                return value
            if result.get("subtype") == "error":
                return {"ok": False, "error": result.get("description") or "js-error"}
            return {"ok": True, "value": value}
        return {"ok": False, "error": "cdp-timeout"}
    finally:
        try:
            sock.close()
        except OSError:
            pass


def via_cdp(cmd: str) -> bool:
    expression = ENTER_JS if cmd == "enter" else EXIT_JS
    try:
        targets = youtube_targets(cdp_targets())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return False
    if not targets:
        return False
    ok = False
    for target in targets:
        try:
            result = cdp_evaluate(target["webSocketDebuggerUrl"], expression)
        except (OSError, ConnectionError, json.JSONDecodeError, TimeoutError):
            continue
        if result.get("ok"):
            ok = True
    return ok


def via_socket(cmd: str) -> bool:
    path = os.path.join(os.environ.get("XDG_RUNTIME_DIR") or "/tmp", SOCK_NAME)
    deadline = time.time() + 0.8
    while time.time() < deadline:
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(0.4)
            sock.connect(path)
            sock.sendall((cmd + "\n").encode("utf-8"))
            sock.close()
            return True
        except OSError:
            time.sleep(0.1)
    return False


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "enter"
    if cmd not in ("enter", "exit"):
        print("usage: pip-cmd.py enter|exit", file=sys.stderr)
        return 2
    cdp_ok = via_cdp(cmd)
    sock_ok = via_socket(cmd)
    if cdp_ok or sock_ok:
        return 0
    print("auto-pip: could not reach Chromium PiP (cdp and extension socket failed)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
