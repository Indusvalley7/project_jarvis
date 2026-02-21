/**
 * Jarvis Control Tower — Dashboard JS
 * Polls APIs, renders service status, runs, workflows, and run detail modals.
 */

const POLL_INTERVAL = 15000;

// ── Initialization ──────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    updateClock();
    setInterval(updateClock, 1000);

    loadDiagnostics();
    loadWorkflows();
    loadRuns();

    setInterval(loadDiagnostics, POLL_INTERVAL);
    setInterval(loadWorkflows, POLL_INTERVAL);
    setInterval(loadRuns, POLL_INTERVAL);
});

// ── Clock ───────────────────────────────────────────────────────
function updateClock() {
    const now = new Date();
    document.getElementById('clock').textContent = now.toLocaleTimeString('en-GB');
}

// ── Diagnostics ─────────────────────────────────────────────────
async function loadDiagnostics() {
    try {
        const resp = await fetch('/diagnostics');
        const data = await resp.json();

        const badge = document.getElementById('system-badge');
        badge.textContent = data.status === 'healthy' ? 'ALL SYSTEMS HEALTHY' : 'DEGRADED';
        badge.className = `badge ${data.status === 'healthy' ? 'badge-healthy' : 'badge-degraded'}`;

        const services = data.services || {};
        updateServiceCard('ollama', services.ollama);
        updateServiceCard('qdrant', services.qdrant);
        updateServiceCard('n8n', services.n8n);
        updateServiceCard('postgres', services.postgres);

        // Telegram is always "up" if the bot container is running
        updateServiceCard('telegram', { status: 'up' });
    } catch (err) {
        console.error('Diagnostics error:', err);
    }
}

function updateServiceCard(name, info) {
    const indicator = document.getElementById(`status-${name}`);
    if (!indicator || !info) return;

    const dot = indicator.querySelector('.status-dot');
    const text = indicator.querySelector('.status-text');
    const isUp = info.status === 'up';

    dot.className = `status-dot ${isUp ? 'dot-up' : 'dot-down'}`;
    text.textContent = isUp ? 'Online' : 'Offline';

    const card = document.getElementById(`card-${name}`);
    if (card) {
        card.className = `card service-card ${isUp ? 'card-up' : 'card-down'}`;
    }
}

