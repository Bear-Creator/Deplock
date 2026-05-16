import threading
import time

import webview
from app.main import app
from uvicorn import Config, Server


def run_uvicorn():
    config = Config(app=app, host="127.0.0.1", port=8000, log_level="info")
    server = Server(config=config)
    server.run()


def main():
    # Start the FastAPI server in a background thread
    t = threading.Thread(target=run_uvicorn, daemon=True)
    t.start()

    # wait a bit for the server to come up
    time.sleep(0.5)

    # Open a native window pointing to the local server
    webview.create_window("Deplock", "http://127.0.0.1:8000")
    webview.start()


if __name__ == "__main__":
    main()
