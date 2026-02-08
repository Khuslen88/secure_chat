// Company AI Chatbot Frontend
(function () {
    // ── DOM Elements ───────────────────────────────────────────
    const messagesEl = document.getElementById("messages");
    const messageInput = document.getElementById("message-input");
    const sendBtn = document.getElementById("send-btn");
    const fileInput = document.getElementById("file-input");
    const filePreview = document.getElementById("file-preview");
    const fileNameEl = document.getElementById("file-name");
    const fileClearBtn = document.getElementById("file-clear");
    const errorBar = document.getElementById("error-bar");
    const typingIndicator = document.getElementById("typing-indicator");
    const welcomeScreen = document.getElementById("welcome");
    const newChatBtn = document.getElementById("new-chat-btn");
    const convListEl = document.getElementById("conversation-list");
    const kbFileInput = document.getElementById("kb-file-input");
    const kbListEl = document.getElementById("kb-list");

    // ── State ──────────────────────────────────────────────────
    let currentConversationId = null;
    let isWaiting = false;

    // ── Error Display ──────────────────────────────────────────
    function showError(msg) {
        errorBar.textContent = msg;
        errorBar.hidden = false;
        setTimeout(function () { errorBar.hidden = true; }, 6000);
    }

    // ── Markdown Renderer ──────────────────────────────────────
    function renderMarkdown(text) {
        // Escape HTML first for safety
        let html = escapeHtml(text);

        // Code blocks (``` ... ```)
        html = html.replace(/```(\w*)\n([\s\S]*?)```/g, function (_, lang, code) {
            return '<pre><code>' + code.trim() + '</code></pre>';
        });

        // Inline code (`...`)
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

        // Headers (###, ##, #)
        html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
        html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
        html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

        // Bold (**...**)
        html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

        // Italic (*...*)
        html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

        // Unordered lists (- item)
        html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
        html = html.replace(/((?:<li>.*<\/li>\n?)+)/g, '<ul>$1</ul>');

        // Ordered lists (1. item)
        html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

        // Paragraphs (double newlines)
        html = html.replace(/\n\n/g, '</p><p>');
        html = '<p>' + html + '</p>';

        // Clean up empty paragraphs
        html = html.replace(/<p>\s*<\/p>/g, '');
        html = html.replace(/<p>\s*(<h[123]>)/g, '$1');
        html = html.replace(/(<\/h[123]>)\s*<\/p>/g, '$1');
        html = html.replace(/<p>\s*(<pre>)/g, '$1');
        html = html.replace(/(<\/pre>)\s*<\/p>/g, '$1');
        html = html.replace(/<p>\s*(<ul>)/g, '$1');
        html = html.replace(/(<\/ul>)\s*<\/p>/g, '$1');

        return html;
    }

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.appendChild(document.createTextNode(text));
        return div.innerHTML;
    }

    // ── Message Rendering ──────────────────────────────────────
    function renderMessage(role, content, suggestions) {
        if (welcomeScreen) welcomeScreen.remove();

        const div = document.createElement("div");
        div.className = "message " + role;

        const label = document.createElement("div");
        label.className = "msg-label";
        label.textContent = role === "user" ? "You" : "🤖 Assistant";
        div.appendChild(label);

        const body = document.createElement("div");
        body.className = "msg-body";
        if (role === "assistant") {
            body.innerHTML = renderMarkdown(content);
        } else {
            body.textContent = content;
        }
        div.appendChild(body);

        // Render suggestion buttons for assistant messages
        if (role === "assistant" && suggestions && suggestions.length > 0) {
            const suggestionsDiv = document.createElement("div");
            suggestionsDiv.className = "suggestions";
            suggestions.forEach(function (suggestion) {
                const btn = document.createElement("button");
                btn.className = "suggestion-btn";
                btn.textContent = suggestion;
                btn.addEventListener("click", function () {
                    sendMessage(suggestion);
                });
                suggestionsDiv.appendChild(btn);
            });
            div.appendChild(suggestionsDiv);
        }

        messagesEl.appendChild(div);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function clearMessages() {
        messagesEl.innerHTML = "";
    }

    // ── Chat API ───────────────────────────────────────────────
    async function sendMessage(text) {
        if (isWaiting) return;
        const message = text || messageInput.value.trim();
        const hasFile = fileInput.files.length > 0;

        if (!message && !hasFile) {
            showError("Please enter a message or attach a file.");
            return;
        }

        isWaiting = true;
        sendBtn.disabled = true;

        // Render user message immediately
        if (message) renderMessage("user", message);
        if (hasFile) renderMessage("user", "📎 " + fileInput.files[0].name + (message ? "\n" + message : ""));

        messageInput.value = "";
        messageInput.style.height = "auto";

        // Show typing indicator
        typingIndicator.hidden = false;
        messagesEl.scrollTop = messagesEl.scrollHeight;

        try {
            let data;

            if (hasFile) {
                // File upload path
                const formData = new FormData();
                formData.append("file", fileInput.files[0]);
                if (message) formData.append("message", message);
                if (currentConversationId) formData.append("conversation_id", currentConversationId);

                const resp = await fetch("/api/chat/upload", { method: "POST", body: formData });
                data = await resp.json();
                if (!resp.ok) { showError(data.error || "Upload failed."); return; }

                fileInput.value = "";
                filePreview.hidden = true;
            } else {
                // Text-only path
                const payload = { message };
                if (currentConversationId) payload.conversation_id = currentConversationId;

                const resp = await fetch("/api/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });
                data = await resp.json();
                if (!resp.ok) { showError(data.error || "Failed to send message."); return; }
            }

            // Update conversation ID
            if (data.conversation_id) currentConversationId = data.conversation_id;

            // Render AI response with suggestions
            if (data.assistant_message) {
                renderMessage("assistant", data.assistant_message.content, data.suggestions || []);
            }

            // Refresh sidebar
            loadConversationList();

        } catch (err) {
            showError("Connection error: " + err.message);
        } finally {
            isWaiting = false;
            sendBtn.disabled = false;
            typingIndicator.hidden = true;
        }
    }

    // ── Conversation Management ────────────────────────────────
    async function loadConversation(convId) {
        currentConversationId = convId;
        clearMessages();

        try {
            const resp = await fetch("/api/conversations/" + convId);
            if (!resp.ok) return;
            const data = await resp.json();

            data.messages.forEach(function (msg) {
                renderMessage(msg.role, msg.content);
            });

            // Highlight active in sidebar
            document.querySelectorAll(".conv-item").forEach(function (el) {
                el.classList.toggle("active", el.dataset.id === convId);
            });
        } catch (err) {
            showError("Failed to load conversation.");
        }
    }

    async function loadConversationList() {
        try {
            const resp = await fetch("/api/conversations");
            const convos = await resp.json();

            convListEl.innerHTML = "";
            convos.forEach(function (conv) {
                const div = document.createElement("div");
                div.className = "conv-item" + (conv.id === currentConversationId ? " active" : "");
                div.dataset.id = conv.id;
                div.textContent = conv.preview || "New conversation";

                const delBtn = document.createElement("button");
                delBtn.className = "conv-delete";
                delBtn.textContent = "✕";
                delBtn.addEventListener("click", function (e) {
                    e.stopPropagation();
                    deleteConversation(conv.id);
                });
                div.appendChild(delBtn);

                div.addEventListener("click", function () {
                    loadConversation(conv.id);
                });

                convListEl.appendChild(div);
            });
        } catch (err) {
            console.error("Failed to load conversations:", err);
        }
    }

    async function deleteConversation(convId) {
        try {
            await fetch("/api/conversations/" + convId, { method: "DELETE" });
            if (currentConversationId === convId) {
                newConversation();
            }
            loadConversationList();
        } catch (err) {
            showError("Failed to delete conversation.");
        }
    }

    function newConversation() {
        currentConversationId = null;
        clearMessages();
        // Re-add welcome screen
        const welcome = document.createElement("div");
        welcome.id = "welcome";
        welcome.className = "welcome-screen";
        welcome.innerHTML =
            '<h2>How can I help you today?</h2>' +
            '<p class="welcome-sub">I can answer company questions, summarize documents, help with IT issues, or assist with writing tasks.</p>' +
            '<div class="quick-actions">' +
                '<button class="quick-action" data-prompt="What are the company\'s PTO policies?">🏖️ PTO Policies</button>' +
                '<button class="quick-action" data-prompt="How do I reset my password?">🔑 Password Reset</button>' +
                '<button class="quick-action" data-prompt="Help me draft a professional email to my team about a project deadline">✉️ Draft Email</button>' +
                '<button class="quick-action" data-prompt="What is the onboarding process for new hires?">🚀 Onboarding Info</button>' +
            '</div>';
        messagesEl.appendChild(welcome);
        bindQuickActions();

        document.querySelectorAll(".conv-item").forEach(function (el) {
            el.classList.remove("active");
        });
    }

    // ── Knowledge Base ─────────────────────────────────────────
    async function loadKnowledgeBase() {
        try {
            const resp = await fetch("/api/knowledge-base");
            const docs = await resp.json();

            kbListEl.innerHTML = "";
            if (docs.length === 0) {
                kbListEl.innerHTML = '<div style="font-size:0.75rem;color:#555;padding:4px 8px">No documents yet</div>';
                return;
            }
            docs.forEach(function (doc) {
                const div = document.createElement("div");
                div.className = "kb-item";

                const name = document.createElement("span");
                name.className = "kb-name";
                name.textContent = "📄 " + doc.original_name;
                div.appendChild(name);

                const delBtn = document.createElement("button");
                delBtn.className = "kb-delete";
                delBtn.textContent = "✕";
                delBtn.addEventListener("click", function () {
                    deleteKBDoc(doc.id);
                });
                div.appendChild(delBtn);

                kbListEl.appendChild(div);
            });
        } catch (err) {
            console.error("Failed to load knowledge base:", err);
        }
    }

    async function uploadKBDoc(file) {
        const formData = new FormData();
        formData.append("file", file);

        try {
            const resp = await fetch("/api/knowledge-base", { method: "POST", body: formData });
            const data = await resp.json();
            if (!resp.ok) {
                showError(data.error || "KB upload failed.");
                return;
            }
            loadKnowledgeBase();
        } catch (err) {
            showError("KB upload failed: " + err.message);
        }
    }

    async function deleteKBDoc(docId) {
        try {
            await fetch("/api/knowledge-base/" + docId, { method: "DELETE" });
            loadKnowledgeBase();
        } catch (err) {
            showError("Failed to delete document.");
        }
    }

    // ── Quick Actions ──────────────────────────────────────────
    function bindQuickActions() {
        document.querySelectorAll(".quick-action").forEach(function (btn) {
            btn.addEventListener("click", function () {
                sendMessage(btn.dataset.prompt);
            });
        });
    }

    // ── File Preview ───────────────────────────────────────────
    fileInput.addEventListener("change", function () {
        if (fileInput.files.length > 0) {
            fileNameEl.textContent = "📎 " + fileInput.files[0].name;
            filePreview.hidden = false;
        }
    });

    fileClearBtn.addEventListener("click", function () {
        fileInput.value = "";
        filePreview.hidden = true;
    });

    // ── Auto-expanding Textarea ────────────────────────────────
    messageInput.addEventListener("input", function () {
        this.style.height = "auto";
        this.style.height = Math.min(this.scrollHeight, 120) + "px";
    });

    // ── Event Bindings ─────────────────────────────────────────
    sendBtn.addEventListener("click", function () { sendMessage(); });

    messageInput.addEventListener("keydown", function (e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    newChatBtn.addEventListener("click", newConversation);

    kbFileInput.addEventListener("change", function () {
        if (kbFileInput.files.length > 0) {
            uploadKBDoc(kbFileInput.files[0]);
            kbFileInput.value = "";
        }
    });

    // ── Initialize ─────────────────────────────────────────────
    bindQuickActions();
    loadConversationList();
    loadKnowledgeBase();
})();
