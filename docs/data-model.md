\# Data Model



This document defines the data structures used by the ChatGPT Obsidian Connector.



\## 1. Data Flow



Conversation data moves through the system in the following form:



```text

ChatGPT DOM

&#x20;   │

&#x20;   ▼

Browser Extension

&#x20;   │

&#x20;   │ Conversation Payload

&#x20;   ▼

Local Connector

&#x20;   │

&#x20;   │ Generated Markdown

&#x20;   ▼

Obsidian Vault

```



The browser extension is responsible for extracting and converting conversation content.



The local connector is responsible for validation, identifier generation, metadata generation, and filesystem storage.



\## 2. Conversation Payload



The browser extension sends a conversation payload to:



```http

POST /conversation

```



The payload has the following logical structure:



```json

{

&#x20; "title": "Example Conversation",

&#x20; "url": "https://chatgpt.com/c/example",

&#x20; "messages": \[

&#x20;   {

&#x20;     "role": "user",

&#x20;     "content": "Example user message."

&#x20;   },

&#x20;   {

&#x20;     "role": "assistant",

&#x20;     "content": "Example assistant response."

&#x20;   }

&#x20; ]

}

```



\## 3. Conversation Object



A conversation object contains:



| Field | Type | Required | Description |

|---|---|---|---|

| `title` | string | Yes | Conversation title |

| `url` | string | Yes | Source ChatGPT conversation URL |

| `messages` | array | Yes | Ordered list of conversation messages |



\### Title



The `title` field contains the conversation title obtained from the ChatGPT page.



The connector sanitizes the title before using it in the generated filename and Markdown heading.



\### URL



The `url` field contains the source ChatGPT conversation URL.



The URL identifies the source conversation from which the capture originated.



\### Messages



The `messages` field contains the ordered conversation messages.



The order of messages is preserved during capture.



\## 4. Message Object



Each message contains:



| Field | Type | Required | Description |

|---|---|---|---|

| `role` | string | Yes | Message author role |

| `content` | string | Yes | Markdown-formatted message content |



Example:



```json

{

&#x20; "role": "user",

&#x20; "content": "Explain the architecture."

}

```



An assistant message uses:



```json

{

&#x20; "role": "assistant",

&#x20; "content": "The architecture consists of..."

}

```



\## 5. Message Roles



The connector maps message roles into Markdown section headings.



```text

user

&#x20; ↓

\### User



assistant

&#x20; ↓

\### ChatGPT

```



Unknown roles are handled using a capitalized representation of the supplied role.



\## 6. Content Representation



Message content is converted from the HTML representation rendered by ChatGPT into Markdown by the browser extension.



The resulting Markdown may contain:



\- Headings

\- Bold text

\- Italic text

\- Ordered lists

\- Unordered lists

\- Links

\- Code blocks

\- Blockquotes

\- Tables

\- Horizontal rules

\- Line breaks



This conversion occurs before the conversation payload is sent to the connector.



\## 7. Conversation Identifier



The connector generates a project-specific conversation identifier.



For project `P001`:



```text

P001-001

P001-002

P001-003

...

```



The numeric component is three digits.



The connector determines the next identifier by examining existing project conversation files.



\## 8. Filename



The generated conversation filename follows the form:



```text

<ID> - <Title>.md

```



Example:



```text

P001-001 - Example Conversation.md

```



The title portion is sanitized before being included in the filename.



\## 9. YAML Frontmatter



Each generated conversation document contains YAML frontmatter.



Example:



```yaml

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



\### Frontmatter Fields



| Field | Type | Description |

|---|---|---|

| `id` | string | Conversation identifier |

| `title` | string | Conversation title |

| `type` | string | Document type |

| `project` | string | Associated project identifier |

| `date` | date | Capture date |

| `tags` | array | Obsidian tags associated with the document |

| `source` | string | Source system |



\## 10. Document Type



Captured conversations currently use:



```yaml

type: conversation

```



This distinguishes conversation archive documents from other potential document types.



Future document types may include durable knowledge notes or other project artifacts.



\## 11. Project Association



Project conversations contain a project identifier.



For the current project:



```yaml

project: P001

```



The project identifier connects the conversation to:



```text

P001 - ChatGPT Obsidian Connector

```



\## 12. Tags



The current generated conversation metadata includes:



```yaml

tags:

&#x20; - project

&#x20; - chatgpt

