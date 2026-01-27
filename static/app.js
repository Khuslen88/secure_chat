// Secure Chat Frontend
(function () {
    const messagesEl = document.getElementById("messages");
    const messageInput = document.getElementById("message-input");
    const sendBtn = document.getElementById("send-btn");
    const usernameInput = document.getElementById("username");
    const fileInput = document.getElementById("file-input");
    const filePreview = document.getElementById("file-preview");
    const fileNameEl = document.getElementById("file-name");
    const fileClearBtn = document.getElementById("file-clear");
    const errorBar = document.getElementById("error-bar");

    let lastMessageCount = 0;

    // --- Per-user colors ---
    const USER_COLORS = [
        "#e94560", "#53a8e2", "#f0a500", "#6bcb77",
        "#c77dff", "#ff6b6b", "#48bfe3", "#ffd166",
    ];
    const userColorMap = {};

    function colorForUser(username) {
        if (!userColorMap[username]) {
            const idx = Object.keys(userColorMap).length % USER_COLORS.length;
            userColorMap[username] = USER_COLORS[idx];
        }
        return userColorMap[username];
    }

    // --- File type icons ---
    function fileIcon(filename) {
        const ext = filename.split(".").pop().toLowerCase();
        const icons = {
            pdf: "📕", png: "🖼️", jpg: "🖼️", jpeg: "🖼️", gif: "🖼️",
            txt: "📝", csv: "📊", docx: "📄",
        };
        return icons[ext] || "📎";
    }

    // --- Error display ---
    function showError(msg) {
        errorBar.textContent = msg;
        errorBar.hidden = false;
        setTimeout(() => { errorBar.hidden = true; }, 4000);
    }

    // --- File preview ---
    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
            fileNameEl.textContent = "📎 " + fileInput.files[0].name;
            filePreview.hidden = false;
        }
    });

    fileClearBtn.addEventListener("click", () => {
        fileInput.value = "";
        filePreview.hidden = true;
    });

    // --- Render messages ---
    function renderMessages(messages) {
        messagesEl.innerHTML = "";
        messages.forEach((msg) => {
            const div = document.createElement("div");
            div.className = "message color-border";
            const color = colorForUser(msg.username);
            div.style.borderLeftColor = color;

            const time = new Date(msg.timestamp).toLocaleTimeString();
            let html = `<div class="meta"><span class="author" style="color:${color}">${escapeHtml(msg.username)}</span> · ${time}</div>`;
            html += `<div class="body">${escapeHtml(msg.content)}</div>`;

            if (msg.filename) {
                const icon = fileIcon(msg.filename);
                html += `<div class="attachment"><a href="/api/files/${encodeURIComponent(msg.filename)}" target="_blank">${icon} ${escapeHtml(msg.filename)}</a></div>`;
            }

            div.innerHTML = html;
            messagesEl.appendChild(div);
        });
    }

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.appendChild(document.createTextNode(text));
        return div.innerHTML;
    }

    // --- Fetch messages ---
    async function fetchMessages() {
        try {
            const resp = await fetch("/api/messages");
            const messages = await resp.json();
            if (messages.length !== lastMessageCount) {
                lastMessageCount = messages.length;
                renderMessages(messages);
                messagesEl.scrollTop = messagesEl.scrollHeight;
            }
        } catch (err) {
            console.error("Failed to fetch messages:", err);
        }
    }

    // --- Send message ---
    async function sendMessage() {
        const username = usernameInput.value.trim();
        const content = messageInput.value.trim();

        if (!username) {
            showError("Please enter a username.");
            usernameInput.focus();
            return;
        }
        if (!content && fileInput.files.length === 0) {
            showError("Please enter a message or attach a file.");
            return;
        }

        // If there is a file, upload it
        if (fileInput.files.length > 0) {
            const formData = new FormData();
            formData.append("file", fileInput.files[0]);
            formData.append("username", username);
            formData.append("content", content || "(file shared)");

            try {
                const resp = await fetch("/api/upload", { method: "POST", body: formData });
                const data = await resp.json();
                if (!resp.ok) {
                    showError(data.error || "Upload failed.");
                    return;
                }
            } catch (err) {
                showError("Upload failed: " + err.message);
                return;
            }

            fileInput.value = "";
            filePreview.hidden = true;
        } else {
            // Text-only message
            try {
                const resp = await fetch("/api/messages", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, content }),
                });
                const data = await resp.json();
                if (!resp.ok) {
                    showError(data.error || "Failed to send message.");
                    return;
                }
            } catch (err) {
                showError("Failed to send message: " + err.message);
                return;
            }
        }

        messageInput.value = "";
        fetchMessages();
    }

    sendBtn.addEventListener("click", sendMessage);
    messageInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") sendMessage();
    });

    // Poll for new messages every 2 seconds
    fetchMessages();
    setInterval(fetchMessages, 2000);
})();
