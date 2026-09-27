// ============================================================
// ChatGPT Obsidian Connector
// background.js
// ============================================================
//
// Responsibilities:
//
//   1. Receive messages from the content script.
//   2. Communicate with the local connector.
//   3. Return connector responses to the content script.
//
// The background service worker is the only extension component
// that communicates directly with the local connector.
//
// ============================================================


// ------------------------------------------------------------
// Message listener
// ------------------------------------------------------------

chrome.runtime.onMessage.addListener(
    (message, sender, sendResponse) => {


        // ----------------------------------------------------
        // Health check
        // ----------------------------------------------------

        if (message.action === "health") {

            fetch(
                "http://127.0.0.1:8765/health"
            )
                .then(response =>
                    response.json()
                )
                .then(data => {

                    sendResponse({
                        ok: true,
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


        // ----------------------------------------------------
        // Get available projects
        // ----------------------------------------------------

        if (message.action === "projects") {

            fetch(
                "http://127.0.0.1:8765/projects"
            )
                .then(async response => {

                    const data =
                        await response.json();

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


        // ----------------------------------------------------
        // Extract and save conversation
        // ----------------------------------------------------

        if (message.action === "extract") {

            const conversation =
                message.data;


            console.log(
                "EXTRACT RECEIVED:",
                conversation.messages.length,
                "messages"
            );


            fetch(
                "http://127.0.0.1:8765/conversation",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify(
                        conversation
                    )
                }
            )
                .then(async response => {

                    const data =
                        await response.json();

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
        // ----------------------------------------------------
        // Create a new project
        // ----------------------------------------------------

        if (message.action === "create-project") {

            fetch(
                "http://127.0.0.1:8765/projects",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify(
                        message.data
                    )
                }
            )
                .then(async response => {

                    const data =
                        await response.json();

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

        // ----------------------------------------------------
        // Obsidian read bridge
        // ----------------------------------------------------

        if (message.action === "obsidian-projects") {

            fetch(
                "http://127.0.0.1:8765/projects"
            )
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


        if (message.action === "obsidian-files") {

            const project = message.project;

            if (typeof project !== "string" || !project.trim()) {

                sendResponse({
                    ok: false,
                    error: "project is required"
                });

                return true;
            }

            fetch(
                "http://127.0.0.1:8765/projects/"
                + encodeURIComponent(project.trim())
                + "/files"
            )
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


        if (message.action === "obsidian-read") {

            const project = message.project;
            const filePath = message.path;

            if (
                typeof project !== "string" ||
                !project.trim()
            ) {

                sendResponse({
                    ok: false,
                    error: "project is required"
                });

                return true;
            }

            if (
                typeof filePath !== "string" ||
                !filePath.trim()
            ) {

                sendResponse({
                    ok: false,
                    error: "path is required"
                });

                return true;
            }

            const url =
                "http://127.0.0.1:8765/projects/"
                + encodeURIComponent(project.trim())
                + "/file?path="
                + encodeURIComponent(filePath.trim());

            fetch(url)
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


        if (message.action === "obsidian-search") {

            const project = message.project;
            const query = message.query;

            if (
                typeof project !== "string" ||
                !project.trim()
            ) {

                sendResponse({
                    ok: false,
                    error: "project is required"
                });

                return true;
            }

            if (
                typeof query !== "string" ||
                !query.trim()
            ) {

                sendResponse({
                    ok: false,
                    error: "query is required"
                });

                return true;
            }

            const url =
                "http://127.0.0.1:8765/projects/"
                + encodeURIComponent(project.trim())
                + "/search?q="
                + encodeURIComponent(query.trim());

            fetch(url)
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


        // ----------------------------------------------------
        // Legacy extension save test
        // ----------------------------------------------------

        if (message.action === "save-test") {

            const filename =
                "P001-EXTENSION-TEST.md";


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


            fetch(
                "http://127.0.0.1:8765/save",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        filename,
                        content
                    })
                }
            )
                .then(async response => {

                    const data =
                        await response.json();

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
    }
);