&#x20; - obsidian

```



Tags provide basic classification inside Obsidian.



A future implementation may introduce more sophisticated automatic tag generation.



\## 13. Generated Markdown Structure



The connector generates the following logical document structure:



```text

YAML Frontmatter

&#x20;      │

&#x20;      ▼

Title

&#x20;      │

&#x20;      ▼

Summary

&#x20;      │

&#x20;      ▼

Key Points

&#x20;      │

&#x20;      ▼

Conversation

&#x20;      │

&#x20;      ├── User

&#x20;      ├── ChatGPT

&#x20;      ├── User

&#x20;      └── ...

&#x20;      │

&#x20;      ▼

Related

```



\## 14. Conversation Document



Example generated document:



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



\# P001-001 — Example Conversation



\## Summary



Conversation captured from ChatGPT.



\## Key Points



\- To be reviewed and summarized.



\## Conversation



\### User



Explain the architecture.



\### ChatGPT



The architecture consists of a browser extension, local connector, and Obsidian vault.



\## Related



\- Previous

\- Next

\- Project

```



\## 15. Save API Data Model



The `/save` endpoint accepts a simpler payload.



Logical structure:



```json

{

&#x20; "filename": "example.md",

&#x20; "content": "# Example\\n"

}

```



\### Save Fields



| Field | Type | Required | Description |

|---|---|---|---|

| `filename` | string | Yes | Markdown filename |

| `content` | string | Yes | Markdown document content |



The `/save` endpoint does not generate conversation metadata or identifiers.



It is a lower-level Markdown file creation interface.



\## 16. Conversation API vs Save API



The two endpoints have different responsibilities.



| Capability | `/save` | `/conversation` |

|---|---:|---:|

| Accept Markdown | Yes | Generated internally |

| Accept title | No | Yes |

| Accept URL | No | Yes |

| Accept messages | No | Yes |

| Generate conversation ID | No | Yes |

| Generate frontmatter | No | Yes |

| Generate conversation structure | No | Yes |

| Prevent overwrite | Yes | Yes |

| Atomic write | Yes | Yes |



The `/conversation` endpoint is the higher-level capture interface used by the browser extension.



The `/save` endpoint provides a lower-level Markdown storage interface.



\## 17. Storage Model



Conversation files are stored in the project conversation directory:



```text

00 - ChatGPT/

└── Projects/

&#x20;   └── P001 - ChatGPT Obsidian Connector/

&#x20;       └── Chats/

&#x20;           ├── P001-001 - Example Conversation.md

&#x20;           ├── P001-002 - Another Conversation.md

&#x20;           └── ...

```



The filesystem is currently the authoritative storage mechanism for captured conversation documents.



\## 18. Data Integrity Rules



The connector applies the following rules before writing a conversation:



1\. Validate the request structure.

2\. Validate the conversation title.

3\. Validate the URL.

4\. Validate the messages array.

5\. Validate each message.

6\. Generate the next conversation identifier.

7\. Sanitize the title.

8\. Construct the destination filename.

9\. Verify that the destination does not already exist.

10\. Write the document using the atomic write process.



\## 19. Data Lifecycle



The current lifecycle is:



```text

ChatGPT Conversation

&#x20;       │

&#x20;       ▼

DOM Extraction

&#x20;       │

&#x20;       ▼

HTML → Markdown

&#x20;       │

&#x20;       ▼

Conversation Payload

&#x20;       │

&#x20;       ▼

Connector Validation

&#x20;       │

&#x20;       ▼

Identifier + Metadata

&#x20;       │

&#x20;       ▼

Markdown Generation

&#x20;       │

&#x20;       ▼

Atomic File Write

&#x20;       │

&#x20;       ▼

Obsidian Vault

```



\## 20. Future Data Model Extensions



The current model is intentionally minimal.



Future extensions may introduce:



\- Capture timestamps

\- Conversation status

\- User-defined tags

\- Automatically suggested categories

\- Previous/next conversation references

\- Project index references

\- Related-conversation references

\- Durable knowledge-note references

\- Content hashes

\- Capture/version metadata



These fields should be introduced without breaking existing Markdown documents.



\## 21. Compatibility Principle



The data model should remain compatible with plain Markdown and YAML.



The system should avoid requiring a proprietary database or binary format for the core conversation archive.



This ensures that captured conversations remain readable and portable independently of the connector software.

