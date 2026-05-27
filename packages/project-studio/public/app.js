// html-video studio — vanilla JS app
// Three-pane: sidebar (projects) | chat-pane (agent ↔ user) | right-pane (template + preview + export)

const API = {
  projects: () => fetch('/api/projects').then(r => r.json()),
  createProject: b => fetch('/api/projects', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(b) }).then(r => r.json()),
  getProject: id => fetch(`/api/projects/${id}`).then(r => r.json()),
  deleteProject: id => fetch(`/api/projects/${id}`, { method: 'DELETE' }).then(r => r.json()),
  templates: () => fetch('/api/templates').then(r => r.json()),
  agents: () => fetch('/api/agents').then(r => r.json()),
  setTemplate: (id, tid) => fetch(`/api/projects/${id}/template`, { method: 'PUT', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ template_id: tid }) }).then(r => r.json()),
  setVars: (id, vars) => fetch(`/api/projects/${id}/variables`, { method: 'PUT', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ variables: vars }) }).then(r => r.json()),
  preview: id => fetch(`/api/projects/${id}/preview`, { method: 'POST' }).then(r => r.json()),
  exportMp4: id => fetch(`/api/projects/${id}/export`, { method: 'POST' }).then(r => r.json()),
  getMessages: id => fetch(`/api/projects/${id}/messages`).then(r => r.json()),
  postMessage: (id, body) => fetch(`/api/projects/${id}/messages`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) }),
  uploadFile: (id, file) => {
    const fd = new FormData();
    fd.append('file', file);
    return fetch(`/api/projects/${id}/assets`, { method: 'POST', body: fd }).then(r => r.json());
  },
};

const state = {
  projects: [],
  templates: [],
  agents: [],
  selectedId: null,
  selected: null,
  messages: [],
  messagesEs: null,  // EventSource for streaming
  composing: false,
};

let varsSaveTimer = null;
const debounceVarsSave = () => {
  clearTimeout(varsSaveTimer);
  varsSaveTimer = setTimeout(saveVarsAndPreview, 350);
};

// ============== boot ==============
async function init() {
  await Promise.all([refreshTemplates(), refreshAgents(), refreshProjects()]);
}
async function refreshTemplates() {
  const r = await API.templates();
  state.templates = r.templates ?? [];
}
async function refreshAgents() {
  try {
    const r = await API.agents();
    state.agents = r.agents ?? [];
  } catch { state.agents = []; }
}
async function refreshProjects() {
  const r = await API.projects();
  state.projects = r.projects ?? [];
  renderSidebar();
}

async function selectProject(id) {
  state.selectedId = id;
  const r = await API.getProject(id);
  state.selected = r.project;
  // Load messages
  try {
    const mr = await API.getMessages(id);
    state.messages = mr.messages ?? [];
  } catch { state.messages = []; }
  renderSidebar();
  renderMain();
}

// ============== sidebar ==============
function renderSidebar() {
  const list = document.getElementById('project-list');
  list.innerHTML = '';
  if (!state.projects.length) {
    list.innerHTML = '<div class="empty-list">no projects yet</div>';
    return;
  }
  for (const p of state.projects) {
    const div = document.createElement('div');
    div.className = 'project-row' + (p.id === state.selectedId ? ' active' : '');
    div.innerHTML = `
      <div class="name">${escapeHtml(p.name)}</div>
      <div class="meta">
        <span class="pill ${p.status}">${p.status}</span>
        <span>${p.template_id ? escapeHtml(p.template_id) : 'no template'}</span>
      </div>
    `;
    div.onclick = () => selectProject(p.id);
    list.appendChild(div);
  }
}

