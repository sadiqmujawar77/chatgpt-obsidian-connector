# Installation and Setup


## Overview

The ChatGPT Obsidian Connector is a local-first system consisting of:

ChatGPT -> Browser Extension -> Local Connector -> Obsidian Vault

The browser extension captures conversations from ChatGPT and sends them to a Python connector running locally on the same Windows computer. The connector writes structured Markdown files into the configured Obsidian vault.

## Prerequisites

The development environment requires:

- Windows
- Python 3.12
- Google Chrome or Microsoft Edge
- Obsidian
- An Obsidian vault

The current connector uses Python standard-library components and does not require a Python package installation for normal operation.

## Repository

Clone or obtain the repository:

git clone https://github.com/sadiqmujawar77/chatgpt-obsidian-connector.git
cd chatgpt-obsidian-connector

If the repository is already present:

cd C:\Users\Sadiq\chatgpt-obsidian-connector

## Obsidian Vault

The connector currently writes captured conversations into the Obsidian vault at:

C:\Users\Sadiq\iCloudDrive\iCloud~md~obsidian

Captured projects are stored under:

C:\Users\Sadiq\iCloudDrive\iCloud~md~obsidian\00 - ChatGPT\Projects

The expected vault structure includes:

00 - ChatGPT\
|-- Projects\
|-- Technical\
|-- Research\
|-- Health\
|-- Hobby\
|-- Learning\
|-- General\

Projects are stored under:

00 - ChatGPT\Projects\

Each project contains a Chats directory for captured conversations.

## Start the Local Connector

Open PowerShell in the repository:

cd C:\Users\Sadiq\chatgpt-obsidian-connector

Start the connector:

python .\connector\src\server.py

A successful startup displays the connector listening on http://127.0.0.1:8765.

Keep this PowerShell window running while using the browser extension.

To stop the connector, press Ctrl+C.

## Verify Connector Health

From another PowerShell window:

Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8765/health

A healthy connector returns HTTP status 200 and reports:

{"status": "ok", "service": "chatgpt-obsidian-connector"}

## Install the Browser Extension

The extension is an unpacked Manifest V3 extension.

### Microsoft Edge

1. Open Edge.
2. Open edge://extensions/.
3. Enable Developer mode.
4. Select Load unpacked.
5. Select the repository extension directory:

C:\Users\Sadiq\chatgpt-obsidian-connector\extension

6. Confirm that ChatGPT Obsidian Connector appears in the extensions list.

### Google Chrome

1. Open Chrome.
2. Open chrome://extensions/.
3. Enable Developer mode.
4. Select Load unpacked.
5. Select:

C:\Users\Sadiq\chatgpt-obsidian-connector\extension

6. Confirm that ChatGPT Obsidian Connector appears in the extensions list.

## Reloading After Code Changes

When extension source files change:

1. Open the browser extension management page.
2. Locate ChatGPT Obsidian Connector.
3. Select Reload.
4. Refresh the ChatGPT page.

Restart the connector when server.py changes.

## Using Conversation Capture

With the connector running and the extension loaded:

1. Open ChatGPT at https://chatgpt.com/.
2. Open the conversation to capture.
3. Use the capture controls provided by the extension.
4. Select the appropriate project.
5. Save the conversation.

Captured conversations are stored as Markdown under the project's Chats directory.

## Capture Modes

### Full Conversation

Use Save to Obsidian to capture the conversation.

The connector creates a new conversation document when necessary and incrementally updates an existing conversation when it has already been captured.

### Latest Response

Use Save Latest Response to capture the latest question/response pair.

If the response has already been captured, the connector avoids creating a duplicate.

### Selective Q/R Capture

Use Save this Q/R to capture an individual question/response pair without capturing the entire conversation.

## Project Selection

Conversation capture can target an existing project or create a new project through the capture interface.

Projects use identifiers such as:

P001
P002
P003

Conversation identifiers are sequential within each project:

P001-001
P001-002
P001-003

Each project contains a Chats directory where its conversation documents are stored.

The connector currently uses P001 as the default project.

## Conversation Files

Captured conversations are stored as Markdown documents with YAML frontmatter.

The document contains the conversation identifier, title, project, date, tags, source, summary, key points, conversation messages, and related conversation links.

Conversation relationships and project indexes are maintained as part of the capture workflow.

## Logging and Diagnostics

The connector writes diagnostic events to:

connector\connector.log

The log file is generated locally and excluded from Git.

Example diagnostic events include:

INFO | HTTP response
INFO | Conversation created
INFO | Conversation updated
WARNING | Conversation rejected
WARNING | Conversation conflict
ERROR | Conversation failed

Conversation contents and complete request bodies are not written to the diagnostic log.

## Troubleshooting

### Connector Does Not Start

Verify Python:

python --version

Check the connector source for syntax errors:

python -m py_compile .\connector\src\server.py

### Health Check Fails

Verify that the connector process is running:

python .\connector\src\server.py

Then test:

Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8765/health

### Extension Does Not Capture

Check the following:

1. The connector is running.
2. The extension is enabled.
3. ChatGPT is using https://chatgpt.com/.
4. The extension was reloaded after source-code changes.
5. The ChatGPT page was refreshed after reloading the extension.

### Capture Fails

Check the connector terminal for errors.

Then inspect connector\connector.log.

### Conversation Appears to Be Duplicated

The connector uses conversation and question fingerprints to prevent duplicate captures.

For an already-captured response, the expected result is that the existing pair is detected rather than appended again.

## Recovery

If the connector stops responding:

1. Stop the connector with Ctrl+C.
2. Start it again with: python .\connector\src\server.py
3. Verify the health endpoint.
4. Refresh ChatGPT if necessary.

Restarting the connector does not remove existing conversation files from the Obsidian vault.



## Development Workflow

Check Git status:

git status

Check Python syntax:

python -m py_compile .\connector\src\server.py

Check whitespace errors:

git diff --check

Review changes:

git diff

Commit changes:

git add .
git commit -m "description of change"

Push changes:

git push origin main

## Security Notes

The connector is designed for local operation.

It binds to 127.0.0.1, validates incoming conversation data, validates filenames, prevents accidental overwrites, uses atomic file writes, and limits request size.

The Obsidian vault does not require third-party cloud storage from the connector.

## Repository Layout

chatgpt-obsidian-connector/
|-- connector/
|   |-- src/
|       |-- server.py
|-- extension/
|   |-- manifest.json
|   |-- src/
|       |-- background.js
|       |-- content.js
|-- obsidian/
|-- tests/
|-- scripts/
|-- docs/
|-- .gitignore
|-- CHANGELOG.md
|-- LICENSE
|-- README.md

The local connector.log file is generated at runtime and excluded from Git.

## Related Documentation

- docs/architecture.md
- docs/data-model.md
- docs/design-decisions.md
- docs/development.md
- docs/milestones.md
- docs/protocol.md
- docs/requirements.md
- docs/security.md
