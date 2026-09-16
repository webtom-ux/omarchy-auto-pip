#!/usr/bin/env python3
"""Native messaging host: bridge Unix-socket commands to the Auto PiP extension."""

import json
import os
import select
import socket
import struct
import sys
import threading

SOCK_NAME = "webtom-auto-pip.sock"


def log(message):
    sys.stderr.write(message + "\n")
    sys.stderr.flush()


def send_native(message):
    data = json.dumps(message).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("=I", len(data)))
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()


def read_native():
    header = sys.stdin.buffer.read(4)
    if not header:
        return None
    (length,) = struct.unpack("=I", header)
    if length <= 0:
        return None
    payload = sys.stdin.buffer.read(length)
    if not payload:
        return None
    try:
        return json.loads(payload.decode("utf-8"))
    except json.JSONDecodeError:
        return None


def socket_path():
    runtime = os.environ.get("XDG_RUNTIME_DIR") or "/tmp"
    return os.path.join(runtime, SOCK_NAME)


def handle_command(raw):
    cmd = (raw or "").strip().lower()
    if cmd in ("enter", "exit"):
        send_native({"cmd": cmd})


def serve_socket(path, stop_event):
    if os.path.exists(path):
        probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            probe.connect(path)
            probe.close()
            log("auto-pip socket already live")
            return
        except OSError:
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        server.bind(path)
    except OSError as error:
        log("auto-pip socket bind failed: " + str(error))
        return
    server.listen(4)
    server.setblocking(False)
    os.chmod(path, 0o600)

    clients = []
    try:
        while not stop_event.is_set():
            readers = [server] + clients
            try:
                ready, _, _ = select.select(readers, [], [], 0.25)
            except (InterruptedError, ValueError):
                continue
            for sock in ready:
                if sock is server:
                    conn, _ = server.accept()
                    conn.setblocking(False)
                    clients.append(conn)
                    continue
                try:
                    data = sock.recv(1024)
                except BlockingIOError:
                    continue
                if not data:
                    clients.remove(sock)
                    sock.close()
                    continue
                for line in data.decode("utf-8", "replace").splitlines():
                    handle_command(line)
    finally:
        for conn in clients:
            conn.close()
        server.close()
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass


def main():
    stop_event = threading.Event()
    thread = threading.Thread(
        target=serve_socket, args=(socket_path(), stop_event), daemon=True
    )
    thread.start()
    try:
        while True:
            message = read_native()
            if message is None:
                break
    finally:
        stop_event.set()


if __name__ == "__main__":
    main()