// ============== main ==============
function renderMain() {
  const main = document.getElementById('main');
  if (!state.selected) {
    main.innerHTML = `<div class="empty-state"><div><div class="ico">🎬</div><h2>No project selected</h2><p>Click <b>+ New Project</b> on the left to start.</p></div></div>`;
    return;
  }
  const p = state.selected;
  const claudeAgent = state.agents.find(a => a.id === 'claude');
  const agentConnected = claudeAgent?.available;

  main.innerHTML = `
    <div class="workspace">
      <!-- Center: Chat pane -->
      <section class="chat-pane">
        <header class="chat-header">
          <input class="name-input" id="proj-name" value="${escapeAttr(p.name)}" />
          <span class="agent-pill ${agentConnected ? 'connected' : ''}" id="agent-pill">
            ${agentConnected ? '● claude' : '○ no agent'}
          </span>
        </header>
        <div class="chat-log" id="chat-log"></div>
        <div class="composer">
          ${renderPinnedVars()}
          <div class="composer-shell">
            <textarea id="composer-input" placeholder="${agentConnected ? 'Tell the agent what you want to make…' : 'Install Claude Code (claude CLI) to enable the agent. Until then, the chat is informational only.'}" rows="2"></textarea>
            <div class="actions">
              <button class="attach-btn" id="btn-attach" title="Attach file">📎</button>
              <button class="attach-btn" id="btn-mention" title="Mention asset / variable">@</button>
              <button class="send-btn" id="btn-send" ${agentConnected ? '' : 'disabled'}>Send</button>
            </div>
          </div>
          <input type="file" id="file-input" style="display:none" multiple />
        </div>
      </section>

      <!-- Right: template + preview -->
      <section class="right-pane">
        <header class="tpl-header">
          <div class="row">
            <h2>Template</h2>
            <select id="template-select">
              <option value="">— choose —</option>
              ${state.templates.map(t => `<option value="${t.id}" ${t.id === p.templateId ? 'selected' : ''}>${escapeHtml(t.name)}</option>`).join('')}
            </select>
          </div>
          ${p.templateId ? `<div class="tpl-info">${(state.templates.find(t => t.id === p.templateId) || {}).category ?? ''} · ${(state.templates.find(t => t.id === p.templateId) || {}).license?.spdx ?? ''}</div>` : ''}
        </header>
        <div class="preview-area" id="preview-area">
          ${p.templateId
            ? `<div class="preview-frame"><iframe id="preview-iframe" sandbox="allow-scripts" src="about:blank"></iframe></div>
               <div class="vars-grid" id="vars-grid"></div>`
            : `<div class="preview-placeholder">Choose a template above to start.<br>The HTML preview will render here in real time.</div>`}
        </div>
        <footer class="right-footer">
          <span class="status">status: <b style="color: var(--text)">${p.status}</b> · ${p.assets.length} assets</span>
          <button class="export-btn" id="btn-export" ${p.templateId ? '' : 'disabled'}>Export MP4</button>
        </footer>
      </section>
    </div>
  `;

  // Wire up
  document.getElementById('proj-name').addEventListener('blur', async (e) => {
    // v0.2 has no rename API yet — informational only
    if (e.target.value.trim() && e.target.value.trim() !== p.name) {
      toast('Rename will be wired in v0.2.1', '');
      e.target.value = p.name;
    }
  });
  document.getElementById('template-select').onchange = async (e) => {
    const tid = e.target.value;
    if (!tid) return;
    const r = await API.setTemplate(p.id, tid);
    state.selected = r.project;
    renderMain();
    maybePreview();
  };
  document.getElementById('btn-export').onclick = async () => {
    if (!confirm(`Export "${p.name}" to MP4?\n\nv0.1 adapter still uses a stub renderer; the file path will be recorded.`)) return;
    const r = await API.exportMp4(p.id);
    if (r.error) { toast('Export failed: ' + r.error, 'error'); return; }
    state.selected = r.project;
    toast('Exported → ' + r.output_path, 'success');
    renderMain();
    refreshProjects();
  };
  document.getElementById('btn-attach').onclick = () => document.getElementById('file-input').click();
  document.getElementById('file-input').onchange = async (e) => {
    for (const f of e.target.files) await API.uploadFile(p.id, f);
    await selectProject(p.id);
    toast(`Added ${e.target.files.length} file(s)`, 'success');
  };
  document.getElementById('btn-send').onclick = sendMessage;
  document.getElementById('composer-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Render messages + form + preview
  renderChatLog();
  if (p.templateId) {
    renderVarsGrid();
    maybePreview();
  }
}

function renderPinnedVars() {
  const p = state.selected;
  if (!p.templateId) return '';
  const t = state.templates.find(x => x.id === p.templateId);
  if (!t || !t.inputs_schema) return '';
  const props = t.inputs_schema.properties ?? {};
  const required = new Set(t.inputs_schema.required ?? []);
  const items = Object.keys(props).map(k => {
    const set = p.variables[k] !== undefined && p.variables[k] !== '';
    const req = required.has(k);
    const cls = set ? 'set' : (req ? 'required' : '');
    return `<span class="pv-item ${cls}">${escapeHtml(k)}${set ? ' ✓' : (req ? ' *' : '')}</span>`;
  }).join('');
  return `<div class="pinned-vars">
    <div class="pv-title">Template variables · ${t.name}</div>
    <div class="pv-list">${items}</div>
  </div>`;
}

function renderChatLog() {
  const log = document.getElementById('chat-log');
  if (!state.messages.length) {
    log.innerHTML = `<div class="chat-empty"><div><div class="ico">💬</div>
      Talk to your local coding agent to fill the template.<br>
      Try: <i>"Make a logo outro for Open Design with tagline 'Design that evolves itself'"</i></div></div>`;
    return;
  }
  log.innerHTML = state.messages.map(m => renderMessage(m)).join('');
  log.scrollTop = log.scrollHeight;
}

function renderMessage(m) {
  if (m.role === 'user') {
    return `<div class="msg user">${escapeHtml(m.content)}</div>`;
  }
  if (m.role === 'system') {
    return `<div class="msg system">${escapeHtml(m.content)}</div>`;
  }
  if (m.role === 'tool') {
    return `<div class="msg tool-card">
      <div class="tool-name">${escapeHtml(m.tool ?? 'tool')}</div>
      <div class="tool-output">${escapeHtml(String(m.output ?? '').slice(0, 600))}</div>
    </div>`;
  }
  // assistant
  return `<div class="msg assistant">
    <div class="role">${escapeHtml(m.agent ?? 'agent')}</div>
    <div class="body">${renderMarkdown(m.content ?? '')}</div>
  </div>`;
}

function renderMarkdown(text) {
  // minimal: code blocks + inline code + escape rest
  let html = escapeHtml(text);
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, body) =>
    `<pre><code>${body}</code></pre>`);
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  return html;
}

