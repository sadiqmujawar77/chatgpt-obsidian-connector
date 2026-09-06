\# Design Decisions



This document records the significant technical decisions made during development of the ChatGPT Obsidian Connector and the reasoning behind them.



\## DD-001 — Local-First Architecture



\### Decision



The system uses a local-first architecture:



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

Obsidian Vault

```



\### Rationale



The primary purpose of the connector is to place captured conversations directly into the user's local Obsidian knowledge repository.



Keeping the storage path local:



\- Avoids unnecessary third-party storage services.

\- Keeps the vault under the user's control.

\- Reduces external dependencies.

\- Fits naturally with Obsidian's local Markdown model.



\## DD-002 — Separate Browser Capture from File Storage



\### Decision



The browser extension does not directly write files into the Obsidian vault.



Instead, it sends structured data to the local connector.



```text

Browser Extension

&#x20;      │

&#x20;      │ HTTP / JSON

&#x20;      ▼

Local Connector

&#x20;      │

&#x20;      │ Filesystem

&#x20;      ▼

Obsidian Vault

```



\### Rationale



The separation provides a clear boundary between:



\- Browser interaction and DOM extraction.

\- Data validation and filesystem operations.



This also allows the local connector to own file naming, identifier generation, validation, and safe writes.



\## DD-003 — Python for the Local Connector



\### Decision



The local connector is implemented in Python 3.12.



\### Rationale



Python was selected because:



\- Python 3.12 is available in the development environment.

\- The connector can be implemented using the standard library.

\- A lightweight local HTTP service is sufficient for the current requirements.

\- Avoiding unnecessary runtime dependencies keeps the connector simple to install and maintain.



The current implementation uses Python's standard-library HTTP server functionality.



\## DD-004 — Browser Extension Manifest V3



\### Decision



The browser integration uses the browser's Manifest V3 extension architecture.



\### Rationale



Manifest V3 provides the current extension architecture needed for the browser-side capture layer.



The implementation separates:



\- Content-script DOM access.

\- Background service-worker communication.



This creates a clear boundary between page interaction and communication with the local service.



\## DD-005 — Isolated Content Script



\### Decision



Conversation extraction is performed from an isolated content script rather than page-context JavaScript.



\### Rationale



The content script needs access to the rendered ChatGPT DOM while avoiding direct dependence on page-context JavaScript APIs.



The page and extension communicate through an explicit message bridge where required.



This keeps extension functionality within the browser extension execution model.



\## DD-006 — Background Service Worker for Local HTTP Requests



\### Decision



The extension background service worker performs HTTP requests to the local connector.



\### Rationale



The browser page itself is subject to the security policies of the ChatGPT page.



During development, attempting to perform the local HTTP request directly from page context was blocked by the page's Content Security Policy.



The background service worker provides the appropriate extension-controlled communication path:



```text

ChatGPT Page

&#x20;    │

&#x20;    ▼

Content Script

&#x20;    │

&#x20;    ▼

Background Service Worker

&#x20;    │

&#x20;    ▼

127.0.0.1:8765

```



\## DD-007 — Loopback-Only Connector Binding



\### Decision



The connector listens on:



```text

127.0.0.1:8765

```



rather than on a network-facing interface.



\### Rationale



The connector is intended to serve the local browser extension on the same computer.



Loopback-only binding:



\- Keeps the service local.

\- Avoids intentionally exposing the API to the local network.

\- Reduces the network attack surface.

\- Matches the local-first architecture.



\## DD-008 — HTTP/JSON Communication



\### Decision



The browser extension communicates with the connector using HTTP and JSON.



\### Rationale



HTTP/JSON provides a simple and explicit interface between the JavaScript extension and Python connector.



It also makes the connector API:



\- Easy to inspect.

\- Easy to test.

\- Independent of the browser implementation.

\- Straightforward to extend.



\## DD-009 — Markdown as the Storage Format



\### Decision



Captured conversations are stored as Markdown files.



\### Rationale



Markdown is the native content format for Obsidian and provides several useful properties:



\- Human-readable files.

\- Portable data.

\- Easy version control.

\- Compatibility with standard text-processing tools.

\- No proprietary database dependency.



\## DD-010 — YAML Frontmatter for Metadata



\### Decision



Conversation documents use YAML frontmatter for structured metadata.



\### Rationale



YAML frontmatter allows metadata to remain embedded in the Markdown document while being exposed by Obsidian as structured properties.



The current metadata model includes:



```yaml

\---

id:

title:

type:

project:

date:

tags:

source: ChatGPT

\---

```



This keeps content and metadata together without requiring a separate metadata database.



\## DD-011 — Sequential Conversation Identifiers



\### Decision



Project conversations use sequential identifiers such as:



```text

P001-001

P001-002

P001-003

