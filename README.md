# ChatGPT Obsidian Connector

A local-first system for capturing ChatGPT conversations and storing them as structured Markdown documents in an Obsidian vault.

## Architecture

`	ext
ChatGPT
   │
   ▼
Browser Extension
   │
   │ HTTP / JSON
   ▼
Local Connector
   │
   ▼
Obsidian Vault
`"
"


### Browser Extension

Responsible for:

- Detecting the active ChatGPT conversation.
- Extracting conversation content and metadata.
- Converting the captured conversation into a structured payload.
- Sending the payload to the local connector.

### Local Connector

Responsible for:

- Accepting requests from the browser extension.
- Validating incoming data.
- Generating or accepting structured Markdown.
- Writing Markdown documents into the configured Obsidian vault.
- Preventing accidental overwrites.
- Performing safe file writes.

### Obsidian

Acts as the local knowledge repository.

Conversation documents are stored as Markdown with YAML frontmatter so that Obsidian can expose structured properties, tags, and links.

## Current Status

The local connector currently provides:

- GET /health
- POST /save

The connector listens only on:

127.0.0.1:8765

The current implementation supports:

- JSON requests
- Markdown file creation
- Filename validation
- Request-size limits
- Existing-file protection
- Atomic file writes

## Project Structure

`	ext
chatgpt-obsidian-connector/
├── connector/
│   └── src/
│       └── server.py
├── tests/
├── .gitignore
└── README.md
`"
"


The current implementation uses Python 3.12.

The project is being developed incrementally:

1. Local connector
2. Connector API contract
3. Browser extension
4. End-to-end conversation capture
5. Project and conversation indexing
6. Additional validation and reliability improvements

## Design Principles

- Local-first
- Privacy-conscious
- Markdown-based
- Obsidian-compatible
- Minimal external dependencies
- Safe file operations
- Clear separation between browser capture and local storage

## License

License to be determined.