async function sendMessage() {
  if (state.composing) return;
  const ta = document.getElementById('composer-input');
  const text = ta.value.trim();
  if (!text) return;
  ta.value = '';
  state.composing = true;
  document.getElementById('btn-send').disabled = true;

  state.messages.push({ role: 'user', content: text, ts: Date.now() });
  // Placeholder assistant message we'll fill from stream
  const asstIdx = state.messages.length;
  state.messages.push({ role: 'assistant', agent: 'claude', content: '', ts: Date.now() });
  renderChatLog();

  try {
    const res = await fetch(`/api/projects/${state.selected.id}/messages`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ content: text }),
    });
    if (!res.ok || !res.body) {
      state.messages[asstIdx].content = '⚠️ Agent failed to start.';
      renderChatLog();
      state.composing = false;
      document.getElementById('btn-send').disabled = false;
      return;
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      // SSE format: "data: <json>\n\n"
      const lines = buf.split('\n\n');
      buf = lines.pop() ?? '';
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        try {
          const ev = JSON.parse(line.slice(6));
          if (ev.type === 'text') {
            state.messages[asstIdx].content += ev.chunk;
            renderChatLog();
          } else if (ev.type === 'error') {
            state.messages[asstIdx].content += '\n\n⚠️ ' + ev.message;
            renderChatLog();
          } else if (ev.type === 'message_end') {
            // ok
          }
        } catch {}
      }
    }
  } catch (e) {
    state.messages[asstIdx].content += '\n\n⚠️ ' + (e.message ?? e);
    renderChatLog();
  }
  state.composing = false;
  document.getElementById('btn-send').disabled = !state.agents.find(a => a.id === 'claude')?.available;
}