```



\### Rationale



Human-readable identifiers make conversations easier to reference and link within the knowledge base.



The project prefix associates the conversation with its project, while the numeric suffix provides ordering.



The identifier is generated by the local connector rather than by the browser extension.



\## DD-012 — Connector-Owned Identifier Generation



\### Decision



The local connector is responsible for determining the next conversation identifier.



\### Rationale



The connector is the component that owns the destination directory and filesystem state.



Generating identifiers at the storage boundary ensures that numbering is based on the actual files already present in the project conversation directory.



This avoids relying on browser-side state.



\## DD-013 — Existing-File Protection



\### Decision



The connector shall reject a save operation when the destination Markdown file already exists.



\### Rationale



The connector is intended to preserve captured knowledge rather than silently replace it.



Rejecting an existing destination:



\- Prevents accidental data loss.

\- Makes duplicate or conflicting writes visible.

\- Allows a future higher-level workflow to explicitly decide how an existing document should be handled.



\## DD-014 — Atomic File Writes



\### Decision



The connector writes content to a temporary file, synchronizes it, and then atomically replaces the destination.



\### Rationale



Writing directly to the final file could leave a partially written document if the process is interrupted during the write.



The temporary-file approach reduces the risk of incomplete Markdown documents appearing in the vault.



\## DD-015 — Request-Size Limit



\### Decision



The connector enforces a maximum request size.



\### Rationale



The connector is a local HTTP service and should not accept arbitrarily large requests.



A request-size limit:



\- Prevents accidental oversized requests.

\- Provides a basic resource-consumption safeguard.

\- Makes the service's input boundary explicit.



The current implementation limits requests to 5 MB.



\## DD-016 — Filename Validation



\### Decision



The connector validates generated or supplied Markdown filenames before writing them.



\### Rationale



Filesystem paths originate at an API boundary and therefore must be constrained before being used for file operations.



Filename validation helps ensure that:



\- Only expected Markdown filenames are accepted.

\- Unexpected path components are rejected.

\- File naming remains predictable.



\## DD-017 — HTML-to-Markdown Conversion in the Extension



\### Decision



Conversation message HTML is converted to Markdown before it reaches the connector.



\### Rationale



ChatGPT renders conversation content as HTML in the browser.



The Obsidian vault, however, stores Markdown.



Performing the conversion in the browser extension allows the captured representation to preserve the structure visible in the ChatGPT conversation.



The converter currently handles common structures such as:



\- Headings

\- Bold and italic text

\- Lists

\- Links

\- Code blocks

\- Blockquotes

\- Tables

\- Horizontal rules

\- Line breaks



\## DD-018 — Structured Conversation Documents



\### Decision



Captured conversations use a consistent Markdown structure containing:



```text

Summary

Key Points

Conversation

Related

```



\### Rationale



A consistent document structure makes captured conversations predictable and easier to process later.



It also provides defined locations for future enrichment such as summaries, key points, and relationships between conversations.



\## DD-019 — Separation of Conversation Archive and Future Knowledge Layer



\### Decision



The initial system treats captured conversations as an archive rather than immediately transforming every conversation into a durable knowledge note.



\### Rationale



A conversation archive preserves the original source material.



Future knowledge extraction can then operate on captured conversations without destroying or replacing the source conversation.



This creates a conceptual separation:



```text

ChatGPT Conversation

&#x20;       │

&#x20;       ▼

Conversation Archive

&#x20;       │

&#x20;       ▼

Future Knowledge Extraction

&#x20;       │

&#x20;       ▼

Durable Knowledge Notes

```



\## DD-020 — Incremental Development



\### Decision



The connector is being developed incrementally with small, testable milestones.



\### Rationale



The system contains multiple boundaries:



\- Browser

\- Extension

\- HTTP API

\- Local filesystem

\- Obsidian



Building and validating each layer independently reduces debugging complexity and makes failures easier to isolate.



The development sequence has therefore progressed through:



1\. Local connector

2\. API contract

3\. Validation tests

4\. Browser extension

5\. End-to-end capture

6\. Formatting validation

7\. Documentation

8\. Future indexing and knowledge features



\## Decision Status



| ID | Decision | Status |

|---|---|---|

| DD-001 | Local-first architecture | Accepted |

| DD-002 | Separate browser capture from storage | Accepted |

| DD-003 | Python connector | Accepted |

| DD-004 | Manifest V3 | Accepted |

| DD-005 | Isolated content script | Accepted |

| DD-006 | Background service worker | Accepted |

| DD-007 | Loopback-only binding | Accepted |

| DD-008 | HTTP/JSON | Accepted |

| DD-009 | Markdown storage | Accepted |

| DD-010 | YAML frontmatter | Accepted |

| DD-011 | Sequential conversation IDs | Accepted |

| DD-012 | Connector-owned ID generation | Accepted |

| DD-013 | Existing-file protection | Accepted |

| DD-014 | Atomic file writes | Accepted |

| DD-015 | Request-size limit | Accepted |

| DD-016 | Filename validation | Accepted |

| DD-017 | HTML-to-Markdown conversion | Accepted |

| DD-018 | Structured conversation documents | Accepted |

| DD-019 | Conversation archive / knowledge separation | Accepted |

| DD-020 | Incremental development | Accepted |

