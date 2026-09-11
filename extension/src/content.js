// ============================================================
// ChatGPT Obsidian Connector
// content.js
// ============================================================
//
// Runs as an isolated content script on chatgpt.com.
//
// Responsibilities:
//   1. Extract ChatGPT conversation messages from the DOM.
//   2. Convert message HTML to Markdown.
//   3. Send the conversation to the extension background worker.
//   4. Provide a user-facing "Save to Obsidian" button.
//
// The background worker is responsible for communicating with
// the local Obsidian connector at 127.0.0.1:8765.
//
// ============================================================


// ------------------------------------------------------------
// Diagnostic: confirm this is running in extension context
// ------------------------------------------------------------

console.log(
    "CONNECTOR CONTENT SCRIPT:",
    typeof chrome,
    typeof chrome?.runtime
);


// ------------------------------------------------------------
// Utility functions
// ------------------------------------------------------------

function normalizeWhitespace(text) {
    return text
        .replace(/\u00a0/g, " ")
        .replace(/[ \t]+\n/g, "\n")
        .replace(/\n[ \t]+/g, "\n")
        .replace(/[ \t]+/g, " ")
        .trim();
}


function escapeMarkdownText(text) {
    return text
        .replace(/\\/g, "\\\\")
        .replace(/([`*_[\]{}])/g, "\\$1");
}


function getTextContent(element) {
    return normalizeWhitespace(element.textContent || "");
}


// ------------------------------------------------------------
// HTML → Markdown converter
// ------------------------------------------------------------

function htmlToMarkdown(element) {

    function convertNode(node, context = {}) {

        if (node.nodeType === Node.TEXT_NODE) {
            const text = node.nodeValue || "";
            return text.replace(/\*/g, "\\*");
        }

        if (node.nodeType !== Node.ELEMENT_NODE) {
            return "";
        }

        const tag = node.tagName.toLowerCase();

        // ----------------------------------------------------
        // Elements that should not appear in the conversation
        // ----------------------------------------------------

        if (
            tag === "button" ||
            tag === "svg" ||
            tag === "nav" ||
            tag === "textarea" ||
            tag === "input" ||
            tag === "form"
        ) {
            return "";
        }


        // ----------------------------------------------------
        // Code blocks
        // ----------------------------------------------------

        if (tag === "pre") {

            const codeElement = node.querySelector("code");

            const code = (
                codeElement
                    ? codeElement.textContent
                    : node.textContent
            ).replace(/\n$/, "");

            let language = "";

            if (codeElement) {
                const className =
                    codeElement.getAttribute("class") || "";

                const match = className.match(
                    /language-([A-Za-z0-9_-]+)/
                );

                if (match) {
                    language = match[1];
                }
            }

            return `\n\n\`\`\`${language}\n${code}\n\`\`\`\n\n`;
        }


        // ----------------------------------------------------
        // Inline code
        // ----------------------------------------------------

        if (tag === "code") {
            return `\`${node.textContent || ""}\``;
        }


        // ----------------------------------------------------
        // Headings
        // ----------------------------------------------------

        if (/^h[1-6]$/.test(tag)) {

            const level = Number(tag.substring(1));

            const content = Array.from(node.childNodes)
                .map(child => convertNode(child, context))
                .join("")
                .trim();

            return `\n\n${"#".repeat(level)} ${content}\n\n`;
        }


        // ----------------------------------------------------
        // Bold / strong
        // ----------------------------------------------------

        if (tag === "strong" || tag === "b") {

            const content = Array.from(node.childNodes)
                .map(child => convertNode(child, context))
                .join("")
                .trim();

            if (!content) {
                return "";
            }

            return `**${content}**`;
        }


        // ----------------------------------------------------
        // Italic / emphasis
        // ----------------------------------------------------

        if (tag === "em" || tag === "i") {

            const content = Array.from(node.childNodes)
                .map(child => convertNode(child, context))
                .join("")
                .trim();

            if (!content) {
                return "";
            }

            return `*${content}*`;
        }


        // ----------------------------------------------------
        // Strikethrough
        // ----------------------------------------------------

        if (tag === "del" || tag === "s" || tag === "strike") {

            const content = Array.from(node.childNodes)
                .map(child => convertNode(child, context))
                .join("")
                .trim();

            if (!content) {
                return "";
            }

            return `~~${content}~~`;
        }


        // ----------------------------------------------------
        // Links
        // ----------------------------------------------------

        if (tag === "a") {

            const href = node.getAttribute("href") || "";

            const content = Array.from(node.childNodes)
                .map(child => convertNode(child, context))
                .join("")
                .trim();

            if (!content) {
                return href;
            }

            if (!href) {
                return content;
            }

            return `[${content}](${href})`;
        }


        // ----------------------------------------------------
        // Blockquote
        // ----------------------------------------------------

        if (tag === "blockquote") {

            const content = Array.from(node.childNodes)
                .map(child => convertNode(child, context))
                .join("")
                .trim();

            if (!content) {
                return "";
            }

            const lines = content
                .split("\n")
                .map(line => `> ${line}`)
                .join("\n");

            return `\n\n${lines}\n\n`;
        }


        // ----------------------------------------------------
        // Line break
        // ----------------------------------------------------

        if (tag === "br") {
            return "\n";
        }


        // ----------------------------------------------------
        // Horizontal rule
        // ----------------------------------------------------

        if (tag === "hr") {
            return "\n\n---\n\n";
        }


        // ----------------------------------------------------
        // Tables
        // ----------------------------------------------------

        if (tag === "table") {
            return convertTable(node);
        }


        // ----------------------------------------------------
        // Unordered list
        // ----------------------------------------------------

        if (tag === "ul") {

            const items = Array.from(node.children)
                .filter(child =>
                    child.tagName.toLowerCase() === "li"
                )
                .map(li => {

                    const content = Array.from(li.childNodes)
                        .map(child =>
                            convertNode(child, {
                                ...context,
                                listItem: true
                            })
                        )
                        .join("")
                        .trim();

                    return `- ${content}`;
                });

            return `\n\n${items.join("\n")}\n\n`;
        }


        // ----------------------------------------------------
        // Ordered list
        // ----------------------------------------------------

        if (tag === "ol") {

            let number = 1;

            const items = Array.from(node.children)
                .filter(child =>
                    child.tagName.toLowerCase() === "li"
                )
                .map(li => {

                    const content = Array.from(li.childNodes)
                        .map(child =>
                            convertNode(child, {
                                ...context,
                                listItem: true
                            })
                        )
                        .join("")
                        .trim();

                    return `${number++}. ${content}`;
                });

            return `\n\n${items.join("\n")}\n\n`;
        }


        // ----------------------------------------------------
        // List item
        // ----------------------------------------------------

        if (tag === "li") {

            return Array.from(node.childNodes)
                .map(child => convertNode(child, context))
                .join("");
        }


        // ----------------------------------------------------
        // Paragraph
        // ----------------------------------------------------

        if (tag === "p") {

            const content = Array.from(node.childNodes)
                .map(child => convertNode(child, context))
                .join("")
                .trim();

            if (!content) {
                return "";
            }

            return `\n\n${content}\n\n`;
        }


        // ----------------------------------------------------
        // Div / span / generic containers
        // ----------------------------------------------------

        if (
            tag === "div" ||
            tag === "section" ||
            tag === "article" ||
            tag === "main" ||
            tag === "span"
        ) {

            const content = Array.from(node.childNodes)
                .map(child => convertNode(child, context))
                .join("");

            return content;
        }


        // ----------------------------------------------------
        // Table row
        // ----------------------------------------------------

        if (tag === "tr") {

            const cells = Array.from(node.children)
                .filter(child => {
                    const childTag =
                        child.tagName.toLowerCase();

                    return (
                        childTag === "td" ||
                        childTag === "th"
                    );
                })
                .map(cell =>
                    Array.from(cell.childNodes)
                        .map(child =>
                            convertNode(child, context)
                        )
                        .join("")
                        .replace(/\|/g, "\\|")
                        .replace(/\n+/g, " ")
                        .trim()
                );

            return `| ${cells.join(" | ")} |\n`;
        }


        // ----------------------------------------------------
        // Table cells
        // ----------------------------------------------------

        if (tag === "td" || tag === "th") {

            return Array.from(node.childNodes)
                .map(child => convertNode(child, context))
                .join("");
        }


        // ----------------------------------------------------
        // Default: recursively process children
        // ----------------------------------------------------

        return Array.from(node.childNodes)
            .map(child => convertNode(child, context))
            .join("");
    }


    // --------------------------------------------------------
    // Table conversion
    // --------------------------------------------------------

    function convertTable(table) {

        const rows = Array.from(
            table.querySelectorAll("tr")
        );

        if (!rows.length) {
            return "";
        }

        const matrix = rows.map(row => {

            return Array.from(row.children)
                .filter(cell => {
                    const tag =
                        cell.tagName.toLowerCase();

                    return tag === "td" || tag === "th";
                })
                .map(cell =>
                    Array.from(cell.childNodes)
                        .map(child =>
                            convertNode(child, {})
                        )
                        .join("")
                        .replace(/\|/g, "\\|")
                        .replace(/\n+/g, " ")
                        .trim()
                );
        });

        if (!matrix.length) {
            return "";
        }

        const columnCount = Math.max(
            ...matrix.map(row => row.length)
        );

        if (!columnCount) {
            return "";
        }

        const normalizedRows = matrix.map(row => {

            const copy = [...row];

            while (copy.length < columnCount) {
                copy.push("");
            }

            return copy;
        });

        const header = normalizedRows[0];

        const separator = Array(columnCount)
            .fill("---");

        const lines = [];

        lines.push(
            `| ${header.join(" | ")} |`
        );

        lines.push(
            `| ${separator.join(" | ")} |`
        );

        for (let i = 1; i < normalizedRows.length; i++) {

            lines.push(
                `| ${normalizedRows[i].join(" | ")} |`
            );
        }

        return `\n\n${lines.join("\n")}\n\n`;
    }


    // --------------------------------------------------------
    // Convert root element
    // --------------------------------------------------------
    //
    // ChatGPT can occasionally place another message element
    // inside the DOM subtree of the message currently being
    // extracted. Clone the message first and remove any nested
    // message-role elements so the converter cannot consume the
    // following User/Assistant message.
    //
    // This keeps the extraction boundary tied to the selected
    // message instead of relying on ChatGPT's current DOM layout.

    const root = element.cloneNode(true);

    root.querySelectorAll(
        "[data-message-author-role]"
    ).forEach(nestedMessage => {
        nestedMessage.remove();
    });

    let markdown = Array.from(root.childNodes)
        .map(node => convertNode(node, {}))
        .join("");

    // Normalize excessive blank lines.

    markdown = markdown
        .replace(/\r\n/g, "\n")
        .replace(/\n{3,}/g, "\n\n")
        .trim();

    return markdown;
}


// ------------------------------------------------------------
// Conversation extraction
// ------------------------------------------------------------

function extractConversation() {

    const messages = [
        ...document.querySelectorAll(
            "[data-message-author-role]"
        )
    ].map(element => {

        const role =
            element.getAttribute(
                "data-message-author-role"
            );

        const content = htmlToMarkdown(element);

        return {
            role,
            content
        };
    });

    return {
        title: document.title,
        url: location.href,
        messages
    };
}

// Convert the extracted role/content stream into stable chronological
// User -> ChatGPT pairs for M005-006 selective/incremental capture.
function messagesToPairs(messages) {
    const pairs = [];
    let currentUser = null;

    for (const message of messages) {
        const role = message?.role;
        const content = typeof message?.content === "string"
            ? message.content.trim()
            : "";

        if (role === "user") {
            if (currentUser !== null) {
                pairs.push({
                    index: pairs.length + 1,
                    user: currentUser,
                    assistant: ""
                });
            }

            currentUser = content;
            continue;
        }

        if (role === "assistant" && currentUser !== null) {
            pairs.push({
                index: pairs.length + 1,
                user: currentUser,
                assistant: content
            });
            currentUser = null;
        }
    }

    // Preserve a final unanswered user message as a pair with an empty
    // assistant response. This keeps the capture lossless if the user saves
    // while ChatGPT is still generating.
    if (currentUser !== null) {
        pairs.push({
            index: pairs.length + 1,
            user: currentUser,
            assistant: ""
        });
    }

    return pairs;
}

function buildCaptureData(conversation, captureMode) {
    const pairs = messagesToPairs(conversation.messages || []);

    if (captureMode === "response") {
        if (!pairs.length) {
            return {
                captureMode,
                pairs: []
            };
        }

        return {
            captureMode,
            pairs: [pairs[pairs.length - 1]]
        };
    }

    return {
        captureMode: "full",
        pairs
    };
}


// ------------------------------------------------------------
// Selective Q/R capture
// ------------------------------------------------------------

function saveSelectedPair(button, pair) {

    const originalText = button.textContent;

    button.disabled = true;
    button.textContent = "Selecting project...";

    const conversation =
        extractConversation();

    selectProject()
        .then(project => {

            conversation.project = project;

            button.textContent =
                "Saving Q/R...";

            chrome.runtime.sendMessage(
                {
                    action: "extract",
                    data: {
                        ...conversation,
                        capture_mode: "pair",
                        pairs: [pair]
                    }
                },
                response => {

                    if (chrome.runtime.lastError) {

                        console.error(
                            "ChatGPT Obsidian Connector: selective save failed",
                            chrome.runtime.lastError
                        );

                        button.disabled = false;
                        button.textContent = originalText;

                        return;
                    }

                    if (
                        !response ||
                        !response.ok
                    ) {

                        console.error(
                            "ChatGPT Obsidian Connector: selective save failed",
                            response
                        );

                        button.disabled = false;
                        button.textContent = originalText;

                        return;
                    }

                    const data =
                        response.data || {};

                    const id =
                        data.id || "";

                    const addedPairs =
                        Number(data.added_pairs || 0);

                    const updatedPairs =
                        Number(data.updated_pairs || 0);

                    const checkmark =
                        "\u2713";

                    if (addedPairs > 0) {

                        button.textContent =
                            id
                                ? `${checkmark} Q/R captured - ${id}`
                                : `${checkmark} Q/R captured`;

                    } else if (updatedPairs > 0) {

                        button.textContent =
                            id
                                ? `${checkmark} Q/R updated - ${id}`
                                : `${checkmark} Q/R updated`;

                    } else {

                        button.textContent =
                            id
                                ? `${checkmark} Already captured - ${id}`
                                : `${checkmark} Already captured`;
                    }

                    button.style.background =
                        "#1f7a4d";

                    setTimeout(
                        () => {
                            button.disabled = false;
                        },
                        4000
                    );
                }
            );
        })
        .catch(error => {

            console.error(
                "ChatGPT Obsidian Connector: selective project/save failed",
                error
            );

            button.disabled = false;
            button.textContent = originalText;
        });
}


function createSelectivePairButtons() {

    const messages = [
        ...document.querySelectorAll(
            "[data-message-author-role]"
        )
    ];

    if (messages.length < 2) {
        return;
    }

    const pairs = messagesToPairs(
        messages.map(element => ({
            role:
                element.getAttribute(
                    "data-message-author-role"
                ),
            content:
                htmlToMarkdown(element)
        }))
    );

    if (!pairs.length) {
        return;
    }

    let pairIndex = 0;

    for (
        let i = 0;
        i < messages.length;
        i++
    ) {

        const userElement =
            messages[i];

        if (
            userElement.getAttribute(
                "data-message-author-role"
            ) !== "user"
        ) {
            continue;
        }

        const assistantElement =
            messages[i + 1];

        if (
            !assistantElement ||
            assistantElement.getAttribute(
                "data-message-author-role"
            ) !== "assistant"
        ) {
            continue;
        }

        const pair =
            pairs[pairIndex++];

        if (!pair) {
            continue;
        }

        if (
            assistantElement.parentElement &&
            assistantElement.parentElement.querySelector(
                `[data-chatgpt-obsidian-pair-fingerprint="${pair.fingerprint}"]`
            )
        ) {
            continue;
        }

        const button =
            document.createElement("button");

        button.type = "button";

        button.dataset.chatgptObsidianPairFingerprint =
            pair.fingerprint;

        button.textContent =
            "Save this Q/R";

        button.style.display =
            "block";

        button.style.marginTop =
            "8px";

        button.style.marginBottom =
            "8px";

        button.style.padding =
            "4px 10px";

        button.style.borderRadius =
            "6px";

        button.style.border =
            "1px solid rgba(255,255,255,0.2)";

        button.style.background =
            "#2f6fed";

        button.style.color =
            "#ffffff";

        button.style.fontSize =
            "12px";

        button.style.cursor =
            "pointer";

        button.style.zIndex =
            "2147483647";

        button.addEventListener(
            "click",
            () => {
                saveSelectedPair(
                    button,
                    pair
                );
            }
        );

        /*
         * Insert the button AFTER the assistant message element.
         * Do not append it to the assistant's parent because ChatGPT's
         * current DOM can use that parent as a layout wrapper whose
         * visual order does not match DOM child order.
         */
        assistantElement.insertAdjacentElement(
            "afterend",
            button
        );
    }
}




// ------------------------------------------------------------
// Window message bridge
// ------------------------------------------------------------
//
// This bridge allows page-context testing / future UI code to
// request an extraction without exposing the connector directly
// to the ChatGPT page.
//
// Actual connector communication still happens through the
// extension background service worker.
// ------------------------------------------------------------

window.addEventListener(
    "message",
    event => {

        if (event.source !== window) {
            return;
        }

        if (
            !event.data ||
            event.data.source !==
                "chatgpt-obsidian-connector"
        ) {
            return;
        }


        // ----------------------------------------------------
        // Extract and save
        // ----------------------------------------------------

        if (event.data.action === "extract") {

            console.log(
                "CONNECTOR: extract request received"
            );

            const conversation =
                extractConversation();

            console.log(
                "CONNECTOR: extracted",
                conversation.messages.length,
                "messages"
            );

            chrome.runtime.sendMessage(
                {
                    action: "extract",
                    data: conversation
                },
                response => {

                    console.log(
                        "CONNECTOR: background response",
                        response
                    );

                    window.postMessage(
                        {
                            source:
                                "chatgpt-obsidian-connector",
                            type: "extract-result",
                            result: response
                        },
                        "*"
                    );
                }
            );

            return;
        }


        // ----------------------------------------------------
        // Preview only
        // ----------------------------------------------------

        if (event.data.action === "preview") {

            const conversation =
                extractConversation();

            window.postMessage(
                {
                    source:
                        "chatgpt-obsidian-connector",
                    type: "preview-result",
                    result: conversation
                },
                "*"
            );

            return;
        }


        // ----------------------------------------------------
        // Legacy extension save test
        // ----------------------------------------------------

        if (event.data.action === "save-test") {

            chrome.runtime.sendMessage(
                {
                    action: "save-test"
                },
                response => {

                    window.postMessage(
                        {
                            source:
                                "chatgpt-obsidian-connector",
                            type: "save-test-result",
                            result: response
                        },
                        "*"
                    );
                }
            );

            return;
        }
    }
);


// ------------------------------------------------------------
// User-facing Save to Obsidian button
// ------------------------------------------------------------

function createSaveButton() {

    // Do not create the button more than once.

    if (
        document.getElementById(
            "chatgpt-obsidian-save-button"
        )
    ) {
        return;
    }

    const button =
        document.createElement("button");

    button.id =
        "chatgpt-obsidian-save-button";

    button.type = "button";

    button.textContent =
        "Save to Obsidian";

    const responseButton =
        document.createElement("button");

    responseButton.id =
        "chatgpt-obsidian-save-response-button";

    responseButton.type = "button";

    responseButton.textContent =
        "Save Latest Response";


    // --------------------------------------------------------
    // Position
    // --------------------------------------------------------

    button.style.position = "fixed";
    button.style.right = "24px";
    button.style.bottom = "24px";

    responseButton.style.position = "fixed";
    responseButton.style.right = "24px";
    responseButton.style.bottom = "70px";

    responseButton.style.zIndex =
        "2147483647";

    button.style.zIndex =
        "2147483647";


    // --------------------------------------------------------
    // Appearance
    // --------------------------------------------------------

    button.style.padding =
        "10px 16px";

    button.style.border =
        "1px solid rgba(255,255,255,0.2)";

    button.style.borderRadius =
        "10px";

    button.style.background =
        "#2f6fed";

    button.style.color =
        "#ffffff";

    button.style.fontFamily =
        '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';

    button.style.fontSize =
        "14px";

    button.style.fontWeight =
        "600";

    button.style.cursor =
        "pointer";

    button.style.boxShadow =
        "0 4px 14px rgba(0, 0, 0, 0.25)";

    button.style.transition =
        "opacity 0.15s ease, transform 0.15s ease";

    responseButton.style.padding =
        "9px 14px";

    responseButton.style.border =
        "1px solid rgba(255,255,255,0.2)";

    responseButton.style.borderRadius =
        "10px";

    responseButton.style.background =
        "#202123";

    responseButton.style.color =
        "#ffffff";

    responseButton.style.fontFamily =
        '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';

    responseButton.style.fontSize =
        "13px";

    responseButton.style.fontWeight =
        "600";

    responseButton.style.cursor =
        "pointer";

    responseButton.style.boxShadow =
        "0 4px 14px rgba(0, 0, 0, 0.25)";

    responseButton.style.transition =
        "opacity 0.15s ease, transform 0.15s ease";


    // --------------------------------------------------------
    // Hover
    // --------------------------------------------------------

    button.addEventListener(
        "mouseenter",
        () => {

            if (!button.disabled) {
                button.style.transform =
                    "translateY(-1px)";
            }
        }
    );


    button.addEventListener(
        "mouseleave",
        () => {

            button.style.transform =
                "translateY(0)";
        }
    );

    responseButton.addEventListener(
        "mouseenter",
        () => {

            if (!responseButton.disabled) {
                responseButton.style.transform =
                    "translateY(-1px)";
            }
        }
    );

    responseButton.addEventListener(
        "mouseleave",
        () => {

            responseButton.style.transform =
                "translateY(0)";
        }
    );


    // --------------------------------------------------------
    // Click
    // --------------------------------------------------------

    button.addEventListener(
        "click",
        () => {

            saveCurrentConversation(button, "full");
        }
    );

    responseButton.addEventListener(
        "click",
        () => {

            saveCurrentConversation(responseButton, "response");
        }
    );


    document.body.appendChild(button);
    document.body.appendChild(responseButton);

    console.log(
        "ChatGPT Obsidian Connector: Save button added."
    );
}
// ------------------------------------------------------------
// Project selection
// ------------------------------------------------------------

function selectProject() {

    return new Promise((resolve, reject) => {

        console.log(
            "ChatGPT Obsidian Connector: loading projects..."
        );

        chrome.runtime.sendMessage(
            {
                action: "projects"
            },
            response => {

                if (
                    chrome.runtime.lastError
                ) {
                    console.error(
                        "ChatGPT Obsidian Connector: project request failed",
                        chrome.runtime.lastError
                    );

                    reject(
                        new Error(
                            chrome.runtime.lastError.message
                        )
                    );

                    return;
                }

                if (
                    !response ||
                    !response.ok ||
                    !response.data?.projects
                ) {
                    console.error(
                        "ChatGPT Obsidian Connector: invalid project response",
                        response
                    );

                    reject(
                        new Error(
                            "Unable to load projects."
                        )
                    );

                    return;
                }

                const projects =
                    response.data.projects;

                if (!projects.length) {

                    reject(
                        new Error(
                            "No projects found."
                        )
                    );

                    return;
                }

                // ------------------------------------------------
                // Overlay
                // ------------------------------------------------

                const overlay =
                    document.createElement("div");

                overlay.id =
                    "chatgpt-obsidian-project-overlay";

                overlay.style.position =
                    "fixed";

                overlay.style.inset =
                    "0";

                overlay.style.zIndex =
                    "2147483647";

                overlay.style.background =
                    "rgba(0, 0, 0, 0.55)";

                overlay.style.display =
                    "flex";

                overlay.style.alignItems =
                    "center";

                overlay.style.justifyContent =
                    "center";

                // ------------------------------------------------
                // Dialog
                // ------------------------------------------------

                const dialog =
                    document.createElement("div");

                dialog.style.width =
                    "360px";

                dialog.style.maxWidth =
                    "calc(100vw - 40px)";

                dialog.style.padding =
                    "24px";

                dialog.style.borderRadius =
                    "12px";

                dialog.style.background =
                    "#202123";

                dialog.style.color =
                    "#ffffff";

                dialog.style.fontFamily =
                    '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';

                dialog.style.boxShadow =
                    "0 10px 40px rgba(0, 0, 0, 0.4)";

                // ------------------------------------------------
                // Title
                // ------------------------------------------------

                const title =
                    document.createElement("div");

                title.textContent =
                    "Save conversation";

                title.style.fontSize =
                    "18px";

                title.style.fontWeight =
                    "600";

                title.style.marginBottom =
                    "8px";

                // ------------------------------------------------
                // Description
                // ------------------------------------------------

                const description =
                    document.createElement("div");

                description.textContent =
                    "Select the project where this conversation should be saved.";

                description.style.fontSize =
                    "14px";

                description.style.lineHeight =
                    "1.4";

                description.style.color =
                    "#c7c7c7";

                description.style.marginBottom =
                    "16px";

                // ------------------------------------------------
                // Select
                // ------------------------------------------------

                const select =
                    document.createElement("select");

                select.style.width =
                    "100%";

                select.style.padding =
                    "10px 12px";

                select.style.border =
                    "1px solid #555";

                select.style.borderRadius =
                    "8px";

                select.style.background =
                    "#2b2d31";

                select.style.color =
                    "#ffffff";

                select.style.fontSize =
                    "14px";

                select.style.boxSizing =
                    "border-box";

                projects.forEach(
                    project => {

                        const option =
                            document.createElement("option");

                        option.value =
                            project.id;

                        option.textContent =
                            project.name ||
                            project.id;

                        select.appendChild(
                            option
                        );
                    }
                );

                // ------------------------------------------------
                // Create Project Button
                // ------------------------------------------------

                const createProjectButton =
                    document.createElement("button");

                createProjectButton.type =
                    "button";

                createProjectButton.textContent =
                    "+ Create New Project";

                createProjectButton.style.width =
                    "100%";

                createProjectButton.style.marginTop =
                    "12px";

                createProjectButton.style.padding =
                    "9px 14px";

                createProjectButton.style.border =
                    "1px solid #555";

                createProjectButton.style.borderRadius =
                    "8px";

                createProjectButton.style.background =
                    "transparent";

                createProjectButton.style.color =
                    "#ffffff";

                createProjectButton.style.cursor =
                    "pointer";

                // ------------------------------------------------
                // Buttons
                // ------------------------------------------------

                const buttons =
                    document.createElement("div");

                buttons.style.display =
                    "flex";

                buttons.style.justifyContent =
                    "flex-end";

                buttons.style.gap =
                    "8px";

                buttons.style.marginTop =
                    "20px";

                const cancelButton =
                    document.createElement("button");

                cancelButton.type =
                    "button";

                cancelButton.textContent =
                    "Cancel";

                cancelButton.style.padding =
                    "9px 14px";

                cancelButton.style.border =
                    "1px solid #555";

                cancelButton.style.borderRadius =
                    "8px";

                cancelButton.style.background =
                    "transparent";

                cancelButton.style.color =
                    "#ffffff";

                cancelButton.style.cursor =
                    "pointer";

                const saveButton =
                    document.createElement("button");

                saveButton.type =
                    "button";

                saveButton.textContent =
                    "Save";

                saveButton.style.padding =
                    "9px 14px";

                saveButton.style.border =
                    "none";

                saveButton.style.borderRadius =
                    "8px";

                saveButton.style.background =
                    "#2f6fed";

                saveButton.style.color =
                    "#ffffff";

                saveButton.style.fontWeight =
                    "600";

                saveButton.style.cursor =
                    "pointer";

                // ------------------------------------------------
                // Create Project
                // ------------------------------------------------

                createProjectButton.addEventListener(
                    "click",
                    () => {

                        const conversationTitle =
                            extractConversation().title || "";

                        const name =
                            window.prompt(
                                "Enter the new project name:",
                                conversationTitle
                            );

                        if (name === null) {
                            return;
                        }

                        const projectName =
                            name.trim();

                        if (!projectName) {

                            window.alert(
                                "Project name cannot be empty."
                            );

                            return;
                        }

                        createProjectButton.disabled =
                            true;

                        createProjectButton.textContent =
                            "Creating...";

                        chrome.runtime.sendMessage(
                            {
                                action: "create-project",
                                data: {
                                    name: projectName
                                }
                            },
                            createResponse => {

                                createProjectButton.disabled =
                                    false;

                                createProjectButton.textContent =
                                    "+ Create New Project";

                                if (
                                    chrome.runtime.lastError
                                ) {
                                    window.alert(
                                        "Unable to create project: " +
                                        chrome.runtime.lastError.message
                                    );

                                    return;
                                }

                                if (
                                    !createResponse ||
                                    !createResponse.ok
                                ) {
                                    const message =
                                        createResponse?.data?.error ||
                                        createResponse?.error ||
                                        "Unable to create project.";

                                    window.alert(
                                        message
                                    );

                                    return;
                                }

                                const newProject =
                                    createResponse.data;

                                const option =
                                    document.createElement("option");

                                option.value =
                                    newProject.id;

                                option.textContent =
                                    newProject.name ||
                                    newProject.id;

                                select.appendChild(
                                    option
                                );

                                select.value =
                                    newProject.id;

                                console.log(
                                    "ChatGPT Obsidian Connector: project created.",
                                    newProject
                                );
                            }
                        );
                    }
                );

                // ------------------------------------------------
                // Cancel
                // ------------------------------------------------

                cancelButton.addEventListener(
                    "click",
                    () => {

                        overlay.remove();

                        resolve(null);
                    }
                );

                // ------------------------------------------------
                // Save
                // ------------------------------------------------

                saveButton.addEventListener(
                    "click",
                    () => {

                        const projectId =
                            select.value;

                        overlay.remove();

                        resolve(
                            projectId
                        );
                    }
                );

                // ------------------------------------------------
                // Assemble dialog
                // ------------------------------------------------

                buttons.appendChild(
                    cancelButton
                );

                buttons.appendChild(
                    saveButton
                );

                dialog.appendChild(
                    title
                );

                dialog.appendChild(
                    description
                );

                dialog.appendChild(
                    select
                );

                dialog.appendChild(
                    createProjectButton
                );

                dialog.appendChild(
                    buttons
                );

                overlay.appendChild(
                    dialog
                );

                document.body.appendChild(
                    overlay
                );

                // ------------------------------------------------
                // Focus
                // ------------------------------------------------

                select.focus();

                console.log(
                    "ChatGPT Obsidian Connector: project selector displayed.",
                    projects
                );
            }
        );
    });
}


// ------------------------------------------------------------
// Save current conversation
// ------------------------------------------------------------

function saveCurrentConversation(button, captureMode = "full") {
	
    const defaultButtonText =
        captureMode === "response"
            ? "Save Latest Response"
            : "Save to Obsidian";

    const defaultButtonBackground =
        captureMode === "response"
            ? "#202123"
            : "#2f6fed";

    // Prevent accidental double-clicks.
    if (button.disabled) {
        return;
    }

	
    // --------------------------------------------------------
    // Selecting project state
    // --------------------------------------------------------

    button.disabled = true;

    button.style.cursor =
        "wait";

    button.style.opacity =
        "0.7";

    button.textContent =
        "Selecting project…";


    console.log(
        "ChatGPT Obsidian Connector: selecting project..."
    );


    // --------------------------------------------------------
    // Select project
    // --------------------------------------------------------

    selectProject()
        .then(projectId => {

            // User cancelled.
            if (!projectId) {

                button.disabled = false;

                button.style.cursor =
                    "pointer";

                button.style.opacity =
                    "1";

                button.textContent =
                    defaultButtonText;

                return;
            }


            continueSavingConversation(
                button,
                projectId,
                captureMode
            );
        })
        .catch(error => {

            console.error(
                "ChatGPT Obsidian Connector: unable to load projects",
                error
            );


            button.disabled = false;

            button.style.cursor =
                "pointer";

            button.style.opacity =
                "1";

            button.textContent =
                "⚠ Connector unavailable";

            button.style.background =
                "#d73a49";


            setTimeout(
                () => {

                    button.textContent =
                        defaultButtonText;

                    button.style.background =
                        defaultButtonBackground;
                },
                4000
            );
        });
}


// ------------------------------------------------------------
// Continue saving after project selection
// ------------------------------------------------------------

function continueSavingConversation(
    button,
    projectId,
    captureMode = "full"
) {

    const defaultButtonText =
        captureMode === "response"
            ? "Save Latest Response"
            : "Save to Obsidian";

    const defaultButtonBackground =
        captureMode === "response"
            ? "#202123"
            : "#2f6fed";

    console.log(
        "ChatGPT Obsidian Connector: saving to project",
        projectId
    );


    // --------------------------------------------------------
    // Saving state
    // --------------------------------------------------------

    button.textContent =
        captureMode === "response"
            ? "Saving response…"
            : "Saving…";


    // --------------------------------------------------------
    // Extract conversation
    // --------------------------------------------------------

    const conversation =
        extractConversation();


    // Attach selected project.
    conversation.project =
        projectId;

    const capture =
        buildCaptureData(
            conversation,
            captureMode
        );


    // --------------------------------------------------------
    // Empty conversation
    // --------------------------------------------------------

    if (
        !capture.pairs.length
    ) {

        button.disabled = false;

        button.style.cursor =
            "pointer";

        button.style.opacity =
            "1";

        button.textContent =
            "No messages found";

        button.style.background =
            "#d73a49";


        console.error(
            "ChatGPT Obsidian Connector: no messages found."
        );


        setTimeout(
            () => {

                button.textContent =
                    "Save to Obsidian";

                button.style.background =
                    "#2f6fed";
            },
            3000
        );


        return;
    }


    // --------------------------------------------------------
    // Send to background service worker
    // --------------------------------------------------------

    chrome.runtime.sendMessage(
        {
            action: "extract",
            data: {
                ...conversation,
                capture_mode: capture.captureMode,
                pairs: capture.pairs
            }
        },
        response => {

            if (
                chrome.runtime.lastError
            ) {

                console.error(
                    "ChatGPT Obsidian Connector: save request failed",
                    chrome.runtime.lastError
                );

                response = {
                    ok: false,
                    error:
                        chrome.runtime.lastError.message
                };
            }


            console.log(
                "ChatGPT Obsidian Connector: save response",
                response
            );


            // ------------------------------------------------
            // Restore normal interaction state
            // ------------------------------------------------

            button.disabled = false;

            button.style.cursor =
                "pointer";

            button.style.opacity =
                "1";


            // ------------------------------------------------
            // Successful save
            // ------------------------------------------------

            if (
                response &&
                response.ok &&
                (
                    response.status === 200 ||
                    response.status === 201
                )
            ) {

                const id =
                    response.data?.id;


                const savedMode =
                    response.data?.capture_mode ||
                    captureMode;

                const checkmark = "\u2713";

                const addedPairs =
                    Number(response.data?.added_pairs || 0);

                const updatedPairs =
                    Number(response.data?.updated_pairs || 0);

                if (savedMode === "response") {

                    if (addedPairs > 0) {
                        button.textContent =
                            id
                                ? `${checkmark} Saved response to ${id}`
                                : `${checkmark} Response saved`;

                    } else if (updatedPairs > 0) {
                        button.textContent =
                            id
                                ? `${checkmark} Updated response in ${id}`
                                : `${checkmark} Response updated`;

                    } else {
                        button.textContent =
                            id
                                ? `${checkmark} Response already captured in ${id}`
                                : `${checkmark} Response already captured`;
                    }

                } else {

                    if (addedPairs > 0) {
                        button.textContent =
                            id
                                ? `${checkmark} Saved ${id}`
                                : `${checkmark} Saved to Obsidian`;

                    } else if (updatedPairs > 0) {
                        button.textContent =
                            id
                                ? `${checkmark} Updated ${id}`
                                : `${checkmark} Conversation updated`;

                    } else {
                        button.textContent =
                            id
                                ? `${checkmark} Already captured ${id}`
                                : `${checkmark} Already captured`;
                    }
                }


                button.style.background =
                    "#238636";


                setTimeout(
                    () => {

                        button.textContent =
                            defaultButtonText;

                        button.style.background =
                            defaultButtonBackground;
                    },
                    3000
                );


                return;
            }


            // ------------------------------------------------
            // Connector unavailable
            // ------------------------------------------------

            if (
                response &&
                response.ok === false &&
                response.error
            ) {

                button.textContent =
                    "⚠ Connector unavailable";

                button.style.background =
                    "#d73a49";


                console.error(
                    "ChatGPT Obsidian Connector: connector unavailable",
                    response
                );


                setTimeout(
                    () => {

                        button.textContent =
                            defaultButtonText;

                        button.style.background =
                            defaultButtonBackground;
                    },
                    4000
                );


                return;
            }


            // ------------------------------------------------
            // Other save failure
            // ------------------------------------------------

            button.textContent =
                "Save failed";

            button.style.background =
                "#d73a49";


            console.error(
                "ChatGPT Obsidian Connector: save failed",
                response
            );


            setTimeout(
                () => {

                    button.textContent =
                        captureMode === "response"
                            ? "Save Latest Response"
                            : "Save to Obsidian";

                    button.style.background =
                        defaultButtonBackground;
                },
                3000
            );
        }
    );
}


// ------------------------------------------------------------
// Add button when page is ready
// ------------------------------------------------------------

function initializeSaveButton() {

    if (!document.body) {
        return;
    }

    createSaveButton();

    let selectivePairRefreshTimer = null;

    function scheduleSelectivePairButtons() {

        if (
            selectivePairRefreshTimer !== null
        ) {
            return;
        }

        selectivePairRefreshTimer =
            setTimeout(
                () => {

                    selectivePairRefreshTimer =
                        null;

                    try {
                        createSelectivePairButtons();
                    } catch (error) {

                        console.error(
                            "ChatGPT Obsidian Connector: selective pair button error",
                            error
                        );
                    }
                },
                150
            );
    }

    scheduleSelectivePairButtons();

    const observer =
        new MutationObserver(
            () => {
                scheduleSelectivePairButtons();
            }
        );

    observer.observe(
        document.body,
        {
            childList: true,
            subtree: true
        }
    );
}


if (
    document.readyState === "loading"
) {

    document.addEventListener(
        "DOMContentLoaded",
        initializeSaveButton,
        {
            once: true
        }
    );

} else {

    initializeSaveButton();
}


// ------------------------------------------------------------
// Final diagnostic
// ------------------------------------------------------------

console.log(
    "ChatGPT Obsidian Connector content script loaded."
);

