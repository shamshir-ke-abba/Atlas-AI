/**
 * ATLAS AI — DESIGN SYSTEM V1
 * Canonical Frontend Client Application
 */

(function () {
  "use strict";

  // ------------------------------------------------------------
  // 01. CONSTANTS & STATE
  // ------------------------------------------------------------
  const SESSION_KEY = "atlas_web_session_v3";
  const THEME_KEY = "atlas_theme_v1";
  const REDUCED_MOTION_KEY = "atlas_reduced_motion_v1";
  const SIDEBAR_STATE_KEY = "atlas_sidebar_collapsed_v1";

  let sessionId = localStorage.getItem(SESSION_KEY);
  if (!sessionId) {
    sessionId =
      typeof crypto !== "undefined" && crypto.randomUUID
        ? crypto.randomUUID()
        : Math.random().toString(36).slice(2) + Date.now().toString(36);
    localStorage.setItem(SESSION_KEY, sessionId);
  }

  let conversationId = null;
  let abortController = null;
  let isGenerating = false;
  let userScrolledAway = false;
  let allConversations = [];
  let availableTools = [];
  let currentActiveTool = null;
  let lastToolResult = "";

  // ------------------------------------------------------------
  // 02. DOM ELEMENT REFERENCES
  // ------------------------------------------------------------
  const appShell = document.getElementById("appShell");
  const drawerBackdrop = document.getElementById("drawerBackdrop");
  const sidebar = document.getElementById("sidebar");
  const sidebarToggleBtn = document.getElementById("sidebarToggleBtn");
  const mobileMenuBtn = document.getElementById("mobileMenuBtn");
  const newChatBtn = document.getElementById("newChatBtn");
  const conversationSearchInput = document.getElementById("conversationSearchInput");
  const conversationList = document.getElementById("conversationList");
  const navToolsBtn = document.getElementById("navToolsBtn");
  const navMemoryBtn = document.getElementById("navMemoryBtn");
  const navSettingsBtn = document.getElementById("navSettingsBtn");
  const toolsCountBadge = document.getElementById("toolsCountBadge");

  const headerTitle = document.getElementById("headerTitle");
  const statusPill = document.getElementById("statusPill");
  const statusDot = document.getElementById("statusDot");
  const statusText = document.getElementById("statusText");
  const themeToggleBtn = document.getElementById("themeToggleBtn");
  const contextDrawerToggleBtn = document.getElementById("contextDrawerToggleBtn");

  const conversationContainer = document.getElementById("conversationContainer");
  const emptyState = document.getElementById("emptyState");
  const chatMessages = document.getElementById("chatMessages");
  const assistantActivity = document.getElementById("assistantActivity");
  const activityText = document.getElementById("activityText");

  const composerCard = document.getElementById("composerCard");
  const messageInput = document.getElementById("messageInput");
  const composerToolsBtn = document.getElementById("composerToolsBtn");
  const sendBtn = document.getElementById("sendBtn");
  const stopBtn = document.getElementById("stopBtn");

  const contextDrawer = document.getElementById("contextDrawer");
  const closeDrawerBtn = document.getElementById("closeDrawerBtn");
  const drawerConvTitle = document.getElementById("drawerConvTitle");
  const drawerConvMsgCount = document.getElementById("drawerConvMsgCount");
  const drawerModelName = document.getElementById("drawerModelName");
  const drawerToolsCount = document.getElementById("drawerToolsCount");
  const drawerActiveToolsList = document.getElementById("drawerActiveToolsList");
  const drawerMemoryCard = document.getElementById("drawerMemoryCard");
  const drawerOllamaHost = document.getElementById("drawerOllamaHost");
  const drawerWebSearchStatus = document.getElementById("drawerWebSearchStatus");

  // Tool Modal
  const toolModal = document.getElementById("toolModal");
  const toolModalBackdrop = document.getElementById("toolModalBackdrop");
  const toolModalCloseBtn = document.getElementById("toolModalCloseBtn");
  const toolModalTitle = document.getElementById("toolModalTitle");
  const toolModalDesc = document.getElementById("toolModalDesc");
  const toolPickerSelect = document.getElementById("toolPickerSelect");
  const toolFormContainer = document.getElementById("toolFormContainer");
  const toolResultWrap = document.getElementById("toolResultWrap");
  const toolResultCode = document.getElementById("toolResultCode");
  const toolRunBtn = document.getElementById("toolRunBtn");
  const toolInsertChatBtn = document.getElementById("toolInsertChatBtn");

  // Settings Modal
  const settingsModal = document.getElementById("settingsModal");
  const settingsModalBackdrop = document.getElementById("settingsModalBackdrop");
  const settingsModalCloseBtn = document.getElementById("settingsModalCloseBtn");
  const themeDarkBtn = document.getElementById("themeDarkBtn");
  const themeLightBtn = document.getElementById("themeLightBtn");
  const reducedMotionToggle = document.getElementById("reducedMotionToggle");
  const settingsSessionId = document.getElementById("settingsSessionId");
  const resetSessionBtn = document.getElementById("resetSessionBtn");

  // ------------------------------------------------------------
  // 03. BRAND & SVG HELPERS
  // ------------------------------------------------------------
  function createAtlasMarkSVG(size = 24, stateClass = "") {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("class", `atlas-mark size-${size} ${stateClass}`.trim());
    svg.setAttribute("viewBox", "0 0 32 32");
    svg.setAttribute("fill", "none");

    const aStroke = document.createElementNS("http://www.w3.org/2000/svg", "path");
    aStroke.setAttribute("class", "atlas-a-stroke");
    aStroke.setAttribute("d", "M6.5 25.5L16 5.5L25.5 25.5");
    aStroke.setAttribute("stroke", "currentColor");
    aStroke.setAttribute("stroke-width", "2.6");
    aStroke.setAttribute("stroke-linecap", "round");
    aStroke.setAttribute("stroke-linejoin", "round");

    const aCross = document.createElementNS("http://www.w3.org/2000/svg", "path");
    aCross.setAttribute("class", "atlas-a-cross");
    aCross.setAttribute("d", "M10 19H22");
    aCross.setAttribute("stroke", "currentColor");
    aCross.setAttribute("stroke-width", "2.2");
    aCross.setAttribute("stroke-linecap", "round");

    const trajectory = document.createElementNS("http://www.w3.org/2000/svg", "path");
    trajectory.setAttribute("class", "atlas-trajectory");
    trajectory.setAttribute("d", "M5.5 21.5L25.5 6.5");
    trajectory.setAttribute("stroke", "var(--brand-ui)");
    trajectory.setAttribute("stroke-width", "2.4");
    trajectory.setAttribute("stroke-linecap", "round");

    const node = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    node.setAttribute("class", "atlas-node");
    node.setAttribute("cx", "25.5");
    node.setAttribute("cy", "6.5");
    node.setAttribute("r", "2.8");
    node.setAttribute("fill", "var(--brand-ui)");

    svg.appendChild(aStroke);
    svg.appendChild(aCross);
    svg.appendChild(trajectory);
    svg.appendChild(node);

    return svg;
  }

  // ------------------------------------------------------------
  // 04. STATE MANAGEMENT & API CALLS
  // ------------------------------------------------------------
  function getHeaders(extra = {}) {
    return {
      "Content-Type": "application/json",
      "X-Atlas-Session": sessionId,
      ...extra,
    };
  }

  function setAssistantState(state, customText = "") {
    statusDot.className = "status-dot " + state.toLowerCase().replace(/\s+/g, "-");
    statusText.textContent = customText || state;

    if (state === "Thinking" || state === "Generating" || state === "Searching") {
      assistantActivity.classList.remove("hidden");
      activityText.textContent = customText || `Atlas is ${state.toLowerCase()}…`;
    } else {
      assistantActivity.classList.add("hidden");
    }
  }

  function scrollChatToBottom(force = false) {
    if (force || !userScrolledAway) {
      conversationContainer.scrollTop = conversationContainer.scrollHeight;
    }
  }

  conversationContainer.addEventListener("scroll", () => {
    const dist =
      conversationContainer.scrollHeight -
      conversationContainer.scrollTop -
      conversationContainer.clientHeight;
    userScrolledAway = dist > 80;
  });

  // ------------------------------------------------------------
  // 05. MARKDOWN / TEXT FORMATTING
  // ------------------------------------------------------------
  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function formatMarkdown(raw) {
    if (!raw) return "";

    // Code blocks with syntax language tag
    let formatted = raw.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (match, lang, code) => {
      const escaped = escapeHtml(code.trimEnd());
      const displayLang = lang ? `<span class="code-lang">${escapeHtml(lang)}</span>` : "";
      return `<div class="code-block-wrapper">
        <div class="code-block-header">${displayLang}<button class="copy-code-btn" title="Copy code">Copy</button></div>
        <pre><code class="language-${lang || 'text'}">${escaped}</code></pre>
      </div>`;
    });

    // Inline code
    formatted = formatted.replace(/`([^`]+)`/g, (match, code) => {
      return `<code>${escapeHtml(code)}</code>`;
    });

    // Headers
    formatted = formatted.replace(/^### (.*$)/gim, "<h3>$1</h3>");
    formatted = formatted.replace(/^## (.*$)/gim, "<h2>$1</h2>");
    formatted = formatted.replace(/^# (.*$)/gim, "<h1>$1</h1>");

    // Blockquotes
    formatted = formatted.replace(/^\> (.*$)/gim, "<blockquote>$1</blockquote>");

    // Bold and Italic
    formatted = formatted.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    formatted = formatted.replace(/\*([^*]+)\*/g, "<em>$1</em>");

    // Unordered lists
    formatted = formatted.replace(/^\s*[-*]\s+(.*$)/gim, "<li>$1</li>");
    formatted = formatted.replace(/(<li>.*<\/li>(\n|$))+/g, "<ul>$&</ul>");

    // Links: [text](url)
    formatted = formatted.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

    // Paragraph breaks
    formatted = formatted
      .split(/\n{2,}/)
      .map((block) => {
        block = block.trim();
        if (!block) return "";
        if (
          block.startsWith("<h") ||
          block.startsWith("<pre") ||
          block.startsWith("<div class=\"code-block-wrapper\"") ||
          block.startsWith("<ul") ||
          block.startsWith("<ol") ||
          block.startsWith("<blockquote")
        ) {
          return block;
        }
        return `<p>${block.replace(/\n/g, "<br>")}</p>`;
      })
      .join("");

    return formatted;
  }

  // ------------------------------------------------------------
  // 06. MESSAGE RENDERING
  // ------------------------------------------------------------
  function renderUserMessage(text) {
    emptyState.classList.add("hidden");

    const group = document.createElement("div");
    group.className = "message-group user";

    const bubble = document.createElement("div");
    bubble.className = "user-bubble";
    bubble.textContent = text;

    group.appendChild(bubble);
    chatMessages.appendChild(group);
    scrollChatToBottom(true);
    return group;
  }

  function renderAtlasMessage(initialText = "") {
    emptyState.classList.add("hidden");

    const group = document.createElement("div");
    group.className = "message-group atlas";

    const row = document.createElement("div");
    row.className = "atlas-row";

    const avatar = document.createElement("div");
    avatar.className = "atlas-avatar";
    avatar.appendChild(createAtlasMarkSVG(24));

    const contentWrap = document.createElement("div");
    contentWrap.className = "atlas-content-wrap";

    const header = document.createElement("div");
    header.className = "atlas-header";

    const name = document.createElement("span");
    name.className = "atlas-identity-label";
    name.textContent = "Atlas";

    const copyBtn = document.createElement("button");
    copyBtn.className = "copy-btn";
    copyBtn.title = "Copy message";
    copyBtn.innerHTML = `
      <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
      </svg>
      <span>Copy</span>
    `;

    header.appendChild(name);
    header.appendChild(copyBtn);

    const body = document.createElement("div");
    body.className = "atlas-body";
    if (initialText) {
      body.innerHTML = formatMarkdown(initialText);
    }

    contentWrap.appendChild(header);
    contentWrap.appendChild(body);

    row.appendChild(avatar);
    row.appendChild(contentWrap);
    group.appendChild(row);

    // Copy event
    copyBtn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(body.innerText);
        const span = copyBtn.querySelector("span");
        span.textContent = "Copied!";
        setTimeout(() => {
          span.textContent = "Copy";
        }, 1200);
      } catch (err) {
        console.error("Copy failed", err);
      }
    });

    chatMessages.appendChild(group);
    scrollChatToBottom();

    return { group, row, contentWrap, body, copyBtn };
  }

  function renderWebSources(contentWrap, sources) {
    if (!Array.isArray(sources) || !sources.length) return;

    const wrap = document.createElement("div");
    wrap.className = "web-sources-wrap";

    const title = document.createElement("div");
    title.className = "web-sources-title";
    title.textContent = "Sources";
    wrap.appendChild(title);

    const list = document.createElement("div");
    list.className = "web-sources-list";

    sources.slice(0, 6).forEach((src) => {
      const url = typeof src === "string" ? src : src.url;
      const label = typeof src === "string" ? src : src.title || src.url;
      if (!url) return;

      const link = document.createElement("a");
      link.className = "source-link-item";
      link.href = url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.innerHTML = `
        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width:12px;height:12px;flex-shrink:0;">
          <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
          <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
        </svg>
        <span>${escapeHtml(label)}</span>
      `;
      list.appendChild(link);
    });

    wrap.appendChild(list);
    contentWrap.appendChild(wrap);
  }

  function renderInlineToolPill(contentWrap, toolName, statusText, isCompleted = false) {
    const pill = document.createElement("div");
    pill.className = `tool-execution-pill ${isCompleted ? "completed" : "active"}`;
    pill.innerHTML = `
      <span class="tool-status-icon">${isCompleted ? "✓" : "⚙"}</span>
      <span>${escapeHtml(statusText || toolName)}</span>
    `;
    contentWrap.insertBefore(pill, contentWrap.querySelector(".atlas-body"));
  }

  // Handle delegated code block copy clicks
  chatMessages.addEventListener("click", async (e) => {
    if (e.target.classList.contains("copy-code-btn")) {
      const btn = e.target;
      const pre = btn.closest(".code-block-wrapper").querySelector("pre code");
      if (pre) {
        await navigator.clipboard.writeText(pre.innerText);
        btn.textContent = "Copied!";
        setTimeout(() => {
          btn.textContent = "Copy";
        }, 1200);
      }
    }
  });

  // Prompt chips in empty state
  document.querySelectorAll(".prompt-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const prompt = chip.dataset.prompt;
      if (prompt) {
        messageInput.value = prompt;
        sendMessage();
      }
    });
  });

  // ------------------------------------------------------------
  // 07. CONVERSATION MANAGEMENT
  // ------------------------------------------------------------
  async function refreshHistory() {
    try {
      const res = await fetch("/api/conversations", {
        headers: getHeaders(),
      });
      if (!res.ok) throw new Error("Could not fetch conversations");

      const data = await res.json();
      allConversations = data.conversations || [];
      renderConversationList(allConversations);
    } catch (err) {
      console.error("Failed to load conversation history", err);
    }
  }

  function renderConversationList(list) {
    conversationList.innerHTML = "";

    if (!list.length) {
      const empty = document.createElement("div");
      empty.className = "history-empty";
      empty.style.padding = "12px 16px";
      empty.style.color = "var(--text-muted)";
      empty.style.fontSize = "12px";
      empty.textContent = "No conversations yet";
      conversationList.appendChild(empty);
      return;
    }

    list.forEach((item) => {
      const div = document.createElement("div");
      div.className = "history-item" + (item.id === conversationId ? " active" : "");
      div.setAttribute("role", "button");
      div.setAttribute("tabindex", "0");
      div.setAttribute("data-id", item.id);

      const title = document.createElement("span");
      title.className = "history-item-title";
      title.textContent = item.title || "New Chat";

      const del = document.createElement("button");
      del.className = "history-item-delete";
      del.title = "Delete conversation";
      del.setAttribute("aria-label", "Delete conversation");
      del.innerHTML = `
        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width:12px;height:12px;">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      `;

      del.addEventListener("click", async (ev) => {
        ev.stopPropagation();
        if (!confirm(`Delete "${item.title || 'conversation'}"?`)) return;

        try {
          const delRes = await fetch(`/api/conversations/${encodeURIComponent(item.id)}`, {
            method: "DELETE",
            headers: getHeaders(),
          });
          if (!delRes.ok) return;

          const resData = await delRes.json();
          if (item.id === conversationId) {
            if (resData.replacement) {
              await loadConversation(resData.replacement);
            } else {
              conversationId = null;
              chatMessages.innerHTML = "";
              emptyState.classList.remove("hidden");
              headerTitle.textContent = "New Chat";
              drawerConvTitle.textContent = "New Chat";
              drawerConvMsgCount.textContent = "0";
            }
          }
          await refreshHistory();
        } catch (err) {
          console.error("Delete failed", err);
        }
      });

      div.appendChild(title);
      div.appendChild(del);

      div.addEventListener("click", () => {
        if (item.id !== conversationId) {
          loadConversation(item.id);
          // Close mobile sidebar if open
          appShell.classList.remove("mobile-sidebar-open");
        }
      });

      div.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          loadConversation(item.id);
        }
      });

      conversationList.appendChild(div);
    });
  }

  // Filter conversations
  conversationSearchInput.addEventListener("input", () => {
    const q = conversationSearchInput.value.toLowerCase().trim();
    if (!q) {
      renderConversationList(allConversations);
      return;
    }
    const filtered = allConversations.filter((c) =>
      (c.title || "").toLowerCase().includes(q)
    );
    renderConversationList(filtered);
  });

  async function loadConversation(id) {
    try {
      const res = await fetch(`/api/conversations/${encodeURIComponent(id)}`, {
        headers: getHeaders(),
      });
      if (!res.ok) throw new Error("Conversation unavailable");

      const data = await res.json();
      conversationId = data.id;
      headerTitle.textContent = data.title || "New Chat";
      drawerConvTitle.textContent = data.title || "New Chat";

      chatMessages.innerHTML = "";
      const msgs = data.messages || [];
      drawerConvMsgCount.textContent = msgs.length;

      if (!msgs.length) {
        emptyState.classList.remove("hidden");
      } else {
        emptyState.classList.add("hidden");
        for (const msg of msgs) {
          const isUser = msg.is_user || (msg.sender && msg.sender.toLowerCase() === "you");
          if (isUser) {
            renderUserMessage(msg.text || msg.content || "");
          } else {
            renderAtlasMessage(msg.text || msg.content || "");
          }
        }
      }

      setAssistantState("Ready");
      await refreshHistory();
      await refreshStatus();
      scrollChatToBottom(true);
    } catch (err) {
      console.error(err);
      setAssistantState("Error", "Load failed");
    }
  }

  async function createNewChat() {
    try {
      const res = await fetch("/api/conversations", {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({ session_id: sessionId }),
      });
      if (!res.ok) throw new Error("Could not create conversation");

      const data = await res.json();
      conversationId = data.conversation_id;
      headerTitle.textContent = "New Chat";
      drawerConvTitle.textContent = "New Chat";
      drawerConvMsgCount.textContent = "0";

      chatMessages.innerHTML = "";
      emptyState.classList.remove("hidden");

      await refreshHistory();
      await refreshStatus();
      messageInput.focus();
      appShell.classList.remove("mobile-sidebar-open");
    } catch (err) {
      console.error("Create chat error", err);
      setAssistantState("Error");
    }
  }

  newChatBtn.addEventListener("click", createNewChat);

  // ------------------------------------------------------------
  // 08. STATUS & MEMORY INTEGRATION
  // ------------------------------------------------------------
  async function refreshStatus() {
    try {
      const res = await fetch("/api/status", {
        headers: getHeaders(),
      });
      if (!res.ok) throw new Error();

      const data = await res.json();
      drawerModelName.textContent = data.model || "—";
      drawerOllamaHost.textContent = data.ollama || "Local";
      if (data.conversation_title) {
        headerTitle.textContent = data.conversation_title;
        drawerConvTitle.textContent = data.conversation_title;
      }
      if (data.history_messages !== undefined) {
        drawerConvMsgCount.textContent = data.history_messages;
      }
      setAssistantState("Ready");
    } catch {
      setAssistantState("Offline");
    }
  }

  async function refreshMemory() {
    try {
      const res = await fetch("/api/memory", {
        headers: getHeaders(),
      });
      if (!res.ok) return;

      const data = await res.json();
      const mem = data.memory || {};
      drawerMemoryCard.innerHTML = "";

      let hasData = false;
      for (const [category, entries] of Object.entries(mem)) {
        if (entries && typeof entries === "object" && Object.keys(entries).length > 0) {
          hasData = true;
          const entryEl = document.createElement("div");
          entryEl.className = "memory-entry";

          const catEl = document.createElement("div");
          catEl.className = "memory-category";
          catEl.textContent = category;

          const contentEl = document.createElement("div");
          contentEl.className = "memory-content";
          contentEl.textContent = Object.entries(entries)
            .map(([k, v]) => `${k}: ${v}`)
            .join(" · ");

          entryEl.appendChild(catEl);
          entryEl.appendChild(contentEl);
          drawerMemoryCard.appendChild(entryEl);
        }
      }

      if (!hasData) {
        drawerMemoryCard.innerHTML = '<div class="memory-empty">No stored facts yet.</div>';
      }
    } catch (err) {
      drawerMemoryCard.innerHTML = '<div class="memory-empty">Memory unavailable.</div>';
    }
  }

  // ------------------------------------------------------------
  // 09. TOOLS INTEGRATION
  // ------------------------------------------------------------
  async function loadTools() {
    try {
      const res = await fetch("/api/tools", { headers: getHeaders() });
      if (!res.ok) throw new Error("Tools unavailable");

      const data = await res.json();
      availableTools = data.tools || [];
      toolsCountBadge.textContent = availableTools.length;
      drawerToolsCount.textContent = availableTools.length;

      // Populate Drawer Tools list
      drawerActiveToolsList.innerHTML = "";
      toolPickerSelect.innerHTML = "";

      availableTools.forEach((tool) => {
        // Drawer row
        const row = document.createElement("div");
        row.className = "active-tool-row";
        row.innerHTML = `
          <span class="active-tool-name">${escapeHtml(tool.display_name || tool.name)}</span>
          <span class="active-tool-status">Ready</span>
        `;
        row.addEventListener("click", () => openToolModal(tool));
        drawerActiveToolsList.appendChild(row);

        // Select option
        const opt = document.createElement("option");
        opt.value = tool.name;
        opt.textContent = tool.display_name || tool.name;
        toolPickerSelect.appendChild(opt);
      });
    } catch (err) {
      console.error("Tools load error", err);
    }
  }

  function openToolModal(selectedTool = null) {
    if (!availableTools.length) return;
    const tool = selectedTool || availableTools[0];
    currentActiveTool = tool;

    toolPickerSelect.value = tool.name;
    buildToolForm(tool);

    toolResultWrap.classList.add("hidden");
    toolResultCode.textContent = "";
    toolInsertChatBtn.style.display = "none";
    lastToolResult = "";

    toolModal.classList.remove("hidden");
  }

  function closeToolModal() {
    toolModal.classList.add("hidden");
    currentActiveTool = null;
  }

  toolPickerSelect.addEventListener("change", () => {
    const selected = availableTools.find((t) => t.name === toolPickerSelect.value);
    if (selected) {
      currentActiveTool = selected;
      buildToolForm(selected);
    }
  });

  function buildToolForm(tool) {
    toolModalTitle.textContent = tool.display_name || tool.name;
    toolModalDesc.textContent = tool.description || "Run tool with structured input.";
    toolFormContainer.innerHTML = "";

    const name = (tool.name || "").toLowerCase();

    if (name === "calculator") {
      createFormField("expression", "Expression", "text", "e.g. 128 * 24 / 6 or 2^8");
    } else if (name === "math") {
      createFormField("expression", "Math Request", "textarea", "e.g. integrate 2x^2 + 4 or solve 3x + 5 = 20");
    } else if (name === "web_search") {
      createFormField("expression", "Search Query", "text", "Current information or query");
    } else if (name === "calendar" || name === "time") {
      const help = document.createElement("div");
      help.className = "tool-help";
      help.textContent = name === "calendar" ? "Returns today's date, day, and week number." : "Returns current local system time.";
      toolFormContainer.appendChild(help);
    } else if (name === "fitness" || name === "nutrition") {
      createFormSelect("action", "Action", ["get_profile", "set_profile", "generate_plan"]);
      createFormField("arguments", "Arguments (JSON)", "textarea", '{"key": "value"}');
    } else {
      createFormField("expression", "Input", "text", "Input parameter for tool");
    }
  }

  function createFormField(name, label, type, placeholder) {
    const wrap = document.createElement("div");
    wrap.className = "tool-field";

    const lbl = document.createElement("label");
    lbl.className = "tool-field-label";
    lbl.textContent = label;

    let input;
    if (type === "textarea") {
      input = document.createElement("textarea");
      input.className = "tool-textarea";
      input.rows = 3;
    } else {
      input = document.createElement("input");
      input.className = "tool-input";
      input.type = type;
    }

    input.name = name;
    input.placeholder = placeholder || "";
    input.dataset.field = name;

    wrap.appendChild(lbl);
    wrap.appendChild(input);
    toolFormContainer.appendChild(wrap);
    return input;
  }

  function createFormSelect(name, label, options) {
    const wrap = document.createElement("div");
    wrap.className = "tool-field";

    const lbl = document.createElement("label");
    lbl.className = "tool-field-label";
    lbl.textContent = label;

    const select = document.createElement("select");
    select.className = "tool-select";
    select.name = name;
    select.dataset.field = name;

    options.forEach((opt) => {
      const el = document.createElement("option");
      el.value = opt;
      el.textContent = opt;
      select.appendChild(el);
    });

    wrap.appendChild(lbl);
    wrap.appendChild(select);
    toolFormContainer.appendChild(wrap);
    return select;
  }

  async function executeActiveTool() {
    if (!currentActiveTool) return;

    toolRunBtn.disabled = true;
    toolRunBtn.textContent = "Running…";

    const inputs = toolFormContainer.querySelectorAll("[data-field]");
    const payload = {
      session_id: sessionId,
      action: "",
      expression: "",
      arguments: {},
    };

    inputs.forEach((inp) => {
      const f = inp.dataset.field;
      if (f === "action") payload.action = inp.value;
      else if (f === "expression") payload.expression = inp.value;
      else if (f === "arguments") {
        try {
          payload.arguments = JSON.parse(inp.value || "{}");
        } catch {
          payload.arguments = { raw: inp.value };
        }
      }
    });

    try {
      const res = await fetch(`/api/tools/${encodeURIComponent(currentActiveTool.name)}/run`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Execution failed");

      lastToolResult = String(data.result ?? "");
      toolResultCode.textContent = lastToolResult;
      toolResultWrap.classList.remove("hidden");
      toolInsertChatBtn.style.display = "inline-flex";
    } catch (err) {
      toolResultCode.textContent = `Error: ${err.message}`;
      toolResultWrap.classList.remove("hidden");
    } finally {
      toolRunBtn.disabled = false;
      toolRunBtn.textContent = "Run Tool";
    }
  }

  toolRunBtn.addEventListener("click", executeActiveTool);
  toolModalCloseBtn.addEventListener("click", closeToolModal);
  toolModalBackdrop.addEventListener("click", closeToolModal);

  toolInsertChatBtn.addEventListener("click", () => {
    if (!lastToolResult) return;
    const msg = renderAtlasMessage();
    renderInlineToolPill(msg.contentWrap, currentActiveTool.name, `✓ ${currentActiveTool.display_name || currentActiveTool.name}`, true);
    msg.body.innerHTML = formatMarkdown(lastToolResult);
    closeToolModal();
    scrollChatToBottom(true);
  });

  navToolsBtn.addEventListener("click", () => openToolModal());
  composerToolsBtn.addEventListener("click", () => openToolModal());

  // ------------------------------------------------------------
  // 10. CHAT SEND & STREAMING
  // ------------------------------------------------------------
  messageInput.addEventListener("input", () => {
    messageInput.style.height = "auto";
    messageInput.style.height = Math.min(messageInput.scrollHeight, 200) + "px";
  });

  messageInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  sendBtn.addEventListener("click", sendMessage);

  stopBtn.addEventListener("click", () => {
    if (abortController) {
      abortController.abort();
    }
  });

  async function sendMessage() {
    if (isGenerating) return;

    const text = messageInput.value.trim();
    if (!text) return;

    if (!conversationId) {
      await createNewChat();
    }

    renderUserMessage(text);
    messageInput.value = "";
    messageInput.style.height = "auto";

    const atlasMsg = renderAtlasMessage("");
    const body = atlasMsg.body;
    const contentWrap = atlasMsg.contentWrap;

    isGenerating = true;
    abortController = new AbortController();

    sendBtn.classList.add("hidden");
    stopBtn.classList.remove("hidden");
    messageInput.disabled = true;

    setAssistantState("Thinking", "Atlas is thinking…");

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({
          message: text,
          conversation_id: conversationId,
          session_id: sessionId,
        }),
        signal: abortController.signal,
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      if (!response.body) throw new Error("Streaming unavailable");

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";
      let accumulatedText = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.trim()) continue;

          let event;
          try {
            event = JSON.parse(line);
          } catch {
            continue;
          }

          if (event.type === "chunk") {
            setAssistantState("Generating", "Atlas is responding…");
            accumulatedText += event.text || "";
            body.innerHTML = formatMarkdown(accumulatedText);
            scrollChatToBottom();
          } else if (event.type === "done") {
            if (event.conversation_id) conversationId = event.conversation_id;
            if (event.title) {
              headerTitle.textContent = event.title;
              drawerConvTitle.textContent = event.title;
            }

            const sources = event.web?.sources || [];
            if (sources.length) {
              renderWebSources(contentWrap, sources);
            }

            await refreshHistory();
            await refreshMemory();
          } else if (event.type === "error") {
            throw new Error(event.message || "Error generating response");
          }
        }
      }
    } catch (err) {
      if (err.name === "AbortError") {
        body.innerHTML += "<p><em>[Generation stopped]</em></p>";
      } else {
        body.innerHTML += `<p class="semantic-error"><strong>Error:</strong> ${escapeHtml(err.message)}</p>`;
        setAssistantState("Error", "Failed");
      }
    } finally {
      isGenerating = false;
      abortController = null;
      messageInput.disabled = false;

      sendBtn.classList.remove("hidden");
      stopBtn.classList.add("hidden");

      setAssistantState("Ready");
      messageInput.focus();
      await refreshStatus();
      scrollChatToBottom();
    }
  }

  // ------------------------------------------------------------
  // 11. SIDEBAR & DRAWER TOGGLES
  // ------------------------------------------------------------
  function toggleSidebar() {
    const isCollapsed = appShell.classList.toggle("sidebar-collapsed");
    localStorage.setItem(SIDEBAR_STATE_KEY, isCollapsed ? "1" : "0");
  }

  sidebarToggleBtn.addEventListener("click", toggleSidebar);

  mobileMenuBtn.addEventListener("click", () => {
    appShell.classList.toggle("mobile-sidebar-open");
  });

  function toggleContextDrawer() {
    const isMobileOrTablet = window.innerWidth <= 1024;
    if (isMobileOrTablet) {
      appShell.classList.toggle("drawer-open");
    } else {
      appShell.classList.toggle("drawer-collapsed");
    }
  }

  contextDrawerToggleBtn.addEventListener("click", toggleContextDrawer);
  closeDrawerBtn.addEventListener("click", () => {
    appShell.classList.remove("drawer-open");
    appShell.classList.add("drawer-collapsed");
  });

  navMemoryBtn.addEventListener("click", () => {
    refreshMemory();
    appShell.classList.remove("drawer-collapsed");
    appShell.classList.add("drawer-open");
  });

  drawerBackdrop.addEventListener("click", () => {
    appShell.classList.remove("mobile-sidebar-open");
    appShell.classList.remove("drawer-open");
  });

  // ------------------------------------------------------------
  // 12. THEME & SETTINGS
  // ------------------------------------------------------------
  function setTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(THEME_KEY, theme);

    if (theme === "dark") {
      themeDarkBtn.classList.add("active");
      themeLightBtn.classList.remove("active");
    } else {
      themeLightBtn.classList.add("active");
      themeDarkBtn.classList.remove("active");
    }
  }

  themeToggleBtn.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme") || "dark";
    setTheme(current === "dark" ? "light" : "dark");
  });

  themeDarkBtn.addEventListener("click", () => setTheme("dark"));
  themeLightBtn.addEventListener("click", () => setTheme("light"));

  navSettingsBtn.addEventListener("click", () => {
    settingsSessionId.textContent = sessionId;
    reducedMotionToggle.checked = localStorage.getItem(REDUCED_MOTION_KEY) === "1";
    settingsModal.classList.remove("hidden");
  });

  settingsModalCloseBtn.addEventListener("click", () => settingsModal.classList.add("hidden"));
  settingsModalBackdrop.addEventListener("click", () => settingsModal.classList.add("hidden"));

  reducedMotionToggle.addEventListener("change", () => {
    const enabled = reducedMotionToggle.checked;
    localStorage.setItem(REDUCED_MOTION_KEY, enabled ? "1" : "0");
    if (enabled) {
      document.body.classList.add("reduced-motion");
    } else {
      document.body.classList.remove("reduced-motion");
    }
  });

  resetSessionBtn.addEventListener("click", () => {
    if (!confirm("Start a completely new session? This will clear session ID.")) return;
    localStorage.removeItem(SESSION_KEY);
    window.location.reload();
  });

  // ------------------------------------------------------------
  // 13. KEYBOARD SHORTCUTS
  // ------------------------------------------------------------
  document.addEventListener("keydown", (e) => {
    // Ctrl+\ or Cmd+\ -> toggle sidebar
    if ((e.ctrlKey || e.metaKey) && e.key === "\\") {
      e.preventDefault();
      toggleSidebar();
    }
    // Ctrl+N or Cmd+N -> new chat
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "n") {
      e.preventDefault();
      createNewChat();
    }
    // Escape -> close modals & drawers
    if (e.key === "Escape") {
      if (!toolModal.classList.contains("hidden")) closeToolModal();
      if (!settingsModal.classList.contains("hidden")) settingsModal.classList.add("hidden");
      appShell.classList.remove("mobile-sidebar-open");
      appShell.classList.remove("drawer-open");
    }
  });

  // ------------------------------------------------------------
  // 14. INITIALIZATION
  // ------------------------------------------------------------
  async function init() {
    // Restore theme
    const savedTheme = localStorage.getItem(THEME_KEY) || "dark";
    setTheme(savedTheme);

    // Restore sidebar state
    if (localStorage.getItem(SIDEBAR_STATE_KEY) === "1") {
      appShell.classList.add("sidebar-collapsed");
    }

    // Restore reduced motion
    if (localStorage.getItem(REDUCED_MOTION_KEY) === "1") {
      document.body.classList.add("reduced-motion");
    }

    // Load initial data concurrently for instant rendering
    await Promise.allSettled([
      loadTools(),
      refreshHistory(),
      refreshMemory(),
      (async () => {
        try {
          const urlParams = new URLSearchParams(window.location.search);
          const targetConvId = urlParams.get("c") || urlParams.get("conv");

          if (targetConvId) {
            await loadConversation(targetConvId);
          } else {
            const statusRes = await fetch("/api/status", { headers: getHeaders() });
            const status = await statusRes.json();
            if (status.conversation_id) {
              await loadConversation(status.conversation_id);
            } else {
              await createNewChat();
            }
          }
        } catch {
          await createNewChat();
        }
      })()
    ]);

    messageInput.focus();
  }

  init();
})();
