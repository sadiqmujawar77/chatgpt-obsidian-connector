from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import re
import tempfile
import os
from datetime import date


HOST = "127.0.0.1"
PORT = 8765


VAULT = Path(
    r"C:\Users\Sadiq\iCloudDrive\iCloud~md~obsidian"
)


PROJECTS_FOLDER = (
    VAULT
    / "00 - ChatGPT"
    / "Projects"
)


DEFAULT_PROJECT = "P001"


MAX_REQUEST_SIZE = 5 * 1024 * 1024  # 5 MB


FILENAME_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9 _().,\-]{0,199}\.md$",
    re.IGNORECASE
)


PROJECT_ID_PATTERN = re.compile(
    r"^P\d{3,}$",
    re.IGNORECASE
)


CONVERSATION_ID_PATTERN = re.compile(
    r"^P(\d{3,})-(\d{3})(?:\s+-\s+.*)?$",
    re.IGNORECASE
)


def project_folder(project_id):
    """
    Resolve a project ID to its project folder.

    Project folders use the naming convention:

        P001 - Project Name
        P002 - Another Project

    The project ID must match the beginning of the folder name.
    """

    if not isinstance(project_id, str):
        raise ValueError("project must be a string")

    project_id = project_id.strip().upper()

    if not PROJECT_ID_PATTERN.fullmatch(project_id):
        raise ValueError("invalid project id")

    PROJECTS_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    matches = []

    for path in PROJECTS_FOLDER.iterdir():

        if not path.is_dir():
            continue

        if re.match(
            rf"^{re.escape(project_id)}(?:\s+-\s+.*)?$",
            path.name,
            re.IGNORECASE
        ):
            matches.append(path)

    if not matches:
        raise ValueError(
            f"project not found: {project_id}"
        )

    if len(matches) > 1:
        raise ValueError(
            f"multiple folders found for project: {project_id}"
        )

    return matches[0]


def chats_folder(project_id):
    """
    Return the Chats folder for a project.
    """

    folder = project_folder(project_id) / "Chats"

    folder.mkdir(
        parents=True,
        exist_ok=True
    )

    return folder


def next_conversation_id(project_id):
    """
    Generate the next conversation ID for a project.

    Numbering is independent for each project.
    """

    chat_folder = chats_folder(project_id)

    highest = 0

    for path in chat_folder.glob(
        f"{project_id}-*.md"
    ):

        match = CONVERSATION_ID_PATTERN.match(
            path.stem
        )

        if not match:
            continue

        matched_project_number = int(
            match.group(1)
        )

        matched_conversation_number = int(
            match.group(2)
        )

        project_number = int(
            project_id[1:]
        )

        if matched_project_number != project_number:
            continue

        highest = max(
            highest,
            matched_conversation_number
        )

    return f"{project_id}-{highest + 1:03d}"


def previous_conversation(project_id):
    """
    Return the most recently numbered conversation for a project.

    Returns:
        Path to the previous conversation file, or None if this
        is the first conversation in the project.
    """

    chat_folder = chats_folder(project_id)

    highest_number = 0
    previous_path = None

    for path in chat_folder.glob(
        f"{project_id}-*.md"
    ):

        match = CONVERSATION_ID_PATTERN.match(
            path.stem
        )

        if not match:
            continue

        matched_project_number = int(
            match.group(1)
        )

        matched_conversation_number = int(
            match.group(2)
        )

        project_number = int(
            project_id[1:]
        )

        if matched_project_number != project_number:
            continue

        if matched_conversation_number > highest_number:

            highest_number = (
                matched_conversation_number
            )

            previous_path = path

    return previous_path

