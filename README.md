# ChatGPT Obsidian Connector

A local-first system for capturing ChatGPT conversations and storing them as structured Markdown documents in an Obsidian vault.

## Architecture

```text
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
```

## Components

### Browser Extension

The browser extension runs on ChatGPT and is responsible for:

- Detecting the active ChatGPT conversation.
- Extracting conversation messages and metadata.
- Converting ChatGPT message HTML into Markdown.
- Preserving headings, formatting, lists, links, code blocks, blockquotes, and tables.
- Sending the captured conversation to the local connector.

The extension uses an isolated content script and a background service worker. The service worker communicates with the local connector so that browser page security policies do not need to be bypassed.

### Local Connector

The local connector is a Python HTTP service running on the user's computer.

It is responsible for:

- Accepting requests from the browser extension.
- Validating incoming data.
- Generating structured conversation Markdown.
- Assigning conversation identifiers.
- Sanitizing conversation titles.
- Writing Markdown documents into the configured Obsidian vault.
- Preventing accidental overwrites.
- Performing atomic file writes.
- Limiting request size.
- Binding only to the local loopback interface.

### Obsidian

Obsidian acts as the local knowledge repository.

Conversation documents are stored as Markdown with YAML frontmatter so that Obsidian can expose structured properties, tags, and links.

## API

The local connector listens on:

```text
127.0.0.1:8765
```

### Health Check

```http
GET /health
```

Returns the connector health status.

### Save Markdown

```http
POST /save
```

Accepts a JSON payload containing a filename and Markdown content.

The endpoint validates the filename, prevents overwriting an existing file, and performs an atomic write.

### Save Conversation

```http
POST /conversation
```

Accepts a structured conversation payload containing:

- Conversation title
- ChatGPT URL
- Conversation messages
- Message roles
- Message content

The connector generates the Markdown document, assigns the next conversation identifier, and saves the document into the configured project conversation directory.

## Conversation Identifiers

Project conversations use sequential identifiers.

For project `P001`:

```text
P001-001
P001-002
P001-003
...
```

The identifier is stored in the Markdown frontmatter and used in the conversation filename.

## Conversation Document Structure

Captured conversations use the following structure:

```markdown
---
id: P001-001
title: Example Conversation
type: conversation
project: P001
date: 2026-09-06
tags:
  - project
  - chatgpt
  - obsidian
source: ChatGPT
---

# P001-001 — Example Conversation

## Summary

Conversation captured from ChatGPT.

## Key Points

- To be reviewed and summarized.

## Conversation

### User

...

### ChatGPT

...

## Related

- Previous
- Next
- Project
```

## Security and Reliability

The connector currently implements several local safety measures:

- Localhost-only binding using `127.0.0.1`.
- Maximum request-size enforcement.
- Filename validation.
- Markdown filename restrictions.
- Existing-file protection.
- Atomic file writes using a temporary file followed by replacement.
- Input validation for conversation requests.

The connector does not require a third-party cloud service to store the Obsidian vault.

## Project Structure

```text
chatgpt-obsidian-connector/
├── connector/
│   ├── src/
│   │   └── server.py
│   └── README.md
├── extension/
│   ├── manifest.json
│   ├── src/
│   │   ├── background.js
│   │   └── content.js
│   └── README.md
├── obsidian/
│   ├── templates/
│   └── README.md
├── tests/
├── scripts/
├── docs/
├── .gitignore
├── CHANGELOG.md
├── LICENSE
└── README.md
```

## Technology

- Python 3.12
- Python standard library HTTP server
- Browser Extension Manifest V3
- JavaScript
- Markdown
- YAML frontmatter
- Obsidian

## Development Status

The project is being developed incrementally.

Current milestones include:

1. Local connector
2. Connector API contract
3. Connector validation tests
4. Browser extension
5. End-to-end conversation capture
6. HTML-to-Markdown conversation formatting
7. Project and conversation indexing
8. Additional validation and reliability improvements

The local connector and browser extension currently support end-to-end conversation capture from ChatGPT into Obsidian.

## Design Principles

- Local-first
- Privacy-conscious
- Markdown-based
- Obsidian-compatible
- Minimal external dependencies
- Safe file operations
- Clear separation between browser capture and local storage
- Incremental, testable development

## License

License to be determined.