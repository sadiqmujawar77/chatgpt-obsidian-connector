from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import re
import tempfile
import os
from datetime import date

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

CONVERSATION_ID_PATTERN = re.compile(
     r"^P001-(\d{3})(?:\s+-\s+.*)?$"
)


def next_conversation_id():
    CHAT_FOLDER.mkdir(parents=True, exist_ok=True)

    highest = 0

    for path in CHAT_FOLDER.glob("P001-*.md"):
        match = CONVERSATION_ID_PATTERN.match(path.stem)

        if match:
            number = int(match.group(1))
            highest = max(highest, number)

    return f"P001-{highest + 1:03d}"


def sanitize_title(title):
    title = title.strip()

    if not title:
        title = "Untitled Conversation"

    title = re.sub(r'[^A-Za-z0-9 _().,\-]+', "", title)
    title = re.sub(r"\s+", " ", title).strip()
    title = title.rstrip(".")

    if not title:
        title = "Untitled Conversation"

    return title


def build_conversation_markdown(conversation_id, title, messages):
    today = date.today().isoformat()

    lines = [
        "---",
        f"id: {conversation_id}",
        f"title: {title}",
        "type: conversation",
        "project: P001",
        f"date: {today}",
        "tags:",
        "  - project",
        "  - chatgpt",
        "  - obsidian",
        "source: ChatGPT",
        "---",
        "",
        f"# {conversation_id} — {title}",
        "",
        "## Summary",
        "",
        "Conversation captured from ChatGPT.",
        "",
        "## Key Points",
        "",
        "- To be reviewed and summarized.",
        "",
        "## Conversation",
        ""
    ]

    for message in messages:
        role = message.get("role", "unknown")
        content = message.get("content", "")

        if role == "user":
            heading = "User"
        elif role == "assistant":
            heading = "ChatGPT"
        else:
            heading = role.capitalize()

        lines.extend([
            f"### {heading}",
            "",
            content.strip(),
            ""
        ])

    lines.extend([
        "## Related",
        "",
        "- Previous",
        "- Next",
        "- Project",
        ""
    ])

    return "\n".join(lines)


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

    def read_json_body(self):
        content_length = int(
            self.headers.get("Content-Length", 0)
        )

        if content_length <= 0:
            raise ValueError("request body is required")

        if content_length > MAX_REQUEST_SIZE:
            raise OverflowError(
                "request body exceeds 5 MB limit"
            )

        raw_body = self.rfile.read(content_length)

        return json.loads(
            raw_body.decode("utf-8")
        )

    def save_file(self, filename, content):
        filename = filename.strip()

        if not filename.lower().endswith(".md"):
            filename += ".md"

        if not FILENAME_PATTERN.fullmatch(filename):
            raise ValueError("invalid filename")

        CHAT_FOLDER.mkdir(
            parents=True,
            exist_ok=True
        )

        destination = CHAT_FOLDER / filename

        if destination.exists():
            raise FileExistsError(
                "file already exists"
            )

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

        return destination

    def do_GET(self):

        if self.path == "/health":

            self.send_json(200, {
                "status": "ok",
                "service": "chatgpt-obsidian-connector"
            })

            return

        self.send_json(
            404,
            {"error": "not_found"}
        )

    def do_POST(self):

        if self.path == "/save":
            self.handle_save()
            return

        if self.path == "/conversation":
            self.handle_conversation()
            return

        self.send_json(
            404,
            {"error": "not_found"}
        )

    def handle_save(self):

        try:
            request = self.read_json_body()

            filename = request.get("filename")
            content = request.get("content")

            if not isinstance(filename, str):
                self.send_json(
                    400,
                    {"error": "filename must be a string"}
                )
                return

            if not isinstance(content, str):
                self.send_json(
                    400,
                    {"error": "content must be a string"}
                )
                return

            destination = self.save_file(
                filename,
                content
            )

            self.send_json(
                201,
                {
                    "status": "saved",
                    "path": str(destination)
                }
            )

        except json.JSONDecodeError:

            self.send_json(
                400,
                {"error": "invalid JSON"}
            )

        except OverflowError as error:

            self.send_json(
                413,
                {"error": str(error)}
            )

        except FileExistsError:

            self.send_json(
                409,
                {"error": "file already exists"}
            )

        except ValueError as error:

            self.send_json(
                400,
                {"error": str(error)}
            )

        except Exception as error:

            self.send_json(
                500,
                {"error": str(error)}
            )

    def handle_conversation(self):

        try:
            request = self.read_json_body()

            title = request.get("title")
            url = request.get("url")
            messages = request.get("messages")

            if not isinstance(title, str):
                self.send_json(
                    400,
                    {"error": "title must be a string"}
                )
                return

            if not isinstance(url, str):
                self.send_json(
                    400,
                    {"error": "url must be a string"}
                )
                return

            if not isinstance(messages, list):
                self.send_json(
                    400,
                    {"error": "messages must be an array"}
                )
                return

            if not messages:
                self.send_json(
                    400,
                    {"error": "messages cannot be empty"}
                )
                return

            for message in messages:

                if not isinstance(message, dict):
                    self.send_json(
                        400,
                        {"error": "each message must be an object"}
                    )
                    return

                if not isinstance(
                    message.get("role"),
                    str
                ):
                    self.send_json(
                        400,
                        {"error": "message role must be a string"}
                    )
                    return

                if not isinstance(
                    message.get("content"),
                    str
                ):
                    self.send_json(
                        400,
                        {"error": "message content must be a string"}
                    )
                    return

            conversation_id = next_conversation_id()
            clean_title = sanitize_title(title)

            markdown = build_conversation_markdown(
                conversation_id,
                clean_title,
                messages
            )

            filename = (
                f"{conversation_id} - "
                f"{clean_title}.md"
            )

            if len(filename) > 200:
                filename = (
                    f"{conversation_id} - "
                    f"{clean_title[:170]}.md"
                )

            destination = self.save_file(
                filename,
                markdown
            )

            self.send_json(
                201,
                {
                    "status": "saved",
                    "id": conversation_id,
                    "title": clean_title,
                    "url": url,
                    "message_count": len(messages),
                    "path": str(destination)
                }
            )

        except json.JSONDecodeError:

            self.send_json(
                400,
                {"error": "invalid JSON"}
            )

        except OverflowError as error:

            self.send_json(
                413,
                {"error": str(error)}
            )

        except FileExistsError:

            self.send_json(
                409,
                {"error": "file already exists"}
            )

        except ValueError as error:

            self.send_json(
                400,
                {"error": str(error)}
            )

        except Exception as error:

            self.send_json(
                500,
                {"error": str(error)}
            )

    def log_message(self, format, *args):
        print(
            f"[HTTP] {self.address_string()} - "
            f"{format % args}"
        )


if __name__ == "__main__":

    print("ChatGPT Obsidian Connector")
    print(f"Listening on http://{HOST}:{PORT}")
    print(
        "Health endpoint: "
        "http://127.0.0.1:8765/health"
    )
    print(
        "Save endpoint: "
        "POST http://127.0.0.1:8765/save"
    )
    print(
        "Conversation endpoint: "
        "POST http://127.0.0.1:8765/conversation"
    )
    print("Press Ctrl+C to stop.")

    server = HTTPServer(
        (HOST, PORT),
        ConnectorHandler
    )

    server.serve_forever()