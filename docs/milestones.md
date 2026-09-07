# Project Milestones

This document records the implementation milestones and validation
results for the ChatGPT Obsidian Connector.

The milestone history is maintained as the engineering progress record
for the project.

---

## M001 — Obsidian Structure & Project Index

**Status:** Complete

### Objective

Establish the Obsidian structure for storing ChatGPT conversations
and organize the project hierarchy.

### Implementation

Created the ChatGPT section:

```text
00 - ChatGPT/
├── Projects/
├── Technical/
├── Research/
├── Health/
├── Hobby/
├── Learning/
└── General/
---

## M005-003 — Project Selection & Creation

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