// ============== vars grid ==============
function renderVarsGrid() {
  const p = state.selected;
  const t = state.templates.find(x => x.id === p.templateId);
  if (!t) return;
  const props = (t.inputs_schema ?? {}).properties ?? {};
  const required = new Set((t.inputs_schema ?? {}).required ?? []);
  const grid = document.getElementById('vars-grid');
  if (!grid) return;
  let html = '<h3>Variables</h3>';
  for (const [k, ps] of Object.entries(props)) {
    html += renderField(k, ps, p.variables[k], required.has(k));
  }
  grid.innerHTML = html;

  document.querySelectorAll('[data-field-key]').forEach(el => {
    el.addEventListener('input', debounceVarsSave);
    el.addEventListener('blur', debounceVarsSave);
    el.addEventListener('change', debounceVarsSave);
  });
  document.querySelectorAll('[data-add-row]').forEach(el => {
    el.onclick = () => {
      const key = el.dataset.addRow;
      const vars = collectVars();
      const cur = Array.isArray(vars[key]) ? vars[key] : [];
      cur.push({ label: '', value: 0 });
      vars[key] = cur;
      state.selected.variables = vars;
      renderVarsGrid();
      debounceVarsSave();
    };
  });
  document.querySelectorAll('[data-rm-row]').forEach(el => {
    el.onclick = () => {
      const [key, idx] = el.dataset.rmRow.split('|');
      const vars = collectVars();
      vars[key] = (vars[key] || []).filter((_, i) => i !== Number(idx));
      state.selected.variables = vars;
      renderVarsGrid();
      debounceVarsSave();
    };
  });
}

function renderField(key, schema, value, required) {
  const desc = schema.description ?? '';
  const reqMark = required ? '<span class="req"> *</span>' : '';
  const labelHtml = `<label>${escapeHtml(key)}${reqMark}${desc ? `<span class="desc">${escapeHtml(desc)}</span>` : ''}</label>`;

  if (schema.type === 'string' && schema.enum) {
    return `<div class="field">${labelHtml}<select data-field-key="${key}" data-field-kind="string">
      ${schema.enum.map(v => `<option value="${escapeAttr(v)}" ${value === v ? 'selected' : ''}>${escapeHtml(v)}</option>`).join('')}
    </select></div>`;
  }
  if (schema.type === 'string') {
    const long = (schema.maxLength ?? 0) > 100;
    const v = value ?? schema.default ?? '';
    return `<div class="field">${labelHtml}${long
      ? `<textarea data-field-key="${key}" data-field-kind="string">${escapeHtml(v)}</textarea>`
      : `<input type="text" data-field-key="${key}" data-field-kind="string" value="${escapeAttr(v)}" />`}</div>`;
  }
  if (schema.type === 'number') {
    const v = value ?? schema.default ?? '';
    const min = schema.minimum != null ? `min="${schema.minimum}"` : '';
    const max = schema.maximum != null ? `max="${schema.maximum}"` : '';
    return `<div class="field">${labelHtml}<input type="number" step="any" ${min} ${max}
      data-field-key="${key}" data-field-kind="number" value="${escapeAttr(v)}" /></div>`;
  }
  if (schema.type === 'array' && schema.items?.type === 'object') {
    const arr = Array.isArray(value) ? value : [];
    const cols = Object.keys(schema.items.properties ?? {});
    return `<div class="field">${labelHtml}<div class="table-rows">
      ${arr.map((row, i) => `<div class="table-row">
        ${cols.map(c => `<input data-field-key="${key}" data-field-kind="array-cell"
          data-row="${i}" data-col="${c}" placeholder="${escapeAttr(c)}"
          value="${escapeAttr(row?.[c] ?? '')}" />`).join('')}
        <button class="rm" data-rm-row="${key}|${i}" title="Remove">✕</button>
      </div>`).join('')}
    </div><button class="add-row" data-add-row="${key}">+ Add row</button></div>`;
  }
  // Fallback JSON
  const v = value !== undefined ? JSON.stringify(value, null, 2) : '';
  return `<div class="field">${labelHtml}<textarea data-field-key="${key}" data-field-kind="json">${escapeHtml(v)}</textarea></div>`;
}

