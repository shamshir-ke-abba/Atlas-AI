
const chat = document.getElementById("chat");
const input = document.getElementById("message");
const sendButton = document.getElementById("send");
const stopButton = document.getElementById("stop");
const activity = document.getElementById("activity");
const activityText = document.getElementById("activityText");

const historyEl = document.getElementById("history");
const newChatButton = document.getElementById("newChat");
const toolList = document.getElementById("toolList");
const toolCount = document.getElementById("toolCount");

const stateEl = document.getElementById("state");
const stateDot = document.getElementById("stateDot");
const connectionText = document.getElementById("connectionText");
const connectionDot = document.getElementById("connectionDot");
const modelEl = document.getElementById("model");
const toolsStatusEl = document.getElementById("toolsStatus");
const conversationTitleEl = document.getElementById("conversationTitle");
const webStatusEl = document.getElementById("webStatus");

const toolModal = document.getElementById("toolModal");
const toolModalTitle = document.getElementById("toolModalTitle");
const toolModalDescription = document.getElementById("toolModalDescription");
const toolModalClose = document.getElementById("toolModalClose");
const toolForm = document.getElementById("toolForm");
const toolRun = document.getElementById("toolRun");
const toolInsert = document.getElementById("toolInsert");
const toolResultWrap = document.getElementById("toolResultWrap");
const toolResult = document.getElementById("toolResult");

const SESSION_KEY = "atlas_web_session_v3";
let sessionId = localStorage.getItem(SESSION_KEY);

if (!sessionId) {
  sessionId =
    crypto.randomUUID
      ? crypto.randomUUID()
      : Math.random().toString(36).slice(2) + Date.now();

  localStorage.setItem(SESSION_KEY, sessionId);
}

let conversationId = null;
let abortController = null;
let generating = false;
let userScrolledAway = false;
let activeTool = null;
let activeToolResult = "";

function headers(extra = {}) {
  return {
    "Content-Type": "application/json",
    "X-Atlas-Session": sessionId,
    ...extra
  };
}

function setState(state) {
  stateEl.innerHTML = "";

  const dot = document.createElement("span");
  dot.className =
    "dot " +
    (
      state === "Thinking" ? "thinking" :
      state === "Error" ? "error" :
      state === "Offline" ? "offline" : "ready"
    );

  stateEl.appendChild(dot);
  stateEl.appendChild(document.createTextNode(state));

  connectionText.textContent = state;
  stateDot.className =
    "dot " +
    (
      state === "Thinking" ? "thinking" :
      state === "Error" ? "error" :
      state === "Offline" ? "offline" : "ready"
    );

  connectionDot.className = stateDot.className;
}

function setActivity(visible, text = "Atlas is thinking…") {
  activity.classList.toggle("hidden", !visible);
  activityText.textContent = text;
}

function scrollIfPinned() {
  if (!userScrolledAway) {
    chat.scrollTop = chat.scrollHeight;
  }
}

chat.addEventListener("scroll", () => {
  const distance =
    chat.scrollHeight - chat.scrollTop - chat.clientHeight;

  userScrolledAway = distance > 90;
});

function addMessage(sender, text, type) {
  const row = document.createElement("div");
  row.className = `message-row ${type}`;

  const bubble = document.createElement("div");
  bubble.className = `bubble ${type}`;

  const senderEl = document.createElement("div");
  senderEl.className = "sender";
  senderEl.textContent = sender;

  const body = document.createElement("div");
  body.className = "body";
  body.textContent = text || "";

  bubble.appendChild(senderEl);
  bubble.appendChild(body);

  if (type === "atlas") {
    const copy = document.createElement("button");
    copy.className = "copy";
    copy.title = "Copy";
    copy.textContent = "⧉";

    copy.addEventListener("click", async () => {
      await navigator.clipboard.writeText(body.textContent);
      copy.textContent = "✓";
      setTimeout(() => {
        copy.textContent = "⧉";
      }, 900);
    });

    bubble.appendChild(copy);
  }

  row.appendChild(bubble);
  chat.appendChild(row);
  scrollIfPinned();

  return { row, bubble, body };
}