// ── Workflows ───────────────────────────────────────────────────
async function loadWorkflows() {
    try {
        const resp = await fetch('/n8n/workflows');
        const data = await resp.json();
        const workflows = data.workflows || data.data || data || [];

        document.getElementById('workflow-count').textContent = workflows.length;
        const tbody = document.getElementById('workflows-body');

        if (workflows.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="table-empty">No workflows found</td></tr>';
            return;
        }

        tbody.innerHTML = workflows.map(wf => `
            <tr>
                <td class="cell-name">${wf.name}</td>
                <td class="cell-id">${wf.id}</td>
                <td><span class="badge ${wf.active ? 'badge-active' : 'badge-inactive'}">
                    ${wf.active ? '● ACTIVE' : '○ INACTIVE'}</span></td>
                <td class="cell-date">${formatDate(wf.updatedAt)}</td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Workflows error:', err);
    }
}

// ── Runs ────────────────────────────────────────────────────────
async function loadRuns() {
    try {
        const resp = await fetch('/dashboard/runs?limit=20');
        const data = await resp.json();
        const runs = data.runs || [];

        const tbody = document.getElementById('runs-body');
        if (runs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="table-empty">No runs yet</td></tr>';
            return;
        }

        tbody.innerHTML = runs.map(run => `
            <tr class="run-row" onclick="showRunDetail('${run.run_id}')">
                <td class="cell-id">${run.run_id.substring(0, 8)}</td>
                <td>${run.user_id || '—'}</td>
                <td class="cell-input">${truncate(run.input_text, 40)}</td>
                <td>${run.intent || '—'}</td>
                <td><span class="badge badge-${run.status}">${(run.status || '').toUpperCase()}</span></td>
                <td>${run.duration_ms ? (run.duration_ms / 1000).toFixed(1) + 's' : '—'}</td>
                <td class="cell-date">${formatDate(run.created_at)}</td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Runs error:', err);
    }
}

// ── Run Detail Modal ────────────────────────────────────────────
async function showRunDetail(runId) {
    const modal = document.getElementById('run-modal');
    const body = document.getElementById('modal-body');
    body.innerHTML = '<div class="loading-spinner">Loading…</div>';
    modal.classList.remove('hidden');

    try {
        const resp = await fetch(`/dashboard/runs/${runId}`);
        const run = await resp.json();

        if (run.error) {
            body.innerHTML = `<p class="error-text">${run.error}</p>`;
            return;
        }

        const steps = run.steps || [];
        const maxLatency = Math.max(...steps.map(s => s.latency_ms || 0), 1);

        body.innerHTML = `
            <div class="detail-grid">
                <div class="detail-section">
                    <h3>Overview</h3>
                    <div class="detail-row"><span class="detail-label">Run ID</span><span class="detail-value">${run.run_id}</span></div>
                    <div class="detail-row"><span class="detail-label">User</span><span class="detail-value">${run.user_id || '—'}</span></div>
                    <div class="detail-row"><span class="detail-label">Input</span><span class="detail-value">${run.input_text || '—'}</span></div>
                    <div class="detail-row"><span class="detail-label">Intent</span><span class="detail-value"><span class="badge badge-intent">${run.intent || 'unknown'}</span></span></div>
                    <div class="detail-row"><span class="detail-label">Status</span><span class="detail-value"><span class="badge badge-${run.status}">${(run.status || '').toUpperCase()}</span></span></div>
                    <div class="detail-row"><span class="detail-label">Duration</span><span class="detail-value">${run.duration_ms ? (run.duration_ms / 1000).toFixed(2) + 's' : '—'}</span></div>
                    <div class="detail-row"><span class="detail-label">Reply</span><span class="detail-value detail-reply">${run.reply || '—'}</span></div>
                </div>

                <div class="detail-section">
                    <h3>Agent Timeline</h3>
                    <div class="timeline">
                        ${steps.map((step, i) => `
                            <div class="timeline-step ${step.error ? 'step-error' : 'step-ok'}">
                                <div class="step-header">
                                    <span class="step-icon">${getStepIcon(step.step_name)}</span>
                                    <span class="step-name">${formatStepName(step.step_name)}</span>
                                    <span class="step-latency">${step.latency_ms ? step.latency_ms.toFixed(0) + 'ms' : '—'}</span>
                                </div>
                                <div class="step-bar-container">
                                    <div class="step-bar ${step.error ? 'bar-error' : 'bar-ok'}"
                                         style="width: ${((step.latency_ms || 0) / maxLatency * 100).toFixed(1)}%"></div>
                                </div>
                                ${step.error ? `<div class="step-error-msg">❌ ${step.error.substring(0, 120)}</div>` : ''}
                                ${step.output_json ? `
                                    <details class="step-details">
                                        <summary>Output</summary>
                                        <pre class="step-json">${JSON.stringify(step.output_json, null, 2)}</pre>
                                    </details>
                                ` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    } catch (err) {
        body.innerHTML = `<p class="error-text">Failed to load run: ${err.message}</p>`;
    }
}

function closeModal() {
    document.getElementById('run-modal').classList.add('hidden');
}

// Close modal on overlay click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) closeModal();
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
});

function getStepIcon(name) {
    const icons = {
        classifier: '🏷️',
        planner: '📋',
        researcher: '🔍',
        executor: '⚡',
        tool_router: '🔧',
        critic: '✅',
    };
    return icons[name] || '📌';
}

function formatStepName(name) {
    const names = {
        classifier: 'Intent Classifier',
        planner: 'Planner',
        researcher: 'Research Agent',
        executor: 'Executor',
        tool_router: 'Tool Router',
        critic: 'Critic',
    };
    return names[name] || name;
}

// ── Quick Test ──────────────────────────────────────────────────
async function sendTest() {
    const input = document.getElementById('test-input');
    const result = document.getElementById('test-result');
    const replyEl = document.getElementById('test-reply');
    const intentEl = document.getElementById('test-intent');

    const text = input.value.trim();
    if (!text) return;

    replyEl.textContent = 'Processing…';
    intentEl.textContent = '';
    result.classList.remove('hidden');

    try {
        const resp = await fetch('/orchestrate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: 'dashboard_user', text }),
        });
        const data = await resp.json();
        replyEl.textContent = data.reply || 'No reply';
        intentEl.textContent = data.intent ? `Intent: ${data.intent}` : '';
        loadRuns(); // Refresh runs after test
    } catch (err) {
        replyEl.textContent = `Error: ${err.message}`;
    }
}

// Submit on Enter
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('test-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendTest();
    });
});

// ── Utilities ───────────────────────────────────────────────────
function formatDate(isoStr) {
    if (!isoStr) return '—';
    const d = new Date(isoStr);
    return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }) + ' '
        + d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
}

function truncate(str, max) {
    if (!str) return '—';
    return str.length > max ? str.substring(0, max) + '…' : str;
}
