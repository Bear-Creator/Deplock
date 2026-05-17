from __future__ import annotations

import importlib.util
import socket
import sys
import threading
import time
from importlib import import_module
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import webview
from uvicorn import Config, Server

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def ensure_supported_python() -> None:
    version = sys.version_info
    if sys.platform == "win32" and version >= (3, 14):
        version_text = f"{version.major}.{version.minor}.{version.micro}"
        raise RuntimeError(
            "Deplock desktop on Windows requires Python 3.13 for pywebview. "
            f"Current version: {version_text}. Recreate the virtual environment with Python 3.13."
        )


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return int(sock.getsockname()[1])


def build_server_url(port: int) -> str:
    return f"http://127.0.0.1:{port}"


def load_app():
    try:
        return import_module("app.main").app
    except Exception as err:
        # Fallback: load by path to avoid issues when package metadata is missing
        main_path = BACKEND_DIR / "app" / "main.py"
        if not main_path.exists():
            raise FileNotFoundError(f"Module not found at {main_path}") from err

        try:
            spec = importlib.util.spec_from_file_location(
                "deplock.backend.app.main", str(main_path)
            )
            if spec is None:
                raise RuntimeError(
                    f"Failed to load module spec from {main_path}"
                ) from None
            if spec.loader is None:
                raise RuntimeError(
                    f"No loader found for module spec at {main_path}"
                ) from None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            return module.app
        except Exception as fallback_err:
            raise RuntimeError(f"Failed to load app from {main_path}") from fallback_err


def start_backend_server(port: int) -> tuple[Server, threading.Thread]:
    config = Config(
        load_app(),
        host="127.0.0.1",
        port=port,
        log_level="warning",
    )
    server = Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    return server, thread


def wait_for_server(base_url: str, timeout: float = 15.0) -> None:
    deadline = time.monotonic() + timeout
    health_url = f"{base_url}/health"

    while time.monotonic() < deadline:
        try:
            with urlopen(health_url) as response:
                if response.status == 200:
                    return
        except URLError:
            time.sleep(0.1)
            continue

    raise RuntimeError(f"Backend did not become ready: {health_url}")


def stop_backend_server(server: Server, thread: threading.Thread) -> None:
    server.should_exit = True
    thread.join(timeout=5)


def main() -> None:
    ensure_supported_python()
    port = find_free_port()
    base_url = build_server_url(port)
    server, thread = start_backend_server(port)

    try:
        wait_for_server(base_url)
        webview.create_window(
            title="Deplock",
            url=base_url,
            min_size=(1100, 720),
            width=1440,
            height=900,
        )
        webview.start()
    finally:
        stop_backend_server(server, thread)


if __name__ == "__main__":
    main()
