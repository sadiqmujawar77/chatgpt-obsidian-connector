chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "health") {
        fetch("http://127.0.0.1:8765/health")
            .then(response => response.json())
            .then(data => {
                sendResponse({ ok: true, data });
            })
            .catch(error => {
                sendResponse({
                    ok: false,
                    error: error.message
                });
            });

        return true;
    }

    if (message.action === "extract") {
        const conversation = message.data;

        console.log(
            "EXTRACT RECEIVED:",
            conversation.messages.length,
            "messages"
        );

        fetch("http://127.0.0.1:8765/conversation", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(conversation)
        })
            .then(async response => {
                const data = await response.json();

                sendResponse({
                    ok: response.ok,
                    status: response.status,
                    data
                });
            })
            .catch(error => {
                sendResponse({
                    ok: false,
                    error: error.message
                });
            });

        return true;
    }

    if (message.action === "save-test") {
        const filename = "P001-EXTENSION-TEST.md";
        const content = `---
id: P001-EXTENSION-TEST
title: Extension Connector Test
type: test
project: P001
date: 2026-09-06
tags:
  - test
  - extension
source: ChatGPT
---

# P001-EXTENSION-TEST — Extension Connector Test

This file was created by the ChatGPT Obsidian Connector browser extension.

`;

        fetch("http://127.0.0.1:8765/save", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                filename,
                content
            })
        })
            .then(async response => {
                const data = await response.json();

                sendResponse({
                    ok: response.ok,
                    status: response.status,
                    data
                });
            })
            .catch(error => {
                sendResponse({
                    ok: false,
                    error: error.message
                });
            });

        return true;
    }
});