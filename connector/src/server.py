from http.server import BaseHTTPRequestHandler, HTTPServer
import hashlib
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


PAIR_MARKER_PATTERN = re.compile(
    r'(?:<!-- COC-PAIR: |%% COC-PAIR: |<span data-coc-pair=")(\d+):([0-9a-f]{64})(?: -->| %%|"></span>)'
)


CONVERSATION_MARKER = "## Conversation"
RELATED_MARKER = "\n## Related\n"


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

    related_marker = RELATED_MARKER

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

    atomic_write_text(
        conversation_path,
        updated_content
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

    atomic_write_text(index_path, updated)

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


def atomic_write_text(path, content):
    """Write UTF-8 text atomically to an existing or new path."""

    path.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_name = tempfile.mkstemp(
        prefix=".chatgpt-",
        suffix=".tmp",
        dir=str(path.parent)
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

        os.replace(temp_name, path)

    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def user_fingerprint(content):
    """
    Return a stable identity for the logical User message.

    Markdown escaping used for Obsidian storage must not change the
    identity of the underlying question.
    """
    normalized = content.strip()

    # Treat escaped Markdown punctuation as the same logical text.
    normalized = re.sub(
        r"\\([*`_~])",
        r"\1",
        normalized
    )

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()


def normalize_pairs(pairs):
    """
    Validate and normalize M005-006 Q/R pairs.

    Each pair is:
        {"index": N, "user": "...", "assistant": "..."}
    """

    if not isinstance(pairs, list):
        raise ValueError("pairs must be an array")

    if not pairs:
        raise ValueError("pairs cannot be empty")

    normalized = []
    seen_indexes = set()

    for pair in pairs:
        if not isinstance(pair, dict):
            raise ValueError("each pair must be an object")

        index = pair.get("index")
        user = pair.get("user")
        assistant = pair.get("assistant")

        if not isinstance(index, int) or isinstance(index, bool) or index < 1:
            raise ValueError("pair index must be a positive integer")

        if index in seen_indexes:
            raise ValueError(f"duplicate pair index: {index}")

        if not isinstance(user, str):
            raise ValueError("pair user content must be a string")

        if not isinstance(assistant, str):
            raise ValueError("pair assistant content must be a string")

        seen_indexes.add(index)

        normalized.append({
            "index": index,
            "user": user.strip(),
            "assistant": assistant.strip(),
            "fingerprint": user_fingerprint(user)
        })

    normalized.sort(key=lambda item: item["index"])
    return normalized


def messages_to_pairs(messages):
    """
    Backward-compatible conversion of the old role/content payload.

    Leading assistant/context messages are ignored for pair capture.
    A pair is a User message followed by its next ChatGPT response.
    """

    if not isinstance(messages, list):
        raise ValueError("messages must be an array")

    pairs = []
    pending_user = None

    for message in messages:
        if not isinstance(message, dict):
            raise ValueError("each message must be an object")

        role = message.get("role")
        content = message.get("content")

        if not isinstance(role, str):
            raise ValueError("message role must be a string")

        if not isinstance(content, str):
            raise ValueError("message content must be a string")

        role = role.strip().lower()

        if role == "user":
            pending_user = content
            continue

        if role == "assistant" and pending_user is not None:
            pairs.append({
                "index": len(pairs) + 1,
                "user": pending_user,
                "assistant": content
            })
            pending_user = None

    if pending_user is not None:
        raise ValueError("user message is missing its ChatGPT response")

    if not pairs:
        raise ValueError("no user/ChatGPT pairs found")

    return normalize_pairs(pairs)


def pair_marker(pair):
    return (
        f'<span data-coc-pair="{pair["index"]}:{pair["fingerprint"]}"></span>'
    )


def build_pair_markdown(pair):
    return "\n".join([
        f"### User {pair_marker(pair)}",
        "",
        pair["user"],
        "",
        "### ChatGPT",
        "",
        pair["assistant"],
        ""
    ])


def build_conversation_markdown(
    conversation_id,
    title,
    project_id,
    url,
    pairs,
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

    for pair in pairs:
        lines.append(build_pair_markdown(pair))

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


def conversation_path_by_url(project_id, url):
    """Find the existing conversation note for an exact ChatGPT URL."""

    chat_folder = chats_folder(project_id)

    for path in chat_folder.glob(f"{project_id}-*.md"):
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue

        match = re.search(
            r"^url:\s*(.*)$",
            content,
            re.MULTILINE
        )

        if match and match.group(1).strip() == url:
            return path

    return None


def parse_existing_pairs(content):
    """
    Read generated COC pair markers from a conversation.

    If an older M005-005 conversation has no markers, migrate its
    User -> ChatGPT sections into numbered pairs while preserving the
    captured message text.
    """

    conversation_start = content.find(
        CONVERSATION_MARKER
    )

    if conversation_start < 0:
        raise ValueError("conversation is missing Conversation section")

    related_start = content.rfind(RELATED_MARKER)

    if related_start < 0 or related_start <= conversation_start:
        raise ValueError("conversation is missing Related section")

    body_start = content.find("\n", conversation_start)
    if body_start < 0:
        body_start = len(content)
    else:
        body_start += 1

    body = content[body_start:related_start]

    markers = list(PAIR_MARKER_PATTERN.finditer(body))

    if markers:
        pairs = []

        for position, marker in enumerate(markers):
            marker_line_start = body.rfind("\n", 0, marker.start()) + 1
            marker_line_prefix = body[marker_line_start:marker.start()]

            if marker_line_prefix.strip() == "":
                # Legacy marker on its own line:
                # <!-- COC-PAIR: ... -->
                # ### User
                block_start = marker.end()
            else:
                # Current marker embedded in the User heading:
                # ### User <!-- COC-PAIR: ... -->
                block_start = marker_line_start

            block_end = (
                markers[position + 1].start()
                if position + 1 < len(markers)
                else len(body)
            )

            block = body[block_start:block_end].strip()

            user_match = re.search(
                r'^### User(?:\s+(?:<!-- COC-PAIR: \d+:[0-9a-f]{64} -->|%% COC-PAIR: \d+:[0-9a-f]{64} %%|<span data-coc-pair="\d+:[0-9a-f]{64}"></span>))?\s*\n(.*?)(?=^### ChatGPT\s*$)',
                block,
                re.MULTILINE | re.DOTALL
            )
            assistant_match = re.search(
                r"^### ChatGPT\s*\n(.*)$",
                block,
                re.MULTILINE | re.DOTALL
            )

            if not user_match or not assistant_match:
                raise ValueError(
                    "invalid COC pair marker block"
                )

            assistant_content = assistant_match.group(1).strip()

            # A browser capture can occasionally leave empty User
            # headings inside the previous assistant message.
            # They are structural noise, not assistant content.
            assistant_content = re.sub(
                r"^### User\s*$",
                "",
                assistant_content,
                flags=re.MULTILINE
            ).strip()

            pairs.append({
                "index": int(marker.group(1)),
                "user": user_match.group(1).strip(),
                "assistant": assistant_content,
                "fingerprint": user_fingerprint(
                    user_match.group(1)
                )
            })

        return sorted(pairs, key=lambda item: item["index"]), False, ""

    # Legacy M005-005 format: extract User -> ChatGPT sections.
    headings = list(re.finditer(
        r"^### (User|ChatGPT)\s*$",
        body,
        re.MULTILINE
    ))

    pairs = []
    pending_user = None
    prefix = ""

    if headings and headings[0].start() > 0:
        prefix = body[:headings[0].start()]

    for position, heading in enumerate(headings):
        role = heading.group(1)
        content_start = heading.end()
        content_end = (
            headings[position + 1].start()
            if position + 1 < len(headings)
            else len(body)
        )
        message_content = body[content_start:content_end].strip()

        if role == "User":
            pending_user = message_content
        elif role == "ChatGPT" and pending_user is not None:
            index = len(pairs) + 1
            pairs.append({
                "index": index,
                "user": pending_user,
                "assistant": message_content,
                "fingerprint": user_fingerprint(pending_user)
            })
            pending_user = None
        elif role == "ChatGPT":
            # Preserve any leading assistant/context block that is not
            # part of a User -> ChatGPT pair.
            prefix += body[heading.start():content_end]

    if pending_user is not None:
        raise ValueError("legacy conversation has an unmatched User message")

    if not pairs:
        raise ValueError("conversation contains no User/ChatGPT pairs")

    return pairs, True, prefix


def render_merged_conversation(content, pairs, legacy_prefix=""):
    """Replace only the generated Conversation body, preserving all other content."""

    conversation_start = content.find(
        CONVERSATION_MARKER
    )

    if conversation_start < 0:
        raise ValueError("conversation is missing Conversation section")

    related_start = content.rfind(RELATED_MARKER)

    if related_start < 0 or related_start <= conversation_start:
        raise ValueError("conversation is missing Related section")

    body_start = content.find("\n", conversation_start)
    if body_start < 0:
        raise ValueError("conversation section is malformed")
    body_start += 1

    rendered_pairs = []

    for pair in sorted(pairs, key=lambda item: item["index"]):
        normalized = {
            "index": pair["index"],
            "user": pair["user"].strip(),
            "assistant": pair["assistant"].strip(),
            "fingerprint": pair.get(
                "fingerprint",
                user_fingerprint(pair["user"])
            )
        }
        rendered_pairs.append(
            build_pair_markdown(normalized)
        )

    new_body = legacy_prefix.rstrip("\n")
    if new_body:
        new_body += "\n\n"
    new_body += "\n".join(rendered_pairs)

    return (
        content[:body_start]
        + new_body
        + "\n"
        + content[related_start:]
    )



def merge_response_pair(path, incoming_pair):
    """
    Merge a single latest-response pair.

    For response capture, the pair index supplied by the browser is only
    positional within the currently rendered DOM and must not be treated
    as the conversation's authoritative index.

    If the same user question already exists, preserve its existing index
    and update its assistant response.

    If the question is new, append it after the current highest pair index.
    """
    content = path.read_text(encoding="utf-8")

    existing_pairs, migrated, legacy_prefix = parse_existing_pairs(content)

    incoming = incoming_pair.copy()
    fingerprint = incoming["fingerprint"]

    existing_by_fingerprint = {
        pair["fingerprint"]: pair
        for pair in existing_pairs
    }

    existing = existing_by_fingerprint.get(fingerprint)

    if existing is not None:
        incoming["index"] = existing["index"]
    else:
        incoming["index"] = max(
            (pair["index"] for pair in existing_pairs),
            default=0
        ) + 1

    return merge_conversation_file(
        path,
        [incoming]
    )


def merge_selected_pair(path, incoming_pair):
    """
    Merge one explicitly selected Q/R pair.

    The browser pair index is positional within the currently
    rendered conversation and may therefore differ from the
    authoritative index already stored in Obsidian.

    If the same user question already exists, preserve its
    existing authoritative index.

    If the question is new, retain the supplied pair index so
    chronological insertion can be performed normally.
    """
    content = path.read_text(encoding="utf-8")

    existing_pairs, migrated, legacy_prefix = parse_existing_pairs(content)

    incoming = incoming_pair.copy()
    fingerprint = incoming["fingerprint"]

    existing_by_fingerprint = {
        pair["fingerprint"]: pair
        for pair in existing_pairs
    }

    existing = existing_by_fingerprint.get(fingerprint)

    if existing is not None:
        incoming["index"] = existing["index"]

    return merge_conversation_file(
        path,
        [incoming]
    )

def merge_conversation_file(path, incoming_pairs):
    """
    Merge incoming Q/R pairs into an existing conversation.

    Existing pairs are never duplicated. A pair with the same question
    fingerprint is updated in place so regenerated responses do not
    create another pair. Missing pairs are inserted chronologically.
    """

    content = path.read_text(encoding="utf-8")
    existing_pairs, migrated, legacy_prefix = parse_existing_pairs(content)

    existing_by_key = {
        (pair["index"], pair["fingerprint"]): pair
        for pair in existing_pairs
    }

    existing_by_fingerprint = {
        pair["fingerprint"]: pair
        for pair in existing_pairs
    }

    added = 0
    updated = 0
    next_index = max(
        (pair["index"] for pair in existing_pairs),
        default=0
    ) + 1

    for incoming in incoming_pairs:
        fingerprint = incoming["fingerprint"]

        if fingerprint in existing_by_fingerprint:
            existing = existing_by_fingerprint[fingerprint]

            # The fingerprint identifies the question. The incoming
            # positional index may be different because ChatGPT can
            # render only part of a conversation in the browser DOM.
            if existing["assistant"] != incoming["assistant"]:
                existing["assistant"] = incoming["assistant"]
                updated += 1
                # The question fingerprint identifies the
                # conversation pair. Preserve the authoritative
                # existing index while updating the assistant response.

            continue

        incoming_copy = incoming.copy()

        occupied_indices = {
            pair["index"]
            for pair in existing_pairs
        }

        if incoming_copy["index"] in occupied_indices:
            # A partial/virtualized browser capture may reuse an index
            # already belonging to an existing Q/R. Never overwrite it.
            # Assign the new question the next available authoritative
            # index instead.
            while next_index in occupied_indices:
                next_index += 1

            incoming_copy["index"] = next_index
            next_index += 1
        else:
            next_index = max(
                next_index,
                incoming_copy["index"] + 1
            )

        existing_pairs.append(incoming_copy)
        existing_by_key[
            (
                incoming_copy["index"],
                incoming_copy["fingerprint"]
            )
        ] = existing_pairs[-1]
        existing_by_fingerprint[
            incoming_copy["fingerprint"]
        ] = existing_pairs[-1]
        added += 1

    updated_content = render_merged_conversation(
        content,
        existing_pairs,
        legacy_prefix=legacy_prefix
    )

    if updated_content != content:
        atomic_write_text(path, updated_content)

    return {
        "added_pairs": added,
        "updated_pairs": updated,
        "total_pairs": len(existing_pairs),
        "migrated_legacy": migrated
    }


class ConnectorHandler(BaseHTTPRequestHandler):

    def send_json(
        self,
        status_code,
        data
    ):

        body = json.dumps(
            data,
            ensure_ascii=False
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

        atomic_write_text(destination, content)
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

            project_id = request.get(
                "project",
                DEFAULT_PROJECT
            )

            capture_mode = request.get(
                "capture_mode",
                "full"
            )

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

            if not url.strip():
                self.send_json(
                    400,
                    {"error": "url cannot be empty"}
                )
                return

            if capture_mode not in {"full", "response", "pair"}:
                self.send_json(
                    400,
                    {"error": "capture_mode must be 'full', 'response', or 'pair'"}
                )
                return

            if not isinstance(project_id, str):
                self.send_json(
                    400,
                    {"error": "project must be a string"}
                )
                return

            project_id = (
                project_id
                .strip()
                .upper()
            )

            if "pairs" in request:
                pairs = normalize_pairs(request.get("pairs"))
            else:
                messages = request.get("messages")
                if not isinstance(messages, list):
                    self.send_json(
                        400,
                        {"error": "messages must be an array"}
                    )
                    return
                pairs = messages_to_pairs(messages)

            if capture_mode in {"response", "pair"} and len(pairs) != 1:
                self.send_json(
                    400,
                    {"error": f"{capture_mode} capture must contain exactly one pair"}
                )
                return

            project_folder_path = project_folder(project_id)
            clean_title = sanitize_title(title)

            existing_path = conversation_path_by_url(
                project_id,
                url.strip()
            )

            if existing_path:
                if capture_mode == "response":
                    result = merge_response_pair(
                        existing_path,
                        pairs[0]
                    )
                elif capture_mode == "pair":
                    result = merge_selected_pair(
                        existing_path,
                        pairs[0]
                    )
                else:
                    result = merge_conversation_file(
                        existing_path,
                        pairs
                    )

                self.send_json(
                    200,
                    {
                        "status": "updated",
                        "id": existing_path.stem.split(" - ", 1)[0],
                        "title": clean_title,
                        "project": project_id,
                        "url": url.strip(),
                        "capture_mode": capture_mode,
                        "added_pairs": result["added_pairs"],
                        "updated_pairs": result["updated_pairs"],
                        "total_pairs": result["total_pairs"],
                        "migrated_legacy": result["migrated_legacy"],
                        "path": str(existing_path)
                    }
                )
                return

            previous_path = previous_conversation(
                project_id
            )

            conversation_id = (
                next_conversation_id(
                    project_id
                )
            )

            previous_link = None

            if previous_path:
                previous_link = previous_path.stem

            markdown = (
                build_conversation_markdown(
                    conversation_id,
                    clean_title,
                    project_id,
                    url.strip(),
                    pairs,
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
                    "status": "created",
                    "id": conversation_id,
                    "title": clean_title,
                    "project": project_id,
                    "url": url.strip(),
                    "capture_mode": capture_mode,
                    "added_pairs": len(pairs),
                    "updated_pairs": 0,
                    "total_pairs": len(pairs),
                    "migrated_legacy": False,
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