def update_next_link(
    conversation_path,
    next_link
):
    """
    Update the Next link in an existing conversation.

    Only the generated Related section at the end of the document
    is modified.
    """

    content = conversation_path.read_text(
        encoding="utf-8"
    )

    print(
        f"Updating Next link: {conversation_path.name}"
    )

    related_marker = "\n## Related\n"

    if related_marker not in content:

        raise ValueError(
            "conversation is missing Related section"
        )

    before_related, related_section = (
        content.rsplit(
            related_marker,
            1
        )
    )

    lines = related_section.splitlines()

    next_line_found = False

    for index, line in enumerate(lines):

        if line.startswith("- Next:"):

            lines[index] = (
                f"- Next: [[{next_link}]]"
            )

            next_line_found = True

            break

    if not next_line_found:

        lines.insert(
            0,
            f"- Next: [[{next_link}]]"
        )

    updated_content = (
        before_related
        + related_marker
        + "\n".join(lines)
        + "\n"
    )

    print(
        f"Next link target: {next_link}"
    )

    conversation_path.write_text(
        updated_content,
        encoding="utf-8"
    )

def update_project_index(project_id):
    project_path = project_folder(project_id)

    index_path = (
        project_path
        / f"{project_id} - Project Index.md"
    )

    chat_folder = chats_folder(project_id)
    conversations = []

    for chat_path in chat_folder.glob(
        f"{project_id}-*.md"
    ):
        match = CONVERSATION_ID_PATTERN.fullmatch(
            chat_path.stem
        )

        if not match:
            continue

        conversation_number = int(match.group(2))
        conversation_id = f"{project_id}-{conversation_number:03d}"
        title = chat_path.stem[len(conversation_id) + 3:]

        conversations.append(
            (
                conversation_number,
                conversation_id,
                title,
                chat_path.stem
            )
        )

    conversations.sort(key=lambda item: item[0])

    table_lines = [
        "| ID | Title | Status |",
        "|---|---|---|"
    ]

    for _, conversation_id, title, stem in conversations:
        table_lines.append(
            f"| [[{stem}]] | {title} | Captured |"
        )

    if index_path.exists():
        existing = index_path.read_text(encoding="utf-8")
        conversations_marker = "## Conversations"

        if conversations_marker in existing:
            before, remainder = existing.split(
                conversations_marker,
                1
            )

            next_section = re.search(
                r"\n## (?!#)",
                remainder
            )

            if next_section:
                after = remainder[next_section.start():]
                updated = (
                    before
                    + conversations_marker
                    + "\n\n"
                    + "\n".join(table_lines)
                    + "\n"
                    + after
                )
            else:
                updated = (
                    before
                    + conversations_marker
                    + "\n\n"
                    + "\n".join(table_lines)
                    + "\n"
                )
        else:
            updated = (
                existing.rstrip()
                + "\n\n## Conversations\n\n"
                + "\n".join(table_lines)
                + "\n"
            )
    else:
        project_name = (
            project_path.name.split(" - ", 1)[1]
            if " - " in project_path.name
            else project_path.name
        )

        today = date.today().isoformat()

        updated = "\n".join([
            "---",
            f"id: {project_id}",
            f"title: {project_name}",
            "type: project",
            "status: active",
            f"date: {today}",
            "tags:",
            "  - project",
            "  - chatgpt",
            "  - obsidian",
            "---",
            "",
            f"# {project_id} — {project_name}",
            "",
            "## Conversations",
            "",
            *table_lines,
            ""
        ])

    index_path.write_text(updated, encoding="utf-8")

    print(f"Project index updated: {index_path}")
    print(f"Conversation entries: {len(conversations)}")

def sanitize_title(title):
    title = title.strip()

    if not title:
        title = "Untitled Conversation"

    title = re.sub(
        r'[^A-Za-z0-9 _().,\-]+',
        "",
        title
    )

    title = re.sub(
        r"\s+",
        " ",
        title
    ).strip()

    title = title.rstrip(".")

    if not title:
        title = "Untitled Conversation"

    return title