function renderSources(bubble, sources) {
  if (!Array.isArray(sources) || !sources.length) return;

  const unique = sources
    .map(source => {
      if (typeof source === "string") {
        return { title: source, url: source };
      }
      return source;
    })
    .filter(source => source && source.url);

  if (!unique.length) return;

  const box = document.createElement("div");
  box.className = "sources";

  const title = document.createElement("div");
  title.className = "sources-title";
  title.textContent = "Sources";
  box.appendChild(title);

  unique.slice(0, 8).forEach(source => {
    const a = document.createElement("a");
    a.className = "source-link";
    a.href = source.url;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.textContent = source.title || source.url;
    a.title = source.url;
    box.appendChild(a);
  });

  bubble.appendChild(box);
}

function renderConversation(messages) {
  chat.innerHTML = "";
  userScrolledAway = false;

  if (!messages || !messages.length) {
    addWelcome();
    return;
  }

  for (const msg of messages) {
    const sender =
      msg.sender ||
      (msg.is_user ? "You" : "Atlas");

    const type =
      msg.is_user ||
      sender.toLowerCase() === "you"
        ? "user"
        : "atlas";

    addMessage(
      sender,
      msg.text || msg.content || "",
      type
    );
  }

  chat.scrollTop = chat.scrollHeight;
}

function addWelcome() {
  const greetings = [
    "Hello! I’m Atlas. Ready when you are.",
    "Hi there — I’m Atlas. What can I help you with?",
    "Atlas online. Ask me anything.",
    "Ready to help. What are we working on?"
  ];

  addMessage(
    "Atlas",
    greetings[
      Math.floor(Math.random() * greetings.length)
    ],
    "atlas"
  );
}

async function refreshHistory() {
  try {
    const res = await fetch(
      "/api/conversations",
      {
        headers: {
          "X-Atlas-Session": sessionId
        }
      }
    );

    if (!res.ok) {
      throw new Error("History unavailable");
    }

    const data = await res.json();
    historyEl.innerHTML = "";

    for (const item of data.conversations || []) {
      const row = document.createElement("div");

      row.className =
        "history-item" +
        (
          item.id === conversationId
            ? " active"
            : ""
        );

      const title = document.createElement("span");
      title.className = "history-title";
      title.textContent =
        item.title || "New Chat";

      const del = document.createElement("button");
      del.className = "delete-chat";
      del.title = "Delete";
      del.textContent = "×";

      del.addEventListener("click", async event => {
        event.stopPropagation();

        if (!confirm("Delete this conversation?")) {
          return;
        }

        const deleteRes = await fetch(
          `/api/conversations/${encodeURIComponent(item.id)}`,
          {
            method: "DELETE",
            headers: {
              "X-Atlas-Session": sessionId
            }
          }
        );

        if (!deleteRes.ok) return;

        const deleted = await deleteRes.json();

        if (item.id === conversationId) {
          if (deleted.replacement) {
            await loadConversation(
              deleted.replacement
            );
          } else {
            conversationId = null;
            renderConversation([]);
            conversationTitleEl.textContent = "New Chat";
          }
        }

        await refreshHistory();
      });

      row.appendChild(title);
      row.appendChild(del);

      row.addEventListener("click", async () => {
        await loadConversation(item.id);
      });

      historyEl.appendChild(row);
    }
  } catch (error) {
    console.error(error);
  }
}

async function loadConversation(id) {
  try {
    const res = await fetch(
      `/api/conversations/${encodeURIComponent(id)}`,
      {
        headers: {
          "X-Atlas-Session": sessionId
        }
      }
    );

    if (!res.ok) {
      throw new Error("Conversation unavailable");
    }

    const data = await res.json();

    conversationId = data.id;
    conversationTitleEl.textContent =
      data.title || "New Chat";

    renderConversation(
      data.messages || []
    );

    await refreshHistory();
    await refreshStatus();

  } catch (error) {
    addMessage(
      "Atlas",
      `Could not load conversation: ${error.message}`,
      "atlas"
    );

    setState("Error");
  }
}

async function createNewChat() {
  try {
    const res = await fetch(
      "/api/conversations",
      {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({
          session_id: sessionId
        })
      }
    );

    if (!res.ok) {
      throw new Error(
        "Could not create conversation"
      );
    }

    const data = await res.json();

    conversationId =
      data.conversation_id;

    conversationTitleEl.textContent =
      "New Chat";

    renderConversation([]);

    await refreshHistory();
    await refreshStatus();

    input.focus();

  } catch (error) {
    setState("Error");
    console.error(error);
  }
}

