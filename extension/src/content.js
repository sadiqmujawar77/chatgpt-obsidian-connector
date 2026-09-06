function htmlToMarkdown(element) {
    const clone = element.cloneNode(true);

    // Remove UI elements that are not part of the message content.
    clone.querySelectorAll(
        "button, svg, nav, textarea, input, form"
    ).forEach(node => node.remove());

    function convert(node) {
        if (node.nodeType === Node.TEXT_NODE) {
            return node.nodeValue;
        }

        if (node.nodeType !== Node.ELEMENT_NODE) {
            return "";
        }

        const tag = node.tagName.toLowerCase();

        const children = () =>
            Array.from(node.childNodes)
                .map(convert)
                .join("");

        switch (tag) {
            case "h1":
                return `\n\n# ${children().trim()}\n\n`;

            case "h2":
                return `\n\n## ${children().trim()}\n\n`;

            case "h3":
                return `\n\n### ${children().trim()}\n\n`;

            case "h4":
                return `\n\n#### ${children().trim()}\n\n`;

            case "h5":
                return `\n\n##### ${children().trim()}\n\n`;

            case "h6":
                return `\n\n###### ${children().trim()}\n\n`;

            case "strong":
            case "b":
                return `**${children().trim()}**`;

            case "em":
            case "i":
                return `*${children().trim()}*`;

            case "del":
            case "s":
            case "strike":
                return `~~${children().trim()}~~`;

            case "code":
                if (node.parentElement?.tagName.toLowerCase() === "pre") {
                    return children();
                }

                return `\`${children().trim()}\``;

            case "pre": {
                const code = node.querySelector("code");

                if (code) {
                    const language =
                        code.className
                            ?.match(/language-([^\s]+)/)?.[1] || "";

                    return `\n\n\`\`\`${language}\n${code.textContent.trim()}\n\`\`\`\n\n`;
                }

                return `\n\n\`\`\`\n${node.textContent.trim()}\n\`\`\`\n\n`;
            }

            case "a": {
                const text = children().trim();
                const href = node.getAttribute("href");

                if (!href) {
                    return text;
                }

                return `[${text}](${href})`;
            }

            case "blockquote":
                return `\n\n${children()
                    .trim()
                    .split("\n")
                    .map(line => `> ${line}`)
                    .join("\n")}\n\n`;

            case "br":
                return "\n";

            case "hr":
                return "\n\n---\n\n";

            case "ul": {
                const items = Array.from(node.children)
                    .filter(child => child.tagName.toLowerCase() === "li")
                    .map(li => {
                        const text = convert(li).trim();
                        return `- ${text}`;
                    });

                return `\n\n${items.join("\n")}\n\n`;
            }

            case "ol": {
                const items = Array.from(node.children)
                    .filter(child => child.tagName.toLowerCase() === "li")
                    .map((li, index) => {
                        const text = convert(li).trim();
                        return `${index + 1}. ${text}`;
                    });

                return `\n\n${items.join("\n")}\n\n`;
            }

            case "li":
                return children();

            case "table":
                return convertTable(node);

            case "p":
            case "div":
                return `\n\n${children()}\n\n`;

            case "span":
                return children();

            default:
                return children();
        }
    }

    function convertTable(table) {
        const rows = Array.from(table.querySelectorAll("tr"));

        if (!rows.length) {
            return "";
        }

        const tableRows = rows.map(row =>
            Array.from(row.children).map(cell =>
                convert(cell)
                    .replace(/\s+/g, " ")
                    .replace(/\|/g, "\\|")
                    .trim()
            )
        );

        const columnCount = Math.max(
            ...tableRows.map(row => row.length)
        );

        if (!columnCount) {
            return "";
        }

        const normalizedRows = tableRows.map(row => {
            while (row.length < columnCount) {
                row.push("");
            }

            return row;
        });

        const header = normalizedRows[0];

        const separator = header.map(() => "---");

        const lines = [
            `| ${header.join(" | ")} |`,
            `| ${separator.join(" | ")} |`
        ];

        for (const row of normalizedRows.slice(1)) {
            lines.push(`| ${row.join(" | ")} |`);
        }

        return `\n\n${lines.join("\n")}\n\n`;
    }

    return convert(clone)
        .replace(/\u00a0/g, " ")
        .replace(/[ \t]+\n/g, "\n")
        .replace(/\n{3,}/g, "\n\n")
        .trim();
}


function extractConversation() {
    const messages = [
        ...document.querySelectorAll("[data-message-author-role]")
    ].map(element => ({
        role: element.getAttribute("data-message-author-role"),
        content: htmlToMarkdown(element)
    }));

    return {
        title: document.title,
        url: location.href,
        messages
    };
}


window.addEventListener("message", event => {
    if (
        event.source !== window ||
        !event.data ||
        event.data.source !== "chatgpt-obsidian-connector"
    ) {
        return;
    }

    if (event.data.action === "extract") {
        chrome.runtime.sendMessage(
            {
                action: "extract",
                data: extractConversation()
            },
            response => {
                window.postMessage({
                    source: "chatgpt-obsidian-connector",
                    type: "extract-result",
                    result: response
                }, "*");
            }
        );
    }
    if (event.data.action === "preview") {
    const conversation = extractConversation();

    window.postMessage({
        source: "chatgpt-obsidian-connector",
        type: "preview-result",
        result: conversation
    }, "*");
    }

    if (event.data.action === "save-test") {
        chrome.runtime.sendMessage(
            {
                action: "save-test"
            },
            response => {
                window.postMessage({
                    source: "chatgpt-obsidian-connector",
                    type: "save-test-result",
                    result: response
                }, "*");
            }
        );
    }
});


console.log(
    "ChatGPT Obsidian Connector loaded. Messages:",
    document.querySelectorAll("[data-message-author-role]").length
);