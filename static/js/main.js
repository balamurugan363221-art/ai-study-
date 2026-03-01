/* ═══════════════════════════════════════════════════
   AI Study Buddy – Frontend Logic
   ═══════════════════════════════════════════════════ */

// ── Theme toggle ──────────────────────────────────────
const themeBtn = document.getElementById("theme-toggle");
if (themeBtn) {
  const saved = localStorage.getItem("theme") || "dark";
  document.documentElement.setAttribute("data-theme", saved);

  themeBtn.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme");
    const next    = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
  });
}

// ── Section navigation ────────────────────────────────
document.querySelectorAll(".nav-item[data-target]").forEach(link => {
  link.addEventListener("click", e => {
    e.preventDefault();
    const target = link.dataset.target;

    // Toggle sections
    document.querySelectorAll("section.card").forEach(s => {
      s.classList.toggle("section-active", s.id === target);
      s.classList.toggle("hidden", s.id !== target);
    });

    // Toggle active nav state
    document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
    link.classList.add("active");
  });
});

// ── Chat ──────────────────────────────────────────────
const chatBox    = document.getElementById("chat-box");
const questionIn = document.getElementById("question-input");
const askBtn     = document.getElementById("ask-btn");
const chatError  = document.getElementById("chat-error");

function appendMsg(type, text) {
  const wrap = document.createElement("div");
  wrap.className = "chat-msg";

  const label = document.createElement("div");
  label.className = "msg-label";
  label.textContent = type === "user" ? "You" : "AI Study Buddy";

  const bubble = document.createElement("div");
  bubble.className = type === "user" ? "msg-user" : "msg-ai";
  bubble.textContent = text;

  wrap.appendChild(label);
  wrap.appendChild(bubble);
  chatBox.appendChild(wrap);
  chatBox.scrollTop = chatBox.scrollHeight;
  return wrap;
}

function showLoading() {
  const el = document.createElement("div");
  el.className = "msg-loading";
  el.id = "loading-dots";
  el.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
  chatBox.appendChild(el);
  chatBox.scrollTop = chatBox.scrollHeight;
}
function hideLoading() {
  const el = document.getElementById("loading-dots");
  if (el) el.remove();
}

async function sendQuestion() {
  const q = (questionIn.value || "").trim();
  if (!q) return;

  chatError.classList.add("hidden");
  questionIn.value = "";
  questionIn.style.height = "";

  appendMsg("user", q);
  showLoading();
  askBtn.disabled = true;
  askBtn.textContent = "…";

  try {
    const res  = await fetch("/api/ask", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ question: q }),
    });
    const data = await res.json();
    hideLoading();
    if (res.ok) {
      appendMsg("ai", data.answer);
    } else {
      chatError.textContent = data.error || "Something went wrong.";
      chatError.classList.remove("hidden");
    }
  } catch {
    hideLoading();
    chatError.textContent = "Network error – please try again.";
    chatError.classList.remove("hidden");
  } finally {
    askBtn.disabled = false;
    askBtn.textContent = "Ask ⚡";
  }
}

if (askBtn) {
  askBtn.addEventListener("click", sendQuestion);
  questionIn.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendQuestion(); }
  });
}

// ── Study Tracker ─────────────────────────────────────
const subjectIn    = document.getElementById("subject-input");
const hoursIn      = document.getElementById("hours-input");
const logBtn       = document.getElementById("log-btn");
const progressGrid = document.getElementById("progress-grid");
const trackerError = document.getElementById("tracker-error");

function renderProgress(progress, totalHours) {
  if (!progressGrid) return;

  const max = Math.max(...progress.map(p => p.total), 1);
  progressGrid.innerHTML = progress.map(p => `
    <div class="progress-card">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.35rem;">
        <div class="progress-subject">${escHtml(p.subject)}</div>
        <div class="progress-hours">${parseFloat(p.total).toFixed(1)} hrs</div>
      </div>
      <div class="progress-bar-wrap">
        <div class="progress-bar" style="width:${Math.min(p.total / max * 100, 100)}%"></div>
      </div>
    </div>
  `).join("");

  // Update header stats
  const statNums = document.querySelectorAll(".stat-num");
  if (statNums[0]) statNums[0].textContent = parseFloat(totalHours).toFixed(1);
}

function escHtml(str) {
  return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

if (logBtn) {
  // Pre-render server-side data
  if (window.INITIAL_PROGRESS && window.INITIAL_PROGRESS.length) {
    renderProgress(window.INITIAL_PROGRESS, parseFloat(
      document.querySelector(".stat-num")?.textContent || 0
    ));
  }

  logBtn.addEventListener("click", async () => {
    const subject = (subjectIn.value || "").trim();
    const hours   = hoursIn.value;

    trackerError.classList.add("hidden");

    if (!subject || !hours) {
      trackerError.textContent = "Please fill in both subject and hours.";
      trackerError.classList.remove("hidden");
      return;
    }

    logBtn.disabled    = true;
    logBtn.textContent = "Logging…";

    try {
      const res  = await fetch("/api/study", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ subject, hours: parseFloat(hours) }),
      });
      const data = await res.json();
      if (res.ok) {
        subjectIn.value = "";
        hoursIn.value   = "";
        renderProgress(data.progress, data.total_hours);
      } else {
        trackerError.textContent = data.error || "Something went wrong.";
        trackerError.classList.remove("hidden");
      }
    } catch {
      trackerError.textContent = "Network error – please try again.";
      trackerError.classList.remove("hidden");
    } finally {
      logBtn.disabled    = false;
      logBtn.textContent = "Log Session";
    }
  });
}
