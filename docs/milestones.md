# Project Milestones

This document records the implementation milestones and validation
results for the ChatGPT Obsidian Connector.

The milestone history is maintained as the engineering progress record
for the project.

---

## M001 â€” Obsidian Structure & Project Index

**Status:** Complete

### Objective

Establish the Obsidian structure for storing ChatGPT conversations
and organize the project hierarchy.

### Implementation

Created the ChatGPT section:

```text
00 - ChatGPT/
â”œâ”€â”€ Projects/
â”œâ”€â”€ Technical/
â”œâ”€â”€ Research/
â”œâ”€â”€ Health/
â”œâ”€â”€ Hobby/
â”œâ”€â”€ Learning/
â””â”€â”€ General/
---

## M005-003 â€” Project Selection & Creation

**Status:** Complete

### Objective

Allow users to select an existing project or create a new project
during conversation capture.

### Implementation

- Added project listing through `GET /projects`.
- Added project-aware conversation routing through `/conversation`.
- Added project selection to the browser extension capture flow.
- Added `+ Create New Project` to the project selection dialog.
- Added project creation through `POST /projects`.
- Automatically assigns the next project ID (`P001`, `P002`, ...).
- Automatically creates the project `Chats` folder.
- Automatically selects a newly created project for the current capture.
- Added server-side project-name validation for Windows filesystem safety.
- Added validation for:
  - Empty project names
  - Invalid Windows filename characters
  - Trailing spaces and periods
  - Reserved Windows device names
  - Project names longer than 100 characters

### Validation

- Existing P001 project was listed and selectable.
- P002 project was selected and successfully used for conversation capture.
- Conversation was saved as `P002-001`.
- New project creation was tested end-to-end through the extension.
- New project was automatically assigned the next available project ID.
- Newly created project was automatically selected for the capture.
- Conversation was saved successfully as `P003-001` during the creation test.
- Invalid project names were rejected with HTTP 400 responses.
- Temporary test artifacts were removed from the Obsidian vault.

### Result

**PASS**

---

## M005-004 â€” Conversation Document Quality

**Status:** Complete

### Objective

Ensure captured ChatGPT conversations are stored as clean, self-contained
Obsidian Markdown documents with useful source metadata.

### Implementation

- Added the original ChatGPT conversation URL to YAML frontmatter.
- Updated conversation Markdown generation to receive the conversation URL.
- Preserved existing conversation structure and metadata.
- Continued using UTF-8 encoding for generated Markdown files.

### Validation

- Captured a real conversation as `P001-008`.
- Verified the generated Markdown file in the Obsidian vault.
- Verified the `url` property is present in YAML frontmatter.
- Verified the ChatGPT URL is recognized by Obsidian as a clickable property.
- Verified YAML frontmatter is correctly interpreted by Obsidian.
- Verified UTF-8 encoding by inspecting the generated file bytes.
- Verified the em dash renders correctly in Obsidian.
- Verified the conversation Markdown renders correctly.
- Verified temporary test project artifacts were not present in the project directory.

### Result

**PASS**

---

## M005-005 â€” Conversation Relationships & Navigation

**Status:** Complete

### Objective

Provide automatic navigation between conversations and maintain project-level conversation indexes.

### Implementation

- Automatically links each captured conversation to its previous conversation.
- Automatically updates the previous conversation with its Next link.
- Adds a Project link from each conversation to its project index.
- Maintains conversation relationships within the selected project.
- Automatically creates a project index when the first conversation is captured into a project that does not yet have one.
- Automatically maintains the project index conversation table after each conversation capture.
- Updates only the generated Related section when adding navigation links, preserving captured conversation content.
- Orders project-index conversations by conversation ID.

### Validation

- Verified bidirectional navigation across the P001 conversation chain.
- Verified P001-014 contains both Previous and Next links.
- Verified P001-015 contains the correct Previous and Project links and no Next link.
- Verified project indexes contain the expected conversation table.
- Created P003 as a clean project-index test.
- Verified automatic creation of P003 - Project Index.md.
- Verified P003-001 appears automatically in the project-index conversation table.
- Verified the generated project-index heading uses the correct UTF-8 em dash encoding.
- Verified the actual file bytes contain the correct UTF-8 sequence E2 80 94.
- Confirmed that the previously observed mojibake output was a PowerShell display/decoding issue rather than corruption in the generated Markdown file.

### Result

M005-005 passed functional validation and is complete.

---

## M005-006 â€” Selective & Incremental Conversation Capture

**Status: PASS**

Implemented selective and incremental conversation capture.

### Implemented

- Added **Save Latest Response** to the browser extension.
- Added capture modes:
  - `full` â€” capture the complete conversation.
  - `response` â€” capture only the latest User â†’ ChatGPT exchange.
- Added conversation pair normalization and stable pair markers.
- Added incremental merging into existing conversation files.
- Added idempotent response capture so repeated saves do not create duplicates.
- Added chronological insertion of newly captured pairs.
- Added existing-conversation detection using the original ChatGPT conversation URL.
- Preserved existing conversation content during incremental updates.
- Preserved conversation relationship/navigation metadata.
- Added response-capture handling for partially rendered ChatGPT conversations.
- Response capture no longer treats a browser-local pair index as the authoritative conversation index.
- Existing full-capture pair identity protection remains strict.

### Verification

Server-side testing verified:

- Selective response capture.
- Incremental capture.
- Q/R pair preservation.
- Stable pair identity.
- Chronological insertion.
- Duplicate prevention.
- Full capture followed by incremental response capture.
- Existing conversation detection.

Browser/Obsidian end-to-end testing verified:

- Extension loads without JavaScript syntax errors.
- `Save Latest Response` button appears.
- Project selection works.
- Response capture reaches the local connector.
- Connector returns HTTP 200 for response capture.
- Latest response is written to the correct P001 conversation.
- Markdown formatting is preserved.
- Existing `Related` navigation remains present.

### Final Result

**M005-006 PASS â€” Selective & Incremental Conversation Capture is operational end-to-end.**