function collectVars() {
  const out = { ...(state.selected?.variables ?? {}) };
  const grouped = {};
  document.querySelectorAll('[data-field-key]').forEach(el => {
    const k = el.dataset.fieldKey;
    const kind = el.dataset.fieldKind;
    if (kind === 'array-cell') {
      const row = Number(el.dataset.row), col = el.dataset.col;
      grouped[k] = grouped[k] || [];
      grouped[k][row] = grouped[k][row] || {};
      let v = el.value;
      if (col === 'value' && v !== '' && !Number.isNaN(Number(v))) v = Number(v);
      grouped[k][row][col] = v;
    } else if (kind === 'number') {
      out[k] = el.value === '' ? undefined : Number(el.value);
    } else if (kind === 'json') {
      try { out[k] = el.value === '' ? undefined : JSON.parse(el.value); }
      catch { out[k] = el.value; }
    } else {
      out[k] = el.value;
    }
  });
  for (const [k, v] of Object.entries(grouped)) out[k] = v;
  return out;
}

async function saveVarsAndPreview() {
  if (!state.selected) return;
  const vars = collectVars();
  const r = await API.setVars(state.selected.id, vars);
  state.selected = r.project;
  // Re-render the pinned vars chips (they reflect filled-state)
  const cont = document.querySelector('.composer .pinned-vars');
  if (cont) cont.outerHTML = renderPinnedVars();
  await maybePreview();
}

let previewToken = 0;
async function maybePreview() {
  if (!state.selected || !state.selected.templateId) return;
  const myToken = ++previewToken;
  const r = await API.preview(state.selected.id);
  if (myToken !== previewToken) return;
  if (r.error) { toast('Preview failed: ' + r.error, 'error'); return; }
  state.selected = r.project;
  const iframe = document.getElementById('preview-iframe');
  if (iframe) iframe.src = `/preview/${state.selected.id}?t=${Date.now()}`;
  refreshProjects();
}

// ============== modal / toast / utils ==============
function openModal() { document.getElementById('modal-bg').classList.add('show');
  document.getElementById('modal-name').focus(); }
function closeModal() { document.getElementById('modal-bg').classList.remove('show');
  document.getElementById('modal-name').value = '';
  document.getElementById('modal-intent').value = ''; }
document.getElementById('btn-new').onclick = openModal;
document.getElementById('modal-cancel').onclick = closeModal;
document.getElementById('modal-ok').onclick = async () => {
  const name = document.getElementById('modal-name').value.trim();
  const intent = document.getElementById('modal-intent').value.trim();
  if (!name) { toast('Name is required', 'error'); return; }
  const r = await API.createProject({ name, ...(intent && { intent }) });
  closeModal();
  await refreshProjects();
  await selectProject(r.project.id);
  toast(`Created "${name}"`, 'success');
};
document.getElementById('modal-bg').addEventListener('click', e => { if (e.target.id === 'modal-bg') closeModal(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

function toast(msg, kind = '') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = `toast show ${kind}`;
  setTimeout(() => t.classList.remove('show'), 2500);
}
function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
}
function escapeAttr(s) { return escapeHtml(s); }

init();
