/**
 * Ed Tutor Assistant — content script
 * Injects a sidebar into Ed Discussion question pages.
 * Reads the question title + body, calls the local backend, and
 * lets the tutor insert the suggested answer into the reply box.
 */

const BACKEND = "http://localhost:8765";

// ── DOM helpers ───────────────────────────────────────────────────────────────

function getQuestionTitle() {
  const selectors = [
    "h2.disthrb-title",           // confirmed Ed Discussion markup
    "[class*='disthrb-title']",
    "h1.thread-title",
    "[class*='thread-title']",
    "h1",
  ];
  for (const sel of selectors) {
    const el = document.querySelector(sel);
    if (el && el.innerText.trim()) {
      // Strip the #37 anchor text from the end
      const clone = el.cloneNode(true);
      clone.querySelectorAll("a").forEach(a => a.remove());
      return clone.innerText.trim();
    }
  }
  return document.title.replace(" - Ed Discussion", "").trim();
}

function getQuestionBody() {
  const selectors = [
    ".disthrb-body [data-testid='content']",   // confirmed Ed Discussion markup
    ".disthrb-body .amber-display-document",
    "[class*='disthrb-body'] [class*='content']",
    "[class*='thread-body'] [class*='content']",
  ];
  for (const sel of selectors) {
    const el = document.querySelector(sel);
    if (el && el.innerText.trim()) return el.innerText.trim().slice(0, 1500);
  }
  return "";
}

function getReplyBox() {
  // Try to find a ProseMirror / contenteditable reply editor
  const selectors = [
    "[class*='reply'] [contenteditable='true']",
    "[class*='Reply'] [contenteditable='true']",
    "[class*='editor'] [contenteditable='true']",
    "[contenteditable='true']",
  ];
  for (const sel of selectors) {
    const el = document.querySelector(sel);
    if (el) return el;
  }
  return null;
}

function insertIntoReplyBox(text) {
  const box = getReplyBox();
  if (!box) {
    alert("Could not find the reply box. Please click inside it and try pasting manually.");
    return false;
  }
  // Focus and set value / innerText depending on element type
  box.focus();
  // For ProseMirror / rich editors: dispatch an input event
  document.execCommand("selectAll", false, null);
  document.execCommand("insertText", false, text);
  return true;
}

// ── Sidebar markup ────────────────────────────────────────────────────────────

function buildSidebar() {
  const sidebar = document.createElement("div");
  sidebar.id = "eta-sidebar";
  sidebar.innerHTML = `
    <div id="eta-header">
      <span>🎓 Tutor Assistant</span>
      <button id="eta-close" title="Hide sidebar">✕</button>
    </div>
    <div id="eta-body">
      <button id="eta-suggest-btn">Suggest Answer</button>
      <div id="eta-status"></div>

      <div id="eta-answer-box">
        <div id="eta-answer-label">Suggested Reply</div>
        <textarea id="eta-answer-text"></textarea>
        <button id="eta-insert-btn">Insert into Reply Box</button>
      </div>

      <div id="eta-matches">
        <div id="eta-matches-label">Matched Threads</div>
        <div id="eta-matches-list"></div>
      </div>
    </div>
  `;
  return sidebar;
}

function buildModal() {
  const overlay = document.createElement("div");
  overlay.id = "eta-modal-overlay";
  overlay.innerHTML = `
    <div id="eta-modal">
      <div id="eta-modal-header">
        <div id="eta-modal-header-title"></div>
        <button id="eta-modal-close">✕</button>
      </div>
      <div id="eta-modal-body"></div>
    </div>
  `;
  overlay.addEventListener("click", e => {
    if (e.target === overlay) closeModal();
  });
  return overlay;
}

function openModal(match) {
  document.getElementById("eta-modal-header-title").textContent =
    `#${match.number} — ${match.title}`;

  const body = document.getElementById("eta-modal-body");
  body.innerHTML = "";

  // Question section
  const qLabel = document.createElement("div");
  qLabel.className = "eta-modal-section-label eta-modal-q-label";
  qLabel.textContent = "Question";
  const qText = document.createElement("div");
  qText.className = "eta-modal-text eta-modal-q-text";
  qText.textContent = match.question || "(no question text)";
  body.appendChild(qLabel);
  body.appendChild(qText);

  // Answer sections
  (match.answers || []).forEach((ans, i) => {
    const aLabel = document.createElement("div");
    aLabel.className = "eta-modal-section-label eta-modal-a-label";
    aLabel.textContent = match.answers.length > 1 ? `Answer ${i + 1}` : "Answer";
    const aText = document.createElement("div");
    aText.className = "eta-modal-text eta-modal-a-text";
    aText.textContent = ans;
    body.appendChild(aLabel);
    body.appendChild(aText);
  });

  document.getElementById("eta-modal-overlay").classList.add("eta-visible");
}

