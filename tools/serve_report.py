from __future__ import annotations

import json
import subprocess
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
SYNC_SCRIPT = PROJECT_DIR / "tools" / "sync_batch_sheets_to_long_format.py"
BUILD_SCRIPT = PROJECT_DIR / "tools" / "build_html_report.py"
HOST = "127.0.0.1"
PORT = 8765


class ReportHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PROJECT_DIR), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.end_headers()

    def do_POST(self) -> None:
        if self.path.rstrip("/") != "/rebuild-report":
            self.send_error(404, "Unknown endpoint")
            return

        sync_result = subprocess.run(
            [sys.executable, str(SYNC_SCRIPT)],
            cwd=str(PROJECT_DIR),
            capture_output=True,
            text=True,
        )

        if sync_result.returncode == 0:
            build_result = subprocess.run(
                [sys.executable, str(BUILD_SCRIPT)],
                cwd=str(PROJECT_DIR),
                capture_output=True,
                text=True,
            )
        else:
            build_result = None

        ok = sync_result.returncode == 0 and build_result is not None and build_result.returncode == 0
        payload = {
            "ok": ok,
            "stdout": sync_result.stdout + (build_result.stdout if build_result else ""),
            "stderr": sync_result.stderr + (build_result.stderr if build_result else ""),
        }
        if not ok:
            payload["error"] = payload["stderr"].strip() or payload["stdout"].strip() or "Report rebuild failed"

        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(200 if ok else 500)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), ReportHandler)
    print(f"Serving CT In-Process Manufacturing Dashboard at http://{HOST}:{PORT}/report/manufacturing_report.html")
    print("Use Ctrl+C to stop the server.")
    server.serve_forever()


if __name__ == "__main__":
    main()