async function refreshStatus() {
  try {
    const res = await fetch(
      "/api/status",
      {
        headers: {
          "X-Atlas-Session": sessionId
        }
      }
    );

    if (!res.ok) {
      throw new Error();
    }

    const data = await res.json();

    modelEl.textContent =
      data.model || "—";

    const toolStatus =
      data.tools || {};

    toolsStatusEl.textContent =
      `${toolStatus.enabled || 0} enabled / ` +
      `${toolStatus.total || 0} total`;

    if (data.conversation_id) {
      conversationId =
        data.conversation_id;

      conversationTitleEl.textContent =
        data.conversation_title ||
        "New Chat";
    }

    setState("Ready");

  } catch {
    setState("Offline");
  }
}

function field(label, type, value, help, name) {
  const wrap = document.createElement("div");
  wrap.className = "tool-field";

  const labelEl = document.createElement("label");
  labelEl.textContent = label;

  let control;

  if (type === "textarea") {
    control = document.createElement("textarea");
    control.value = value || "";
  } else {
    control = document.createElement("input");
    control.type = type || "text";
    control.value = value || "";
  }

  control.dataset.field = name;

  wrap.appendChild(labelEl);
  wrap.appendChild(control);

  if (help) {
    const helpEl = document.createElement("div");
    helpEl.className = "tool-help";
    helpEl.textContent = help;
    wrap.appendChild(helpEl);
  }

  toolForm.appendChild(wrap);
  return control;
}

function selectField(label, options, value, name) {
  const wrap = document.createElement("div");
  wrap.className = "tool-field";

  const labelEl = document.createElement("label");
  labelEl.textContent = label;

  const select = document.createElement("select");
  select.dataset.field = name;

  for (const option of options) {
    const el = document.createElement("option");
    el.value = option;
    el.textContent = option;
    select.appendChild(el);
  }

  select.value = value || options[0];

  wrap.appendChild(labelEl);
  wrap.appendChild(select);
  toolForm.appendChild(wrap);

  return select;
}

function openTool(tool) {
  activeTool = tool;

  toolModalTitle.textContent =
    tool.display_name || tool.name;

  toolModalDescription.textContent =
    tool.description || "Run this Atlas tool directly.";

  toolForm.innerHTML = "";
  toolResultWrap.classList.add("hidden");
  toolResult.textContent = "";
  toolInsert.classList.add("hidden");
  activeToolResult = "";

  const name = String(
    tool.name || ""
  ).toLowerCase();

  if (name === "calculator") {
    field(
      "Expression",
      "text",
      "",
      "Examples: 5/2, 1/2 + 1/3, 2^8",
      "expression"
    );
  } else if (name === "math") {
    field(
      "Math request",
      "textarea",
      "",
      "Examples: integrate 2x^2 + 4 · differentiate x^3",
      "expression"
    );
  } else if (name === "web_search") {
    field(
      "Search query",
      "textarea",
      "",
      "Ask a current-information question or enter a web search.",
      "expression"
    );
  } else if (name === "calendar" || name === "time") {
    const help = document.createElement("div");
    help.className = "tool-help";
    help.textContent =
      name === "calendar"
        ? "Run Calendar to get today's date and day."
        : "Run Time to get the current local time.";
    toolForm.appendChild(help);
  } else if (name === "fitness") {
    selectField(
      "Action",
      [
        "set_profile",
        "get_exercises",
        "generate_workout"
      ],
      "get_exercises",
      "action"
    );

    field(
      "Arguments (JSON)",
      "textarea",
      '{"muscle_group":"chest"}',
      'Examples: {"muscle_group":"chest"} or {"frequency":3}',
      "arguments"
    );
  } else if (name === "nutrition") {
    selectField(
      "Action",
      [
        "set_profile",
        "generate_meal_plan",
        "get_meal_plan"
      ],
      "get_meal_plan",
      "action"
    );

    field(
      "Arguments (JSON)",
      "textarea",
      "{}",
      'Example: {"age":16,"weight":60,"height":170}',
      "arguments"
    );
  } else {
    field(
      "Input",
      "textarea",
      "",
      "This tool accepts a generic input.",
      "expression"
    );
  }

  toolModal.classList.remove("hidden");

  setTimeout(() => {
    const first =
      toolForm.querySelector(
        "input, textarea, select"
      );

    if (first) first.focus();
  }, 20);
}