def build_conversation_markdown(
    conversation_id,
    title,
    project_id,
    url,
    messages,
    previous_link=None,
    next_link=None,
    project_link=None
):

    today = date.today().isoformat()

    lines = [
        "---",
        f"id: {conversation_id}",
        f"title: {title}",
        "type: conversation",
        f"project: {project_id}",
        f"date: {today}",
        "tags:",
        "  - project",
        "  - chatgpt",
        "  - obsidian",
        "source: ChatGPT",
        f"url: {url}",
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

        role = message.get(
            "role",
            "unknown"
        )

        content = message.get(
            "content",
            ""
        )

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
        ""
    ])

    if previous_link:
        lines.append(
            f"- Previous: [[{previous_link}]]"
        )

    if next_link:
        lines.append(
            f"- Next: [[{next_link}]]"
        )

    if project_link:
        lines.append(
            f"- Project: [[{project_link}]]"
        )

    lines.append("")

    return "\n".join(lines)


class ConnectorHandler(BaseHTTPRequestHandler):

    def send_json(
        self,
        status_code,
        data
    ):

        body = json.dumps(
            data
        ).encode("utf-8")

        self.send_response(
            status_code
        )

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
            self.headers.get(
                "Content-Length",
                0
            )
        )

        if content_length <= 0:
            raise ValueError(
                "request body is required"
            )

        if content_length > MAX_REQUEST_SIZE:
            raise OverflowError(
                "request body exceeds 5 MB limit"
            )

        raw_body = self.rfile.read(
            content_length
        )

        return json.loads(
            raw_body.decode("utf-8")
        )


    def save_file(
        self,
        folder,
        filename,
        content
    ):

        filename = filename.strip()

        if not filename.lower().endswith(".md"):
            filename += ".md"

        if not FILENAME_PATTERN.fullmatch(
            filename
        ):
            raise ValueError(
                "invalid filename"
            )

        folder.mkdir(
            parents=True,
            exist_ok=True
        )

        destination = folder / filename

        if destination.exists():
            raise FileExistsError(
                "file already exists"
            )

        fd, temp_name = tempfile.mkstemp(
            prefix=".chatgpt-",
            suffix=".tmp",
            dir=str(folder)
        )

        try:

            with os.fdopen(
                fd,
                "w",
                encoding="utf-8",
                newline=""
            ) as temp_file:

                temp_file.write(
                    content
                )

                temp_file.flush()

                os.fsync(
                    temp_file.fileno()
                )

            os.replace(
                temp_name,
                destination
            )

        except Exception:

            try:
                os.unlink(
                    temp_name
                )

            except OSError:
                pass

            raise

        return destination


    def do_GET(self):

        if self.path == "/health":

            self.send_json(
                200,
                {
                    "status": "ok",
                    "service":
                        "chatgpt-obsidian-connector"
                }
            )

            return


        if self.path == "/projects":

            self.handle_projects()

            return


        self.send_json(
            404,
            {
                "error": "not_found"
            }
        )


    def do_POST(self):

        if self.path == "/save":

            self.handle_save()

            return


        if self.path == "/projects":

            self.handle_create_project()

            return


        if self.path == "/conversation":

            self.handle_conversation()

            return


        self.send_json(
            404,
            {
                "error": "not_found"
            }
        )


    def handle_projects(self):

        try:

            PROJECTS_FOLDER.mkdir(
                parents=True,
                exist_ok=True
            )

            projects = []

            for path in sorted(
                PROJECTS_FOLDER.iterdir(),
                key=lambda p: p.name.lower()
            ):

                if not path.is_dir():
                    continue

                match = re.match(
                    r"^(P\d{3,})(?:\s+-\s+(.*))?$",
                    path.name,
                    re.IGNORECASE
                )

                if not match:
                    continue

                project_id = match.group(1).upper()

                project_name = (
                    match.group(2)
                    or ""
                ).strip()

                projects.append(
                    {
                        "id": project_id,
                        "name": project_name,
                        "folder": path.name
                    }
                )

            self.send_json(
                200,
                {
                    "projects": projects
                }
            )

        except Exception as error:

            self.send_json(
                500,
                {
                    "error": str(error)
                }
            )


    def handle_create_project(self):
        try:
            data = self.read_json_body()

            name = data.get("name")

            if not isinstance(name, str):
                self.send_json(
                    400,
                    {"error": "project name must be a string"}
                )
                return

            name = name.strip()

            if not name:
                self.send_json(
                    400,
                    {"error": "project name is required"}
                )
                return

            if len(name) > 100:
                self.send_json(
                    400,
                    {"error": "project name is too long"}
                )
                return

            if any(
                character in name
                for character in '<>:"/\\|?*'
            ):
                self.send_json(
                    400,
                    {
                        "error":
                        "project name contains invalid Windows filename characters"
                    }
                )
                return

            if name.endswith(".") or name.endswith(" "):
                self.send_json(
                    400,
                    {
                        "error":
                        "project name cannot end with a space or period"
                    }
                )
                return

            reserved_names = {
                "CON",
                "PRN",
                "AUX",
                "NUL",
                *(f"COM{i}" for i in range(1, 10)),
                *(f"LPT{i}" for i in range(1, 10)),
            }

            if name.upper() in reserved_names:
                self.send_json(
                    400,
                    {
                        "error":
                        "project name is a reserved Windows filename"
                    }
                )
                return

            PROJECTS_FOLDER.mkdir(
                parents=True,
                exist_ok=True
            )

            numbers = []

            for path in PROJECTS_FOLDER.iterdir():
                if not path.is_dir():
                    continue

                match = re.match(
                    r"^P(\d{3,})\s+-\s+",
                    path.name
                )

                if match:
                    numbers.append(
                        int(match.group(1))
                    )

            next_number = max(
                numbers,
                default=0
            ) + 1

            project_id = f"P{next_number:03d}"

            project_folder_name = (
                f"{project_id} - {name}"
            )

            project_path = (
                PROJECTS_FOLDER /
                project_folder_name
            )

            chats_path = (
                project_path /
                "Chats"
            )

            try:
                project_path.mkdir(
                    parents=False,
                    exist_ok=False
                )

                chats_path.mkdir(
                    parents=False,
                    exist_ok=False
                )

            except Exception:
                if project_path.exists():
                    try:
                        chats_path.rmdir()
                    except Exception:
                        pass

                    try:
                        project_path.rmdir()
                    except Exception:
                        pass

                raise

            self.send_json(
                201,
                {
                    "status": "created",
                    "id": project_id,
                    "name": name,
                    "folder": project_folder_name
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


    def handle_save(self):

        try:

            request = self.read_json_body()

            filename = request.get(
                "filename"
            )

            content = request.get(
                "content"
            )

            if not isinstance(
                filename,
                str
            ):

                self.send_json(
                    400,
                    {
                        "error":
                            "filename must be a string"
                    }
                )

                return


            if not isinstance(
                content,
                str
            ):

                self.send_json(
                    400,
                    {
                        "error":
                            "content must be a string"
                    }
                )

                return


            destination = self.save_file(
                PROJECTS_FOLDER,
                filename,
                content
            )


            self.send_json(
                201,
                {
                    "status": "saved",
                    "path": str(
                        destination
                    )
                }
            )


        except json.JSONDecodeError:

            self.send_json(
                400,
                {
                    "error":
                        "invalid JSON"
                }
            )


        except OverflowError as error:

            self.send_json(
                413,
                {
                    "error": str(error)
                }
            )


        except FileExistsError:

            self.send_json(
                409,
                {
                    "error":
                        "file already exists"
                }
            )


        except ValueError as error:

            self.send_json(
                400,
                {
                    "error": str(error)
                }
            )


        except Exception as error:

            self.send_json(
                500,
                {
                    "error": str(error)
                }
            )


    def handle_conversation(self):

        try:

            request = self.read_json_body()

            title = request.get(
                "title"
            )

            url = request.get(
                "url"
            )

            messages = request.get(
                "messages"
            )

            project_id = request.get(
                "project",
                DEFAULT_PROJECT
            )


            if not isinstance(
                title,
                str
            ):

                self.send_json(
                    400,
                    {
                        "error":
                            "title must be a string"
                    }
                )

                return


            if not isinstance(
                url,
                str
            ):

                self.send_json(
                    400,
                    {
                        "error":
                            "url must be a string"
                    }
                )

                return


            if not isinstance(
                messages,
                list
            ):

                self.send_json(
                    400,
                    {
                        "error":
                            "messages must be an array"
                    }
                )

                return


            if not messages:

                self.send_json(
                    400,
                    {
                        "error":
                            "messages cannot be empty"
                    }
                )

                return


            if not isinstance(
                project_id,
                str
            ):

                self.send_json(
                    400,
                    {
                        "error":
                            "project must be a string"
                    }
                )

                return


            project_id = (
                project_id
                .strip()
                .upper()
            )


            for message in messages:

                if not isinstance(
                    message,
                    dict
                ):

                    self.send_json(
                        400,
                        {
                            "error":
                                "each message must be an object"
                        }
                    )

                    return


                if not isinstance(
                    message.get("role"),
                    str
                ):

                    self.send_json(
                        400,
                        {
                            "error":
                                "message role must be a string"
                        }
                    )

                    return


                if not isinstance(
                    message.get("content"),
                    str
                ):

                    self.send_json(
                        400,
                        {
                            "error":
                                "message content must be a string"
                        }
                    )

                    return


            project_folder_path = (
                project_folder(
                    project_id
                )
            )

            previous_path = previous_conversation(
                project_id
            )


            conversation_id = (
                next_conversation_id(
                    project_id
                )
            )


            clean_title = sanitize_title(
                title
            )

            previous_link = None

            if previous_path:

                previous_link = previous_path.stem

            markdown = (
                build_conversation_markdown(
                    conversation_id,
                    clean_title,
                    project_id,
                    url,
                    messages,
                    previous_link=previous_link,
                    project_link=f"{project_id} - Project Index"
                )
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
                project_folder_path / "Chats",
                filename,
                markdown
            )

            if previous_path:


                update_next_link(
                previous_path,
                destination.stem
            )


            update_project_index(
                project_id
            )


            self.send_json(
                201,
                {
                    "status": "saved",
                    "id": conversation_id,
                    "title": clean_title,
                    "project": project_id,
                    "url": url,
                    "message_count":
                        len(messages),
                    "path": str(
                        destination
                    )
                }
            )


        except json.JSONDecodeError:

            self.send_json(
                400,
                {
                    "error":
                        "invalid JSON"
                }
            )


        except OverflowError as error:

            self.send_json(
                413,
                {
                    "error": str(error)
                }
            )


        except FileExistsError:

            self.send_json(
                409,
                {
                    "error":
                        "file already exists"
                }
            )


        except ValueError as error:

            self.send_json(
                400,
                {
                    "error": str(error)
                }
            )


        except Exception as error:

            self.send_json(
                500,
                {
                    "error": str(error)
                }
            )


    def log_message(
        self,
        format,
        *args
    ):

        print(
            f"[HTTP] {self.address_string()} - "
            f"{format % args}"
        )


if __name__ == "__main__":

    print(
        "ChatGPT Obsidian Connector"
    )

    print(
        f"Listening on http://{HOST}:{PORT}"
    )

    print(
        "Health endpoint: "
        "http://127.0.0.1:8765/health"
    )

    print(
        "Projects endpoint: "
        "http://127.0.0.1:8765/projects"
    )

    print(
        "Save endpoint: "
        "POST http://127.0.0.1:8765/save"
    )

    print(
        "Conversation endpoint: "
        "POST http://127.0.0.1:8765/conversation"
    )

    print(
        "Create project endpoint: "
        "POST http://127.0.0.1:8765/projects"
    )

    print(
        "Press Ctrl+C to stop."
    )


    server = HTTPServer(
        (HOST, PORT),
        ConnectorHandler
    )

    server.serve_forever()
