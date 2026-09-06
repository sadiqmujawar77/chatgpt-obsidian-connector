\# System Architecture



\## Overview



The ChatGPT Obsidian Connector is a local-first system that captures ChatGPT conversations from a web browser and stores them as structured Markdown documents in an Obsidian vault.



The system is composed of three primary components:



```text

ChatGPT

&#x20;  │

&#x20;  ▼

Browser Extension

&#x20;  │

&#x20;  │ HTTP / JSON

&#x20;  ▼

Local Connector

&#x20;  │

&#x20;  ▼

Obsidian Vault

```



The architecture intentionally keeps vault storage local to the user's computer and separates browser-side conversation capture from filesystem operations.



\## Components



\### 1. ChatGPT



ChatGPT is the source of the conversation data.



The browser extension runs on ChatGPT pages and reads the rendered conversation from the page DOM.



The extension extracts:



\- Conversation title

\- Conversation URL

\- Message roles

\- Message content



The extension does not directly write files into the Obsidian vault.



\### 2. Browser Extension



The browser extension provides the browser-side capture layer.



It is implemented using the browser's Manifest V3 extension architecture.



The extension consists of:



```text

extension/

├── manifest.json

└── src/

&#x20;   ├── background.js

&#x20;   └── content.js

```



\#### Content Script



The content script runs within the ChatGPT page and is responsible for:



\- Detecting conversation messages.

\- Reading message roles from the ChatGPT DOM.

\- Extracting message content.

\- Converting HTML content into Markdown.

\- Collecting conversation metadata.

\- Communicating with the extension background service worker.



The HTML-to-Markdown conversion preserves common document structures including:



\- Headings

\- Bold and italic formatting

\- Ordered lists

\- Unordered lists

\- Links

\- Code blocks

\- Blockquotes

\- Tables

\- Horizontal rules

\- Line breaks



\#### Background Service Worker



The background service worker acts as the extension's communication layer with the local connector.



It receives extracted conversation data from the content script and sends HTTP requests to:



```text

http://127.0.0.1:8765

```



This separation avoids relying on page-context JavaScript for communication with the local connector.



\## 3. Local Connector



The local connector is a Python HTTP service running on the user's computer.



Implementation:



```text

connector/

└── src/

&#x20;   └── server.py

```



The connector currently uses Python's standard-library HTTP server implementation.



It listens only on:



```text

127.0.0.1:8765

```



This means the service is bound to the local loopback interface rather than a network-facing interface.



\### Connector Responsibilities



The connector is responsible for:



\- Receiving requests from the browser extension.

\- Validating request data.

\- Generating conversation identifiers.

\- Sanitizing conversation titles.

\- Generating structured Markdown.

\- Writing Markdown files into the Obsidian vault.

\- Preventing accidental overwrites.

\- Performing atomic file writes.

\- Enforcing request-size limits.



\## 4. Obsidian Vault



Obsidian provides the local Markdown-based knowledge repository.



The connector writes captured conversations directly into the configured vault.



The current project location is:



```text

00 - ChatGPT/

└── Projects/

&#x20;   └── P001 - ChatGPT Obsidian Connector/

&#x20;       └── Chats/

```



Conversation files use Markdown with YAML frontmatter.



Example:



```markdown

\---

id: P001-001

title: Example Conversation

type: conversation

project: P001

date: 2026-09-06

tags:

&#x20; - project

&#x20; - chatgpt

&#x20; - obsidian

source: ChatGPT

\---

```



This allows Obsidian to expose structured metadata as properties while keeping the stored documents portable Markdown files.



\## Data Flow



A conversation capture follows this sequence:



```text

1\. User opens a ChatGPT conversation

&#x20;            │

&#x20;            ▼

2\. Content script detects conversation messages

&#x20;            │

&#x20;            ▼

3\. Message HTML is converted to Markdown

&#x20;            │

&#x20;            ▼

4\. Conversation metadata is collected

&#x20;            │

&#x20;            ▼

5\. Content script sends data to background worker

&#x20;            │

&#x20;            ▼

6\. Background worker sends HTTP POST /conversation

&#x20;            │

&#x20;            ▼

7\. Local connector validates the request

&#x20;            │

&#x20;            ▼

8\. Connector assigns the next conversation ID

&#x20;            │

&#x20;            ▼

9\. Connector generates structured Markdown

&#x20;            │

&#x20;            ▼

10\. Connector performs an atomic file write

&#x20;            │

&#x20;            ▼

11\. Markdown file appears in the Obsidian vault

```



\## Communication Boundaries



The architecture deliberately separates responsibilities across communication boundaries.



\### Browser Page → Content Script



The content script reads the rendered ChatGPT DOM.



\### Content Script → Background Worker



The extension components communicate through the browser extension messaging mechanism.



\### Background Worker → Local Connector



The background worker sends HTTP/JSON requests to the local connector.



```text

Browser Extension

&#x20;      │

&#x20;      │ HTTP / JSON

&#x20;      ▼

127.0.0.1:8765

```



\### Local Connector → Vault



The connector performs filesystem operations directly against the configured Obsidian vault.



```text

Local Connector

&#x20;      │

&#x20;      │ Filesystem

&#x20;      ▼

Obsidian Vault

```



\## Identifier Generation



Project conversations use sequential identifiers.



For project `P001`:



```text

P001-001

P001-002

P001-003

...

```



The connector scans the project conversation directory for existing conversation files and determines the next available identifier.



This keeps conversation identifiers independent from filenames generated by the browser.



\## File Safety



The connector is designed to avoid destructive filesystem operations.



Current protections include:



\- Localhost-only network binding.

\- Request-size limits.

\- Filename validation.

\- Input validation.

\- Existing-file protection.

\- Temporary-file writes.

\- Filesystem synchronization before replacement.

\- Atomic file replacement.



An existing conversation file is not silently overwritten.



\## Local-First Design



The system is intentionally local-first.



The data path is:



```text

ChatGPT

&#x20;  │

&#x20;  ▼

Browser Extension

&#x20;  │

&#x20;  ▼

Local Connector

&#x20;  │

&#x20;  ▼

Local Obsidian Vault

```



There is no requirement for a third-party cloud storage service between the connector and the Obsidian vault.



The local connector provides the boundary between browser-based capture and local filesystem storage.



\## Current Architecture Status



The following architecture components are implemented:



\- Local Python connector.

\- `/health` endpoint.

\- `/save` endpoint.

\- `/conversation` endpoint.

\- Browser extension Manifest V3 structure.

\- ChatGPT DOM conversation extraction.

\- HTML-to-Markdown conversion.

\- Background-worker communication.

\- End-to-end conversation capture.

\- Sequential project conversation numbering.

\- Structured Markdown generation.

\- Local Obsidian vault storage.

\- Existing-file protection.

\- Atomic file writes.



\## Future Architecture



The architecture is intended to evolve to support additional capture and knowledge-management workflows, including:



\- Saving the current ChatGPT response.

\- Saving selected text.

\- Appending content to an existing note.

\- Project selection and creation.

\- Automatic project and global indexes.

\- Previous/next conversation links.

\- Related-conversation discovery.

\- Searching previous conversations for existing discussions.

\- Extracting durable knowledge notes from conversation archives.



These capabilities are planned extensions and are not considered part of the currently implemented core architecture.