function closeModal() {
  document.getElementById("eta-modal-overlay").classList.remove("eta-visible");
}

function buildToggle() {
  const btn = document.createElement("button");
  btn.id = "eta-toggle";
  btn.title = "Open Tutor Assistant";
  btn.textContent = "Tutor Assistant";
  return btn;
}

// ── Logic ─────────────────────────────────────────────────────────────────────

function setStatus(msg, color = "#666") {
  const el = document.getElementById("eta-status");
  if (el) { el.textContent = msg; el.style.color = color; }
}

async function fetchSuggestion() {
  const title = getQuestionTitle();
  const body = getQuestionBody();
  console.log("[ETA] title:", title);
  console.log("[ETA] body:", body?.slice(0, 150));

  const btn = document.getElementById("eta-suggest-btn");
  btn.disabled = true;
  setStatus("Searching past Q&A records…");
  document.getElementById("eta-answer-box").style.display = "none";
  document.getElementById("eta-matches").style.display = "none";

  try {
    const res = await fetch(`${BACKEND}/suggest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, body }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      setStatus(`Error: ${err.detail || res.statusText}`, "#C00000");
      return;
    }

    const data = await res.json();

    // Fill answer textarea
    document.getElementById("eta-answer-text").value = data.suggested_answer;
    document.getElementById("eta-answer-box").style.display = "flex";

    // Fill matched threads
    const list = document.getElementById("eta-matches-list");
    list.innerHTML = "";
    for (const m of data.matched_threads) {
      const div = document.createElement("div");
      div.className = "eta-match";
      const snippet = m.answers[0] ? m.answers[0].slice(0, 120) + (m.answers[0].length > 120 ? "…" : "") : "";
      div.innerHTML = `
        <div class="eta-match-title">#${m.number} — ${escHtml(m.title)}</div>
        <div class="eta-match-snippet">${escHtml(snippet)}</div>
        <div class="eta-match-score">Similarity: ${(m.score * 100).toFixed(0)}%  · <em>click to view full thread</em></div>
      `;
      div.addEventListener("click", () => openModal(m));
      list.appendChild(div);
    }
    document.getElementById("eta-matches").style.display = "block";
    setStatus("Done. Edit the reply below if needed.", "#375623");

  } catch (e) {
    setStatus("Cannot reach backend (is it running on port 8765?)", "#C00000");
  } finally {
    btn.disabled = false;
  }
}

function escHtml(str) {
  return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

// ── Init ──────────────────────────────────────────────────────────────────────

function init() {
  if (document.getElementById("eta-sidebar")) return; // already injected

  const sidebar = buildSidebar();
  const toggle = buildToggle();
  const modal = buildModal();
  document.body.appendChild(sidebar);
  document.body.appendChild(toggle);
  document.body.appendChild(modal);

  document.getElementById("eta-modal-close").addEventListener("click", closeModal);
  document.addEventListener("keydown", e => { if (e.key === "Escape") closeModal(); });

  // Wire up buttons
  document.getElementById("eta-close").addEventListener("click", () => {
    sidebar.classList.add("eta-hidden");
    toggle.style.display = "block";
  });

  toggle.addEventListener("click", () => {
    sidebar.classList.remove("eta-hidden");
    toggle.style.display = "none";
  });

  document.getElementById("eta-suggest-btn").addEventListener("click", fetchSuggestion);

  document.getElementById("eta-insert-btn").addEventListener("click", () => {
    const text = document.getElementById("eta-answer-text").value;
    if (insertIntoReplyBox(text)) {
      setStatus("Inserted into reply box.", "#375623");
    }
  });
}

// Wait for Ed Discussion to finish rendering, then inject
function waitAndInit() {
  // Only activate on question/post pages
  if (!window.location.href.includes("/discussion/")) return;
  // Give Ed's React app a moment to hydrate
  setTimeout(init, 1500);
}

waitAndInit();

// Also re-init on client-side navigation (Ed is a SPA)
let lastUrl = location.href;
new MutationObserver(() => {
  if (location.href !== lastUrl) {
    lastUrl = location.href;
    waitAndInit();
  }
}).observe(document, { subtree: true, childList: true });