function closeTool() {
  activeTool = null;
  toolModal.classList.add("hidden");
}

function getToolPayload() {
  const name =
    String(activeTool?.name || "")
      .toLowerCase();

  const inputs =
    toolForm.querySelectorAll(
      "[data-field]"
    );

  const values = {};

  for (const inputEl of inputs) {
    values[inputEl.dataset.field] =
      inputEl.value;
  }

  let argumentsObject = {};

  if (values.arguments) {
    try {
      argumentsObject =
        JSON.parse(values.arguments || "{}");
    } catch {
      throw new Error(
        "Arguments must be valid JSON."
      );
    }
  }

  return {
    session_id: sessionId,
    action: values.action || "",
    expression: values.expression || "",
    arguments: argumentsObject
  };
}

async function runActiveTool() {
  if (!activeTool) return;

  toolRun.disabled = true;
  toolRun.textContent = "Running…";
  toolResultWrap.classList.add("hidden");
  toolInsert.classList.add("hidden");

  try {
    const payload =
      getToolPayload();

    const res = await fetch(
      `/api/tools/${encodeURIComponent(activeTool.name)}/run`,
      {
        method: "POST",
        headers: headers(),
        body: JSON.stringify(payload)
      }
    );

    const data = await res.json();

    if (!res.ok) {
      throw new Error(
        data.detail || "Tool execution failed."
      );
    }

    activeToolResult =
      String(data.result ?? "");

    toolResult.textContent =
      activeToolResult;

    toolResultWrap.classList.remove("hidden");
    toolInsert.classList.remove("hidden");

    webStatusEl.textContent =
      activeTool.name === "web_search"
        ? "Web Search executed"
        : "Tool executed";

  } catch (error) {
    toolResult.textContent =
      `Error: ${error.message}`;

    toolResultWrap.classList.remove(
      "hidden"
    );

  } finally {
    toolRun.disabled = false;
    toolRun.textContent = "Run Tool";
  }
}

function insertToolResultIntoChat() {
  if (!activeToolResult) return;

  const message =
    addMessage(
      activeTool?.display_name ||
        activeTool?.name ||
        "Tool",
      activeToolResult,
      "atlas"
    );

  userScrolledAway = false;
  chat.scrollTop = chat.scrollHeight;

  closeTool();
  return message;
}

async function loadTools() {
  try {
    const res = await fetch("/api/tools");

    if (!res.ok) {
      throw new Error(
        "Tool catalog unavailable"
      );
    }

    const data = await res.json();
    const tools = data.tools || [];

    toolList.innerHTML = "";
    toolCount.textContent = tools.length;

    for (const tool of tools) {
      const card =
        document.createElement("button");

      card.type = "button";
      card.className = "tool-card";
      card.title =
        `Open ${tool.display_name || tool.name}`;

      const icon =
        document.createElement("div");

      icon.className = "tool-icon";
      icon.textContent =
        tool.icon || "🧩";

      const content =
        document.createElement("div");

      const name =
        document.createElement("div");

      name.className = "tool-name";
      name.textContent =
        tool.display_name ||
        tool.name;

      const desc =
        document.createElement("div");

      desc.className = "tool-desc";
      desc.textContent =
        tool.description || "";

      content.appendChild(name);
      content.appendChild(desc);

      card.appendChild(icon);
      card.appendChild(content);

      // THIS was previously missing.
      card.addEventListener(
        "click",
        () => openTool(tool)
      );

      toolList.appendChild(card);
    }

  } catch (error) {
    console.error(
      "Tool loading failed:",
      error
    );
  }
}

function updateClock() {
  const now = new Date();

  document.getElementById(
    "clockTime"
  ).textContent =
    now.toLocaleTimeString(
      [],
      {
        hour: "2-digit",
        minute: "2-digit"
      }
    );

  document.getElementById(
    "clockDate"
  ).textContent =
    now.toLocaleDateString(
      [],
      {
        weekday: "long",
        day: "numeric",
        month: "short",
        year: "numeric"
      }
    );
}

stopButton.addEventListener(
  "click",
  () => {
    if (abortController) {
      abortController.abort();
    }
  }
);

sendButton.addEventListener(
  "click",
  sendMessage
);

newChatButton.addEventListener(
  "click",
  createNewChat
);

toolModalClose.addEventListener(
  "click",
  closeTool
);

