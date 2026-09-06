from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import re
import tempfile
import os

HOST = "127.0.0.1"
PORT = 8765

VAULT = Path(r"C:\Users\Sadiq\iCloudDrive\iCloud~md~obsidian")

CHAT_FOLDER = (
    VAULT
    / "00 - ChatGPT"
    / "Projects"
    / "P001 - ChatGPT Obsidian Connector"
    / "Chats"
)

MAX_REQUEST_SIZE = 5 * 1024 * 1024  # 5 MB

FILENAME_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9 _().,\-]{0,199}\.md$",
    re.IGNORECASE
)


class ConnectorHandler(BaseHTTPRequestHandler):

    def send_json(self, status_code, data):
        body = json.dumps(data).encode("utf-8")

        self.send_response(status_code)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )
        self.send_header(
            "Content-Length",
            str(len(body))
        )
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):

        if self.path == "/health":

            self.send_json(200, {
                "status": "ok",
                "service": "chatgpt-obsidian-connector"
            })

        else:

            self.send_json(404, {
                "error": "not_found"
            })

    def do_POST(self):

        if self.path != "/save":

            self.send_json(404, {
                "error": "not_found"
            })

            return

        try:

            content_length = int(
                self.headers.get("Content-Length", 0)
            )

            if content_length <= 0:

                self.send_json(400, {
                    "error": "request body is required"
                })

                return

            if content_length > MAX_REQUEST_SIZE:

                self.send_json(413, {
                    "error": "request body exceeds 5 MB limit"
                })

                return

            raw_body = self.rfile.read(content_length)

            request = json.loads(
                raw_body.decode("utf-8")
            )

            filename = request.get("filename")
            content = request.get("content")

            if not isinstance(filename, str):

                self.send_json(400, {
                    "error": "filename must be a string"
                })

                return

            if not isinstance(content, str):

                self.send_json(400, {
                    "error": "content must be a string"
                })

                return

            filename = filename.strip()

            if not filename.lower().endswith(".md"):

                filename += ".md"

            if not FILENAME_PATTERN.fullmatch(filename):

                self.send_json(400, {
                    "error": "invalid filename"
                })

                return

            CHAT_FOLDER.mkdir(
                parents=True,
                exist_ok=True
            )

            destination = CHAT_FOLDER / filename

            # Never overwrite an existing note.
            if destination.exists():

                self.send_json(409, {
                    "error": "file already exists",
                    "path": str(destination)
                })

                return

            # Write to a temporary file in the same directory.
            # This allows an atomic rename into the final location.
            fd, temp_name = tempfile.mkstemp(
                prefix=".chatgpt-",
                suffix=".tmp",
                dir=str(CHAT_FOLDER)
            )

            try:

                with os.fdopen(
                    fd,
                    "w",
                    encoding="utf-8",
                    newline=""
                ) as temp_file:

                    temp_file.write(content)
                    temp_file.flush()
                    os.fsync(temp_file.fileno())

                os.replace(
                    temp_name,
                    destination
                )

            except Exception:

                try:
                    os.unlink(temp_name)
                except OSError:
                    pass

                raise

            self.send_json(201, {
                "status": "saved",
                "path": str(destination)
            })

        except json.JSONDecodeError:

            self.send_json(400, {
                "error": "invalid JSON"
            })

        except Exception as error:

            self.send_json(500, {
                "error": str(error)
            })

    def log_message(self, format, *args):

        print(
            f"[HTTP] {self.address_string()} - "
            f"{format % args}"
        )


if __name__ == "__main__":

    print("ChatGPT Obsidian Connector")
    print(f"Listening on http://{HOST}:{PORT}")
    print("Health endpoint: http://127.0.0.1:8765/health")
    print("Save endpoint: POST http://127.0.0.1:8765/save")
    print("Press Ctrl+C to stop.")

    server = HTTPServer(
        (HOST, PORT),
        ConnectorHandler
    )

    server.serve_forever()
