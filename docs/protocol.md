# Connector API Protocol

## Status

Draft

## Purpose

Define the HTTP API used by the browser extension to communicate with the local ChatGPT Obsidian Connector.

The protocol separates browser-side conversation capture from local filesystem storage.

## Base URL

http://127.0.0.1:8765

---

## GET /health

Checks whether the local connector is running.

### Request

GET /health

### Response

Status:

200 OK

Body:

{
  "status": "ok",
  "service": "chatgpt-obsidian-connector"
}

---

## POST /save

Creates a Markdown file in the configured ChatGPT project folder.

### Request

POST /save
Content-Type: application/json

Body:

{
  "filename": "example.md",
  "content": "# Example\n"
}

### Request Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `filename` | string | Yes | Destination Markdown filename |
| `content` | string | Yes | Complete Markdown document |

### Filename Rules

The connector:

- accepts Markdown filenames ending in `.md`
- adds `.md` when omitted
- rejects invalid filename characters
- limits filenames to 200 characters
- does not accept path separators
- does not allow directory traversal
- does not overwrite an existing file

---

### Success Response

Status:

201 Created

Body:

{
  "status": "saved",
  "path": "C:\\path\\to\\file.md"
}

### Existing File

If the destination already exists:

Status:

409 Conflict

Body:

{
  "error": "file already exists",
  "path": "C:\\path\\to\\file.md"
}

The existing file must remain unchanged.

### Invalid Request

For malformed or invalid requests:

Status:

400 Bad Request

Example:

{
  "error": "invalid filename"
}

### Request Too Large

Requests larger than the configured maximum request size must be rejected.

Current maximum:

5 MB

Status:

413 Content Too Large

### Unknown Endpoint

Unknown HTTP endpoints return:

Status:

404 Not Found

Example:

{
  "error": "not_found"
}

---

## Error Handling

The connector should return:

1. an appropriate HTTP status code
2. a JSON response body
3. a short machine-readable error description

The browser extension must not assume that every request succeeds.

---

## Security Requirements

The connector must:

- bind only to `127.0.0.1`
- validate all incoming request data
- enforce request-size limits
- reject unsafe filenames
- prevent directory traversal
- prevent accidental overwrites
- use atomic file writes
- avoid exposing the Obsidian vault over the network

The browser extension and connector should not rely on unrestricted CORS.

Authentication between the browser extension and connector may be added in a future protocol revision.

---

## Conversation API

A dedicated conversation endpoint is planned:

POST /conversation

This endpoint is not implemented yet.

Its purpose will be to accept structured conversation data rather than requiring the browser extension to construct the final filename and Markdown document itself.

The planned payload will contain information such as:

- conversation ID
- title
- conversation type
- project
- date
- tags
- messages
- source metadata

The exact schema will be defined before implementation.

---

## Protocol Evolution

Changes to the API should preserve backward compatibility where practical.

Breaking changes should:

- be documented
- update this protocol specification
- include corresponding tests
- update the browser extension
- use an explicit API version when necessary
