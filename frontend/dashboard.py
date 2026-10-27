"""Buildless conversation canvas served by FastAPI."""

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Visual Second Brain</title><style>

:root{--paper:#f5f5ee;--panel:#fffefa;--ink:#25342c;--muted:#687168;--line:#dce0d5;--green:#335c41;--soft:#e9eedf;--accent:#d7e98c;--red:#a33d30;--radius:18px;font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif;color:var(--ink);background:var(--paper)}
*{box-sizing:border-box}body{margin:0}button,input,textarea,select{font:inherit}button,a,input,textarea,select{outline-offset:4px}button{cursor:pointer;border:1px solid var(--line);border-radius:9px;padding:10px 15px;background:var(--panel);color:var(--ink);font-weight:600}button:hover{border-color:var(--green);background:var(--soft)}button:disabled{opacity:.55;cursor:wait}a{color:var(--green)}input,textarea,select{width:100%;border:1px solid var(--line);background:var(--panel);border-radius:9px;padding:10px;color:var(--ink)}textarea{resize:vertical;min-height:78px}label{display:block;font-size:12px;font-weight:650;margin-bottom:6px}.field{margin-bottom:14px}h1,h2,h3,p{margin:0}h1{font-size:clamp(30px,4vw,43px);letter-spacing:-1.6px;font-weight:550;line-height:1.15}h2{font-size:19px;letter-spacing:-.5px;font-weight:600}h3{font-size:15px}p{line-height:1.6}.muted{color:var(--muted);font-size:13px}.eyebrow{font-family:ui-monospace,monospace;text-transform:uppercase;font-size:10px;letter-spacing:1.4px;color:var(--muted)}.primary{background:var(--green);color:white;border-color:var(--green)}.primary:hover{background:#24482f;color:white}.small{font-size:12px;padding:7px 10px}.ghost{background:transparent}.row{display:flex;align-items:center;gap:10px}.between{justify-content:space-between}.wrap{flex-wrap:wrap}.stack{display:grid;gap:16px}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px}.brand-mark{width:30px;height:30px;background:var(--green);color:var(--accent);display:grid;place-items:center;border-radius:9px;font-size:20px}.topbar{height:76px;max-width:1440px;margin:auto;padding:0 42px;border-bottom:1px solid var(--line)}.brand{font-size:14px;font-weight:700;letter-spacing:-.3px}.tag{font:10px ui-monospace,monospace;text-transform:uppercase;letter-spacing:.7px;background:var(--soft);padding:6px 9px;border-radius:6px;color:var(--green)}main{max-width:1440px;margin:auto;padding:38px 42px 60px}.intro{margin-bottom:30px;align-items:flex-end}.intro p{margin-top:12px}.date{font-size:12px;color:var(--muted)}.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:25px}.stat{border:1px solid var(--line);padding:18px 21px;border-radius:12px;display:flex;align-items:center;justify-content:space-between;background:#ffffff60}.stat strong{font-weight:500;font-size:27px}.workspace{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(330px,.9fr);gap:24px;align-items:start}.panel{border:1px solid var(--line);border-radius:var(--radius);background:var(--panel);overflow:hidden}.panel-head{padding:23px 24px;border-bottom:1px solid var(--line)}.panel-body{padding:22px 24px}.section-note{margin-top:6px}.task{padding:18px 22px;border-bottom:1px solid var(--line);transition:background .15s}.task:last-child{border-bottom:0}.task.selected{background:#eff3e8;border-left:3px solid var(--green);padding-left:19px}.task.child{margin-left:28px;border-left:1px solid var(--line)}.task-main{align-items:flex-start}.check{width:20px;height:20px;flex:none;margin:2px 0 0;accent-color:var(--green);cursor:pointer}.task-title{display:block;text-align:left;border:0;background:none;padding:0;font-weight:600;font-size:14px;line-height:1.5}.task-title:hover{background:transparent;text-decoration:underline}.task-title.done{text-decoration:line-through;color:var(--muted)}.task-copy{flex:1;min-width:0}.task-description{font-size:12px;white-space:pre-wrap;overflow-wrap:anywhere;max-height:85px;overflow:auto;color:var(--muted);margin-top:5px}.meta{display:flex;gap:7px;align-items:center;flex-wrap:wrap;margin-top:9px;font-size:10px;color:var(--muted)}.pill{border-radius:5px;padding:3px 6px;background:var(--soft);font-size:10px;color:var(--green)}.pill.high,.pill.very_high{background:#f1e8cd;color:#786022}.empty{padding:30px 24px;text-align:center;color:var(--muted)}.empty-symbol{font-size:31px;display:block;color:#8f9e7e;margin-bottom:12px}.empty p{font-size:13px;max-width:280px;margin:8px auto}.task-form{border-top:1px solid var(--line);padding:20px 24px;background:#fafbf5}.task-form summary{cursor:pointer;font-size:13px;font-weight:650}.task-form[open] summary{margin-bottom:18px}.focus{padding:18px;background:var(--soft);border-radius:12px;margin-bottom:18px}.focus h3{margin-top:7px;overflow-wrap:anywhere}.context{margin-top:24px}.reply{white-space:pre-wrap;font-size:13px;line-height:1.7;margin:14px 0;overflow-wrap:anywhere}.proposal{border:1px solid var(--line);padding:17px;border-radius:12px;margin-top:15px;background:#fbfcf7}.proposal-head{margin-bottom:15px}.proposal-step{padding-top:13px;border-top:1px solid var(--line);margin-top:13px}.proposal-step textarea{font-size:12px;min-height:58px;margin-top:7px}.proposal-step input{font-size:13px}.review-actions{margin-top:15px;display:flex;gap:9px}.activity{margin-top:22px}.activity-item{padding:12px 0;border-bottom:1px solid var(--line);font-size:12px}.activity-item:last-child{border:0}.dot{width:7px;height:7px;border-radius:50%;background:#8e9d83;display:inline-block;margin-right:8px}.dot.running{background:#c68a2b;animation:pulse 1.4s infinite}.dot.failed,.dot.stale{background:var(--red)}.history{max-height:240px;overflow:auto}.chat-message{font-size:12px;padding:11px 12px;margin:9px 0;background:var(--soft);border-radius:9px;white-space:pre-wrap;overflow-wrap:anywhere}.chat-message.user{background:var(--paper)}.chat-message small{display:block;color:var(--muted);font-size:10px;margin-bottom:5px}.error{border:1px solid #e2b8af;background:#fff1ed;color:#82372a;border-radius:10px;padding:14px 18px;margin-bottom:18px;font-size:13px;white-space:pre-wrap}.notice{font-size:12px;color:var(--green);min-height:20px;margin-bottom:12px}.pet{position:fixed;right:22px;bottom:20px;border-radius:50%;width:52px;height:52px;background:var(--green);color:var(--accent);box-shadow:0 5px 18px #23382a22;padding:0;font-size:24px;z-index:3}.pet:hover{background:#24482f;color:var(--accent)}dialog{background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:18px;padding:25px;max-width:500px;width:calc(100% - 32px)}dialog::backdrop{background:#15291b66}dialog h2{margin-bottom:22px}footer{margin-top:28px;font-size:11px;color:var(--muted)}[hidden]{display:none!important}@keyframes pulse{50%{opacity:.35}}@media(max-width:800px){.workspace{grid-template-columns:1fr}.topbar{padding:0 20px}main{padding:28px 20px}.intro{align-items:flex-start;gap:20px}.stats{gap:8px}.stat{padding:13px;display:block}.stat strong{display:block;margin-top:6px}.panel-head,.panel-body{padding:20px}.topbar .tag{display:none}}@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}

body{background:#f8f9f5}.topbar{height:70px;border:0}.topbar a{font-size:12px;text-decoration:none}.canvas-layout{display:grid;grid-template-columns:minmax(0,1fr) 380px;gap:48px;align-items:start}main{max-width:1280px;padding-top:32px}.canvas{min-width:0}.canvas h1{font-size:32px;font-weight:500;letter-spacing:-1px}.canvas .intro{margin-bottom:24px}.canvas .intro p{max-width:430px}.cards{display:grid;gap:16px}.card{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:24px}.card h2{font-size:18px;overflow-wrap:anywhere}.card p{font-size:13px;white-space:pre-wrap;overflow-wrap:anywhere;color:var(--muted);margin-top:10px}.card .task{padding:14px 0}.card .task:last-child{padding-bottom:0}.card.completed h2{text-decoration:line-through;color:var(--muted)}.chat{position:sticky;top:24px;min-width:0}.chat h2{font-size:16px;margin-bottom:20px}.history{max-height:45vh}.chat-message{font-size:13px;padding:14px;margin-bottom:12px}.chat-message.user{background:#edf0e8}.composer{background:var(--panel);border:1px solid #cbd3c5;border-radius:16px;padding:16px;box-shadow:0 8px 24px #25342c06}.composer textarea{border:0;padding:0;min-height:100px;resize:vertical;background:none;line-height:1.6}.composer label{font-size:12px;color:var(--muted);font-weight:500;margin-bottom:12px}.composer .row{margin-top:12px}.composer .muted{font-size:11px}.status{font-size:12px;color:var(--muted);min-height:24px;margin:10px 0}.proposal{margin-bottom:16px}.proposal .field{margin-top:12px}.proposal input,.proposal textarea{background:var(--panel)}.proposal h3{font-size:16px}.proposal .review-actions{flex-wrap:wrap}.review-heading{font-size:12px;color:var(--green);margin:24px 0 8px}.save-hint{font-size:11px;color:var(--muted);margin-top:14px}.canvas-state{border:1px dashed var(--line);border-radius:16px;padding:32px;min-height:180px;display:flex;flex-direction:column;justify-content:center;align-items:flex-start;gap:10px;color:var(--muted)}.canvas-state h2{font-size:16px;font-weight:500;color:var(--ink)}.canvas-state p{font-size:13px;max-width:360px}.canvas-state .empty-mark{font-size:24px;color:#7b8e71;margin-bottom:4px}.task-title{text-align:left}.meta button{font-size:11px}#reviews:empty{display:none}.error{margin-top:8px}button:focus-visible,a:focus-visible{outline:2px solid var(--green)}@media(max-width:900px){.canvas-layout{grid-template-columns:1fr;gap:32px}.chat{position:static;width:100%}.history{max-height:340px}.topbar{padding:0 20px}.topbar .brand{font-size:12px}.card{padding:20px}main{padding:20px 20px 50px}}
.voice-preview{font-size:12px;color:var(--muted);white-space:pre-wrap;overflow-wrap:anywhere;margin-top:10px}.voice-status{font-size:11px;line-height:1.5;margin-top:10px;color:var(--muted)}#voice[aria-pressed="true"]{background:var(--soft);border-color:var(--green)}
</style></head><body>
<header class="topbar row between"><div class="row"><span class="brand-mark" aria-hidden="true">✳</span><span class="brand">Visual Second Brain</span></div><nav class="row"><button id="refresh" class="small ghost">Refresh</button><a href="/dev">Dev ↗</a><button id="signout" class="small ghost" hidden>Sign out</button></nav></header>
<main><div id="error" class="error" role="alert" hidden></div><div id="notice" class="notice" role="status" aria-live="polite"></div>
<section id="access" class="panel" hidden style="margin-bottom:24px"><form id="access-form" class="panel-body"><h2>Demo access</h2><p class="muted">Enter the app’s demo access token. Your connection is shared with the dev page for eight hours.</p><div class="row" style="margin-top:12px"><input id="token" type="password" aria-label="Demo access token" autocomplete="off" maxlength="4096" required><button class="primary">Connect</button></div></form></section>
<div id="layout" class="canvas-layout"><section class="canvas" aria-label="Your saved tasks"><div class="intro"><div class="eyebrow">Your workspace</div><h1 style="margin-top:12px">A little clarity.</h1><p class="muted">Saved plans, ready when you are.</p></div><div id="canvas" aria-live="polite"><div class="canvas-state"><p>Loading your workspace…</p></div></div></section>
<aside class="chat" aria-label="Chat with Muse"><h2>With Muse</h2><div id="conversation" class="history" aria-live="polite"></div><div id="status" class="status" role="status" aria-live="polite"></div>
<form id="chat-form" class="composer"><label for="message">What’s on your mind?</label><textarea id="message" maxlength="10000" required placeholder="Tell Muse what you need to do…"></textarea><div class="row between"><div class="row wrap" style="margin:0"><button id="voice" class="small" type="button" aria-pressed="false" aria-describedby="voice-status voice-privacy">Use voice</button><button id="voice-retry" class="small ghost" type="button" hidden>Retry transcription</button><button id="voice-cancel" class="small ghost" type="button" hidden>Cancel</button></div><button id="send" class="primary" type="submit">Send ↗</button></div><p id="voice-status" class="voice-status" role="status" aria-live="polite"></p><p id="voice-preview" class="voice-preview" hidden></p><p id="voice-privacy" class="voice-status">Record up to one minute. Stop &amp; transcribe sends audio to Meta for transcription. Review the text before Send. This app does not save audio.</p></form><p class="save-hint">Muse proposes. You review and save.</p><div id="reviews"></div></aside></div></main>
<dialog id="edit-dialog"><form id="edit-form"><div class="row between" style="margin-bottom:20px"><h2 style="margin:0">Edit task</h2><button type="button" id="close-edit" class="small" aria-label="Close editor">✕</button></div><input id="edit-id" type="hidden"><div class="field"><label for="edit-title">Task</label><input id="edit-title" required maxlength="300"></div><div class="field"><label for="edit-description">Details</label><textarea id="edit-description" maxlength="10000"></textarea></div><div class="grid2"><div class="field"><label for="edit-deadline">Due date</label><input id="edit-deadline" type="date"></div><div class="field"><label for="edit-importance">Importance</label><select id="edit-importance" data-level-select></select></div></div><div class="field"><label for="edit-status">Status</label><select id="edit-status"><option value="pending">Pending</option><option value="in_progress">In progress</option><option value="completed">Completed</option></select></div><button class="primary" type="submit">Save changes</button></form></dialog>
<script>
'use strict';
const $=s=>document.querySelector(s),esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels={very_low:'Very low',low:'Low',medium:'Medium',high:'High',very_high:'Very high'};
let state={tasks:[],messages:[],runs:[]},ranges={},busy=false,pending=null,editVersion=null;
const drafts=new Map();
document.querySelectorAll('[data-level-select]').forEach(el=>el.innerHTML='<option value="">Let Muse assess</option>'+Object.entries(labels).map(([k,v])=>`<option value="${k}">${v}</option>`).join(''));
function level(t){return t.user_importance_level||Object.keys(ranges).find(k=>t.importance_score!==null&&t.importance_score>=ranges[k].min&&t.importance_score<=ranges[k].max)||'';}
function badge(t){return `<span class="pill ${esc(level(t))}">${esc(labels[level(t)]||'Unassessed')}</span>`;}
function error(e){$('#error').textContent=e.message||'Something went wrong. Your draft is still here.';$('#error').hidden=false;}
async function api(path,method='GET',body){let r;try{r=await fetch(path,{method,credentials:'same-origin',headers:{'Content-Type':'application/json'},...(body===undefined?{}:{body:JSON.stringify(body)})});}catch{throw Error('Could not reach the server. Your draft is preserved; try again.');}let data;try{data=await r.json();}catch{throw Error('The server returned an unreadable response. Your draft is preserved.');}if(!r.ok){if(r.status===401){endVoice({discard:true});$('#access').hidden=false;$('#signout').hidden=true;state={tasks:[],messages:[],runs:[]};render();}throw Error((data.error?.message||'Request failed')+(r.status===409?' Refresh to see the latest state.':''));}return data;}
function setBusy(value){if(value)endVoice({discard:true});busy=value;document.querySelectorAll('button,input,textarea,select').forEach(el=>el.disabled=value);$('#send').textContent=value?'Working…':'Send ↗';syncVoice();}
async function refresh(){const [data,levels,health]=await Promise.all([api('/api/dashboard'),api('/api/importance-levels'),api('/health')]);state=data;ranges=levels;$('#access').hidden=true;$('#signout').hidden=!health.demo_access_required;render();}
async function action(work,success){if(busy)return;setBusy(true);$('#error').hidden=true;$('#notice').textContent='';try{await work();await refresh();if(success)$('#notice').textContent=success;}catch(e){$('#status').textContent='';error(e);}finally{setBusy(false);}}
function taskRow(t){return `<div class="task"><div class="row task-main"><input class="check" type="checkbox" data-complete="${t.id}" aria-label="Mark ${esc(t.title)} ${t.status==='completed'?'pending':'complete'}" ${t.status==='completed'?'checked':''}><div class="task-copy"><button class="task-title ${t.status==='completed'?'done':''}" data-edit="${t.id}">${esc(t.title)}</button>${t.description?`<p class="task-description">${esc(t.description)}</p>`:''}<div class="meta">${badge(t)}${t.deadline?`<span>Due ${esc(t.deadline)}</span>`:''}${t.status==='in_progress'?'<span>In progress</span>':''}</div></div><button class="small ghost" data-edit="${t.id}">Edit</button></div>${state.tasks.filter(c=>c.parent_task_id===t.id).sort((a,b)=>a.position-b.position).map(taskRow).join('')}</div>`;}
function render(){
 const roots=state.tasks.filter(t=>!t.parent_task_id);
 $('#canvas').innerHTML=roots.length?`<div class="cards">${roots.map(t=>`<article class="card ${t.status==='completed'?'completed':''}"><div class="row between"><h2>${esc(t.title)}</h2><button class="small ghost" data-edit="${t.id}" aria-label="Edit ${esc(t.title)}">Edit</button></div>${t.description?`<p>${esc(t.description)}</p>`:''}<div class="meta">${badge(t)}${t.deadline?`<span>Due ${esc(t.deadline)}</span>`:''}<span>${esc(t.status.replace('_',' '))}</span><button class="small ghost" data-toggle="${t.id}">${t.status==='completed'?'Reopen':'Mark complete'}</button></div>${state.tasks.filter(c=>c.parent_task_id===t.id).sort((a,b)=>a.position-b.position).map(taskRow).join('')}</article>`).join('')}</div>`:'<div class="canvas-state"><span class="empty-mark" aria-hidden="true">✳</span><h2>Your plans will live here.</h2><p>Tell Muse what needs doing. Review a proposed plan, then save it to your workspace.</p></div>';
 $('#conversation').innerHTML=state.messages.slice(-40).map(m=>{const run=state.runs.find(r=>r.id===m.run_id),status=run?.status;const label=m.role==='user'?'YOU':status==='awaiting_review'?'MUSE · PROPOSAL, NOT SAVED':status==='superseded'?'MUSE · EARLIER PROPOSAL':status==='stale'?'MUSE · OUTDATED PROPOSAL':'MUSE';return `<div class="chat-message ${m.role==='user'?'user':''}"><small>${label}</small>${esc(m.content)}</div>`;}).join('');$('#conversation').scrollTop=$('#conversation').scrollHeight;
 const running=state.runs.some(r=>r.status==='running');$('#status').textContent=running?'Muse is planning…':state.runs.at(-1)?.status==='failed'?'The last request failed. Your saved work is unchanged.':'';
 const reviews=state.runs.filter(r=>r.task_id===null&&r.status==='awaiting_review');
 $('#reviews').innerHTML=reviews.map(r=>{if(!drafts.has(r.id))drafts.set(r.id,structuredClone(r.proposal));const p=drafts.get(r.id);return `<div class="review-heading">Proposed changes · not saved yet</div><section class="proposal" data-run="${r.id}">${p.tasks.map((t,i)=>`<div data-object="${i}" class="proposal-step"><div class="row between"><h3>${t.task_id?'Update task':'New task'}</h3>${badge(t)}<button class="small ghost" data-remove-task="${i}">Remove</button></div><div class="field"><label for="title-${r.id}-${i}">Task</label><input id="title-${r.id}-${i}" data-key="title" maxlength="300" value="${esc(t.title)}"></div><div class="field"><label for="desc-${r.id}-${i}">Details</label><textarea id="desc-${r.id}-${i}" data-key="description" maxlength="10000">${esc(t.description)}</textarea></div><div class="field"><label for="date-${r.id}-${i}">Due date · confirm before saving</label><input id="date-${r.id}-${i}" data-key="deadline" type="date" value="${esc(t.deadline||'')}"></div>${t.subtasks.map((c,j)=>`<div class="proposal-step" data-child="${j}"><div class="row between"><label for="step-${r.id}-${i}-${j}">Step ${j+1}</label><button class="small ghost" data-remove-step="${j}">Remove</button></div><input id="step-${r.id}-${i}-${j}" data-key="title" maxlength="300" value="${esc(c.title)}"><textarea data-key="description" aria-label="Step ${j+1} details" maxlength="10000">${esc(c.description)}</textarea></div>`).join('')}${t.task_id&&t.subtasks.length?'<p class="muted">These steps will be added to the existing plan.</p>':''}</div>`).join('')}<div class="review-actions"><button class="primary small" data-save="${r.id}">Save reviewed plan</button><button class="small" data-reject="${r.id}">Dismiss</button></div></section>`;}).join('');
}
$('#chat-form').onsubmit=e=>{e.preventDefault();if(voiceSession||busy)return;const message=$('#message').value.trim();if(!message)return;if(message.length>10000){error(Error('Shorten your message to 10,000 characters before sending. Your transcript is preserved.'));return;}const latest=state.runs.filter(r=>r.task_id===null&&r.status==='awaiting_review').at(-1),review_draft=latest?(drafts.get(latest.id)||latest.proposal):null;const input={message,review_draft};if(!pending||JSON.stringify({message:pending.message,review_draft:pending.review_draft})!==JSON.stringify(input))pending={request_id:crypto.randomUUID(),...structuredClone(input)};const request=pending;action(async()=>{$('#status').textContent='Muse is planning…';const run=await api('/api/conversation','POST',request);if(run.status==='running')throw Error('Muse is still planning. Refresh to check, or retry the same message.');pending=null;await refresh();if(run.status==='failed')throw Error(run.error||'Muse could not reply. Try again.');if(run.status==='stale')throw Error('Your workspace changed during planning. Send again for a fresh proposal.');$('#message').value='';},'');};
$('#reviews').oninput=e=>{const section=e.target.closest('[data-run]'),object=e.target.closest('[data-object]');if(!section||!object||!e.target.dataset.key)return;let item=drafts.get(section.dataset.run).tasks[+object.dataset.object];const child=e.target.closest('[data-child]');if(child)item=item.subtasks[+child.dataset.child];item[e.target.dataset.key]=e.target.dataset.key==='deadline'?(e.target.value||null):e.target.value;};
$('#reviews').onclick=e=>{if(busy)return;const section=e.target.closest('[data-run]');if(!section)return;const id=section.dataset.run,p=drafts.get(id),object=e.target.closest('[data-object]');if(e.target.closest('[data-remove-task]')){p.tasks.splice(+object.dataset.object,1);render();}else if(e.target.closest('[data-remove-step]')){p.tasks[+object.dataset.object].subtasks.splice(+e.target.dataset.removeStep,1);render();}else if(e.target.closest('[data-save]')){if(!p.tasks.length||p.tasks.some(t=>!t.title.trim()||t.subtasks.some(c=>!c.title.trim()))){error(Error('Keep at least one task and give each task and step a title.'));return;}action(()=>api('/api/conversation/'+id+'/approve','POST',{proposal:p}),'Your reviewed plan is saved.');}else if(e.target.closest('[data-reject]'))action(()=>api('/api/runs/'+id+'/reject','POST'),'Proposal dismissed.');};
function openEditor(id){const t=state.tasks.find(t=>t.id===id);editVersion=t.version;$('#edit-id').value=t.id;$('#edit-title').value=t.title;$('#edit-description').value=t.description;$('#edit-deadline').value=t.deadline||'';$('#edit-importance').value=t.user_importance_level||'';$('#edit-status').value=t.status;$('#edit-dialog').showModal();}
function complete(id,value){const t=state.tasks.find(t=>t.id===id);action(()=>api('/api/tasks/'+id,'PATCH',{expected_version:t.version,status:value?'completed':'pending'}),'Task updated.');}
$('#canvas').onclick=e=>{if(busy)return;const edit=e.target.closest('[data-edit]'),toggle=e.target.closest('[data-toggle]');if(edit)openEditor(edit.dataset.edit);if(toggle)complete(toggle.dataset.toggle,state.tasks.find(t=>t.id===toggle.dataset.toggle).status!=='completed');};
$('#canvas').onchange=e=>{const el=e.target.closest('[data-complete]');if(!el)return;const checked=el.checked;el.checked=!checked;complete(el.dataset.complete,checked);};
$('#edit-form').onsubmit=e=>{e.preventDefault();action(async()=>{await api('/api/tasks/'+$('#edit-id').value,'PATCH',{expected_version:editVersion,title:$('#edit-title').value,description:$('#edit-description').value,deadline:$('#edit-deadline').value||null,user_importance_level:$('#edit-importance').value||null,status:$('#edit-status').value});$('#edit-dialog').close();},'Your correction is saved. Muse will use it next time.');};$('#close-edit').onclick=()=>$('#edit-dialog').close();
$('#refresh').onclick=()=>action(async()=>{},'Saved state refreshed.');$('#access-form').onsubmit=e=>{e.preventDefault();const token=$('#token').value;action(async()=>{await api('/api/session','POST',{token});$('#token').value='';},'Connected.');};
$('#signout').onclick=async()=>{if(busy)return;endVoice({discard:true});setBusy(true);$('#error').hidden=true;try{await api('/api/session','DELETE');state={tasks:[],messages:[],runs:[]};drafts.clear();pending=null;$('#chat-form').reset();$('#edit-form').reset();$('#edit-dialog').close();render();$('#access').hidden=false;$('#signout').hidden=true;$('#notice').textContent='Signed out.';}catch(e){error(e);}finally{setBusy(false);}};
// Voice input: local microphone capture, server-side Meta transcription, reviewed text.
const AudioContextClass=window.AudioContext||window.webkitAudioContext;
const voiceAvailable=!!(window.isSecureContext&&navigator.mediaDevices?.getUserMedia&&AudioContextClass&&window.AudioWorkletNode);
let voiceSession=null,voiceRecording=null;
const recorderCode=`class VoiceCapture extends AudioWorkletProcessor {
 process(inputs){const input=inputs[0]?.[0];if(input)this.port.postMessage(new Float32Array(input));return true;}
}registerProcessor('voice-capture',VoiceCapture);`;
function syncVoice(){
 const active=!!voiceSession,phase=voiceSession?.phase;
 $('#voice').disabled=busy||!voiceAvailable||phase==='requesting'||phase==='transcribing';
 $('#voice').textContent=phase==='requesting'?'Starting…':phase==='transcribing'?'Transcribing…':active?'Stop & transcribe':'Use voice';
 $('#voice').setAttribute('aria-pressed',String(active));
 $('#voice-cancel').hidden=!active&&!voiceRecording;$('#voice-cancel').disabled=busy;
 $('#voice-retry').hidden=active||!voiceRecording;$('#voice-retry').disabled=busy;
 $('#message').readOnly=active;$('#send').disabled=busy||active;
}
function releaseCapture(session){
 clearTimeout(session.timer);
 if(session.node){session.node.port.onmessage=null;session.node.disconnect();}
 if(session.source)session.source.disconnect();
 if(session.mute)session.mute.disconnect();
 if(session.stream)session.stream.getTracks().forEach(track=>track.stop());
 if(session.context)session.context.close().catch(()=>{});
 if(session.moduleURL)URL.revokeObjectURL(session.moduleURL);
}
function endVoice({cancel=false,message,discard=false}={}){
 const session=voiceSession;voiceSession=null;
 if(session){releaseCapture(session);session.controller?.abort();}
 if(cancel||discard)voiceRecording=null;
 $('#voice-preview').textContent='';$('#voice-preview').hidden=true;
 if(message)$('#voice-status').textContent=message;
 else if(session||cancel)$('#voice-status').textContent=cancel?'Recording discarded. Your typed draft is kept.':'Voice input stopped. Your typed draft is kept.';
 syncVoice();
}
function encodeWav(session){
 const buffer=new ArrayBuffer(44+session.samples*2),view=new DataView(buffer);
 const word=(offset,text)=>{for(let i=0;i<text.length;i++)view.setUint8(offset+i,text.charCodeAt(i));};
 word(0,'RIFF');view.setUint32(4,36+session.samples*2,true);word(8,'WAVE');word(12,'fmt ');
 view.setUint32(16,16,true);view.setUint16(20,1,true);view.setUint16(22,1,true);
 view.setUint32(24,session.rate,true);view.setUint32(28,session.rate*2,true);view.setUint16(32,2,true);view.setUint16(34,16,true);
 word(36,'data');view.setUint32(40,session.samples*2,true);
 let offset=44;
 for(const chunk of session.chunks)for(const value of chunk){const sample=Math.max(-1,Math.min(1,value));view.setInt16(offset,Math.round(sample*(sample<0?32768:32767)),true);offset+=2;}
 return new Blob([buffer],{type:'audio/wav'});
}
async function transcribeVoice(session){
 session.phase='transcribing';session.controller=new AbortController();syncVoice();
 $('#voice-preview').hidden=true;$('#voice-status').textContent='Transcribing your recording with Meta…';
 session.timer=setTimeout(()=>{if(voiceSession===session)endVoice({message:'Transcription timed out. Your draft and recording are kept. Retry transcription or continue typing.'});},55000);
 try{
  const response=await fetch('/api/voice/transcribe',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'audio/wav'},body:voiceRecording,signal:session.controller.signal});
  let data;try{data=await response.json();}catch{throw Error('The server returned an unreadable transcription response.');}
  if(voiceSession!==session)return;
  if(!response.ok){
   if(response.status===401){endVoice({discard:true,message:'Your demo session expired. Reconnect before recording again.'});api('/api/dashboard').catch(error);return;}
   throw Error(data.error?.message||'Voice transcription failed.');
  }
  if(typeof data.transcript!=='string'||!data.transcript.trim()||data.transcript.length>10000)throw Error('The server returned an invalid transcript.');
  const transcript=data.transcript.trim();
  $('#message').value=session.base+(session.base?' ':'')+transcript;
  endVoice({discard:true,message:$('#message').value.length>10000?'Transcript kept. Shorten your message to 10,000 characters before sending.':'Transcript ready. Review or edit it, then Send.'});
 }catch(e){
  if(voiceSession!==session)return;
  endVoice({message:(e instanceof TypeError?'Could not reach the transcription server. Check that the backend is running.':e.message)+' Your draft and recording are kept. Retry transcription or continue typing.'});
 }
}
function stopVoice(){
 const session=voiceSession;
 if(!session||!['recording','recorded'].includes(session.phase))return;
 releaseCapture(session);
 if(session.samples<session.rate/4){endVoice({discard:true,message:'The recording was too short. Speak for at least a moment, then stop.'});return;}
 voiceRecording=encodeWav(session);session.chunks=[];
 transcribeVoice(session);
}
$('#voice').onclick=async()=>{
 if(busy||!voiceAvailable)return;
 if(voiceSession){stopVoice();return;}
 voiceRecording=null;
 const session={base:$('#message').value,phase:'requesting',chunks:[],samples:0,seconds:-1};
 voiceSession=session;syncVoice();$('#voice-status').textContent='Waiting for microphone access…';
 session.timer=setTimeout(()=>{if(voiceSession===session)endVoice({message:'Microphone setup timed out. Check browser permission and try again.'});},20000);
 try{
  const stream=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:true,noiseSuppression:true}});
  if(voiceSession!==session){stream.getTracks().forEach(track=>track.stop());return;}
  session.stream=stream;
  session.context=new AudioContextClass({sampleRate:24000});session.rate=session.context.sampleRate;
  if(![16000,24000].includes(session.rate))throw Error('This browser could not capture audio at the required sample rate.');
  session.moduleURL=URL.createObjectURL(new Blob([recorderCode],{type:'text/javascript'}));
  await session.context.audioWorklet.addModule(session.moduleURL);
  if(voiceSession!==session)return;
  session.source=session.context.createMediaStreamSource(stream);
  session.node=new AudioWorkletNode(session.context,'voice-capture',{channelCount:1,channelCountMode:'explicit'});
  session.mute=session.context.createGain();session.mute.gain.value=0;
  session.source.connect(session.node);session.node.connect(session.mute);session.mute.connect(session.context.destination);
  session.node.port.onmessage=event=>{
   if(voiceSession!==session||session.phase!=='recording')return;
   const remaining=session.rate*60-session.samples,chunk=event.data.slice(0,remaining);
   session.chunks.push(chunk);session.samples+=chunk.length;
   const seconds=Math.floor(session.samples/session.rate);
   if(seconds!==session.seconds){session.seconds=seconds;$('#voice-preview').textContent=`Recorded ${seconds}s / 60s`;}
  };
  stream.getTracks().forEach(track=>track.onended=()=>{if(voiceSession===session&&session.phase==='recording')endVoice({discard:true,message:'The microphone disconnected. Your typed draft is kept. Connect it and try again.'});});
  await session.context.resume();
  if(voiceSession!==session)return;
  clearTimeout(session.timer);session.phase='recording';syncVoice();
  $('#voice-preview').textContent='Recorded 0s / 60s';$('#voice-preview').hidden=false;
  $('#voice-status').textContent='Recording… Stop & transcribe when you’re ready.';
  session.timer=setTimeout(()=>{if(voiceSession!==session)return;session.phase='recorded';releaseCapture(session);syncVoice();$('#voice-status').textContent='One-minute limit reached. Choose Stop & transcribe, or Cancel.';},60000);
 }catch(e){
  if(voiceSession!==session)return;
  const message=e.name==='NotAllowedError'?'Microphone access was denied. Allow this site to use your microphone in browser settings, or type your message.':e.name==='NotFoundError'?'No microphone was found. Connect one and try again, or type your message.':'Microphone capture could not start. Check your microphone and browser permissions, or type your message.';
  endVoice({discard:true,message});
 }
};
$('#voice-retry').onclick=()=>{if(busy||voiceSession||!voiceRecording)return;const session={base:$('#message').value,phase:'transcribing'};voiceSession=session;transcribeVoice(session);};
$('#voice-cancel').onclick=()=>endVoice({cancel:true});
window.addEventListener('pagehide',()=>endVoice({discard:true}));
document.addEventListener('visibilitychange',()=>{if(document.hidden)endVoice({discard:true});});
$('#voice-status').textContent=voiceAvailable?'Record your thoughts, then review the transcript.':!window.isSecureContext?'Voice input needs HTTPS or localhost. You can still type your message.':'Microphone recording is unavailable in this browser. You can still type your message.';
syncVoice();
// End voice input.

refresh().catch(error);
window.addEventListener('pageshow',event=>{if(event.persisted)refresh().catch(error);});
setInterval(()=>{if(busy&&pending)api('/api/dashboard').then(data=>{$('#status').textContent=data.runs.some(r=>r.status==='running')?'Muse is planning…':'';}).catch(()=>{});},4000);
</script></body></html>"""