toolRun.addEventListener(
  "click",
  runActiveTool
);

toolInsert.addEventListener(
  "click",
  insertToolResultIntoChat
);

toolModal.addEventListener(
  "click",
  event => {
    if (event.target === toolModal) {
      closeTool();
    }
  }
);

document.addEventListener(
  "keydown",
  event => {
    if (
      event.key === "Escape" &&
      !toolModal.classList.contains("hidden")
    ) {
      closeTool();
    }
  }
);

input.addEventListener(
  "input",
  () => {
    input.style.height = "auto";
    input.style.height =
      Math.min(
        input.scrollHeight,
        140
      ) + "px";
  }
);

input.addEventListener(
  "keydown",
  event => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();
      sendMessage();
    }
  }
);

async function sendMessage() {
  if (generating) return;

  const text =
    input.value.trim();

  if (!text) return;

  if (!conversationId) {
    await createNewChat();
  }

  addMessage(
    "You",
    text,
    "user"
  );

  input.value = "";
  input.style.height = "auto";

  const atlas =
    addMessage(
      "Atlas",
      "",
      "atlas"
    );

  const body = atlas.body;

  generating = true;
  abortController =
    new AbortController();

  sendButton.classList.add("hidden");
  stopButton.classList.remove("hidden");
  input.disabled = true;

  setState("Thinking");
  setActivity(
    true,
    "Atlas is thinking…"
  );

  try {
    const response =
      await fetch(
        "/api/chat",
        {
          method: "POST",
          headers: headers(),
          body: JSON.stringify({
            message: text,
            conversation_id: conversationId,
            session_id: sessionId
          }),
          signal: abortController.signal
        }
      );

    if (!response.ok) {
      throw new Error(
        `HTTP ${response.status}`
      );
    }

    if (!response.body) {
      throw new Error(
        "Streaming is unavailable."
      );
    }

    const reader =
      response.body.getReader();

    const decoder =
      new TextDecoder("utf-8");

    let buffer = "";

    while (true) {
      const {
        value,
        done
      } = await reader.read();

      if (done) break;

      buffer += decoder.decode(
        value,
        { stream: true }
      );

      const lines =
        buffer.split("\n");

      buffer =
        lines.pop() || "";

      for (const line of lines) {
        if (!line.trim()) continue;

        let event;

        try {
          event = JSON.parse(line);
        } catch {
          continue;
        }

        if (event.type === "chunk") {
          setActivity(
            true,
            "Atlas is writing…"
          );

          body.textContent +=
            event.text || "";

          scrollIfPinned();
        }

        if (event.type === "done") {
          conversationId =
            event.conversation_id ||
            conversationId;

          conversationTitleEl.textContent =
            event.title ||
            conversationTitleEl.textContent;

          const sources =
            event.web?.sources || [];

          if (sources.length) {
            renderSources(
              atlas.bubble,
              sources
            );

            webStatusEl.textContent =
              `Searched: ${
                event.web.query || "web"
              }`;
          } else {
            webStatusEl.textContent =
              "Ready for live search";
          }

          await refreshHistory();
        }

        if (event.type === "error") {
          throw new Error(
            event.message ||
            "Atlas error"
          );
        }
      }
    }

  } catch (error) {
    if (error.name === "AbortError") {
      body.textContent +=
        "\n\n[Generation stopped]";
    } else {
      body.textContent =
        `Error: ${error.message}`;
      setState("Error");
    }

  } finally {
    generating = false;
    abortController = null;
    input.disabled = false;

    sendButton.classList.remove(
      "hidden"
    );

    stopButton.classList.add(
      "hidden"
    );

    setActivity(false);

    if (
      stateEl.textContent !==
      "Error"
    ) {
      setState("Ready");
    }

    input.focus();

    await refreshStatus();

    scrollIfPinned();
  }
}

async function init() {
  updateClock();
  setInterval(
    updateClock,
    1000
  );

  await loadTools();
  await refreshHistory();

  try {
    const statusRes =
      await fetch(
        "/api/status",
        {
          headers: {
            "X-Atlas-Session":
              sessionId
          }
        }
      );

    const status =
      await statusRes.json();

    if (status.conversation_id) {
      conversationId =
        status.conversation_id;

      await loadConversation(
        conversationId
      );

    } else {
      await createNewChat();
    }

  } catch {
    await createNewChat();
  }

  input.focus();
}

init();
