# Security

This document defines the security principles and controls for the
ChatGPT Obsidian Connector.

The connector is designed as a local-first system. Conversation data
is transferred from the browser extension to a local connector running
on the user's Windows machine and is then written to the local Obsidian
vault.

---

## Security Objectives

The connector should:

- Keep captured conversation data local.
- Avoid unnecessary third-party services.
- Restrict the local connector to localhost access.
- Validate all incoming requests.
- Prevent arbitrary filesystem writes.
- Prevent accidental overwriting of existing conversation files.
- Limit the size of incoming requests.
- Keep the browser extension and local connector separated by a
  controlled API boundary.

---

## Local-Only Connector

The connector binds to:

```text
127.0.0.1:8765