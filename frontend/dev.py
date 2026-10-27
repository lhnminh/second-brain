"""Read-only development diagnostics served by the same-origin application."""

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#f5f7f8">
<title>Developer console · Visual Second Brain</title>
<style>
:root{font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif;color:#26343d;background:#f5f7f8;font-synthesis:none;--ink:#26343d;--muted:#6c7b84;--line:#e0e6e9;--green:#34745b;--soft:#eef3f2;--panel:#fff;--red:#a64846;--mono:ui-monospace,SFMono-Regular,Consolas,monospace}
*{box-sizing:border-box}body{margin:0;font-size:14px;line-height:1.5}button,input,select{font:inherit}button,a,input,select,summary{outline-offset:4px}button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible,summary:focus-visible{outline:2px solid var(--green)}button{cursor:pointer;border:1px solid var(--line);border-radius:8px;background:#fff;color:var(--ink);padding:8px 13px;font-weight:600;font-size:12px}button:hover{background:#f3f6f5;border-color:#bbc9c4}button:disabled{opacity:.5;cursor:wait}a{color:var(--green);text-decoration:none}a:hover{text-decoration:underline}input,select{border:1px solid var(--line);border-radius:8px;padding:9px 11px;color:var(--ink);background:#fff;min-width:0}input[type=search]{width:100%}input[type=checkbox]{accent-color:var(--green);margin:0}h1,h2,h3,p{margin:0}h1{font-size:30px;letter-spacing:-1px;line-height:1.2;font-weight:600}h2{font-size:18px;letter-spacing:-.4px;font-weight:600}h3{font-size:14px;font-weight:650}pre,code{font-family:var(--mono);font-size:11px}pre{margin:0;white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.8}code{overflow-wrap:anywhere}.muted{color:var(--muted)}.small{font-size:12px}.mono{font-family:var(--mono);font-size:11px;overflow-wrap:anywhere}.row{display:flex;align-items:center;gap:10px}.between{justify-content:space-between}.wrap{flex-wrap:wrap}.primary{background:var(--green);color:#fff;border-color:var(--green)}.primary:hover{background:#285d48;color:#fff}.eyebrow{font:10px var(--mono);letter-spacing:1.3px;text-transform:uppercase;color:var(--muted)}.topbar{height:72px;background:#fff;border-bottom:1px solid var(--line);padding:0 32px;display:flex;align-items:center;justify-content:space-between;gap:16px}.brand{font-size:13px;font-weight:700}.brand-mark{width:28px;height:28px;display:grid;place-items:center;background:#335c41;color:#d7e98c;border-radius:8px;font-size:19px}.divider{width:1px;height:18px;background:var(--line);margin:0 4px}.topbar nav{display:flex;align-items:center;gap:16px;font-size:12px}.shell{max-width:1500px;margin:auto;display:grid;grid-template-columns:195px minmax(0,1fr);gap:40px;padding:34px 32px 64px}.sidebar{position:sticky;top:28px;align-self:start}.sidebar nav{display:grid;gap:5px;margin:18px 0 28px}.sidebar nav a{color:var(--muted);padding:10px 12px;border-radius:8px;font-size:12px;display:flex;justify-content:space-between;gap:10px}.sidebar nav a:hover{background:#e9efed;color:var(--green);text-decoration:none}.sidebar nav a:first-child{background:#e9efed;color:var(--green)}.sidebar-note{border-top:1px solid var(--line);padding:18px 12px;font-size:11px;line-height:1.8;color:var(--muted)}.sidebar-note strong{display:block;color:var(--ink);font-weight:550;margin-bottom:4px}main{min-width:0}.hero{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;margin-bottom:26px}.hero .eyebrow{margin-bottom:10px}.hero p{margin-top:10px;max-width:600px;color:var(--muted);font-size:13px}.refresh-controls{display:flex;align-items:center;gap:12px;flex-wrap:wrap;justify-content:flex-end}.refresh-controls label{font-size:11px;color:var(--muted);display:flex;gap:6px;align-items:center}.notice{margin-bottom:20px;display:flex;align-items:center;justify-content:space-between;gap:12px;color:var(--muted);font-size:11px;min-height:22px}.connection{display:flex;gap:8px;align-items:center}.dot{width:7px;height:7px;display:inline-block;background:#a0aab0;border-radius:50%;flex:none}.dot.ok{background:#509078}.dot.warn{background:#c89a42}.dot.error{background:#b75a55}.error{padding:14px 16px;border:1px solid #ebc8c4;background:#fff4f2;border-radius:10px;margin-bottom:20px;color:#8e4340;font-size:12px;white-space:pre-wrap}.access{border:1px solid #d8e1dd;background:#f0f5f2;border-radius:12px;padding:22px;margin-bottom:24px}.access p{color:var(--muted);font-size:12px;margin-top:6px}.access form{margin-top:16px;display:flex;gap:8px;max-width:520px}.access input{flex:1}.overview{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:13px}.metric{background:#fff;border:1px solid var(--line);border-radius:12px;padding:19px}.metric .number{font-size:29px;font-weight:500;line-height:1.3;letter-spacing:-.8px;margin:10px 0 5px}.metric .caption{font-size:11px;color:var(--muted)}.snapshot{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px 24px;padding:22px 0 0}.snapshot dt{font-size:10px;text-transform:uppercase;letter-spacing:.7px;color:var(--muted);margin-bottom:6px}.snapshot dd{margin:0;font-size:12px;overflow-wrap:anywhere}.annotation{border-left:2px solid #c8d9d0;padding-left:12px;font-size:11px;color:var(--muted);margin-top:20px}.section{margin-top:38px;scroll-margin-top:24px}.section-head{display:flex;justify-content:space-between;align-items:flex-start;gap:18px;margin-bottom:17px}.section-head p{color:var(--muted);font-size:12px;margin-top:5px}.panel{background:#fff;border:1px solid var(--line);border-radius:12px;overflow:hidden}.filters{display:flex;gap:9px;padding:15px;border-bottom:1px solid var(--line);background:#fcfdfd;align-items:center}.filters label{font-size:11px;color:var(--muted)}.filters input{flex:1}.filters select{max-width:190px;font-size:12px}.explorer{display:grid;grid-template-columns:minmax(230px,.8fr) minmax(0,1.5fr);min-height:420px}.run-list{border-right:1px solid var(--line);max-height:760px;overflow:auto}.run-button{border:0;border-bottom:1px solid var(--line);border-radius:0;display:block;width:100%;padding:17px;text-align:left;font-weight:400;background:#fff}.run-button:last-child{border-bottom:0}.run-button:hover{background:#f8faf9}.run-button[aria-pressed=true]{background:#edf4f0;box-shadow:inset 3px 0 var(--green)}.run-button .title{font-size:12px;font-weight:600;line-height:1.6;margin:10px 0 7px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;overflow-wrap:anywhere}.run-button .row{gap:8px}.run-button .kind{font:9px var(--mono);color:var(--muted);text-transform:uppercase;letter-spacing:.4px}.badge{font-size:10px;padding:3px 7px;border-radius:5px;background:#eef2f4;color:#63747e;font-weight:500;white-space:nowrap}.badge.applied,.badge.answered{background:#e8f2ec;color:#39735a}.badge.running,.badge.awaiting_review{background:#f9f0db;color:#96752f}.badge.failed,.badge.stale{background:#faeae7;color:#a34c44}.detail{padding:24px;min-width:0}.detail-title{margin:8px 0 12px;font-size:17px;overflow-wrap:anywhere;font-weight:600;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}.detail .metadata{display:grid;grid-template-columns:1fr 1fr;gap:15px;margin:20px 0}.metadata dt{font-size:10px;color:var(--muted);margin-bottom:3px}.metadata dd{font-size:11px;margin:0;overflow-wrap:anywhere}.detail-block{border-top:1px solid var(--line);padding-top:19px;margin-top:20px}.detail-block h3{margin-bottom:11px;font-size:12px}.prose{font-size:12px;line-height:1.8;white-space:pre-wrap;overflow-wrap:anywhere}.empty{padding:35px 22px;text-align:center;font-size:12px;color:var(--muted)}.empty strong{display:block;color:#4f626c;font-size:13px;font-weight:550;margin-bottom:6px}.detail .empty{padding:85px 20px}.proposal-note{padding:10px 12px;background:#f6f8f7;border-radius:7px;font-size:11px;color:#61776b;margin-top:13px}.proposal-task{border:1px solid var(--line);border-radius:8px;padding:14px;margin-top:12px}.proposal-task h4{font-size:12px;line-height:1.6;margin:7px 0}.proposal-task p{font-size:11px;line-height:1.7;margin:7px 0;color:var(--muted);white-space:pre-wrap;overflow-wrap:anywhere}.proposal-task ol{font-size:11px;padding-left:19px;margin:12px 0 0}.proposal-task li{padding:5px 0}.proposal-task li p{margin:2px 0}.json{background:#f6f8fa;border:1px solid #e7ecee;border-radius:7px;padding:13px;max-height:400px;overflow:auto;margin-top:10px}details{margin-top:14px}summary{font-size:11px;color:#607882;cursor:pointer;line-height:1.8}details[open]>summary{margin-bottom:8px}.message{border-left:2px solid #e0e8e3;padding:1px 0 1px 12px;margin:12px 0}.message .label{font-size:9px;font-family:var(--mono);text-transform:uppercase;color:var(--muted);margin-bottom:5px}.table-scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:11px;text-align:left}th{font-weight:500;font-size:10px;text-transform:uppercase;letter-spacing:.4px;color:var(--muted);background:#fcfdfd;white-space:nowrap}th,td{padding:12px 16px;border-bottom:1px solid var(--line);vertical-align:top}tbody tr:last-child td{border-bottom:0}.table-title{font-weight:600;color:#344c57;display:block;max-width:420px;overflow-wrap:anywhere}.table-sub{font-size:10px;color:var(--muted);margin-top:4px;display:block;overflow-wrap:anywhere}.inspect{padding:3px 8px;font-size:10px;white-space:nowrap}.object-detail{padding:0 20px 20px;border-top:1px solid var(--line)}.object-detail h3{margin-top:20px}.object-fields{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:18px 0}.object-fields dt{font-size:10px;color:var(--muted);margin-bottom:4px}.object-fields dd{margin:0;font-size:11px;overflow-wrap:anywhere}.content-box{background:#f8faf9;padding:13px;border-radius:7px}.event-kind{font:10px var(--mono);color:#47665a}.event-row details{margin:0}.event-row summary{font-size:10px}.event-time{white-space:nowrap;color:var(--muted);font-size:10px}.footer{font-size:11px;color:var(--muted);margin-top:28px;padding-top:18px;border-top:1px solid var(--line)}.count{font:10px var(--mono);color:var(--muted);font-weight:400}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}[hidden]{display:none!important}@media(max-width:1100px){.shell{grid-template-columns:150px minmax(0,1fr);gap:24px}.overview{grid-template-columns:repeat(2,minmax(0,1fr))}.snapshot{grid-template-columns:repeat(2,minmax(0,1fr))}.explorer{grid-template-columns:minmax(210px,.7fr) minmax(0,1fr)}}@media(max-width:800px){.topbar{height:auto;min-height:72px;padding:16px 20px;flex-wrap:wrap;gap:12px}.topbar .divider,.topbar .console-label{display:none}.shell{display:block;padding:24px 20px 40px}.sidebar{position:static}.sidebar .eyebrow,.sidebar-note{display:none}.sidebar nav{display:flex;overflow:auto;margin:0 0 24px;gap:4px}.sidebar nav a{white-space:nowrap;padding:8px 10px}.sidebar nav a span{display:none}.hero{display:block}.hero h1{font-size:26px}.refresh-controls{justify-content:flex-start;margin-top:18px}.snapshot{gap:16px}.explorer{grid-template-columns:1fr}.run-list{max-height:320px;border-right:0;border-bottom:1px solid var(--line)}.detail{padding:20px}.filters{flex-wrap:wrap}.filters input{flex-basis:100%}.filters select{flex:1;max-width:none}.object-fields{grid-template-columns:repeat(2,minmax(0,1fr))}.notice{align-items:flex-start;flex-direction:column;gap:4px}.topbar nav{gap:10px;flex-wrap:wrap}.brand{font-size:12px}.metric{padding:15px}.metric .number{font-size:25px}.access form{flex-wrap:wrap}.access input{width:100%;flex-basis:100%}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
</style>
</head>
<body>
<header class="topbar"><div class="row"><span class="brand-mark" aria-hidden="true">✳</span><span class="brand">Visual Second Brain</span><span class="divider"></span><span class="muted small console-label">Developer console</span></div><nav aria-label="Application navigation"><a href="/">← Workspace</a><a href="/docs">API reference ↗</a><button id="sign-out" hidden>Sign out</button></nav></header>
<div class="shell">
<aside class="sidebar"><div class="eyebrow">Inspect the system</div><nav aria-label="Console sections"><a href="#overview">Overview <span>01</span></a><a href="#run-explorer">Model runs <span>02</span></a><a href="#objects">Stored objects <span>03</span></a><a href="#events">Change log <span>04</span></a></nav><div class="sidebar-note"><strong>Read-only diagnostics</strong>Inspect what was requested, what Muse returned, and what was saved. Review proposals in the workspace.</div></aside>
<main>
<div class="hero"><div><div class="eyebrow">Development / Observability</div><h1>See what’s happening.</h1><p>Trace a conversation from request to proposal to saved objects. Every record here comes from this account’s actual stored state.</p></div><div class="refresh-controls"><label><input id="auto-refresh" type="checkbox"> Refresh every 10s</label><button id="refresh" class="primary">Refresh snapshot</button></div></div>
<div class="notice"><div class="connection" role="status" aria-live="polite"><span id="connection-dot" class="dot"></span><span id="connection">Loading diagnostics…</span></div><span id="updated">No snapshot loaded</span></div>
<div id="error" class="error" role="alert" hidden></div>
<section id="access" class="access" hidden aria-labelledby="access-heading"><h2 id="access-heading">Connect to the demo</h2><p>Use the app’s demo access token. Your session is shared with the workspace.</p><form id="access-form"><label class="sr-only" for="token">Demo access token</label><input id="token" type="password" autocomplete="current-password" placeholder="Demo access token" required><button id="connect" class="primary">Connect</button></form></section>
<section id="overview" aria-labelledby="overview-heading"><h2 id="overview-heading" class="sr-only">Snapshot overview</h2><div class="overview" id="metrics"><div class="metric"><div class="eyebrow">Saved tasks</div><div class="number">—</div><div class="caption">Waiting for an account snapshot</div></div><div class="metric"><div class="eyebrow">Proposals to review</div><div class="number">—</div><div class="caption">Not applied to saved work</div></div><div class="metric"><div class="eyebrow">Model runs</div><div class="number">—</div><div class="caption">Actual persisted requests</div></div><div class="metric"><div class="eyebrow">Context records</div><div class="number">—</div><div class="caption">Structured context available to Muse</div></div></div><dl class="snapshot" id="snapshot-info"></dl><p class="annotation">Service health reports liveness and configuration. It does not test model access or database readiness. A loaded snapshot confirms that this account’s state was read.</p></section>
<section id="run-explorer" class="section" aria-labelledby="runs-heading"><div class="section-head"><div><h2 id="runs-heading">Model runs <span class="count" id="run-count"></span></h2><p>Select a request to inspect its input, response, and recorded changes.</p></div><a href="/" class="small">Review proposals in workspace ↗</a></div><div class="panel"><div class="filters"><label class="sr-only" for="run-search">Search model runs</label><input id="run-search" type="search" placeholder="Search message, task, or run ID…"><label class="sr-only" for="run-status">Filter by run status</label><select id="run-status"><option value="">All statuses</option><option value="running">Running</option><option value="awaiting_review">Awaiting review</option><option value="answered">Answered</option><option value="applied">Applied</option><option value="failed">Failed</option><option value="stale">Stale</option><option value="superseded">Superseded</option><option value="rejected">Rejected</option></select><label class="sr-only" for="run-kind">Filter by run type</label><select id="run-kind"><option value="">All request types</option><option value="conversation">Conversation</option><option value="task">Task planning</option></select></div><div class="explorer"><div id="run-list" class="run-list" aria-label="Model requests"><div class="empty">Loading requests…</div></div><div id="run-detail" class="detail" aria-live="polite"><div class="empty">Select a run to inspect it.</div></div></div></div></section>
<section id="objects" class="section" aria-labelledby="objects-heading"><div class="section-head"><div><h2 id="objects-heading">Stored objects</h2><p>Saved records are separate from model proposals. Inspect ownership, relationships, versions, and sources.</p></div></div><div class="panel"><div class="filters"><label class="sr-only" for="object-kind">Object type</label><select id="object-kind"><option value="tasks">Tasks &amp; steps</option><option value="context">User context</option><option value="messages">Conversation messages</option></select><label class="sr-only" for="object-search">Search stored objects</label><input id="object-search" type="search" placeholder="Search stored objects…"><span class="count" id="object-count"></span></div><div id="object-table" class="table-scroll"><div class="empty">Loading saved objects…</div></div><div id="object-detail" class="object-detail" hidden></div></div><details><summary>Inspect the full account snapshot as JSON</summary><pre id="raw-state" class="json">No account snapshot loaded.</pre></details></section>
<section id="events" class="section" aria-labelledby="events-heading"><div class="section-head"><div><h2 id="events-heading">Change log <span id="event-count" class="count"></span></h2><p>Recorded planning transitions and saved changes, newest first.</p></div></div><div class="panel"><div class="filters"><label class="sr-only" for="event-search">Search change events</label><input id="event-search" type="search" placeholder="Search event kind, entity ID, or recorded details…"></div><div id="event-list" class="table-scroll"><div class="empty">Loading recorded events…</div></div></div><p id="event-limit" class="small muted" style="margin-top:10px"></p></section>
<footer class="footer">This console does not execute model calls or edit work. Timings use recorded timestamps; provider token usage and provider latency are not currently recorded.</footer>
</main></div>
<script>
'use strict';
const $ = selector => document.querySelector(selector);
const esc = value => String(value ?? '').replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
const pretty = value => JSON.stringify(value, null, 2);
const statusLabels = {running:'Running',awaiting_review:'Awaiting review',answered:'Answered',applied:'Applied',failed:'Failed',stale:'Stale',superseded:'Superseded',rejected:'Rejected'};
let state = null, health = null, selectedRun = null, selectedObject = null, refreshing = false, lastLoaded = null, snapshotMs = null;
let authRequired = false;
function date(value) {
    if (!value) return 'Not recorded';
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleString(undefined, {month:'short',day:'numeric',hour:'numeric',minute:'2-digit',second:'2-digit'});
}
function badge(status) { return `<span class="badge ${esc(status)}">${esc(statusLabels[status] || status || 'Unknown')}</span>`; }
function raw(value) { return `<pre class="json">${esc(pretty(value))}</pre>`; }
function empty(title, note='') { return `<div class="empty"><strong>${esc(title)}</strong>${esc(note)}</div>`; }
function field(label, value, mono=false) { return `<div><dt>${esc(label)}</dt><dd${mono?' class="mono"':''}>${esc(value ?? 'Not recorded')}</dd></div>`; }
function setConnection(message, tone='') {
    $('#connection').textContent = message;
    $('#connection-dot').className = 'dot' + (tone ? ' ' + tone : '');
}
function showError(error) { $('#error').textContent = error.message || 'Could not load diagnostics.'; $('#error').hidden = false; }
function clearState() {
    state = null; selectedRun = null; selectedObject = null; lastLoaded = null; snapshotMs = null;
    $('#updated').textContent = 'No account snapshot loaded';
    $('#auto-refresh').checked = false;
    render();
}
async function request(path, method='GET', body) {
    let response;
    try {
        response = await fetch(path, {method, credentials:'same-origin', headers:{'Content-Type':'application/json'}, ...(body===undefined ? {} : {body:JSON.stringify(body)})});
    } catch {
        throw Error('Could not reach the server. The last loaded snapshot may be out of date.');
    }
    let data;
    try { data = await response.json(); } catch { throw Error('The server returned an unreadable response.'); }
    if (!response.ok) {
        if (response.status === 401) {
            clearState();
            $('#access').hidden = false;
            $('#sign-out').hidden = true;
            setConnection('Demo session required', 'warn');
        }
        const error = Error(data.error?.message || `Request failed (${response.status}).`);
        error.status = response.status;
        throw error;
    }
    return data;
}
async function refresh() {
    if (refreshing) return;
    refreshing = true;
    $('#refresh').disabled = true;
    $('#error').hidden = true;
    setConnection(state ? 'Refreshing account snapshot…' : 'Connecting…');
    const snapshotRequest = async () => {
        const started = performance.now();
        const data = await request('/api/dashboard');
        return {data, milliseconds:Math.round(performance.now()-started)};
    };
    const [healthResult, snapshotResult] = await Promise.allSettled([request('/health'), snapshotRequest()]);
    if (healthResult.status === 'fulfilled') {
        health = healthResult.value;
        authRequired = health.demo_access_required === true;
    } else { health = null; }
    if (snapshotResult.status === 'fulfilled') {
        state = snapshotResult.value.data;
        snapshotMs = snapshotResult.value.milliseconds;
        lastLoaded = new Date();
        $('#updated').textContent = 'Snapshot loaded ' + lastLoaded.toLocaleTimeString();
        $('#access').hidden = true;
        $('#sign-out').hidden = !authRequired;
        setConnection(healthResult.status === 'fulfilled' ? 'Account snapshot connected' : 'Snapshot loaded · health unavailable', healthResult.status === 'fulfilled' ? 'ok' : 'warn');
        if (healthResult.status === 'rejected') showError(healthResult.reason);
    } else {
        const failure = snapshotResult.reason;
        if (failure.status !== 401) setConnection(state ? 'Connection failed · showing previous snapshot' : 'Account snapshot unavailable', 'error');
        showError(failure);
    }
    render();
    refreshing = false;
    $('#refresh').disabled = false;
}
function renderOverview() {
    const tasks = state?.tasks || [], runs = state?.runs || [];
    const values = [
        ['Saved tasks', state ? tasks.length : '—', state ? `${tasks.filter(task=>!task.parent_task_id).length} root tasks · ${tasks.filter(task=>task.parent_task_id).length} steps · ${tasks.filter(task=>task.status==='completed').length} complete` : 'No account snapshot loaded'],
        ['Proposals to review', state ? runs.filter(run=>run.status==='awaiting_review').length : '—', 'Not applied to saved work'],
        ['Model runs', state ? runs.length : '—', state ? `${runs.filter(run=>run.status==='running').length} running · ${runs.filter(run=>run.status==='failed').length} failed · ${runs.filter(run=>run.status==='stale').length} stale` : 'Actual persisted requests'],
        ['Context records', state ? state.context.length : '—', state ? `${state.messages.length} messages · ${state.events.length} change events` : 'Structured context available to Muse']
    ];
    $('#metrics').innerHTML = values.map(([label,value,caption])=>`<div class="metric"><div class="eyebrow">${label}</div><div class="number">${value}</div><div class="caption">${esc(caption)}</div></div>`).join('');
    const authMode = !health ? 'Unknown' : authRequired ? 'Protected demo session' : 'Open local demo';
    $('#snapshot-info').innerHTML = field('Configured model', health?.model, true) + field('Access mode', authMode) + field('Workspace ID', state?.user_id, true) + field('Service liveness', health?.status || 'Unavailable') + field('Snapshot fetch', snapshotMs===null ? 'Not measured' : `${snapshotMs} ms in this browser`) + field('Identity', health?.authentication==='mock' ? 'Anonymous browser workspace' : health?.authentication);
}
function runTitle(run) { return state?.tasks.find(task=>task.id===run.task_id)?.title || run.message || 'Conversation'; }
function elapsed(run) {
    const duration = new Date(run.updated_at) - new Date(run.created_at);
    return Number.isFinite(duration) && duration>=0 ? `${(duration/1000).toFixed(1)}s between recorded timestamps` : 'Unavailable';
}
function renderRuns() {
    const query = $('#run-search').value.toLowerCase(), status = $('#run-status').value, kind = $('#run-kind').value;
    const runs = [...(state?.runs || [])].reverse().filter(run=>(!status || run.status===status) && (!kind || (run.task_id ? 'task' : 'conversation')===kind) && (!query || `${runTitle(run)} ${run.message} ${run.id} ${run.request_id} ${run.model}`.toLowerCase().includes(query)));
    $('#run-count').textContent = state ? `${runs.length} / ${state.runs.length}` : '';
    if (!runs.some(run=>run.id===selectedRun)) selectedRun = runs[0]?.id || null;
    $('#run-list').innerHTML = runs.length ? runs.map(run=>`<button class="run-button" data-run="${esc(run.id)}" aria-pressed="${run.id===selectedRun}"><div class="row between">${badge(run.status)}<span class="kind">${run.task_id?'Task plan':'Conversation'}</span></div><div class="title">${esc(runTitle(run))}</div><div class="muted" style="font-size:10px">${esc(date(run.created_at))}</div><div class="mono muted" style="font-size:9px;margin-top:6px">${esc(run.id)}</div></button>`).join('') : empty(!state ? 'Connect to inspect runs' : state.runs.length ? 'No matching requests' : 'No model requests yet', state && !state.runs.length ? 'Start a conversation in the workspace. Its recorded request will appear here.' : '');
    renderRunDetail();
}
function proposalTask(item, index) {
    const target = item.task_id ? `Update saved object ${item.task_id}` : 'New task object';
    const steps = item.subtasks || [];
    return `<article class="proposal-task"><span class="eyebrow">${esc(target)}</span><h4>${index+1}. ${esc(item.title)}</h4>${item.description?`<p>${esc(item.description)}</p>`:''}<div class="row wrap muted" style="font-size:10px"><span>Due ${esc(item.deadline || 'not set')}</span><span>Agent importance ${esc(item.importance_score ?? 'not assessed')}</span></div>${steps.length?`<ol>${steps.map(step=>`<li><strong>${esc(step.title)}</strong>${step.description?`<p>${esc(step.description)}</p>`:''}<span class="muted">Agent importance ${esc(step.importance_score)}</span></li>`).join('')}</ol>`:'<p>No new steps proposed.</p>'}</article>`;
}
function renderProposal(run) {
    const proposal = run.proposal;
    if (!proposal) return '<p class="small muted">No validated proposal recorded.</p>';
    const tasks = proposal.tasks;
    let html = proposal.reply ? `<div class="prose">${esc(proposal.reply)}</div>` : '';
    if (Array.isArray(tasks)) html += tasks.length ? tasks.map(proposalTask).join('') : '<p class="proposal-note">This response contains no task changes.</p>';
    else html += `<p class="small muted" style="margin-top:12px">Parent importance: ${esc(proposal.importance_score)} · ${(proposal.subtasks || []).length} proposed steps</p>${(proposal.subtasks || []).map((step,index)=>`<article class="proposal-task"><h4>${index+1}. ${esc(step.title)}</h4><p>${esc(step.description)}</p><span class="small muted">Agent importance ${esc(step.importance_score)}</span></article>`).join('')}`;
    return html + `<details><summary>Validated proposal JSON</summary>${raw(proposal)}</details>`;
}
function renderRunDetail() {
    const run = state?.runs.find(item=>item.id===selectedRun);
    if (!run) { $('#run-detail').innerHTML = empty('No request selected', 'Choose a request from the list to inspect its actual records.'); return; }
    const messages = state.messages.filter(message=>message.run_id===run.id);
    const events = state.events.filter(event=>event.entity_id===run.id || event.details?.run_id===run.id);
    const statusNote = {awaiting_review:'This proposal has not been saved. Review and accept it in the workspace.',running:'The recorded request is running. Refresh for its latest stored status.',applied:'This reviewed proposal was applied. See the resulting task records and events.',answered:'Muse replied without proposing task changes.',failed:'The request failed. No successful result is implied by this run.',stale:'This proposal is outdated and cannot be applied.',superseded:'A newer conversation proposal replaced this draft.',rejected:'The proposal was dismissed without applying it.'}[run.status] || 'Inspect recorded state below.';
    $('#run-detail').innerHTML = `<div class="row between wrap"><span class="eyebrow">${run.task_id?'Task planning request':'Conversation request'}</span>${badge(run.status)}</div><h3 class="detail-title">${esc(runTitle(run))}</h3><p class="proposal-note">${esc(statusNote)}</p>${run.error?`<div class="error" style="margin-top:16px">${esc(run.error)}</div>`:''}<dl class="metadata">${field('Run ID',run.id,true)}${field('Request / retry ID',run.request_id,true)}${field('Model used',run.model,true)}${field('Snapshot revision',run.snapshot_revision)}${field('Created',date(run.created_at))}${field('Last recorded update',date(run.updated_at))}${field('Recorded interval',elapsed(run))}${field('Task target',run.task_id || 'No initial task required',true)}</dl><section class="detail-block"><h3>User request</h3><div class="prose">${esc(run.message)}</div><details><summary>Request input · includes any submitted review draft</summary>${run.input_payload?raw(run.input_payload):'<p class="small muted">Full request payload was not recorded for this legacy run. The user message is shown above.</p>'}</details></section><section class="detail-block"><h3>Model response &amp; proposed objects</h3>${renderProposal(run)}</section><section class="detail-block"><h3>Related conversation · ${messages.length} messages</h3>${messages.length?messages.map(message=>`<div class="message"><div class="label">${esc(message.role)} · ${esc(date(message.created_at))}</div><div class="prose">${esc(message.content)}</div></div>`).join(''):'<p class="small muted">No linked messages recorded.</p>'}</section><section class="detail-block"><h3>Related events · ${events.length}</h3>${events.length?events.map(event=>`<details><summary><span class="event-kind">${esc(event.kind)}</span> · ${esc(date(event.created_at))}</summary>${raw(event)}</details>`).join(''):'<p class="small muted">No events directly linked to this run.</p>'}</section><details class="detail-block"><summary>Complete run record</summary>${raw(run)}</details>`;
}
function objectRows() {
    const kind = $('#object-kind').value, query = $('#object-search').value.toLowerCase();
    return (state?.[kind] || []).filter(record=>!query || pretty(record).toLowerCase().includes(query));
}
function renderObjects() {
    const kind = $('#object-kind').value, records = objectRows();
    $('#object-count').textContent = state ? `${records.length} records` : '';
    if (!records.some(record=>record.id===selectedObject)) selectedObject = null;
    if (!records.length) $('#object-table').innerHTML = empty(!state ? 'Connect to inspect stored objects' : 'No matching saved records', state && !$('#object-search').value ? 'Proposed objects only become saved tasks after review.' : '');
    else {
        const columns = kind==='tasks' ? ['Task / relationship','State','Importance','Version / updated',''] : kind==='context' ? ['Context / category','Provenance','Source','Version / updated',''] : ['Message','Role','Run','Created',''];
        const rows = records.map(record=>{
            let cells;
            if (kind==='tasks') {
                const parent = state.tasks.find(task=>task.id===record.parent_task_id);
                cells = [`<span class="table-title">${esc(record.title)}</span><span class="table-sub">${record.parent_task_id?'Step of '+esc(parent?.title || record.parent_task_id):'Root task'} · ${esc(record.id)}</span>`,`${badge(record.status)}<span class="table-sub">Due ${esc(record.deadline || 'not set')}</span>`,`<span>${esc(record.user_importance_level?.replaceAll('_',' ') || 'No user override')}</span><span class="table-sub">Agent score ${esc(record.importance_score ?? 'not assessed')}</span>`,`v${esc(record.version)}<span class="table-sub">${esc(date(record.updated_at))}</span>`];
            } else if (kind==='context') cells = [`<span class="table-title">${esc(record.id)}</span><span class="table-sub">${esc(record.category?.replaceAll('_',' '))}</span>`,esc(record.provenance?.replaceAll('_',' ')),esc(record.source),`v${esc(record.version)}<span class="table-sub">${esc(date(record.updated_at))}</span>`];
            else cells = [`<span class="table-title">${esc(record.content.length>160?record.content.slice(0,160)+'…':record.content)}</span><span class="table-sub">${esc(record.id)}</span>`,esc(record.role),`<span class="mono">${esc(record.run_id)}</span>`,esc(date(record.created_at))];
            return `<tr>${cells.map(cell=>`<td>${cell}</td>`).join('')}<td><button class="inspect" data-object="${esc(record.id)}" aria-label="Inspect ${esc(record.title || record.id)}">Inspect</button></td></tr>`;
        }).join('');
        $('#object-table').innerHTML = `<table><thead><tr>${columns.map(column=>`<th scope="col">${column}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table>`;
    }
    renderObjectDetail();
}
function renderObjectDetail() {
    const kind = $('#object-kind').value, record = state?.[kind].find(item=>item.id===selectedObject);
    $('#object-detail').hidden = !record;
    if (!record) { $('#object-detail').innerHTML = ''; return; }
    const exclude = new Set(['description','content']);
    const values = Object.entries(record).filter(([key,value])=>!exclude.has(key) && (typeof value!=='object' || value===null));
    $('#object-detail').innerHTML = `<div class="row between" style="margin-top:18px"><h3 style="margin:0">${esc(record.title || record.id)}</h3><button id="close-object" class="inspect">Close inspection</button></div><dl class="object-fields">${values.map(([key,value])=>field(key.replaceAll('_',' '),value,key.endsWith('id'))).join('')}</dl>${record.description||record.content?`<div class="content-box prose">${esc(record.description || record.content)}</div>`:''}<details><summary>Complete saved record</summary>${raw(record)}</details>`;
}
function renderEvents() {
    const query = $('#event-search').value.toLowerCase();
    const events = [...(state?.events || [])].reverse().filter(event=>!query || pretty(event).toLowerCase().includes(query));
    $('#event-count').textContent = state ? `${events.length} / ${state.events.length}` : '';
    $('#event-limit').textContent = events.length>100 ? `Showing the newest 100 of ${events.length} matching events. Narrow the search to inspect older records.` : '';
    $('#event-list').innerHTML = events.length ? `<table><thead><tr><th scope="col">Recorded</th><th scope="col">Event</th><th scope="col">Entity</th><th scope="col">Details</th></tr></thead><tbody>${events.slice(0,100).map(event=>`<tr class="event-row"><td class="event-time">${esc(date(event.created_at))}</td><td class="event-kind">${esc(event.kind)}</td><td class="mono">${esc(event.entity_id)}</td><td><details><summary>Inspect change</summary>${raw(event.details)}</details></td></tr>`).join('')}</tbody></table>` : empty(!state ? 'Connect to inspect the change log' : 'No matching recorded changes', state && !state.events.length ? 'Saved task edits and planning transitions will appear here.' : '');
}
function render() {
    renderOverview(); renderRuns(); renderObjects(); renderEvents();
    $('#raw-state').textContent = state ? pretty(state) : 'No account snapshot loaded.';
}
$('#refresh').onclick = refresh;
$('#run-search').oninput = renderRuns;
$('#run-status').onchange = renderRuns;
$('#run-kind').onchange = renderRuns;
$('#run-list').onclick = event => { const button=event.target.closest('[data-run]'); if(button){selectedRun=button.dataset.run;renderRuns();} };
$('#object-search').oninput = renderObjects;
$('#object-kind').onchange = () => {selectedObject=null;renderObjects();};
$('#object-table').onclick = event => {const button=event.target.closest('[data-object]');if(button){selectedObject=button.dataset.object;renderObjectDetail();}};
$('#object-detail').onclick = event => {if(event.target.closest('#close-object')){selectedObject=null;renderObjectDetail();}};
$('#event-search').oninput = renderEvents;
$('#access-form').onsubmit = async event => {
    event.preventDefault(); if(refreshing)return;
    $('#connect').disabled = true; $('#error').hidden = true;
    const secret = $('#token').value; $('#token').value = '';
    try { await request('/api/session','POST',{token:secret}); await refresh(); }
    catch(error) { showError(error); }
    finally { $('#connect').disabled = false; }
};
$('#sign-out').onclick = async () => {
    if(refreshing)return;
    $('#sign-out').disabled = true;
    try {
        await request('/api/session','DELETE');
        clearState(); $('#error').hidden = true; $('#sign-out').hidden = true;
        $('#access').hidden = false; setConnection('Signed out of the demo session','warn');
    } catch(error) { showError(error); }
    finally { $('#sign-out').disabled = false; }
};
setInterval(()=>{if($('#auto-refresh').checked && !document.hidden)refresh();},10000);
window.addEventListener('pageshow',event=>{if(event.persisted)refresh();});
refresh();
</script>
</body>
</html>"""
