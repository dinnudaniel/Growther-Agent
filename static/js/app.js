/* ======================================================
   Growther Agent — Frontend JavaScript
   Handles: form submit, SSE streaming, chat UI, markdown
   ====================================================== */

"use strict";

// ── Simple Markdown renderer ──────────────────────────────────────────────
function renderMarkdown(text) {
  // Escape HTML first (for user messages)
  // For agent messages we want to render markdown so we process it.
  let html = text
    // Code blocks (before inline)
    .replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) =>
      `<pre><code class="${lang}">${escapeHtml(code.trim())}</code></pre>`)
    // Inline code
    .replace(/`([^`]+)`/g, (_, code) => `<code>${escapeHtml(code)}</code>`)
    // Bold **text** and __text__
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/__(.*?)__/g, '<strong>$1</strong>')
    // Italic *text* and _text_
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/_(.*?)_/g, '<em>$1</em>')
    // Horizontal rules
    .replace(/^---$/gm, '<hr>')
    // H1–H3
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm,  '<h2>$1</h2>')
    .replace(/^# (.+)$/gm,   '<h1>$1</h1>')
    // Blockquotes
    .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
    // Unordered lists
    .replace(/^\s*[-*] (.+)$/gm, '<li>$1</li>')
    // Ordered lists
    .replace(/^\s*\d+\. (.+)$/gm, '<li>$1</li>');

  // Wrap consecutive <li> in <ul>
  html = html.replace(/(<li>.*<\/li>\n?)+/g, match => `<ul>${match}</ul>`);

  // Convert double newlines to paragraphs, single newlines to <br> inside paragraphs
  html = html.split(/\n\n+/).map(block => {
    block = block.trim();
    if (!block) return '';
    // Don't wrap blocks that are already HTML elements
    if (/^<(h[1-6]|ul|ol|li|pre|hr|blockquote|div)/.test(block)) return block;
    return `<p>${block.replace(/\n/g, '<br>')}</p>`;
  }).join('\n');

  return html;
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Message builder ───────────────────────────────────────────────────────
function createMessageEl(role) {
  const wrap = document.createElement('div');
  wrap.className = `message ${role}-message`;

  const avatar = document.createElement('div');
  avatar.className = 'message-avatar';
  avatar.textContent = role === 'agent' ? '⚡' : '👤';

  const content = document.createElement('div');
  content.className = 'message-content';

  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';

  content.appendChild(bubble);
  wrap.appendChild(avatar);
  wrap.appendChild(content);
  return { wrap, bubble };
}

function scrollToBottom(container) {
  container.scrollTop = container.scrollHeight;
}

// ── SSE streaming helper ──────────────────────────────────────────────────
async function streamChat(url, body, onChunk, onDone, onError) {
  try {
    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ error: resp.statusText }));
      onError(err.error || 'Server error');
      return;
    }

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buf = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });

      const lines = buf.split('\n');
      buf = lines.pop(); // keep incomplete line in buffer

      for (const line of lines) {
        if (!line.startsWith('data:')) continue;
        const json = line.slice(5).trim();
        if (!json) continue;
        try {
          const data = JSON.parse(json);
          if (data.done) {
            onDone();
            return;
          }
          if (data.chunk) onChunk(data.chunk);
        } catch (_) { /* ignore parse errors */ }
      }
    }
    onDone();
  } catch (err) {
    onError(err.message);
  }
}

// ======================================================
// PAGE: DASHBOARD
// ======================================================
function initDashboard() {
  const messagesEl = document.getElementById('chat-messages');
  const inputEl    = document.getElementById('chat-input');
  const sendBtn    = document.getElementById('send-btn');
  const loadingMsg = document.getElementById('loading-message');
  const quickBtns  = document.querySelectorAll('.quick-action-btn');
  const disconnectBtn = document.getElementById('disconnect-btn');

  if (!messagesEl) return; // not on dashboard

  let isStreaming = false;
  let rawBuffer = ''; // accumulates text for the current streaming bubble

  function setInputEnabled(enabled) {
    inputEl.disabled = !enabled;
    sendBtn.disabled = !enabled;
    if (enabled) inputEl.focus();
  }

  // ── Render a complete agent message (replaces streaming bubble)
  function finalizeAgentMessage(bubble, text) {
    bubble.classList.remove('streaming');
    bubble.innerHTML = renderMarkdown(text);
    scrollToBottom(messagesEl);
  }

  // ── Append user message
  function appendUserMessage(text) {
    const { wrap, bubble } = createMessageEl('user');
    bubble.textContent = text;
    messagesEl.appendChild(wrap);
    scrollToBottom(messagesEl);
  }

  // ── Start streaming agent message
  function startAgentStream() {
    const { wrap, bubble } = createMessageEl('agent');
    bubble.classList.add('streaming');
    messagesEl.appendChild(wrap);
    scrollToBottom(messagesEl);
    return bubble;
  }

  // ── Initial auto-analysis ─────────────────────────────────────────────
  let rawInit = '';

  // Remove the static loading message, replace with a real streaming bubble
  const initBubble = startAgentStream();
  if (loadingMsg) loadingMsg.remove();

  isStreaming = true;

  streamChat(
    '/chat/init', {},
    (chunk) => {
      rawInit += chunk;
      // Strip internal tool notices for display
      const display = rawInit.replace(/_\[Running .*?\.\.\.\]_\n\n/g, '');
      initBubble.innerHTML = renderMarkdown(display);
      initBubble.classList.add('streaming');
      scrollToBottom(messagesEl);
    },
    () => {
      const display = rawInit.replace(/_\[Running .*?\.\.\.\]_\n\n/g, '');
      finalizeAgentMessage(initBubble, display);
      isStreaming = false;
      setInputEnabled(true);
    },
    (err) => {
      initBubble.classList.remove('streaming');
      initBubble.innerHTML = `<em style="color:#f87171">Error: ${escapeHtml(err)}</em>`;
      isStreaming = false;
      setInputEnabled(true);
    }
  );

  // ── Send user message ──────────────────────────────────────────────────
  function sendMessage(text) {
    if (!text.trim() || isStreaming) return;
    isStreaming = true;
    setInputEnabled(false);
    inputEl.value = '';
    inputEl.style.height = 'auto';

    appendUserMessage(text);

    let raw = '';
    const bubble = startAgentStream();

    streamChat(
      '/chat/message', { message: text },
      (chunk) => {
        raw += chunk;
        const display = raw.replace(/_\[Running .*?\.\.\.\]_\n\n/g, '');
        bubble.innerHTML = renderMarkdown(display);
        bubble.classList.add('streaming');
        scrollToBottom(messagesEl);
      },
      () => {
        const display = raw.replace(/_\[Running .*?\.\.\.\]_\n\n/g, '');
        finalizeAgentMessage(bubble, display);
        isStreaming = false;
        setInputEnabled(true);
      },
      (err) => {
        bubble.classList.remove('streaming');
        bubble.innerHTML = `<em style="color:#f87171">Error: ${escapeHtml(err)}</em>`;
        isStreaming = false;
        setInputEnabled(true);
      }
    );
  }

  // ── Input events ───────────────────────────────────────────────────────
  sendBtn.addEventListener('click', () => sendMessage(inputEl.value));

  inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputEl.value);
    }
  });

  // Auto-resize textarea
  inputEl.addEventListener('input', () => {
    inputEl.style.height = 'auto';
    inputEl.style.height = Math.min(inputEl.scrollHeight, 140) + 'px';
  });

  // Quick action buttons
  quickBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const msg = btn.dataset.message;
      if (msg && !isStreaming) sendMessage(msg);
    });
  });

  // Disconnect
  if (disconnectBtn) {
    disconnectBtn.addEventListener('click', async () => {
      await fetch('/disconnect', { method: 'POST' });
      window.location.href = '/';
    });
  }
}

// ======================================================
// PAGE: CONNECT FORM
// ======================================================
function initConnectForm() {
  const form = document.getElementById('connect-form');
  if (!form) return;

  const platform = form.dataset.platform;

  // Toggle Shorts fields (YouTube only)
  const shortsCheck = document.getElementById('uses_shorts');
  const shortsFields = document.getElementById('shorts-fields');
  if (shortsCheck && shortsFields) {
    shortsCheck.addEventListener('change', () => {
      shortsFields.classList.toggle('hidden', !shortsCheck.checked);
    });
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const data = new FormData(form);
    const profile = { platform };

    // Collect all form values
    for (const [key, value] of data.entries()) {
      if (key === 'uses_shorts' || key === 'has_x_premium') {
        profile[key] = true; // checkbox: present = checked
      } else if (value !== '') {
        // Try to parse as number for numeric fields
        const num = Number(value);
        profile[key] = isNaN(num) || value.includes(',') ? value : num;
      }
    }

    // Ensure booleans default to false when not checked
    if (!profile.uses_shorts)   profile.uses_shorts = false;
    if (!profile.has_x_premium) profile.has_x_premium = false;

    // Show loading overlay
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.innerHTML = `
      <div class="loading-spinner"></div>
      <p>Connecting your account…</p>
    `;
    document.body.appendChild(overlay);

    try {
      const resp = await fetch('/save-profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ platform, profile }),
      });
      const result = await resp.json();
      if (result.redirect) {
        window.location.href = result.redirect;
      } else {
        overlay.remove();
        alert(result.error || 'Something went wrong. Please try again.');
      }
    } catch (err) {
      overlay.remove();
      alert('Network error. Please check your connection and try again.');
    }
  });
}

// ======================================================
// PAGE: HOME
// ======================================================
function initHome() {
  // Smooth scroll to platforms section
  const ctaBtn = document.querySelector('.cta-button');
  if (ctaBtn) {
    ctaBtn.addEventListener('click', (e) => {
      const target = document.getElementById('platforms');
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  }

  // Stagger animate cards on load
  const cards = document.querySelectorAll('.platform-card');
  cards.forEach((card, i) => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    card.style.transition = `opacity .4s ease ${i * 0.08}s, transform .4s ease ${i * 0.08}s`;
    setTimeout(() => {
      card.style.opacity = '1';
      card.style.transform = 'translateY(0)';
    }, 100 + i * 80);
  });
}

// ── Init ──────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initHome();
  initConnectForm();
  initDashboard();
});
