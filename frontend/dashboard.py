"""Buildless conversation canvas served by FastAPI."""

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Visual Second Brain</title><style>

/* Shared palette and controls. No external fonts or asset requests. */
:root{--paper:#f3efe5;--panel:#fffcf5;--ink:#252b25;--muted:#666b60;--line:#d7d5c8;--green:#304b36;--soft:#e8ecdd;--accent:#e4ef95;--red:#973e32;font-family:ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink);background:var(--paper);font-synthesis:none}

*{box-sizing:border-box}
body{margin:0}
button,input,textarea,select{font:inherit;color:inherit}
button,a,input,textarea,select{outline-offset:4px}
button{cursor:pointer;border:1px solid var(--line);border-radius:9px;padding:10px 15px;background:var(--panel);font-size:13px;font-weight:600;transition:background .15s,border-color .15s}
button:hover{border-color:#9aaa98;background:var(--soft)}
button:disabled{opacity:.55;cursor:wait}
button[data-handoff]:disabled{cursor:default}
a{color:var(--green);text-underline-offset:4px}
button:focus-visible,a:focus-visible,input:focus-visible,textarea:focus-visible,select:focus-visible{outline:2px solid var(--green)}
input,textarea,select{width:100%;min-width:0;border:1px solid var(--line);background:var(--panel);border-radius:8px;padding:11px}
textarea{resize:vertical;min-height:84px;line-height:1.6}
label{display:block;font-size:12px;font-weight:600;margin-bottom:7px}
.field{margin-bottom:16px}
h1,h2,h3,p{margin:0}
h1{font-size:clamp(32px,3.4vw,46px);font-weight:500;letter-spacing:-1.8px;line-height:1.15}
h2{font-size:19px;font-weight:600;letter-spacing:-.5px}
h3{font-size:15px}
p{line-height:1.65}
.muted{color:var(--muted);font-size:13px}
.eyebrow{font-size:10px;font-weight:650;text-transform:uppercase;letter-spacing:1.7px;color:var(--muted)}
.primary{background:var(--green);color:white;border-color:var(--green)}
.primary:hover{background:#244832;color:white}
.small{font-size:12px;padding:7px 10px}
.ghost{background:transparent}
.row{display:flex;align-items:center;gap:10px}
.between{justify-content:space-between}
.wrap{flex-wrap:wrap}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
[hidden]{display:none!important}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap;border:0}

/* A full-width canvas, with Muse available from a corner launcher. */
.topbar{height:82px;max-width:none;margin:auto;padding:0 32px;border-bottom:1px solid var(--line)}
.brand-mark{width:34px;height:34px;background:var(--green);color:var(--accent);display:grid;place-items:center;border-radius:11px;font-size:25px}
.brand{font-size:14px;font-weight:650;letter-spacing:-.4px}
.topbar nav{gap:20px}
.topbar a{font-size:12px;text-decoration:none}
.topbar a:hover{text-decoration:underline}
main{max-width:none;margin:auto;padding:28px 32px 120px}
.canvas-layout{display:block}.canvas{max-width:1040px;margin:0 auto}
.canvas{min-width:0}
.intro{margin:2px 0 34px}
.intro h1{margin-top:15px}
.intro p{margin-top:12px;max-width:440px}
.workspace-date{font-size:11px;color:var(--muted);letter-spacing:.2px}
.canvas-state{border:1px dashed #cdd4c5;border-radius:18px;min-height:310px;padding:38px;display:flex;flex-direction:column;justify-content:center;align-items:flex-start;gap:12px;background:linear-gradient(145deg,#fffefa88,#edf1e633)}
.canvas-state h2{font-size:20px;font-weight:500}
.canvas-state p{font-size:13px;color:var(--muted);max-width:340px}
.empty-mark{width:44px;height:44px;display:grid;place-items:center;background:var(--soft);border-radius:14px;font-size:29px;color:var(--green);margin-bottom:12px}
.canvas-state a{font-size:12px;margin-top:6px}

/* Saved objects stay visually distinct from proposals. */
.cards{display:grid;gap:20px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:25px 26px;box-shadow:0 3px 12px #283c3203}
.card-head{align-items:flex-start}
.card h2{font-size:20px;line-height:1.4;overflow-wrap:anywhere}
.card p{font-size:13px;white-space:pre-wrap;overflow-wrap:anywhere;color:var(--muted);margin-top:10px}
.card.completed h2{text-decoration:line-through;color:var(--muted)}
.meta{display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin-top:14px;font-size:11px;color:var(--muted)}
.pill{border-radius:5px;padding:4px 7px;background:var(--soft);font-size:10px;font-weight:600;color:var(--green)}
.pill.high,.pill.very_high{background:#f4ebd5;color:#765b20}
.task-progress{display:flex;align-items:center;gap:12px;margin:21px 0 5px;font-size:11px;color:var(--muted)}
progress{appearance:none;width:72px;height:4px;border:0;border-radius:4px;background:var(--soft);accent-color:var(--green)}
progress::-webkit-progress-bar{background:var(--soft);border-radius:4px}
progress::-webkit-progress-value{background:var(--green);border-radius:4px}
progress::-moz-progress-bar{background:var(--green);border-radius:4px}
.task{padding:16px 0;border-bottom:1px solid var(--line)}
.task:last-child{border-bottom:0;padding-bottom:0}
.task .task{margin-left:16px}
.task-main{align-items:flex-start}
.check{width:18px;height:18px;flex:none;margin:3px 0 0;accent-color:var(--green);cursor:pointer}
.task-copy{flex:1;min-width:0}
.task-title{display:block;text-align:left;border:0;background:none;padding:0;font-weight:500;font-size:13px;line-height:1.6;overflow-wrap:anywhere}
.task-title:hover{background:none;text-decoration:underline}
.task-title.done{text-decoration:line-through;color:var(--muted)}
.task-description{font-size:12px;white-space:pre-wrap;overflow-wrap:anywhere;color:var(--muted);margin-top:5px}
.task .meta{margin-top:7px}
.task .ghost{font-size:11px}
.card-actions{margin-top:20px;padding-top:16px;border-top:1px solid var(--line);display:flex;justify-content:flex-end}
.task-status{font-size:10px;letter-spacing:.5px;text-transform:uppercase}

/* Muse is a companion panel; greeting text is guidance, not a model reply. */
.chat{position:fixed;z-index:20;right:28px;bottom:104px;width:400px;max-width:calc(100vw - 56px);max-height:calc(100dvh - 132px);overflow-y:auto;overscroll-behavior:auto;min-width:0;background:linear-gradient(160deg,#fffefa,#f0f3e9);border:1px solid #d7decf;border-radius:24px;padding:22px;box-shadow:0 24px 80px #233c3226,0 4px 16px #233c3210;transform-origin:calc(100% - 24px) bottom;opacity:0;visibility:hidden;pointer-events:none;transform:translateY(16px) scale(.94);transition:opacity .2s ease,transform .24s cubic-bezier(.2,.8,.2,1),visibility .24s}
.chat.is-open{visibility:visible;opacity:1;pointer-events:auto;transform:translateY(0) scale(1);transition-delay:0s}
.muse-launcher{position:fixed;z-index:21;right:28px;bottom:24px;bottom:max(24px,env(safe-area-inset-bottom));display:grid;place-items:center;width:64px;height:64px;padding:0;border-radius:50%;color:#e9f3ce;background:radial-gradient(circle at 30% 20%,#5d8062,#315b43 65%,#244432);border:1px solid #456d4e;box-shadow:0 7px 24px #233c3230,inset 0 1px 1px #ffffff40;transition:transform .2s,box-shadow .2s}
.muse-launcher:hover{color:#f3f9e5;background:radial-gradient(circle at 30% 20%,#6c8c6a,#315b43 65%);transform:translateY(-3px);box-shadow:0 12px 28px #233c3238}
.muse-launcher[aria-expanded="true"]{box-shadow:0 0 0 5px #dfe8d5,0 7px 24px #233c3220}
.muse-launcher svg{width:32px;height:32px;filter:drop-shadow(0 2px 3px #173d2733)}
.launcher-caption{position:absolute;right:76px;white-space:nowrap;background:var(--panel);color:var(--green);border:1px solid var(--line);border-radius:8px;padding:7px 11px;font-size:11px;box-shadow:0 3px 12px #233c3208;pointer-events:none}
.muse-launcher[aria-expanded="true"] .launcher-caption{display:none}
.chat-head-copy{flex:1}.chat-close{width:32px;height:32px;padding:0;border:0;border-radius:50%;background:var(--paper);color:var(--muted);font-size:19px;font-weight:400}
.chat-entry{display:inline-block;margin-top:16px;color:var(--green);font-size:12px;background:transparent;border:0;padding:0;text-decoration:underline;text-underline-offset:4px}
.chat-head{margin-bottom:18px;padding-bottom:16px;border-bottom:1px solid #d9ded1}
.muse-mark{display:grid;place-items:center;width:36px;height:36px;background:var(--panel);border:1px solid var(--line);border-radius:50%;font-size:23px;color:var(--green)}
.chat h2{font-size:15px;letter-spacing:-.2px}
.chat-head p{font-size:11px;color:var(--muted);margin-top:3px}
.chat-welcome{padding:8px 2px 22px}
.chat-welcome h3{font-size:20px;font-weight:500;letter-spacing:-.5px;line-height:1.4}
.chat-welcome p{font-size:13px;color:var(--muted);margin-top:10px}
.history{max-height:28vh;overflow:auto;overscroll-behavior:auto}
.chat-message{font-size:13px;line-height:1.7;padding:14px 2px;margin-bottom:14px;white-space:pre-wrap;overflow-wrap:anywhere}
.chat-message.user{background:#fffefa;border:1px solid var(--line);padding:13px 15px;border-radius:12px}
.chat-message small{display:block;color:var(--muted);font-size:9px;letter-spacing:1px;font-weight:650;margin-bottom:7px}
.composer{background:#fff;border:1px solid #dce2d5;border-radius:20px;padding:16px 16px 10px;box-shadow:0 3px 14px #283c3205;transition:border-color .18s,box-shadow .18s}
.composer textarea{display:block;width:100%;height:72px;min-height:72px;max-height:180px;resize:none;border:0;border-radius:0;padding:0 2px;background:transparent;font-size:14px;line-height:1.65;box-shadow:none}
.composer textarea::placeholder{color:#869186;font-weight:400}
.composer textarea:focus-visible{outline:0}
.composer:focus-within{border-color:#8ba687;box-shadow:0 0 0 3px #dfe8d555,0 5px 18px #283c3206}
.composer label{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap}
.composer>.row{margin-top:10px;padding-top:9px;border-top:1px solid #eef0e9;align-items:center;flex-wrap:wrap;gap:8px}
.composer #send{display:grid;place-items:center;flex:none;width:34px;height:34px;margin-left:auto;padding:0;border-radius:50%;font-size:21px;line-height:1;font-weight:400;box-shadow:0 2px 5px #315b4315}
.composer button{font-size:11px;padding:7px 10px;border-radius:20px}
.composer #voice{display:grid;place-items:center;flex:none;width:34px;height:34px;padding:0;border-radius:50%;background:var(--soft);border-color:transparent;color:var(--green)}.composer #voice svg{width:18px;height:18px}.composer #voice[data-phase="requesting"] svg,.composer #voice[data-phase="transcribing"] svg{animation:mic-spin 1s linear infinite}@keyframes mic-spin{to{transform:rotate(360deg)}}
.composer #voice:hover{background:#dfe5fa}
.composer #voice[aria-pressed="true"]{background:var(--green);border-color:var(--green);color:#fff}
.voice-note{margin:10px 3px 0;color:var(--muted);font-size:10px;line-height:1.6}
.voice-note summary{cursor:pointer;list-style:none;color:#758071}
.voice-note summary::-webkit-details-marker{display:none}
.disclosure-chevron{display:block;width:14px;height:14px;flex:none}
.workspace-menu[open]>summary .disclosure-chevron,.voice-note[open]>summary .disclosure-chevron{transform:rotate(180deg)}
.voice-note .voice-status{margin-top:6px}
.voice-status:empty{display:none}
.status{font-size:12px;color:var(--muted);margin:10px 0;line-height:1.6}
.status:empty{display:none}
.save-hint{font-size:10px;color:var(--muted);margin-top:13px;text-align:center}
.voice-preview{font-size:12px;color:var(--green);margin-top:10px}
.voice-status{font-size:10px;line-height:1.6;margin-top:10px;color:var(--muted);overflow-wrap:anywhere}
#voice[aria-pressed="true"]{background:var(--green);border-color:var(--green);color:#fff}
#review-link{display:block;padding:11px 13px;margin-bottom:16px;border:1px solid #c5d2b0;border-radius:9px;background:#e3ebd6;font-size:12px;text-decoration:none}

/* Old unsaved plans remain recoverable; new chat requests save actual tasks. */
#reviews{scroll-margin-top:24px}#reviews:empty{display:none}.legacy-plan{padding:18px;border:1px solid var(--line);border-radius:12px;background:var(--panel);margin-bottom:20px;font-size:12px}.legacy-plan p{color:var(--muted)}.legacy-plan ul{padding-left:20px}.legacy-plan .row{flex-wrap:wrap;margin-top:12px}
.error{border:1px solid #e2b8af;background:#fff1ed;color:var(--red);border-radius:10px;padding:14px 18px;margin-bottom:20px;font-size:13px;white-space:pre-wrap;overflow-wrap:anywhere}
.notice{font-size:12px;color:var(--green);margin-bottom:18px}
.notice:empty{display:none}
.panel{border:1px solid var(--line);border-radius:16px;background:var(--panel)}
.panel-body{padding:24px}
.panel-body h2{margin-bottom:8px}
dialog{background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:18px;padding:26px;max-width:520px;width:calc(100% - 32px);max-height:calc(100dvh - 40px);overflow:auto}
dialog::backdrop{background:#182a2266}
dialog h2{margin-bottom:22px}




@media(max-width:1000px){.topbar{padding:0 28px}
main{padding:32px 28px 120px}

.card{padding:22px}
.workspace-date{display:none}
}

@media(max-width:760px){.topbar{height:70px;padding:0 18px}
.topbar nav{gap:10px}
.brand{font-size:12px;max-width:100px}
.brand-mark{width:28px;height:28px;font-size:22px}
.topbar a{font-size:11px}
.topbar button{font-size:11px;padding:6px}

main{padding:28px 18px 120px}
.intro{margin-bottom:24px}
h1{font-size:36px}
.canvas-state{min-height:210px;padding:26px}
.chat{right:16px;bottom:96px;width:400px;max-width:calc(100vw - 32px);max-height:calc(100dvh - 112px);padding:20px;border-radius:20px}.muse-launcher{right:16px;bottom:18px;bottom:max(18px,env(safe-area-inset-bottom));width:60px;height:60px}
.history{max-height:25vh}

.card{padding:20px}
.proposal{padding:18px}
.grid2{grid-template-columns:1fr}
.card-head{gap:15px}
.card h2{font-size:18px}
.composer textarea{height:64px;min-height:64px}
}

@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}
}


/* Three-panel daily overview. Details stay behind disclosure controls. */
.canvas{max-width:none}.intro{margin-bottom:22px;gap:14px}.intro h1.eyebrow{font-size:11px;letter-spacing:1.7px;margin:0 0 6px;line-height:1.4}.intro .workspace-date{display:block}
.overview-toolbar{display:flex;align-items:center;gap:12px}
.overview-grid{display:grid;grid-template-columns:1.15fr 1fr;gap:22px}.overview-panel{background:var(--panel);border:1px solid var(--line);border-radius:22px;padding:26px;min-width:0}
.panel-top{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:24px}.panel-top h2{font-size:18px;letter-spacing:-.5px}.panel-kicker{font-size:10px;letter-spacing:1.6px;text-transform:uppercase;color:var(--muted);margin-bottom:6px}
.panel-icon{display:grid;place-items:center;width:38px;height:38px;border-radius:12px;background:var(--soft);font-size:21px;color:var(--green)}
.focus-list{display:grid;gap:12px}.focus-item{padding:18px;background:#f5f5ef;border:1px solid transparent;border-radius:14px;min-width:0}.focus-item:first-child{background:#ecf1df;border-color:#dce5c9}
.focus-context{display:flex;align-items:center;gap:10px;margin-bottom:12px;min-width:0}.focus-rank{font-size:10px;color:var(--muted)}.focus-plan{font-size:15px;font-weight:600;line-height:1.45;color:var(--ink);flex:1;min-width:0;overflow-wrap:anywhere}.focus-plan button{font:inherit;color:inherit;text-align:left;padding:0;border:0;background:none}.focus-plan button:hover{text-decoration:underline;background:none}.next-action-label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}.focus-item.is-single .step-title{font-size:15px;font-weight:600}.focus-item:not(.is-single)>.next-steps .step-title{font-size:13px}.focus-fraction{font-size:10px;color:var(--muted);white-space:nowrap}.focus-context progress{width:52px;flex:none}
.next-steps{display:grid;gap:10px}.step-line{display:flex;align-items:flex-start;gap:10px;min-width:0}.step-title{flex:1;min-width:0;text-align:left;padding:0;border:0;background:none;font-size:14px;font-weight:500;line-height:1.6;overflow-wrap:anywhere}.step-title:hover{background:none;text-decoration:underline}.step-title.done{text-decoration:line-through;color:var(--muted)}.next-steps{min-height:24px}.step-line .check{margin-top:4px;width:17px;height:17px}.step-state{font-size:10px;color:var(--muted);white-space:nowrap;padding-top:4px}.steps-finished{font-size:12px;color:var(--muted)}
.focus-details{margin-top:14px;border-top:1px solid #dce2d1;padding-top:10px}.focus-details>summary,.completed-steps>summary{cursor:pointer;font-size:11px;color:var(--muted);list-style:none}.focus-details>summary::after{content:' ＋';float:right}.focus-details[open]>summary::after{content:' −'}.focus-details summary::-webkit-details-marker{display:none}.plan-info{margin-top:12px}.plan-info p{font-size:12px;color:var(--muted);margin-top:10px;white-space:pre-wrap;overflow-wrap:anywhere;max-width:65ch}.focus-meta{display:flex;align-items:center;gap:10px;flex-wrap:wrap;font-size:10px;color:var(--muted)}.focus-details .card-actions{margin-top:12px;padding-top:10px;gap:8px}.focus-details .step-title{font-size:12px}.remaining-steps{display:grid;gap:10px;margin-top:14px}.completed-steps{margin-top:14px}.completed-steps .step-line{margin-top:10px}
.plan-notes{margin:10px 0 0}.plan-step{padding:12px 0;border-bottom:1px solid var(--line)}.plan-step:last-child{border-bottom:0}.step-notes,.step-children{margin:6px 0 0 27px;font-size:11px;color:var(--muted)}.step-notes summary,.step-children summary{cursor:pointer}.step-notes p{margin:8px 0;white-space:pre-wrap;overflow-wrap:anywhere}.step-children .plan-step{padding:10px 0}.all-plans>.plan-step{padding:14px 0}
.panel-foot{margin-top:20px;font-size:11px;color:var(--muted)}.all-plans{margin-top:18px}.all-plans>summary{font-size:12px;cursor:pointer;color:var(--green)}.all-plans .task{padding:12px 0}.quiet-empty{display:flex;flex-direction:column;align-items:flex-start;justify-content:center;min-height:222px;gap:12px;color:var(--muted)}.quiet-empty strong{font-size:17px;font-weight:500;color:var(--ink)}.quiet-empty p{font-size:12px;max-width:260px}.quiet-empty .chat-entry{margin-top:0}
.direction-panel{background:linear-gradient(135deg,#f1f3e9,#f8f8f1)}.goal-item{width:100%;text-align:left;padding:12px 6px;border:0;border-bottom:1px solid #dce2d1;border-radius:0;background:transparent;display:flex;align-items:center;gap:16px}.goal-item:hover{background:#e7ecdf}.goal-title{overflow-wrap:anywhere;min-width:0}.direction-more{margin-top:14px}.direction-more>summary{cursor:pointer;color:var(--muted);font-size:11px}.goal-item:last-of-type{border-bottom:0}.goal-symbol{width:48px;height:48px;display:grid;place-items:center;border-radius:50%;background:#e1e9d2;color:#496641;font-size:24px;flex:none}.goal-item:nth-child(3) .goal-symbol{background:#eee4d4;color:#886d49}.goal-item:nth-child(4) .goal-symbol{background:#dce7e6;color:#4b706d}.goal-title{font-weight:500;font-size:17px;line-height:1.4}.goal-note{font-size:11px;color:var(--muted);margin-top:5px}.direction-caption{font-size:11px;color:var(--muted);margin-top:22px}
.backlog-panel{grid-column:1/-1}.bubble-field{position:relative;min-height:280px;background:radial-gradient(ellipse at center,#edf1e67a,transparent 72%);isolation:isolate}.task-bubble{--bubble-size:148px;--bubble-ink:#45623e;--bubble-fill:#e5eddc;position:absolute;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;flex:0 0 auto;width:var(--bubble-size);height:var(--bubble-size);padding:22px;border-radius:50%;border:1px solid #ffffffb3;color:var(--bubble-ink);background:var(--bubble-fill);box-shadow:0 4px 12px #30452d08;transition:box-shadow .2s;overflow:hidden;cursor:grab;touch-action:none;user-select:none;-webkit-user-select:none}.task-bubble.very_high{--bubble-size:210px;--bubble-ink:#78532f;--bubble-fill:#eedcc1}.task-bubble.high{--bubble-size:180px;--bubble-ink:#6c642b;--bubble-fill:#e8e4bd}.task-bubble.medium{--bubble-size:152px;--bubble-fill:#dfe9d2}.task-bubble.low{--bubble-size:130px;--bubble-ink:#506d67;--bubble-fill:#dfebe5}.task-bubble.very_low{--bubble-size:112px;--bubble-ink:#63716c;--bubble-fill:#e9eeea}.task-bubble.unassessed{--bubble-size:130px;--bubble-ink:#69716b;--bubble-fill:#eef0e9;border:1px dashed #a5afa1}.task-bubble:hover{background:var(--bubble-fill);border-color:#ffffff;box-shadow:0 6px 16px #30452d12}.task-bubble.is-dragging{cursor:grabbing;z-index:3;box-shadow:0 10px 22px #30452d20}.task-bubble[aria-expanded="true"]{outline:2px solid var(--bubble-ink);outline-offset:5px}.bubble-title{font-size:15px;font-weight:550;line-height:1.4;text-align:center;overflow-wrap:anywhere;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;max-width:100%}.task-bubble.very_high .bubble-title{font-size:21px}.task-bubble.high .bubble-title{font-size:18px}.task-bubble.very_low .bubble-title{font-size:12px}.bubble-hint{font-size:11px;color:var(--muted)}.bubble-detail{max-width:720px;margin:12px auto 0;padding:22px;background:#f5f7ef;border:1px solid var(--line);border-radius:16px;scroll-margin:24px}.bubble-detail h3{font-size:18px;overflow-wrap:anywhere}.bubble-detail .focus-meta{margin-top:10px}.bubble-close{width:28px;height:28px;padding:0;border-radius:50%;flex:none}.backlog-details{display:grid;gap:12px;margin-top:20px}.backlog-details .step-title{font-size:13px}.backlog-details .card-actions{gap:8px;margin-top:4px}.bubble-detail .next-label{font-size:10px;text-transform:uppercase;letter-spacing:1px;color:var(--muted)}
@media(max-width:900px){.overview-grid{gap:16px}.overview-panel{padding:20px}.canvas{max-width:100%}}
@media(max-width:650px){.overview-grid{grid-template-columns:1fr}.backlog-panel{grid-column:auto}.overview-toolbar{align-items:flex-start;gap:8px;flex-wrap:wrap}.panel-top{flex-wrap:wrap}.goal-title{font-size:16px}.bubble-field{min-height:280px}.task-bubble{width:calc(var(--bubble-size)*.82);height:calc(var(--bubble-size)*.82);padding:16px}.task-bubble.very_high .bubble-title{font-size:17px}.task-bubble.high .bubble-title{font-size:15px}.bubble-title{font-size:12px}.task-bubble.very_low .bubble-title{font-size:11px}.bubble-detail{padding:18px}}

.handoff-fields{margin-top:12px;padding:12px;border:1px solid var(--line);border-radius:10px}.handoff-fields .field:last-child{margin-bottom:0}.handoff-fields textarea{min-height:55px;font-size:12px}.handoff-details{font-size:11px;color:var(--muted);max-width:56ch}.handoff-details summary{cursor:pointer}.handoff-details p{margin:7px 0;white-space:pre-wrap;overflow-wrap:anywhere}.step-line.is-saving::after{content:"Saving…";font-size:10px;color:var(--muted);padding-top:4px;white-space:nowrap}.agent-actions{flex-wrap:wrap;align-items:center;display:flex;gap:8px;margin-top:8px}.agent-actions button{font-size:11px;padding:6px 10px}.card-actions .agent-actions{margin:0 auto 0 0}
/* Give immediate completion feedback while the save runs. */
.step-line.is-saving .step-title:disabled,.step-line.is-finishing .step-title:disabled{opacity:1}
.is-finishing .step-title{text-decoration:line-through;color:var(--green)}

/* Quiet workspace: readable tasks, one action per row, details on demand. */
:root{--paper:#f7f8fa;--panel:#ffffff;--ink:#242b3b;--muted:#626b7d;--line:#e3e6ed;--green:#435ac6;--soft:#edf0fa;--accent:#e4e9fc;--red:#a83d3d;font-family:"Segoe UI",ui-sans-serif,system-ui,-apple-system,sans-serif}
body{background:var(--paper);font-size:15px;-webkit-font-smoothing:antialiased}
button{font-size:14px;font-weight:500;min-height:40px;border-radius:9px;padding:9px 14px}
button:hover{border-color:#b9c3e0;background:#f0f3fb}.primary:hover{background:#354ab0}
.small{font-size:14px;padding:8px 12px}.muted{font-size:14px}label{font-size:14px}
.topbar{height:76px;padding:0 max(24px,calc((100vw - 1280px)/2));background:var(--panel);border-bottom:1px solid var(--line)}
.brand-mark{width:32px;height:32px;border-radius:10px;background:var(--ink);color:#fff;display:grid;place-items:center;font-size:22px;transform:none}
.brand{font-size:16px;letter-spacing:-.5px}.topbar nav{gap:12px}.topbar a{font-size:14px}
.workspace-menu{position:relative;font-size:14px}.workspace-menu>summary{cursor:pointer;list-style:none;padding:10px 12px;border-radius:8px}.workspace-menu>summary::-webkit-details-marker{display:none}.workspace-menu>summary:hover{background:var(--paper)}
.workspace-menu-items{position:absolute;right:0;top:44px;z-index:25;width:180px;padding:8px;background:var(--panel);border:1px solid var(--line);border-radius:12px;box-shadow:0 10px 32px #242b3b14;display:grid;gap:4px}.workspace-menu-items>*{text-align:left;margin:0;text-decoration:none;padding:10px 12px;border:0;border-radius:6px}.workspace-menu-items a:hover{background:var(--soft)}
main{max-width:1360px;padding:42px 40px 110px;margin:auto}.intro{margin-bottom:32px;align-items:center;gap:20px}
.intro h1.eyebrow{font:500 clamp(30px,3vw,40px)/1.15 "Segoe UI",sans-serif;letter-spacing:-1.4px;text-transform:none;color:var(--ink);margin:0 0 10px}
.workspace-date{font-size:14px;color:var(--muted)}.overview-toolbar{gap:12px}.overview-toolbar button{font-size:14px}
.overview-grid{grid-template-columns:minmax(0,1.2fr) minmax(0,1fr);gap:24px;align-items:start}
.overview-panel{border-radius:16px;border:1px solid var(--line);padding:26px 28px;background:var(--panel);box-shadow:none;min-width:0}
.panel-top{margin-bottom:24px;gap:16px}.panel-top h2{font-size:19px;font-weight:600;letter-spacing:-.5px;text-transform:none;line-height:1.3}
.section-count{min-width:26px;height:26px;padding:2px 7px;display:grid;place-items:center;background:#f0f2f6;color:var(--muted);border-radius:7px;font-size:13px}
.focus-list{gap:0}.focus-item,.focus-item:first-child{background:none;border:0;border-top:1px solid var(--line);border-radius:0;padding:22px 0;min-width:0}.focus-item:first-child{padding-top:0;border-top:0}.focus-item:last-child{padding-bottom:0}
.focus-context{display:flex;align-items:flex-start;gap:12px;margin-bottom:14px;min-width:0;flex-wrap:nowrap}
.focus-rank{font-size:13px;line-height:26px;flex:none;width:26px;text-align:center;background:#f0f2f6;color:var(--muted);border-radius:50%;padding:0}
.focus-plan{flex:1;min-width:0;font-size:21px;font-weight:600;letter-spacing:-.5px;line-height:1.3;margin:0}
.task-deadline{display:block;font-size:13px;font-weight:400;letter-spacing:0;line-height:1.5;color:var(--muted);margin-top:5px}.focus-fraction{font-size:13px;color:var(--muted);white-space:nowrap;line-height:26px;padding:0}
.next-steps{margin-left:38px;gap:12px}.step-line{display:flex;align-items:flex-start;gap:12px;min-width:0;flex-wrap:wrap}
.step-title,.focus-item:not(.is-single)>.next-steps .step-title,.focus-details .step-title,.backlog-details .step-title{flex:1;min-width:0;font-size:15px;font-weight:400;line-height:1.5;letter-spacing:0;overflow-wrap:anywhere}
.focus-item.is-single .next-steps{margin-left:0}.focus-item.is-single .focus-context{display:none}.focus-item.is-single .step-title{font-size:21px;font-weight:600;letter-spacing:-.5px;line-height:1.3}
.step-line>.agent-actions{margin:0 0 0 auto;flex:none;align-self:flex-start}.agent-actions{gap:8px;margin-top:12px}.agent-actions button{font-size:13px;min-height:34px;padding:6px 10px;border:1px solid #dce2f3;background:#f5f7fd;color:#3e50a4;white-space:nowrap;border-radius:7px}.agent-actions button:hover{background:var(--soft);border-color:#aebae4}
.focus-context>.agent-actions,.bubble-detail .row>.agent-actions{margin:0 0 0 auto;flex:none}
.check,.step-line .check{width:20px;height:20px;flex:none;margin:2px 0 0}
input.check{appearance:none;-webkit-appearance:none;display:grid;place-content:center;border:1.5px solid #9aa3b4;border-radius:6px;background:transparent;padding:0;position:relative;cursor:pointer}
input.check:checked{color:var(--green);border-color:var(--green);background:var(--soft)}input.check:checked::after{content:'✓';font-size:14px;font-weight:600;line-height:1}input.check:focus-visible{outline:2px solid var(--green);outline-offset:3px}input.check:disabled{cursor:wait}
.focus-details{margin:12px 0 0 38px;padding:0;border:0}.focus-details>summary{display:flex;align-items:center;justify-content:space-between;min-height:36px;padding:6px 0;font-size:14px;color:var(--muted);cursor:pointer;list-style:none}.focus-details>summary::after{display:none}.focus-details[open]>summary{color:var(--green)}
.focus-item.is-single .focus-details{margin-left:32px}.focus-meta{font-size:13px;gap:12px}.pill{font-size:13px;padding:4px 8px}.plan-info{margin-top:12px}.plan-info p,.step-notes,.step-children{font-size:14px}.remaining-steps{gap:14px;margin-top:16px}.completed-steps>summary{font-size:14px;min-height:36px;padding-block:8px}.completed-steps .step-line{margin-top:12px}.card-actions{gap:10px}.steps-finished,.step-state{font-size:14px}
.direction-panel{background:#f0f2fa;border-color:#e0e4f2;overflow:visible}.direction-panel::after{display:none}.goal-list{display:grid}.goal-item,.goal-item:last-of-type{display:flex;align-items:center;gap:14px;width:100%;border:0;border-bottom:1px solid #dce1ef;border-radius:0;padding:21px 0;background:none;text-align:left;min-height:78px}.goal-item:last-of-type{border-bottom:0}.goal-item:hover{background:#e8ecf8}.goal-symbol,.goal-item:nth-child(n) .goal-symbol{width:36px;height:36px;font-size:20px;border:1px solid #d9dff0;background:#e5e9f6;border-radius:11px;color:#465ba4;flex:none}.goal-title{font:500 19px/1.4 "Segoe UI",sans-serif;letter-spacing:-.35px;overflow-wrap:anywhere}.goal-arrow{margin-left:auto;color:#7380a0;font-size:20px}.direction-more{margin-top:12px}.direction-more>summary,.workspace-overview>summary{font-size:14px;color:#526085;cursor:pointer;min-height:40px;padding-block:10px}.workspace-overview{margin-top:20px;border-top:1px solid #dce1ef;padding-top:8px}.workspace-summary{display:grid;gap:12px;padding:12px 0 0}.summary-lead{font-size:22px;line-height:1.3;letter-spacing:-.5px}.summary-context{font-size:15px;line-height:1.6}.summary-context button{font:inherit;min-height:0;padding:0;border:0;background:none;text-decoration:underline;text-align:left}.summary-progress{font-size:14px;color:var(--muted);line-height:1.6;border:0;padding:0}.direction-empty{font-size:15px;color:var(--muted);padding:16px 0;line-height:1.7}
.backlog-panel{grid-column:1/-1;border:0;border-top:1px solid var(--line);border-radius:0;padding:28px 0 0;background:transparent;box-shadow:none;margin-top:8px}.backlog-panel .panel-top{margin-bottom:10px}.bubble-hint{font-size:14px;color:var(--muted)}.bubble-field{background:none;min-height:250px}
.task-bubble{border:1px solid #242b3b0d;box-shadow:none;padding:20px}.task-bubble.very_high{--bubble-size:210px;--bubble-fill:#f0d5c6;--bubble-ink:#624333}.task-bubble.high{--bubble-size:186px;--bubble-fill:#eae3bf;--bubble-ink:#5f532e}.task-bubble.medium{--bubble-size:166px;--bubble-fill:#dce5d6;--bubble-ink:#40573e}.task-bubble.low{--bubble-size:148px;--bubble-fill:#d8e5ec;--bubble-ink:#3c596a}.task-bubble.very_low{--bubble-size:132px;--bubble-fill:#e3dfed;--bubble-ink:#574b6e}.task-bubble.unassessed{--bubble-size:148px;--bubble-fill:#e7e9ef;--bubble-ink:#535e74}
.bubble-title{font-size:18px;font-weight:500;letter-spacing:-.35px;line-height:1.35}.task-bubble.very_high .bubble-title{font-size:23px}.task-bubble.high .bubble-title{font-size:20px}.task-bubble.very_low .bubble-title{font-size:16px}.task-bubble:hover{border-color:var(--bubble-ink);box-shadow:0 5px 18px #242b3b0d}.task-bubble.is-dragging{box-shadow:0 8px 24px #242b3b16}
.bubble-detail{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:24px;margin-top:24px}.bubble-detail h3{font-size:23px;letter-spacing:-.5px}.bubble-detail .next-label{font-size:14px;text-transform:none;letter-spacing:0}.bubble-close{width:36px;min-height:36px;font-size:21px;border-radius:8px}.all-plans>summary{font-size:14px;padding-block:12px}
input.task-name{font:inherit;color:inherit;letter-spacing:inherit;line-height:inherit;width:100%;min-width:0;border:1px solid transparent;border-radius:5px;background:transparent;padding:2px 3px;margin:-3px -4px;box-shadow:none}input.task-name:hover{border-color:var(--line);background:var(--paper);text-decoration:none}input.task-name:focus{border-color:var(--green);outline:2px solid var(--accent);background:var(--panel)}input.task-name.step-title{width:0;flex:1}
.quiet-empty{min-height:180px;gap:12px}.quiet-empty strong{font-size:24px;font-weight:500;letter-spacing:-.5px}.chat-entry{font-size:15px;min-height:40px}.quiet-empty .chat-entry{margin:0}
.chat{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:24px;box-shadow:0 16px 60px #242b3b24;bottom:100px}.chat h2{font-size:18px}.chat-head p{font-size:14px}.chat-welcome h3{font-size:25px;line-height:1.3;letter-spacing:-.6px}.chat-message{font-size:15px}.chat-message small{font-size:12px;letter-spacing:.3px}.chat-close{min-height:36px;width:36px}.composer textarea{font-size:15px}.composer #voice,.composer #send{width:40px;height:40px}.voice-note,.voice-note .voice-status,.voice-status{font-size:13px;line-height:1.6}.voice-note summary{min-height:36px;padding-top:8px}.muse-mark{font-size:22px;color:var(--green);background:var(--soft);border:0}
.muse-launcher{display:flex;gap:10px;width:auto;height:50px;min-height:50px;border-radius:14px;padding:0 20px;background:var(--ink);color:#fff;border:0;box-shadow:0 4px 16px #242b3b20;right:28px;bottom:24px}.muse-launcher svg{width:22px;height:22px;filter:none}.muse-launcher:hover{background:#39445d;color:#fff;transform:translateY(-2px)}.muse-launcher[aria-expanded="true"]{box-shadow:0 0 0 4px var(--accent)}.launcher-caption,.muse-launcher[aria-expanded="true"] .launcher-caption{display:inline;position:static;background:none;color:inherit;border:0;border-radius:0;padding:0;box-shadow:none;font-size:15px}
dialog{border:1px solid var(--line);border-radius:16px;padding:28px}.handoff-fields,.handoff-details{font-size:14px}.handoff-fields textarea{font-size:14px}.error{font-size:14px}.notice{font-size:14px}.notice:empty{display:none}
@media(max-width:1050px){.overview-grid{grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:18px}.overview-panel{padding:22px}.focus-context{flex-wrap:wrap}.focus-plan{flex-basis:calc(100% - 42px)}.focus-fraction{margin-left:38px;line-height:18px}.goal-title{font-size:18px}}
@media(max-width:700px){.topbar{height:66px;padding-inline:20px}.brand{font-size:14px}.topbar .row{gap:10px}main{padding:30px 20px 110px}.intro{align-items:flex-start;gap:16px}.intro h1.eyebrow{font-size:32px}.overview-toolbar{flex-wrap:wrap;gap:8px}.overview-grid{grid-template-columns:1fr}.overview-panel{padding:22px}.backlog-panel{padding:24px 0 0}.focus-context{flex-wrap:nowrap}.focus-plan{font-size:20px;flex-basis:auto}.focus-fraction{margin-left:0;line-height:26px}.goal-title{font-size:19px}.bubble-hint{font-size:13px;max-width:130px;text-align:right}.backlog-panel h2{max-width:190px}.task-bubble{padding:14px}.bubble-title{font-size:16px}.task-bubble.very_high .bubble-title{font-size:20px}.task-bubble.high .bubble-title{font-size:18px}.task-bubble.very_low .bubble-title{font-size:14px}.chat{right:16px;max-width:calc(100vw - 32px)}.muse-launcher{right:20px}.step-line>.agent-actions{margin-left:32px}.focus-details{margin-left:38px}.direction-panel{min-height:0}}
@media(max-width:420px){.intro{display:block}.overview-toolbar{margin-top:18px}.focus-plan{font-size:18px}.focus-fraction{font-size:12px}.focus-rank{width:23px;line-height:23px}.next-steps,.focus-details{margin-left:0}.focus-context{gap:9px}.step-line>.agent-actions{margin-left:32px}.panel-top h2{font-size:18px}.brand{font-size:13px}}

/* Task conversations and a single ordered subtask disclosure. */
.intro h1.eyebrow .workspace-date{font:inherit;color:var(--ink)}
.focus-context{align-items:flex-start}.focus-fraction{white-space:normal;text-align:right;max-width:120px;line-height:1.4}
.focus-details,.focus-item.is-single .focus-details{margin:14px 0 0 38px}.focus-details>summary{justify-content:flex-start;gap:10px;color:var(--ink)}
.focus-details>summary::before{content:'+';display:grid;place-items:center;width:22px;height:22px;border:1px solid var(--line);border-radius:5px;font-size:16px;color:var(--muted)}
.focus-details[open]>summary::before{content:'−'}.plan-subtasks{display:grid;gap:0;margin-top:12px}.plan-subtasks .step-line{padding:12px 0;border-bottom:1px solid var(--line)}.plan-subtasks .step-line:last-child{border-bottom:0}.step-title.done{text-decoration:line-through;color:var(--muted)}.plan-description{font-size:14px;line-height:1.6;color:var(--muted);margin-top:14px;white-space:pre-wrap}
.focus-item>.card-actions{margin:14px 0 0 38px}.goal-item{padding:22px 0}.goal-title{flex:1}.bubble-detail{max-height:calc(100dvh - 48px);overflow:auto;overscroll-behavior:auto;scroll-margin-top:24px;overflow-anchor:none}.bubble-detail .focus-details{margin-left:0}.bubble-detail>button[data-task-chat]{margin-top:16px}.detail-progress{font-size:14px;color:var(--muted);margin-top:12px}
#chat-scope{margin-top:8px;font-size:14px;padding:8px;background:var(--paper);border-color:var(--line)}.chat-head-copy{min-width:0}.chat-head{align-items:flex-start}.chat-close{flex:none}.history{max-height:34vh}.composer #send{width:auto;min-width:64px;font-size:14px;border-radius:9px}
@media(max-width:700px){.focus-context{flex-wrap:wrap}.focus-plan{flex-basis:calc(100% - 40px)}.focus-fraction{margin-left:38px;text-align:left;max-width:none}.bubble-detail{padding:20px}.bubble-detail .focus-details{margin-left:0}}
@media(max-width:420px){.focus-details,.focus-item.is-single .focus-details{margin-left:0}.focus-item>button[data-task-chat]{margin-left:0}}

/* Let wheel/touch scrolling continue through nested text surfaces at their edges. */
.chat,.history,.bubble-detail,textarea{overscroll-behavior:auto}
.section-count{white-space:nowrap;min-width:64px}
.step-label{display:flex;flex-direction:column;flex:1;min-width:0;gap:5px}
.step-label input.task-name.step-title{width:100%;flex:none}
.step-label .task-deadline{margin:0;font-size:13px}.task-bubble .task-deadline{color:inherit;font-size:13px;font-weight:400;letter-spacing:0;margin:0}
.bubble-detail .plan-description{overflow-wrap:anywhere}
/* Compact direction, visible deadlines, and consistent task actions. */
.direction-panel{align-self:start;padding-block:22px}
.goal-list{max-height:none;overflow-y:auto;overscroll-behavior:auto;align-content:start}
.goal-item,.goal-item:last-of-type{display:block;min-height:0;padding:0;border-bottom:1px solid #dce1ef}
.goal-item:last-child{border-bottom:0}.goal-item:hover{background:none}
.goal-item>summary{list-style:none;cursor:pointer;padding:13px 4px;min-height:48px;font-size:17px;line-height:1.35}
.goal-item>summary::-webkit-details-marker,.past-task>summary::-webkit-details-marker{display:none}
.goal-item>summary:hover{color:var(--green);background:#e8ecf8;border-radius:6px}
.goal-item[open]>summary{color:var(--green)}.goal-subtasks{padding:0 4px 14px}.goal-subtasks .plan-description{margin:0 0 12px;line-height:1.6;font-size:14px}
.goal-subtasks .card-actions{flex-wrap:wrap;margin-top:12px;padding-top:12px}
.card-actions{display:flex;flex-wrap:wrap;align-items:center;justify-content:flex-end;gap:8px}.card-actions .agent-actions{margin:0 auto 0 0}
.task-deadline,.step-label .task-deadline,.task-bubble .task-deadline{display:table;width:fit-content;padding:4px 8px;border-radius:6px;background:#e5f3e9;color:#27613b;font-size:13px;font-weight:600;line-height:1.4;margin-top:8px}
.task-deadline[data-urgency="approaching"]{background:#fbf2cd;color:#766013}
.task-deadline[data-urgency="soon"]{background:#ffead8;color:#93470d}
.task-deadline[data-urgency="urgent"]{background:#fce6e5;color:#a32c2c}
.task-deadline[data-urgency="overdue"]{background:#f9d9d9;color:#922525}
.task-bubble .task-deadline{font-size:12px;font-weight:600;letter-spacing:0;margin:0;padding:3px 7px}
.bubble-detail>.plan-subtasks{margin-top:18px}.bubble-detail>.plan-description{margin-top:16px}.bubble-detail>.small{margin-top:14px}
.past-panel{grid-column:1/-1;padding:24px 0 0;border:0;border-top:1px solid var(--line);background:none;scroll-margin-top:24px}
.past-task{padding:16px 0;border-top:1px solid var(--line)}.past-task>summary{list-style:none;cursor:pointer;display:flex;align-items:center;justify-content:space-between;gap:16px;font-size:16px}.past-state{font-size:13px;color:var(--muted);white-space:nowrap}.past-task .plan-subtasks{margin-top:18px}.past-task>.plan-description{margin-top:14px}.past-task>.small{margin-top:14px}
.workspace-menu>summary,.voice-note>summary{display:flex;align-items:center;gap:8px}
.voice-note>summary{padding-block:8px;color:var(--muted)}
.topbar>nav{gap:12px}
.chat-close{display:grid;place-items:center;border-radius:9px;background:var(--paper);color:var(--muted)}.chat-close:hover{background:var(--soft);color:var(--green)}
@media(max-width:700px){.topbar{height:auto;min-height:66px;flex-wrap:wrap;gap:8px;padding-block:12px}.topbar>nav{margin-left:auto;gap:8px}.direction-panel{padding:22px}.goal-item>summary{font-size:17px}.past-task>summary{align-items:flex-start}.past-state{font-size:12px;white-space:normal;max-width:115px;text-align:right}}
/* Direct task creation and inline task content. */
.section-actions{display:flex;align-items:center;gap:10px;flex:none}.section-actions .add-task{font-size:13px;white-space:nowrap}.section-actions .section-count{min-width:0}.panel-top{gap:12px}
.inline-description{display:block;box-sizing:border-box;width:100%;min-height:58px;max-height:220px;field-sizing:content;font:inherit;font-size:14px;line-height:1.6;color:var(--muted);padding:8px;border:1px solid transparent;border-radius:6px;background:transparent;resize:vertical;margin-top:10px}.inline-description:hover{border-color:var(--line)}.inline-description:focus{border-color:var(--green);background:var(--panel);outline:2px solid var(--soft)}
.goal-title input.task-name{font:inherit;font-size:17px;width:100%;margin:0}.goal-subtasks .inline-description{margin:0 0 10px}.goal-subtasks>.small{margin-left:8px}.goal-subtasks .inline-date{margin-bottom:8px}
.inline-date{position:relative;display:table;width:fit-content;cursor:pointer;margin-top:8px;font-size:13px;font-weight:400}.inline-date .task-deadline{margin:0}.inline-date input{position:absolute;inset:0;opacity:0;width:100%;height:100%;padding:0;cursor:pointer}.inline-date:focus-within input{position:static;opacity:1;width:154px;height:32px;padding:4px 6px;border:1px solid var(--green);border-radius:6px;background:var(--panel)}.inline-date:focus-within .task-deadline{display:none}.task-deadline.is-empty{background:transparent;color:var(--muted);font-weight:400;border:1px dashed var(--line)}
.step-label .inline-description{font-size:13px;margin-top:0;min-height:44px}.step-label .inline-description:placeholder-shown,.step-label .inline-date:has(.is-empty){display:none}.step-label:focus-within .inline-description,.step-label:focus-within .inline-date{display:block}.step-label .inline-date{margin-top:0}
.past-task-heading{display:flex;align-items:center;gap:16px}.past-task-heading h3{font-size:16px;font-weight:500;margin:0;flex:1;overflow-wrap:anywhere}.past-task-heading>button{flex:none}.past-task-heading .past-state{margin-left:auto}
#add-dialog{width:min(500px,calc(100vw - 32px))}.bubble-detail>.inline-description{margin-top:14px}
@media(max-width:700px){.panel-top{flex-wrap:wrap}.section-actions{margin-left:auto;gap:6px}.past-task-heading{flex-wrap:wrap;gap:10px}.past-task-heading h3{flex-basis:55%}.past-task-heading .past-state{margin:0}.past-task-heading>button{margin-left:auto}}
/* A separate subtask control keeps title editing predictable. */
.goal-heading{display:flex;align-items:center;gap:12px;padding:10px 4px;min-height:52px}.goal-heading>input.task-name{font:500 17px/1.4 "Segoe UI",sans-serif;flex:1;min-width:0;width:100%;margin:0}.subtasks-toggle{display:grid;place-items:center;width:36px;height:36px;padding:0;border:0;border-radius:8px;flex:none;background:transparent;color:var(--muted)}.subtasks-toggle:hover{background:#e2e7f7;color:var(--green)}.subtasks-toggle[aria-expanded="true"] .disclosure-chevron{transform:rotate(180deg)}
.manual-subtasks{display:grid;gap:8px;margin:10px 0}.manual-subtask{display:flex;align-items:center;gap:8px}.manual-subtask input{min-width:0;flex:1}.manual-step-number{color:var(--muted);font-size:13px;width:20px;text-align:center;flex:none}.manual-subtask>button{width:32px;height:32px;padding:0;flex:none}
.past-groups{display:grid;grid-template-columns:1fr 1fr;gap:28px}.past-group-heading{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:0 0 12px}.past-group-heading h3{font-size:16px;font-weight:600}.past-task-heading h4{font-size:15px;font-weight:500;margin:0;flex:1;overflow-wrap:anywhere}.past-group .past-state{font-size:12px}.past-group>.muted{font-size:14px;padding:12px 0}
@media(max-width:850px){.past-groups{grid-template-columns:1fr}.past-task-heading{flex-wrap:wrap}}

/* Keep the header, composer, and disclosure in view; only messages scroll. */
.chat{display:flex;flex-direction:column;height:min(760px,calc(100dvh - 128px));max-height:calc(100dvh - 128px);overflow:hidden;padding:18px;gap:10px}
.chat-head{flex:none;margin:0;padding-bottom:12px}.chat-head-copy{overflow:hidden}#chat-scope{width:100%;text-overflow:ellipsis}#chat-scope:focus{outline:none;box-shadow:none}#chat-scope:focus-visible{border-color:var(--muted)}
.history{flex:1 1 0;min-height:0;max-height:none;overflow-y:auto}.chat-message{margin-bottom:8px;padding-block:10px;line-height:1.5}.chat-welcome{flex:none;padding:4px 2px}.chat-welcome h3{font-size:21px}
.composer{flex:none;padding:12px;border-radius:12px}.composer textarea{height:56px;min-height:40px;max-height:90px}.composer>.row{margin-top:6px;padding-top:6px}
.chat>.status:empty,.chat>.voice-status:empty{display:none}.chat>.status,.chat>.voice-status{flex:none;font-size:12px;margin:0}.voice-note{flex:none;margin:0;font-size:12px;line-height:1.4}.voice-note summary{min-height:24px;padding:2px 0}.voice-note p{font-size:12px;line-height:1.4;margin-top:6px}.voice-note .voice-status{font-size:12px;line-height:1.4}
.step-actions{display:flex;align-items:flex-start;gap:8px;flex-wrap:wrap;justify-content:flex-end}.step-actions .agent-actions{margin:0}.step-actions>button{font-size:12px;min-height:34px;white-space:nowrap}.step-label .inline-description:placeholder-shown{display:block}.step-label [hidden]{display:none}.step-label .inline-description{margin-top:8px}
.goal-subtasks>[data-task-chat]{margin-top:12px}.goal-subtasks>.inline-date{margin:0 0 12px}
@media(max-height:600px){.chat{bottom:82px;height:calc(100dvh - 94px);max-height:calc(100dvh - 94px);padding:12px;gap:6px}.chat-head{padding-bottom:6px}.chat-head h2{font-size:16px}#chat-scope{margin-top:4px;padding:5px}.composer textarea{height:40px}.chat-welcome{display:none}.voice-note p{max-height:52px;overflow:auto}}
@media(max-width:700px){.step-actions{margin-left:32px}.step-line{flex-wrap:wrap}.step-label{flex-basis:calc(100% - 44px)}.chat{right:12px;max-width:calc(100vw - 24px)}}
.add-subtask{margin-top:12px}.goal-subtasks .plan-subtasks{margin-top:0}.plan-subtasks .step-title,.focus-details .step-title,.backlog-details .step-title{font:500 14px/1.6 "Segoe UI",sans-serif}
.card-actions .ask-muse{background:#f5f7fd;color:#3e50a4;border:1px solid #dce2f3}.step-line>.agent-actions{margin:0 0 0 auto;flex:none}.focus-item>.card-actions{padding-top:12px;border-top:1px solid var(--line)}

.chat{width:min(580px,calc(100vw - 32px));max-width:calc(100vw - 32px);height:min(820px,calc(100dvh - 112px));max-height:calc(100dvh - 112px)}
.composer textarea{height:48px;min-height:48px;max-height:120px;font-size:16px;line-height:1.5;resize:vertical}.chat-head-copy{min-width:0}.chat-head h2{overflow-wrap:anywhere}.chat-context{font-size:13px;color:var(--muted);margin-top:5px}#chat-scope{display:none}#task-chat-dialog{width:min(1120px,calc(100vw - 32px));max-width:calc(100vw - 32px);height:min(900px,92dvh);max-height:92dvh;padding:0;overflow:hidden}#task-chat-host{height:100%}.chat.is-task-chat{position:static;inset:auto;width:100%;max-width:none;height:100%;max-height:none;border:0;border-radius:0;box-shadow:none;padding:24px;transform:none}.is-task-chat .history{padding:14px 20px}.is-task-chat .composer textarea{height:56px;min-height:48px;max-height:140px}.is-task-chat .chat-head h2{font-size:21px}.chat>#chat-error{flex:none;font-size:13px;line-height:1.5;margin:0}.chat-sources{display:flex;flex-wrap:wrap;gap:8px 16px;margin-top:12px;font-size:13px}.chat-sources a{color:#3e50a4}.chat-message a{overflow-wrap:anywhere}.chat-message code{white-space:pre-wrap}
.trash-task{display:inline-grid;place-items:center;width:28px;height:28px;min-height:28px;padding:4px;border:0;background:transparent;color:#8b8f99;border-radius:6px;flex:none}.trash-task svg{width:17px;height:17px}.trash-task:hover{color:#b34141;background:#fbefef}.focus-context{display:grid;grid-template-columns:28px minmax(0,1fr) auto;column-gap:12px;row-gap:8px}.rank-actions{display:flex;flex-direction:column;align-items:center;gap:8px;grid-row:1/span 2}.rank-actions .focus-rank{margin:0}.task-deadline-row{display:flex;align-items:center;justify-content:space-between;gap:12px;width:100%;margin-top:8px}.task-deadline-row .inline-date{margin:0}.task-deadline-row .handoff-whole{margin-left:auto;font-size:12px;min-height:32px;white-space:nowrap;background:#f5f7fd;color:#3e50a4;border:1px solid #dce2f3}.focus-context>.task-deadline-row{grid-column:2/-1;margin-top:0}.goal-heading .trash-task{margin-left:auto}.goal-heading .subtasks-toggle{margin-left:0}.step-line>.trash-task{margin:0 0 0 -4px}.step-line>.check{margin-top:5px}#trash-undo{display:flex;align-items:center;justify-content:space-between;gap:16px;position:fixed;bottom:24px;left:24px;z-index:40;background:var(--ink);color:white;padding:12px 16px;border-radius:12px;box-shadow:0 8px 30px #0002;max-width:calc(100vw - 48px)}#trash-undo[hidden]{display:none}#trash-undo button{color:white;border-color:#ffffff50;background:transparent}#trash-undo .undo-error{color:#ffc6c6}.focus-plan{min-width:0}.goal-subtasks>.task-deadline-row{margin:0 0 16px}
@media(max-height:600px){.chat{height:calc(100dvh - 94px);max-height:calc(100dvh - 94px)}.composer textarea{height:48px;min-height:40px;max-height:90px}.chat.is-task-chat{height:100%;max-height:none}.is-task-chat .composer textarea{height:48px;min-height:40px;max-height:90px}}
@media(max-width:700px){.chat{right:12px;width:calc(100vw - 24px);max-width:calc(100vw - 24px)}.chat.is-task-chat{width:100%;max-width:none;padding:14px}.is-task-chat .history{padding:8px}.is-task-chat .chat-head h2{font-size:18px}.step-line>.trash-task{margin:0}.step-line .step-label{flex-basis:calc(100% - 86px)}.task-deadline-row{flex-wrap:wrap}#task-chat-dialog{height:94dvh;max-height:94dvh}}
/* Dense task rows and readable assistant output. */
.focus-item,.focus-item:first-child{padding-block:14px}.focus-item:first-child{padding-top:0}.focus-item:last-child{padding-bottom:0}.focus-context{margin-bottom:6px;row-gap:4px}.focus-plan{font-size:19px}.rank-actions{gap:2px}.focus-details{margin-top:4px}.focus-details>summary{min-height:30px;padding-block:3px}.plan-subtasks{margin-top:6px}.plan-subtasks .step-line{padding-block:7px;gap:8px}.add-subtask{margin-top:6px}.card-actions{margin-top:8px;padding-top:8px}.focus-list>.focus-item>.card-actions{border-top:0;margin:6px 0 0 38px;padding-top:6px;gap:6px}.focus-list>.focus-item>.card-actions button{font-size:13px;min-height:32px;padding:5px 9px}.chat-message small{margin-bottom:10px}.chat-body{white-space:normal}.chat-body p{margin:0 0 12px}.chat-body h4{font-size:16px;margin:16px 0 8px}.chat-body ul,.chat-body ol{margin:8px 0 14px;padding-left:24px}.chat-body li{margin:5px 0}.chat-body pre{white-space:pre-wrap}.chat-body>:last-child{margin-bottom:0}.handoff-whole:disabled{opacity:.45;cursor:default}
/* Stable details, quiet completion, and more space for conversation. */
.bubble-detail{width:100%;max-width:860px;max-height:none;overflow:visible}.bubble-detail-header{display:grid;grid-template-columns:minmax(0,1fr) 28px 36px;align-items:center;gap:10px}.bubble-detail-header h3{min-width:0;width:100%;margin:0}.bubble-detail-header .task-name{width:100%;font-size:20px}.bubble-detail>.task-deadline-row{margin-top:10px}.step-line.is-saving::after{display:none}.step-line.is-saving{opacity:.75}
#trash-undo{gap:12px}#trash-label{overflow-wrap:anywhere}#dismiss-trash{padding:2px 6px;font-size:20px;line-height:1;flex:none;border:0}
.chat,.chat.is-task-chat{padding:12px;gap:6px}.chat.is-task-chat{padding:16px}.chat .chat-head{align-items:center;padding-bottom:6px;gap:10px}.chat .chat-head-copy{display:flex;align-items:baseline;flex-wrap:wrap;column-gap:10px;row-gap:2px}.chat .chat-context{margin:0;font-size:12px}.chat .chat-head h2,.is-task-chat .chat-head h2{font-size:18px;line-height:1.25}.chat .history,.is-task-chat .history{padding:4px 8px}.chat-message{padding-block:6px;margin-bottom:6px}.chat-message small{margin-bottom:5px}.chat-body p{margin-bottom:8px}.chat-body li{margin-block:3px}.chat-body ul,.chat-body ol{margin-block:6px 10px}.chat-body h4{margin-top:10px}.composer{display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:end;gap:8px;padding:8px}.composer textarea,.is-task-chat .composer textarea{height:44px;min-height:44px;max-height:120px;font-size:15px}.composer>.row{margin:0;padding:0;border:0;flex-wrap:nowrap;gap:8px;align-items:center}.composer #voice,.composer #send{height:36px;min-height:36px}.composer #voice{width:36px}.composer #send{min-width:56px}.composer:has(#voice-cancel:not([hidden])),.composer:has(#voice-retry:not([hidden])){grid-template-columns:1fr}.voice-note summary{min-height:20px;padding:0}.chat .voice-note{margin:0}.chat-message.user{padding:10px 12px}
@media(max-width:700px){.chat.is-task-chat{padding:12px}.bubble-detail-header .task-name{font-size:18px}}
/* Stable row alignment and four-line default chat input. */
.workspace-menu>summary{display:inline-flex;align-items:center;justify-content:center;gap:8px;line-height:20px;min-height:40px}.workspace-menu>summary>span{display:block;line-height:20px}.workspace-menu>summary .disclosure-chevron{width:16px;height:16px;align-self:center;transform-origin:center}
.plan-subtasks .step-line{display:grid;grid-template-columns:28px 20px minmax(0,1fr) auto;align-items:start;column-gap:8px;row-gap:6px}.step-line>.check{margin:6px 0 0}.step-line>.trash-task{margin:2px 0 0}.step-line .step-label{gap:4px}.step-label input.task-name.step-title{height:32px;line-height:24px;padding:3px 4px;margin:0}.step-line>.agent-actions{margin:0;align-self:start}.step-line .inline-date{margin-left:4px}
.chat .composer textarea{height:24px;min-height:24px;max-height:144px;line-height:24px;resize:none;overflow-y:hidden}.bubble-detail{scroll-margin-block:16px}
@media(max-width:700px){.step-line>.agent-actions{grid-column:3/-1;justify-self:end}}
.file-list{display:flex;flex-wrap:wrap;gap:6px;grid-column:1/-1;min-width:0}.file-list[hidden]{display:none}.file-chip,.file-link{display:flex;align-items:center;gap:8px;max-width:100%;min-width:0;border:1px solid #dfe3ea;border-radius:10px;padding:6px 8px;background:#f6f7fa;color:#313b4b;font-size:12px;text-decoration:none}.file-chip{flex:1 1 180px}.file-name,.file-link>span:last-child{min-width:0;overflow-wrap:anywhere;flex:1}.file-chip small,.file-link small{display:block;color:#6c7482;font-size:11px}.file-type{font-size:9px;letter-spacing:.04em;font-weight:700;color:#53627a;background:#e9edf4;border-radius:5px;padding:5px}.file-remove,.file-retry{border:0;background:transparent;box-shadow:none;padding:3px;min-height:24px;line-height:1;color:#667085}.file-remove{font-size:20px}.sent-files{margin-top:8px}.file-link:hover{border-color:#9baeca;background:#edf1f8}.composer #attach{width:32px;height:36px;min-height:36px;padding:7px}.composer #attach svg{width:19px;height:19px;display:block}.composer .file-list~textarea{grid-column:1}
.attachment-picker{position:relative;display:flex;align-items:center}.attachment-menu{position:absolute;bottom:calc(100% + 10px);right:0;z-index:30;width:180px;padding:5px;background:#fff;border:1px solid #e0e4ec;border-radius:13px;box-shadow:0 8px 30px #17203524}.attachment-menu[hidden]{display:none}.attachment-menu button{display:flex;align-items:center;gap:10px;width:100%;padding:9px 10px;min-height:40px;border:0;border-radius:8px;background:transparent;box-shadow:none;color:#313b4b;font-size:13px;text-align:left}.attachment-menu button:hover,.attachment-menu button:focus-visible{background:#eef2fa}.attachment-menu button:focus-visible{outline:2px solid #8798cf;outline-offset:-2px}.attachment-menu .file-type{width:31px;text-align:center;padding:5px 2px}.attachment-menu svg{width:26px;height:26px;margin-inline:2px;color:#53627a;flex-shrink:0}
</style></head><body>
<header class="topbar row between"><div class="row"><span class="brand">Visual Second Brain</span></div><nav class="row" aria-label="Workspace"><details class="workspace-menu"><summary><span>Workspace</span><svg class="disclosure-chevron" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m4 6 4 4 4-4"/></svg></summary><div class="workspace-menu-items"><button id="refresh" class="small ghost">Refresh</button><button id="undo-trash-menu" class="small ghost" hidden>Undo last deletion</button><a href="/dev">Developer console</a><button id="signout" class="small ghost" hidden>Sign out</button></div></details></nav></header>
<main><div id="error" class="error" role="alert" hidden></div>
<section id="access" class="panel" hidden style="margin-bottom:24px"><form id="access-form" class="panel-body"><h2>Demo access</h2><p class="muted">Enter the app’s demo access token. Access lasts eight hours. Your workspace belongs to this browser; clearing cookies starts a new one.</p><div class="row" style="margin-top:12px"><input id="token" type="password" aria-label="Demo access token" autocomplete="off" maxlength="4096" required><button class="primary">Connect</button></div></form></section>
<div id="layout" class="canvas-layout"><section class="canvas" aria-label="Your saved tasks"><div class="intro row between wrap"><div><h1 class="eyebrow"><time id="workspace-date" class="workspace-date"></time></h1></div></div><div id="reviews" tabindex="-1"></div><div id="canvas" aria-live="polite"><div class="canvas-state"><p>Loading your workspace…</p></div></div></section>
<aside id="muse-chat" class="chat" aria-labelledby="muse-title" aria-hidden="true" inert><div class="chat-head row"><div class="chat-head-copy"><h2 id="muse-title">Muse</h2><p id="chat-context" class="chat-context">General chat</p><label class="sr-only" for="chat-scope" aria-hidden="true">Conversation</label><select id="chat-scope" hidden aria-hidden="true" tabindex="-1"><option value="">General chat</option></select></div><button id="close-muse" class="chat-close" type="button" data-chat-control aria-label="Close Muse chat"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18"/></svg></button></div><a id="review-link" href="#reviews" hidden>Review proposed changes</a><div id="chat-welcome" class="chat-welcome" hidden><h3>What’s on your mind?</h3></div><p id="chat-error" class="error" role="alert" hidden></p><div id="conversation" class="history" aria-live="polite"></div><div id="status" class="status" role="status" aria-live="polite"></div>
<form id="chat-form" class="composer"><label for="message">What’s on your mind?</label><div id="draft-attachments" class="file-list" hidden></div><input id="file-input" type="file" accept=".pdf,.txt,.docx,.png,.jpg,.jpeg,.webp,.gif" multiple hidden><textarea id="message" rows="1" maxlength="10000" placeholder="Message Muse…"></textarea><div class="row between"><div class="row wrap" style="margin:0"><div id="attachment-picker" class="attachment-picker"><button id="attach" class="small ghost" type="button" aria-label="Attach files" title="Attach files" aria-haspopup="menu" aria-controls="attachment-menu" aria-expanded="false"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m8 12 6-6a3 3 0 0 1 4 4l-8 8a5 5 0 0 1-7-7l9-9M6 14l8-8"/></svg></button><div id="attachment-menu" class="attachment-menu" role="menu" aria-label="File type" hidden><button type="button" role="menuitem" data-file-kind="pdf"><span class="file-type" aria-hidden="true">PDF</span>PDF</button><button type="button" role="menuitem" data-file-kind="txt"><span class="file-type" aria-hidden="true">TXT</span>TXT</button><button type="button" role="menuitem" data-file-kind="word"><span class="file-type" aria-hidden="true">DOCX</span>Word (.docx)</button><button type="button" role="menuitem" data-file-kind="image"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8" cy="8" r="1.5"/><path d="m4 18 5-5 4 4 3-4 5 5"/></svg>Image</button></div></div><button id="voice" class="small" type="button" aria-pressed="false" aria-label="Record voice message" title="Record voice message" aria-describedby="voice-status voice-privacy"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><rect x="9" y="3" width="6" height="12" rx="3"/><path d="M5 11v1a7 7 0 0 0 14 0v-1M12 19v3M9 22h6"/></svg></button><button id="voice-retry" class="small ghost" type="button" hidden>Retry transcription</button><button id="voice-cancel" class="small ghost" type="button" hidden>Cancel</button></div><button id="send" class="primary" type="submit" aria-label="Send message" title="Send message (Enter; Shift+Enter for a new line)">Send</button></div></form><p id="voice-status" class="voice-status" role="status" aria-live="polite"></p><p id="voice-preview" class="voice-preview" hidden></p><details class="voice-note"><summary>Voice uses Meta transcription<svg class="disclosure-chevron" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m4 6 4 4 4-4"/></svg></summary><p id="voice-privacy" class="voice-status">Record up to three minutes. Stop &amp; transcribe sends audio to Meta for transcription. Review the text before sending. This app does not save audio.</p></details></aside></div></main>
<button id="muse-launcher" class="muse-launcher" type="button" data-chat-control aria-label="Open Muse chat" aria-expanded="false" aria-controls="muse-chat"><svg viewBox="0 0 40 40" fill="none" aria-hidden="true"><path d="M9 8h22a4 4 0 0 1 4 4v13a4 4 0 0 1-4 4H18l-9 6v-6a4 4 0 0 1-4-4V12a4 4 0 0 1 4-4Z" stroke="currentColor" stroke-width="2.2"/><path d="M13 17h14M13 23h9" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg><span class="launcher-caption" aria-hidden="true">Talk to Muse</span></button>
<dialog id="task-chat-dialog" aria-label="Task conversation"><div id="task-chat-host"></div></dialog><div id="trash-undo" role="status" hidden><span id="trash-label"></span><button id="undo-trash" type="button" data-chat-control>Undo</button><button id="dismiss-trash" type="button" data-chat-control aria-label="Dismiss deletion notification">×</button></div>
<dialog id="add-dialog" aria-labelledby="add-title"><form id="add-form"><div class="row between" style="margin-bottom:20px"><h2 id="add-title">Add task</h2><button type="button" id="close-add" class="small" aria-label="Close new task">×</button></div><input id="add-horizon" type="hidden"><div class="field"><label for="add-name">Task name</label><input id="add-name" required maxlength="300" autocomplete="off"></div><div id="add-steps-field" class="field"><label id="add-steps-label">Subtasks</label><div id="add-subtasks" class="manual-subtasks" role="group" aria-labelledby="add-steps-label"></div><button type="button" id="add-subtask" class="small ghost">+ Add subtask</button></div><div class="grid2"><div class="field"><label for="add-deadline">Deadline</label><input id="add-deadline" type="date"></div><div class="field"><label for="add-importance">Importance</label><select id="add-importance" data-level-select></select></div></div><p id="add-error" class="error" role="alert" hidden></p><div class="row between"><button type="button" id="cancel-add" class="small ghost">Cancel</button><button class="primary" type="submit">Add task</button></div></form></dialog>
<dialog id="subtask-dialog" aria-labelledby="subtask-heading"><form id="subtask-form"><div class="row between" style="margin-bottom:20px"><h2 id="subtask-heading">Add subtask</h2><button type="button" id="close-subtask" class="small" aria-label="Close new subtask">×</button></div><input id="subtask-parent" type="hidden"><div class="field"><label for="subtask-name">Subtask name</label><input id="subtask-name" required maxlength="300" autocomplete="off" placeholder="What needs to be done?"></div><p id="subtask-error" class="error" role="alert" hidden></p><div class="row between"><button type="button" id="cancel-subtask" class="small ghost">Cancel</button><button class="primary" type="submit">Add subtask</button></div></form></dialog>
<dialog id="edit-dialog" aria-labelledby="edit-heading"><form id="edit-form"><div class="row between" style="margin-bottom:20px"><h2 id="edit-heading">Edit task</h2><button type="button" id="close-edit" class="small" aria-label="Close editor">×</button></div><input id="edit-id" type="hidden"><div class="field"><label for="edit-horizon">Focus section</label><select id="edit-horizon"><option value="short_term">Short-term</option><option value="long_term">Long-term</option></select></div><div class="field"><label for="edit-importance">Importance</label><select id="edit-importance" data-level-select></select></div><button class="primary" type="submit">Save changes</button></form></dialog>
<script>
'use strict';
const $=s=>document.querySelector(s),esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels={very_low:'Very low',low:'Low',medium:'Medium',high:'High',very_high:'Very high'};
let state={tasks:[],messages:[],runs:[]},ranges={},busy=false,pending=null,editVersion=null;

// Chat messages live on the server; only unsent drafts stay in this page.
let conversationId=null,chatTaskId=null,chatWorkId=null,delegatedTaskId=null;
const chatDrafts=new Map(),chatRequests=new Map(),attachmentDrafts=new Map(),chatFiles=new Map();
function newChat(){conversationId=null;chatTaskId=null;chatWorkId=null;delegatedTaskId=null;chatDrafts.clear();chatRequests.clear();attachmentDrafts.clear();chatFiles.clear();pending=null;$('#chat-form').reset();}
function rootTaskId(id,tasks=state.tasks){let task=tasks.find(t=>t.id===id),seen=new Set();while(task?.parent_task_id&&!seen.has(task.id)){seen.add(task.id);task=tasks.find(t=>t.id===task.parent_task_id);}return task?.id||null;}
function runChatScope(run,tasks=state.tasks,savedEvents=state.events||[]){const root=id=>rootTaskId(id,tasks);if(Object.hasOwn(run,'chat_scope_id'))return root(run.chat_scope_id);const original=root(run.input_payload?.chat_task_id);if(!['applied','answered'].includes(run.status))return original;const explicit=root(run.proposal?.chat_task_id),created=[...new Set(savedEvents.filter(e=>e.kind==='task.created'&&e.details?.run_id===run.id&&root(e.entity_id)===e.entity_id).map(e=>e.entity_id))],affected=[...new Set((run.related_task_ids||[]).map(id=>root(id)).filter(Boolean))];return explicit||(created.length===1?created[0]:affected.length===1?affected[0]:original);}
function chatRuns(){return state.runs.filter(r=>!r.chat_hidden&&r.task_id===null&&r.input_payload?.operation!=='draft'&&runChatScope(r)===chatTaskId);}
const today=new Date();$('#workspace-date').dateTime=[today.getFullYear(),String(today.getMonth()+1).padStart(2,'0'),String(today.getDate()).padStart(2,'0')].join('-');$('#workspace-date').textContent=today.toLocaleDateString(undefined,{weekday:'long',month:'short',day:'numeric'});
document.querySelectorAll('[data-level-select]').forEach(el=>el.innerHTML=(el.id==='add-importance'?'<option value="">Not assessed</option>':'')+Object.entries(labels).map(([k,v])=>`<option value="${k}">${v}</option>`).join(''));
function level(t){return t.user_importance_level||Object.keys(ranges).find(k=>t.importance_score!==null&&t.importance_score>=ranges[k].min&&t.importance_score<=ranges[k].max)||'';}
function badge(t){return `<span class="pill ${esc(level(t))}">${esc(labels[level(t)]||'Unassessed')}</span>`;}
function error(e){const message=e.message||'Something went wrong. Your draft is still here.';$('#error').textContent=message;$('#error').hidden=false;$('#chat-error').textContent=message;$('#chat-error').hidden=false;}
async function api(path,method='GET',body){let r;try{r=await fetch(path,{method,credentials:'same-origin',headers:{'Content-Type':'application/json'},...(body===undefined?{}:{body:JSON.stringify(body)})});}catch{throw Error('Could not reach the server. Your draft is preserved; try again.');}let data;try{data=await r.json();}catch{throw Error('The server returned an unreadable response. Your draft is preserved.');}if(!r.ok){if(r.status===401){endVoice({discard:true});$('#access').hidden=false;$('#signout').hidden=true;newChat();state={tasks:[],messages:[],runs:[]};render();}throw Error((data.error?.message||'Request failed')+(r.status===409?' Refresh to see the latest state.':''));}return data;}
function setBusy(value){if(value)endVoice({discard:true});busy=value;document.querySelectorAll('button:not([data-chat-control]),input,textarea,select').forEach(el=>el.disabled=value);$('#send').textContent=value?'…':'Send';syncVoice();updateHandoffControls();}
async function refresh(){const [data,levels,health]=await Promise.all([api('/api/dashboard'),api('/api/importance-levels'),api('/health')]);if(state.user_id!==data.user_id){chatTaskId=null;chatWorkId=null;delegatedTaskId=null;}state=data;if(chatTaskId)chatTaskId=rootTaskId(chatTaskId);ranges=levels;$('#access').hidden=true;$('#signout').hidden=!health.demo_access_required;render();loadTrashUndo();}
async function action(work){if(busy)return;setBusy(true);$('#error').hidden=true;$('#chat-error').hidden=true;try{await work();await refresh();}catch(e){$('#status').textContent='';error(e);}finally{setBusy(false);}}
function stepProgress(task){const steps=state.tasks.filter(t=>t.parent_task_id===task.id);if(!steps.length)return '';const done=steps.filter(t=>t.status==='completed').length;return `<div class="task-progress"><progress value="${done}" max="${steps.length}" aria-label="Completed steps for ${esc(task.title)}"></progress><span>${done} of ${steps.length} steps complete</span></div>`;}
let selectedBubble=null;
const openPlans=new Set();
function orderedChildren(id,tasks=state.tasks){return tasks.filter(t=>t.parent_task_id===id).sort((a,b)=>(a.position??0)-(b.position??0));}
function leafSteps(id,tasks=state.tasks){return orderedChildren(id,tasks).flatMap(t=>orderedChildren(t.id,tasks).length?leafSteps(t.id,tasks):[t]);}
function taskNameInput(task,classes=''){
 return `<input class="task-name ${classes}" data-task-name="${esc(task.id)}" data-version="${task.version}" value="${esc(task.title)}" aria-label="Task name" title="${esc(task.title)}" required maxlength="300">`;
}
function editableDeadline(t){
 return `<label class="inline-date">${taskDeadline(t)||'<span class="task-deadline is-empty">Add deadline</span>'}<input type="date" data-task-field="deadline" data-task-id="${esc(t.id)}" data-version="${t.version||1}" value="${esc(t.deadline||'')}" aria-label="Deadline for ${esc(t.title)}"></label>`;
}
function trashButton(t){return `<button type="button" class="trash-task" data-delete-task="${esc(t.id)}" aria-label="Delete ${esc(t.title)}" title="Delete task"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 10v7M14 10v7"/></svg></button>`;}
function taskDeadlineRow(t){return `<div class="task-deadline-row">${editableDeadline(t)}${taskHorizon(t)==='short_term'?`<button type="button" class="small handoff-whole" data-handoff="${esc(t.id)}" ${busy||!canHandoff(t)?'disabled':''} title="${canHandoff(t)?'Hand off to Muse':'All subtasks must be suitable for Muse before handing off the whole task.'}">Hand off task</button>`:''}</div>`;}
function focusStep(t){
 const done=t.status==='completed';
 return `<div class="step-line ${done?'is-done':''}" data-step-id="${esc(t.id)}">${trashButton(t)}<input class="check" type="checkbox" data-complete="${esc(t.id)}" aria-label="Mark ${esc(t.title)} ${done?'pending':'complete'}" ${done?'checked':''}><div class="step-label">${taskNameInput(t,`step-title ${done?'done':''}`)}${editableDeadline(t)}</div>${agentActions(t)}</div>`;
}
function taskDeadline(t){
 if(!t.deadline)return '';
 const today=new Date(),days=Math.round((Date.parse(t.deadline)-Date.UTC(today.getFullYear(),today.getMonth(),today.getDate()))/86400000);
 const urgency=days<0?'overdue':days<=1?'urgent':days<=3?'soon':days<=7?'approaching':'later',date=new Date(t.deadline+'T12:00:00').toLocaleDateString(undefined,{month:'short',day:'numeric'});
 const label=days<0?'Overdue':days===0?'Due today':days===1?'Due tomorrow':'Due';
 return `<span class="task-deadline" data-urgency="${urgency}">${label} · ${esc(date)}</span>`;
}
function addSubtaskButton(t){return `<button class="small ghost add-subtask" type="button" data-add-subtask="${esc(t.id)}" aria-label="Add subtask to ${esc(t.title)}">+ Add subtask</button>`;}
function taskActions(t){
 const completed=t.status==='completed';
 return `<div class="card-actions"><div class="agent-actions"><button type="button" class="ask-muse" data-task-chat="${esc(t.id)}">Ask Muse</button></div><button class="small ghost" data-edit="${esc(t.id)}">Edit task</button><button class="small ghost" data-toggle="${esc(t.id)}">${completed?'Reopen task':'Complete task'}</button></div>`;
}
function overviewFocus(t,i,tasks=state.tasks){
 const steps=leafSteps(t.id,tasks),done=steps.filter(c=>c.status==='completed').length;
 return `<article class="focus-item" data-plan-id="${esc(t.id)}" data-focus-rank="${i}"><div class="focus-context"><div class="rank-actions"><span class="focus-rank" aria-hidden="true">${i+1}</span>${trashButton(t)}</div><h3 class="focus-plan">${taskNameInput(t)}</h3>${steps.length?`<span class="focus-fraction">${done} / ${steps.length} completed</span>`:''}${taskDeadlineRow(t)}</div><details class="focus-details" data-plan-disclosure="${esc(t.id)}"><summary>Subtasks</summary>${steps.length?`<div class="plan-subtasks">${steps.map(c=>focusStep(c)).join('')}</div>`:''}${addSubtaskButton(t)}</details>${taskActions(t)}</article>`;
}
// Focus grouping.
function handoffRoot(task){let current=task;const seen=new Set();while(current?.parent_task_id&&!seen.has(current.id)){seen.add(current.id);current=state.tasks.find(t=>t.id===current.parent_task_id);}return current;}
function canHandoff(task){const root=handoffRoot(task);if(!task||!root||task.status==='completed'||root.status==='completed'||taskHorizon(root)!=='short_term')return false;const steps=leafSteps(task.id);return steps.length?steps.every(t=>t.handoff?.handler==='muse'):task.handoff?.handler==='muse';}

function hasNextAction(task,tasks=state.tasks){if(task.status==='completed'||task.completed)return false;if(task.status==='in_progress')return true;const steps=leafSteps(task.id,tasks);return !steps.length||steps.some(t=>t.status!=='completed');}
function taskHorizon(t,tasks=state.tasks){return t.time_horizon||((t.deadline||leafSteps(t.id,tasks).length)?'short_term':'long_term');}
function dashboardGroups(plans,tasks){
 const active=plans.filter(t=>hasNextAction(t,tasks));
 const isShort=t=>taskHorizon(t,tasks)==='short_term';
 const byImportance=(a,b)=>(b.importance_score??-1)-(a.importance_score??-1)||String(a.id).localeCompare(String(b.id));
 return {
  active,
  short:active.filter(isShort).sort((a,b)=>(a.deadline||'9999-12-31').localeCompare(b.deadline||'9999-12-31')||byImportance(a,b)),
  long:active.filter(t=>!isShort(t)).sort(byImportance),
  past:plans.filter(t=>!hasNextAction(t,tasks)).sort((a,b)=>String(b.updated_at||'').localeCompare(String(a.updated_at||'')))
 };
}
function longTermEntry(t){
 const open=openPlans.has(t.id),tasks=state.tasks,steps=leafSteps(t.id,tasks);
 return `<article class="goal-item" data-plan-id="${esc(t.id)}"><div class="goal-heading">${taskNameInput(t)}${trashButton(t)}<button type="button" class="subtasks-toggle" data-toggle-subtasks="${esc(t.id)}" aria-expanded="${open}" aria-controls="goal-subtasks-${esc(t.id)}" aria-label="${open?'Hide':'Show'} subtasks for ${esc(t.title)}"><svg class="disclosure-chevron" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m4 6 4 4 4-4"/></svg></button></div><div id="goal-subtasks-${esc(t.id)}" class="goal-subtasks" ${open?'':'hidden'}>${taskDeadlineRow(t)}${steps.length?`<div class="plan-subtasks">${steps.map(step=>focusStep(step)).join('')}</div>`:''}${addSubtaskButton(t)}${taskActions(t)}</div></article>`;
}
function toggleTaskSubtasks(button){
 const id=button.dataset.toggleSubtasks,open=button.getAttribute('aria-expanded')!=='true',panel=document.getElementById('goal-subtasks-'+id);
 if(!panel)return;
 if(open)openPlans.add(id);else openPlans.delete(id);
 panel.hidden=!open;button.setAttribute('aria-expanded',String(open));
 const task=state.tasks.find(t=>t.id===id);
 button.setAttribute('aria-label',`${open?'Hide':'Show'} subtasks for ${task?.title||'task'}`);
}
function pastTask(t,tasks){
 const completed=t.status==='completed'||t.completed;
 return `<article class="past-task" data-plan-id="${esc(t.id)}"><div class="past-task-heading"><h4>${esc(t.title)}</h4><span class="past-state">${completed?'Completed':'All subtasks completed'}</span><button class="small ghost" type="button" data-reopen="${esc(t.id)}">Reopen task</button></div></article>`;
}
function renderPastGroups(plans,tasks){
 return ['short_term','long_term'].map(horizon=>{
  const entries=plans.filter(t=>taskHorizon(t,tasks)===horizon),name=horizon==='short_term'?'Short-term':'Long-term';
  return `<section class="past-group" aria-label="Past ${name.toLowerCase()} tasks"><div class="past-group-heading"><h3>${name}</h3><span class="section-count">${entries.length} ${entries.length===1?'task':'tasks'}</span></div>${entries.map(t=>pastTask(t,tasks)).join('')||'<p class="muted">No past tasks.</p>'}</section>`;
 }).join('');
}
function sectionTaskControls(horizon){
 return `<div class="section-actions"><button type="button" class="small ghost add-task" data-add-task="${horizon}" aria-label="Add ${horizon==='short_term'?'short-term':'long-term'} task">+ Add task</button></div>`;
}
let focusSizeObserver=null;
function syncFocusHeights(){
 const short=$('[aria-labelledby="focus-title"]'),long=$('.direction-panel'),list=$('.goal-list');if(!short||!long||!list)return;
 if(window.matchMedia('(max-width:700px)').matches){list.style.maxHeight='none';return;}
 const style=getComputedStyle(long),header=long.querySelector('.panel-top'),headStyle=getComputedStyle(header);
 const chrome=parseFloat(style.paddingTop)+parseFloat(style.paddingBottom)+parseFloat(style.borderTopWidth)+parseFloat(style.borderBottomWidth)+header.getBoundingClientRect().height+parseFloat(headStyle.marginBottom);
 list.style.maxHeight=Math.max(52,short.getBoundingClientRect().height-chrome)+'px';
}
function watchFocusHeights(){focusSizeObserver?.disconnect();const short=$('[aria-labelledby="focus-title"]');if(short){focusSizeObserver=new ResizeObserver(syncFocusHeights);focusSizeObserver.observe(short);}syncFocusHeights();}
function renderOverview(){
 stopBubbleWorld();
 const roots=state.tasks.filter(t=>!t.parent_task_id),tasks=state.tasks;
 const groups=dashboardGroups(roots,tasks),boardPlans=groups.active;
 const focus=groups.short.map((t,i)=>overviewFocus(t,i,tasks)).join('');
 if(!boardPlans.some(t=>t.id===selectedBubble))selectedBubble=null;
 $('#canvas').innerHTML=`<div class="overview-grid"><section class="overview-panel" aria-labelledby="focus-title"><div class="panel-top"><h2 id="focus-title">Short-term focus</h2>${sectionTaskControls('short_term')}</div><div class="focus-list">${focus||`<div class="quiet-empty"><strong>Add your next task.</strong><button class="chat-entry" type="button" data-open-muse>Plan with Muse</button></div>`}</div></section><section class="overview-panel direction-panel" aria-labelledby="direction-title"><div class="panel-top"><h2 id="direction-title">Long-term focus</h2>${sectionTaskControls('long_term')}</div><div class="goal-list">${groups.long.map(t=>longTermEntry(t)).join('')||'<p class="direction-empty">Add a goal you want to work toward.</p>'}</div></section><section class="overview-panel backlog-panel" aria-labelledby="backlog-title"><div class="panel-top"><h2 id="backlog-title">Everything on your mind</h2></div><span id="bubble-move-help" class="sr-only">Drag to move, or use arrow keys when focused. Press Enter to open task details.</span><div class="bubble-field" role="group" aria-label="Tasks by importance">${boardPlans.map(backlogBubble).join('')||'<p class="muted">Your tasks will find a place here.</p>'}</div>${renderBubbleDetails(boardPlans,tasks)}</section><section id="past-tasks" class="overview-panel past-panel" aria-labelledby="past-title"><div class="panel-top"><h2 id="past-title" tabindex="-1">Past tasks</h2></div>${groups.past.length?`<div class="past-groups">${renderPastGroups(groups.past,tasks)}</div>`:'<p class="muted">Completed tasks will stay here. Reopen one to continue.</p>'}</section></div>`;
 watchFocusHeights();
 document.querySelectorAll('[data-plan-disclosure]').forEach(el=>{el.open=openPlans.has(el.dataset.planDisclosure);});
 layoutBubbles();
}
// Seeded placement gives the backlog an irregular shape without changing on reload.
function bubbleSeed(id){let seed=2166136261;for(const char of String(id))seed=Math.imul(seed^char.charCodeAt(0),16777619);return seed>>>0;}
function scatterBubbles(items,width){
 const inset=12,gap=20,available=Math.max(1,width-inset*2);
 const circles=items.map(item=>({...item,r:Math.min(item.size,available)/2})).sort((a,b)=>b.r-a.r||bubbleSeed(a.id)-bubbleSeed(b.id));
 let height=Math.max(280,circles.reduce((sum,c)=>sum+Math.PI*(c.r+gap/2)**2,0)/(Math.max(width,1)*.44));
 const placed=[];
 for(const circle of circles){
  let seed=bubbleSeed(circle.id),found=false;
  const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
  while(!found){
   for(let attempt=0;attempt<240;attempt++){
    const x=inset+circle.r+random()*Math.max(0,width-2*(inset+circle.r));
    const y=inset+circle.r+random()*Math.max(0,height-2*(inset+circle.r));
    if(placed.every(other=>Math.hypot(x-other.x,y-other.y)>=circle.r+other.r+gap)){
     placed.push({...circle,x,y});found=true;break;
    }
   }
   if(!found)height+=Math.max(60,circle.r);
  }
 }
 return {circles:placed,height:Math.ceil(Math.max(280,...placed.map(c=>c.y+c.r+inset)))};
}
function layoutBubbles(){
 stopBubbleWorld();
 const field=$('#canvas').querySelector('.bubble-field');if(!field||!field.clientWidth)return;
 const buttons=[...field.querySelectorAll('[data-bubble]')];if(!buttons.length){field.style.height='auto';return;}
 const scale=window.matchMedia('(max-width:650px)').matches ? 0.82 : 1;
 const items=buttons.map(button=>({id:button.dataset.bubble,size:parseFloat(getComputedStyle(button).getPropertyValue('--bubble-size'))*scale}));
 const layout=scatterBubbles(items,field.clientWidth),positions=new Map(layout.circles.map(c=>[c.id,c]));
 field.style.height=layout.height+'px';
 buttons.forEach(button=>{const c=positions.get(button.dataset.bubble);Object.assign(button.style,{left:(c.x-c.r)+'px',top:(c.y-c.r)+'px',width:(c.r*2)+'px',height:(c.r*2)+'px'});});
 startBubbleWorld(field,layout,buttons);
}
// Small, local physics controller. Moving a bubble changes presentation only.
let bubbleWorld=null;
const bubblePositions=new Map();
function clampBubble(body,world){
 const inset=12;
 if(body.x<body.r+inset){body.x=body.r+inset;body.vx=Math.abs(body.vx)*.45;}
 if(body.x>world.width-body.r-inset){body.x=world.width-body.r-inset;body.vx=-Math.abs(body.vx)*.45;}
 if(body.y<body.r+inset){body.y=body.r+inset;body.vy=Math.abs(body.vy)*.45;}
 if(body.y>world.height-body.r-inset){body.y=world.height-body.r-inset;body.vy=-Math.abs(body.vy)*.45;}
}
function advanceBubbleWorld(world,dt=1,reduced=false){
 const held=world.drag?.body;
 for(const body of world.bodies){
  if(body!==held){body.x+=reduced?0:body.vx*dt;body.y+=reduced?0:body.vy*dt;body.vx*=Math.pow(.91,dt);body.vy*=Math.pow(.91,dt);}
  clampBubble(body,world);
 }
 let displacement=0;
 for(let pass=0;pass<5;pass++){
  for(let i=0;i<world.bodies.length;i++)for(let j=i+1;j<world.bodies.length;j++){
   const a=world.bodies[i],b=world.bodies[j],dx=b.x-a.x,dy=b.y-a.y,distance=Math.hypot(dx,dy),overlap=a.r+b.r+12-distance;
   if(overlap<=0)continue;
   const nx=distance>.001?dx/distance:1,ny=distance>.001?dy/distance:0,ia=a===held?0:1/(a.r*a.r),ib=b===held?0:1/(b.r*b.r),sum=ia+ib;
   if(!sum)continue;
   a.x-=nx*overlap*ia/sum;a.y-=ny*overlap*ia/sum;b.x+=nx*overlap*ib/sum;b.y+=ny*overlap*ib/sum;
   const speed=(b.vx-a.vx)*nx+(b.vy-a.vy)*ny;
   if(speed<0&&!reduced){const impulse=-1.45*speed/sum;a.vx-=impulse*nx*ia;a.vy-=impulse*ny*ia;b.vx+=impulse*nx*ib;b.vy+=impulse*ny*ib;}
   displacement=Math.max(displacement,overlap);clampBubble(a,world);clampBubble(b,world);
  }
 }
 for(const body of world.bodies){if(reduced)body.vx=body.vy=0;else{body.vx=Math.max(-16,Math.min(16,body.vx));body.vy=Math.max(-16,Math.min(16,body.vy));}}
 return displacement>.15||world.bodies.some(b=>Math.hypot(b.vx,b.vy)>.06);
}
function paintBubbleWorld(world){
 for(const body of world.bodies){body.button.style.left=(body.x-body.r)+'px';body.button.style.top=(body.y-body.r)+'px';bubblePositions.set(world.scope+body.id,{x:body.x/world.width,y:body.y/world.height});}
}
function stopBubbleWorld(){
 const world=bubbleWorld;if(!world)return;world.disposed=true;cancelAnimationFrame(world.frame);
 if(world.drag){const {button,pointerId}=world.drag;world.drag=null;button.classList.remove('is-dragging');if(button.hasPointerCapture?.(pointerId))button.releasePointerCapture(pointerId);}
 bubbleWorld=null;
}
function wakeBubbleWorld(world){
 if(world.disposed||world.frame)return;
 if(window.matchMedia('(prefers-reduced-motion: reduce)').matches){advanceBubbleWorld(world,1,true);paintBubbleWorld(world);return;}
 world.lastTime=0;world.idle=0;
 const tick=time=>{
  world.frame=null;if(world.disposed||document.hidden)return;
  const dt=world.lastTime?Math.min(2,Math.max(.25,(time-world.lastTime)/16.667)):1;world.lastTime=time;
  const moving=advanceBubbleWorld(world,dt);paintBubbleWorld(world);
  world.idle=moving||world.drag?0:world.idle+1;
  if(world.idle<8)world.frame=requestAnimationFrame(tick);
 };
 world.frame=requestAnimationFrame(tick);
}
function startBubbleWorld(field,layout,buttons){
 stopBubbleWorld();
 const scope='live:',byId=new Map(buttons.map(button=>[button.dataset.bubble,button]));
 const world={field,width:field.clientWidth,height:layout.height,scope,bodies:layout.circles.map(c=>{const cached=bubblePositions.get(scope+c.id);return {...c,x:cached?cached.x*field.clientWidth:c.x,y:cached?cached.y*layout.height:c.y,vx:0,vy:0,button:byId.get(c.id)};}),frame:null,drag:null,disposed:false};
 bubbleWorld=world;
 world.bodies.forEach(body=>clampBubble(body,world));advanceBubbleWorld(world,1,true);paintBubbleWorld(world);
 const bodyFor=event=>{const button=event.target.closest('[data-bubble]');return world.bodies.find(body=>body.button===button);};
 const reduced=()=>window.matchMedia('(prefers-reduced-motion: reduce)').matches;
 field.addEventListener('pointerdown',event=>{
  if(world.disposed||world.drag||busy||event.button!==0||event.isPrimary===false)return;
  const body=bodyFor(event);if(!body)return;
  const rect=field.getBoundingClientRect();body.vx=body.vy=0;
  world.drag={body,button:body.button,pointerId:event.pointerId,startX:event.clientX,startY:event.clientY,offsetX:body.x-(event.clientX-rect.left),offsetY:body.y-(event.clientY-rect.top),lastTime:performance.now(),moved:false};
  body.button.setPointerCapture(event.pointerId);
 });
 field.addEventListener('pointermove',event=>{
  const drag=world.drag;if(world.disposed||!drag||event.pointerId!==drag.pointerId)return;
  if(!drag.moved&&Math.hypot(event.clientX-drag.startX,event.clientY-drag.startY)<5)return;
  event.preventDefault();drag.moved=true;drag.button.classList.add('is-dragging');
  const rect=field.getBoundingClientRect(),time=performance.now(),elapsed=Math.max(8,time-drag.lastTime),body=drag.body;
  const x=event.clientX-rect.left+drag.offsetX,y=event.clientY-rect.top+drag.offsetY;
  body.vx=Math.max(-16,Math.min(16,(x-body.x)*16.667/elapsed));body.vy=Math.max(-16,Math.min(16,(y-body.y)*16.667/elapsed));body.x=x;body.y=y;drag.lastTime=time;
  clampBubble(body,world);paintBubbleWorld(world);wakeBubbleWorld(world);
 });
 const release=(event,canceled=false)=>{
  const drag=world.drag;if(!drag||event.pointerId!==drag.pointerId)return;
  world.drag=null;drag.button.classList.remove('is-dragging');
  if(drag.moved){world.suppressClick={id:drag.body.id,until:performance.now()+500};if(canceled||reduced()||performance.now()-drag.lastTime>90)drag.body.vx=drag.body.vy=0;wakeBubbleWorld(world);}
  if(drag.button.hasPointerCapture(event.pointerId))drag.button.releasePointerCapture(event.pointerId);
 };
 field.addEventListener('pointerup',event=>release(event));
 field.addEventListener('pointercancel',event=>release(event,true));
 field.addEventListener('lostpointercapture',event=>release(event,true));
 field.addEventListener('click',event=>{const body=bodyFor(event);if(event.detail!==0&&body&&world.suppressClick?.id===body.id&&performance.now()<world.suppressClick.until){event.preventDefault();event.stopPropagation();world.suppressClick=null;}},true);
 field.addEventListener('keydown',event=>{
  const direction={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]}[event.key],body=bodyFor(event);
  if(!direction||!body||busy)return;
  event.preventDefault();body.x+=direction[0]*24;body.y+=direction[1]*24;body.vx=direction[0]*2;body.vy=direction[1]*2;clampBubble(body,world);wakeBubbleWorld(world);
 });
 // Resolve resized/restored layouts, then stop requesting frames once still.
 wakeBubbleWorld(world);
}

function backlogBubble(task){
 const importance=level(task);
 return `<button type="button" class="task-bubble ${esc(importance||'unassessed')}" data-bubble="${esc(task.id)}" aria-expanded="${task.id===selectedBubble}" aria-controls="bubble-details" aria-describedby="bubble-move-help" aria-label="${esc(task.title)} · ${esc(labels[importance]||'Unassessed')} importance" title="${esc(task.title)}"><span class="bubble-title">${esc(task.title)}</span>${taskDeadline(task)}</button>`;
}
function renderBubbleDetails(plans,tasks=state.tasks){
 const task=plans.find(t=>t.id===selectedBubble);if(!task)return '<div id="bubble-details" hidden></div>';
 const steps=leafSteps(task.id,tasks),done=steps.filter(t=>t.status==='completed').length;
 return `<section id="bubble-details" class="bubble-detail" data-backlog-id="${esc(task.id)}" aria-labelledby="bubble-detail-title"><div class="bubble-detail-header"><h3 id="bubble-detail-title">${taskNameInput(task)}</h3>${trashButton(task)}<button class="bubble-close" data-close-bubble type="button" aria-label="Close task details">×</button></div>${taskDeadlineRow(task)}${steps.length?`<p class="detail-progress">${done} / ${steps.length} completed</p><div class="plan-subtasks">${steps.map(t=>focusStep(t)).join('')}</div>`:''}${addSubtaskButton(task)}${taskActions(task)}</section>`;
}
// Animate native disclosures without replacing their keyboard or form behavior.
const disclosureMotion=new WeakMap();
function animateDisclosure(details){
 const previous=disclosureMotion.get(details),open=previous?!previous.open:!details.open,start=details.getBoundingClientRect().height;
 if(details.dataset.planDisclosure){if(open)openPlans.add(details.dataset.planDisclosure);else openPlans.delete(details.dataset.planDisclosure);}
 const overflow=previous?.overflow??details.style.overflow;
 previous?.animation.cancel();
 if(!motionAllowed()||!details.animate){details.open=open;details.style.overflow=overflow;disclosureMotion.delete(details);return;}
 details.open=open;const end=details.getBoundingClientRect().height;
 details.open=true;details.style.overflow='hidden';
 const animation=details.animate([{height:start+'px'},{height:end+'px'}],{duration:230,easing:'cubic-bezier(.2,.8,.2,1)'});
 const transition={open,overflow,animation};disclosureMotion.set(details,transition);
 const finish=()=>{if(disclosureMotion.get(details)!==transition)return;details.open=open;details.style.overflow=overflow;disclosureMotion.delete(details);};
 animation.finished.then(finish,finish);
}
function revealBubbleDetails(){
 const id=selectedBubble;requestAnimationFrame(()=>{const panel=$('#bubble-details');if(!panel||panel.hidden||id!==selectedBubble)return;panel.scrollIntoView({block:'end',inline:'nearest',behavior:motionAllowed()?'smooth':'instant'});});
}

// Completion feedback starts on click; failed saves restore the previous task.
function completionTarget(id){
 const canvas=$('#canvas'),rows=[...canvas.querySelectorAll('.plan-subtasks [data-step-id]')].filter(el=>el.dataset.stepId===id);
 const row=rows.find(el=>el.contains(document.activeElement))||rows[0],cards=[...canvas.querySelectorAll('[data-plan-id],[data-backlog-id]')];
 const card=row?.closest('[data-plan-id],[data-backlog-id]')||cards.find(el=>(el.dataset.planId||el.dataset.backlogId)===id&&el.contains(document.activeElement))||cards.find(el=>el.dataset.planId===id);
 const board=!!card?.dataset.backlogId;
 return card?{node:row||card,planId:card.dataset.planId||card.dataset.backlogId,rank:board?[...canvas.querySelectorAll('[data-backlog-id]')].indexOf(card):card.dataset.focusRank,board,open:card.open,hadFocus:card.contains(document.activeElement)}:null;
}
function motionAllowed(){return !window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;}
function restoreCompletionFocus(transition,id){
 if(!transition?.hadFocus)return;
 const canvas=$('#canvas'),card=[...canvas.querySelectorAll('[data-plan-id],[data-backlog-id]')].find(el=>(el.dataset.planId||el.dataset.backlogId)===transition.planId&&!!el.dataset.backlogId===transition.board);
 const same=card?.querySelector(`[data-complete="${CSS.escape(id)}"]`),next=same||card?.querySelector('[data-complete],summary')||[...canvas.querySelectorAll('[data-bubble]')].find(el=>el.dataset.bubble===transition.planId);
 if(next)next.focus({preventScroll:true});else{const heading=$('#focus-title');heading?.setAttribute('tabindex','-1');heading?.focus({preventScroll:true});}
}
function handleOverviewClick(e){
 const bubble=e.target.closest('[data-bubble]'),close=e.target.closest('[data-close-bubble]');
 if(bubble||close){const id=bubble?.dataset.bubble||selectedBubble;selectedBubble=close||selectedBubble===id?null:id;const roots=state.tasks.filter(t=>!t.parent_task_id&&hasNextAction(t));$('#bubble-details').outerHTML=renderBubbleDetails(roots);document.querySelectorAll('[data-bubble]').forEach(el=>el.setAttribute('aria-expanded',String(el.dataset.bubble===selectedBubble)));[...$('#canvas').querySelectorAll('[data-bubble]')].find(el=>el.dataset.bubble===id)?.focus({preventScroll:true});if(selectedBubble)revealBubbleDetails();return true;}
 return false;
}

function safeChatUrl(value){try{const url=new URL(value);return ['http:','https:'].includes(url.protocol)&&!url.username&&!url.password?url.href:null;}catch{return null;}}
function resizeComposer(){
 const input=$('#message');if(!input?.isConnected)return;
 const line=parseFloat(getComputedStyle(input).lineHeight)||24,max=line*6;
 input.style.height='0px';const needed=Math.max(line,input.scrollHeight);
 input.style.height=Math.min(needed,max)+'px';input.style.overflowY=needed>max?'auto':'hidden';
}
function chatInline(value){
 return String(value||'').replace(/【[^】\n]*】|\uE200[^\uE201\n]*\uE201/g,'').split(/(\[[^\]\n]{1,200}\]\(https?:\/\/[^\s)]{1,2000}\)|https?:\/\/[^\s<>"`]+|```[\s\S]*?```)/g).map(part=>{
  const link=part.match(/^\[([^\]]+)\]\((https?:\/\/.+)\)$/),url=safeChatUrl(link?link[2]:part);
  if(url)return `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(link?link[1]:part)}</a>`;
  if(part.startsWith('```')&&part.endsWith('```'))return `<pre><code>${esc(part.slice(3,-3).replace(/^\w*\n/,''))}</code></pre>`;
  return esc(part).replace(/\*\*([^*\n]+)\*\*/g,'<strong>$1</strong>').replace(/`([^`\n]+)`/g,'<code>$1</code>');
 }).join('');
}
function chatContent(value){
 const text=String(value||'').replace(/【[^】\n]*】|\uE200[^\uE201\n]*\uE201/g,'');
 return '<div class="chat-body">'+text.split(/(```[\s\S]*?```)/g).map(block=>{
  if(block.startsWith('```'))return chatInline(block);
  const lines=block.split('\n'),out=[];let paragraph=[],items=[],kind=null;
  const flushParagraph=()=>{if(paragraph.length){out.push('<p>'+paragraph.map(chatInline).join('<br>')+'</p>');paragraph=[];}};
  const flushList=()=>{if(items.length){out.push('<'+kind+'>'+items.map(item=>'<li>'+chatInline(item)+'</li>').join('')+'</'+kind+'>');items=[];kind=null;}};
  for(const line of lines){const heading=line.match(/^#{1,6}\s+(.+)$/),list=line.match(/^\s*(?:[-*+]\s+|(\d+)[.)]\s+)(.+)$/);
   if(!line.trim()){flushParagraph();flushList();continue;}
   if(heading){flushParagraph();flushList();out.push('<h4>'+chatInline(heading[1])+'</h4>');}
   else if(list){flushParagraph();const next=list[1]?'ol':'ul';if(kind&&kind!==next)flushList();kind=next;items.push(list[2]);}
   else{flushList();paragraph.push(line);}
  }flushParagraph();flushList();return out.join('');
 }).join('')+'</div>';
}
// General file attachments; drafts are kept separately for each chat.
function draftFiles(){return attachmentDrafts.get(chatTaskId||'')||[];}
function fileSize(bytes){return bytes<1000000?Math.max(1,Math.round(bytes/1000))+' KB':(bytes/1000000).toFixed(1)+' MB';}
function fileLinks(files){return files.length?'<div class="file-list sent-files">'+files.map(file=>`<a class="file-link" href="/api/attachments/${esc(file.id)}" download><span class="file-type">${esc(file.filename.split('.').at(-1).toUpperCase())}</span><span>${esc(file.filename)}<small>${fileSize(file.size)}</small></span></a>`).join('')+'</div>':'';}
function renderAttachments(){
 const files=draftFiles(),host=$('#draft-attachments');host.hidden=!files.length;
 host.innerHTML=files.map(file=>`<div class="file-chip"><span class="file-type">${esc(file.filename.split('.').at(-1).toUpperCase())}</span><span class="file-name">${esc(file.filename)}<small>${file.uploading?'Uploading…':file.error?esc(file.error):fileSize(file.size)}</small></span>${file.error?`<button type="button" class="file-retry" data-retry-file="${esc(file.id)}" aria-label="Retry upload of ${esc(file.filename)}">Retry</button>`:''}<button type="button" class="file-remove" data-remove-file="${esc(file.id)}" aria-label="Remove ${esc(file.filename)}">×</button></div>`).join('');
 $('#send').disabled=busy||!!voiceSession||files.some(file=>file.uploading||file.error);
 $('#attach').disabled=busy||!!voiceSession;
}
async function uploadFile(file,key){
 file.uploading=true;file.error=null;renderAttachments();
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),60000);
 try{
  const response=await fetch('/api/attachments/'+file.id+'?filename='+encodeURIComponent(file.filename),{method:'PUT',credentials:'same-origin',headers:{'Content-Type':'application/octet-stream'},body:file.source,signal:controller.signal});
  let data;try{data=await response.json();}catch{throw Error('Upload failed. Retry.');}
  if(!response.ok)throw Error(data.error?.message||'Upload failed. Retry.');
  // A discarded upload or signed-out workspace must not repopulate its draft.
  if(!(attachmentDrafts.get(key)||[]).includes(file))return;
  Object.assign(file,data);chatFiles.set(file.id,data);delete file.source;
 }catch(e){file.error=e.name==='AbortError'?'Upload timed out.':e instanceof TypeError?'Could not upload. Check your connection.':e.message;}
 finally{clearTimeout(timer);file.uploading=false;renderAttachments();}
}
const fileAccept={pdf:'.pdf',txt:'.txt',word:'.docx',image:'.png,.jpg,.jpeg,.webp,.gif'};
function closeAttachmentMenu({focus=false}={}){$('#attachment-menu').hidden=true;$('#attach').setAttribute('aria-expanded','false');if(focus)$('#attach').focus({preventScroll:true});}
$('#attach').onclick=()=>{
 if(busy||voiceSession)return;
 const open=$('#attachment-menu').hidden;$('#attachment-menu').hidden=!open;$('#attach').setAttribute('aria-expanded',String(open));
 if(open)$('#attachment-menu').querySelector('[role="menuitem"]').focus({preventScroll:true});
};
$('#attachment-menu').onclick=event=>{
 const option=event.target.closest('[data-file-kind]');if(!option||busy||voiceSession)return;
 $('#file-input').accept=fileAccept[option.dataset.fileKind];closeAttachmentMenu({focus:true});$('#file-input').click();
};
$('#attachment-picker').onkeydown=event=>{
 const menu=$('#attachment-menu');
 if(event.key==='Escape'&&!menu.hidden){event.preventDefault();event.stopPropagation();closeAttachmentMenu({focus:true});return;}
 if(menu.hidden||!['ArrowDown','ArrowUp','Home','End'].includes(event.key))return;
 event.preventDefault();const options=[...menu.querySelectorAll('[role="menuitem"]')],index=options.indexOf(document.activeElement);
 const next=event.key==='Home'?0:event.key==='End'?options.length-1:(index+(event.key==='ArrowUp'?-1:1)+options.length)%options.length;
 options[next].focus({preventScroll:true});
};
$('#attachment-picker').onfocusout=event=>{if(!event.currentTarget.contains(event.relatedTarget))closeAttachmentMenu();};
document.addEventListener('click',event=>{if(!event.target.closest('#attachment-picker'))closeAttachmentMenu();});
$('#file-input').onchange=()=>{
 const selected=[...$('#file-input').files],key=chatTaskId||'',files=draftFiles();$('#file-input').value='';
 if(busy||voiceSession)return;
 if(files.length+selected.length>5){error(Error('Attach up to 5 files per message.'));return;}
 if(selected.some(file=>!file.size||file.size>4000000)){error(Error('Choose nonempty files up to 4 MB each.'));return;}
 const added=selected.map(source=>({id:crypto.randomUUID(),filename:source.name,size:source.size,source,uploading:true}));
 attachmentDrafts.set(key,[...files,...added]);added.forEach(file=>uploadFile(file,key));renderAttachments();
};
$('#draft-attachments').onclick=e=>{
 if(busy)return;
 const remove=e.target.closest('[data-remove-file]'),retry=e.target.closest('[data-retry-file]');
 if(remove){attachmentDrafts.set(chatTaskId||'',draftFiles().filter(file=>file.id!==remove.dataset.removeFile));renderAttachments();}
 if(retry){const file=draftFiles().find(file=>file.id===retry.dataset.retryFile);if(file?.source)uploadFile(file,chatTaskId||'');}
};
// End file attachments.
function renderChat(){
 renderAttachments();
 const ids=new Set(chatRuns().map(r=>r.id)),visible=state.messages.filter(m=>ids.has(m.run_id));
 $('#chat-scope').innerHTML='<option value="">General chat</option>'+state.tasks.filter(t=>!t.parent_task_id).map(t=>`<option value="${esc(t.id)}">${esc(t.title)}</option>`).join('');
 $('#chat-scope').value=chatTaskId||'';
 $('#muse-title').textContent=chatTaskId?(state.tasks.find(t=>t.id===chatTaskId)?.title||'Task chat'):'Muse';
 $('#chat-context').textContent=chatTaskId?'Task chat':'General chat';
 const entries=visible.map(m=>{
  const run=state.runs.find(r=>r.id===m.run_id),sources=m.role==='assistant'?(run?.proposal?.sources||[]):[];
  const links=sources.filter(s=>safeChatUrl(s.url)).map(s=>`<a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">${esc(s.title||s.url)}</a>`).join('');
  return {at:m.created_at,html:`<div class="chat-message ${m.role==='user'?'user':''}"><small>${m.role==='user'?'YOU':'MUSE'}${m.role!=='user'&&run?.proposal?.web_search_used?' · WEB SEARCH':''}</small>${chatContent(m.content)}${fileLinks(m.attachments||[])}${links?`<div class="chat-sources">${links}</div>`:''}</div>`};
 });
 $('#chat-welcome').hidden=entries.length>0||!!pending;
 $('#conversation').innerHTML=entries.sort((a,b)=>String(a.at||'').localeCompare(String(b.at||''))).map(e=>e.html).join('');
 if(pending&&!visible.some(m=>m.role==='user'&&state.runs.some(r=>r.id===m.run_id&&r.request_id===pending.request_id)))$('#conversation').innerHTML+=`<div class="chat-message user"><small>YOU · SENDING</small>${esc(pending.message)}${fileLinks((pending.attachment_ids||[]).map(id=>chatFiles.get(id)).filter(Boolean))}</div>`;
 resizeComposer();$('#conversation').scrollTop=$('#conversation').scrollHeight;
 const latest=chatRuns().at(-1);
 $('#status').textContent=latest?.status==='running'?'Muse is working on your message…':latest?.status==='failed'?'The last request failed. Your saved work is unchanged.':'';
}
function openTaskChat(id=null){
 if(busy)return;
 $('#chat-error').hidden=true;const requested=id;if(id){id=rootTaskId(id);if(!id)return;}
 chatWorkId=requested;delegatedTaskId=null;
 chatDrafts.set(chatTaskId||'', $('#message').value);chatRequests.set(chatTaskId||'',pending);
 chatTaskId=id;try{localStorage.setItem('second-brain-chat:'+state.user_id,id||'');}catch{}pending=chatRequests.get(id||'')||null;delegatedTaskId=pending?.delegated_task_id||null;if(delegatedTaskId)chatWorkId=delegatedTaskId;
 $('#message').value=chatDrafts.get(id||'')||'';
 renderChat();setMuseOpen(true);
}
$('#chat-scope').onchange=()=>openTaskChat($('#chat-scope').value||null);
function render(){
 renderOverview();renderChat();
 const reviews=state.runs.filter(r=>r.task_id===null&&r.status==='awaiting_review');
 $('#review-link').hidden=!reviews.length;$('#review-link').textContent='An earlier unsaved plan is available';
 $('#reviews').innerHTML=reviews.map(r=>`<section class="legacy-plan" data-run="${esc(r.id)}"><h3>Earlier unsaved plan</h3><p>These tasks were prepared before direct saving. Add them to your dashboard and edit them there.</p><ul>${r.proposal.tasks.map(t=>`<li>${esc(t.title)}${t.subtasks.length?` · ${t.subtasks.length} steps`:''}</li>`).join('')}</ul><div class="row"><button class="small primary" data-save="${esc(r.id)}">Add these tasks</button><button class="small ghost" data-reject="${esc(r.id)}">Dismiss</button></div></section>`).join('');
}
function forgetSentMessage(request){
 const key=rootTaskId(request.chat_task_id)||'';
 if((chatDrafts.get(key)||'').trim()===request.message)chatDrafts.delete(key);
 if(chatRequests.get(key)?.request_id===request.request_id)chatRequests.delete(key);
 if(pending?.request_id===request.request_id)pending=null;
 if($('#message').value.trim()===request.message)$('#message').value='';
}
function followTaskChat(run){
 if(run.input_payload?.keep_chat_scope)return;
 if(!['applied','answered'].includes(run.status))return;
 const saved=state.runs.find(r=>r.id===run.id)||run,target=runChatScope(saved);
 if(!target||target===chatTaskId)return;
 chatDrafts.set(chatTaskId||'',$('#message').value);chatRequests.delete(chatTaskId||'');
 chatTaskId=target;pending=chatRequests.get(target)||null;
 const draft=chatDrafts.get(target)||'';
 $('#message').value=saved.message&&draft.trim()===saved.message.trim()?'':draft;
 try{localStorage.setItem('second-brain-chat:'+state.user_id,target);}catch{}
 renderChat();
}
$('#chat-form').onsubmit=e=>{
 e.preventDefault();if(voiceSession||busy)return;
 const message=$('#message').value.trim(),files=draftFiles(),key=chatTaskId||'',owner=state.user_id;
 if(files.some(file=>file.uploading||file.error))return;
 if(!message&&!files.length)return;
 if(message.length>10000){error(Error('Shorten your message to 10,000 characters before sending. Your transcript is preserved.'));return;}
 const attachment_ids=files.map(file=>file.id);
 const input={message,attachment_ids,apply_immediately:true,chat_task_id:chatTaskId,keep_chat_scope:true,web_enabled:true,delegated_task_id:delegatedTaskId};
 if(!pending||pending.message!==message||pending.apply_immediately!==true||pending.delegated_task_id!==delegatedTaskId||JSON.stringify(pending.attachment_ids||[])!==JSON.stringify(attachment_ids))pending={request_id:crypto.randomUUID(),conversation_id:conversationId,...input};
 const request=pending;let delivered=false;$('#message').value='';attachmentDrafts.delete(key);renderChat();
 action(async()=>{try{
  $('#status').textContent='Muse is working…';const run=await api('/api/conversation','POST',request);
  if(run.status==='running')throw Error('Muse is still processing this request. Refresh to check, or retry the same message.');
  if(run.status==='failed'){pending=null;throw Error(run.error||'Muse could not update your tasks. Try again.');}
  if(run.status==='stale'){pending=null;throw Error('Your workspace changed while Muse was processing. Send again to use the latest task state.');}
  if(!['applied','answered'].includes(run.status))throw Error('This reply used the earlier planning flow. Restart the updated backend, then try again.');
  delivered=true;delegatedTaskId=null;forgetSentMessage(request);await refresh();followTaskChat(run);
 }catch(e){
  if(!delivered&&state.user_id===owner){if(!$('#message').value)$('#message').value=message;if(!draftFiles().length)attachmentDrafts.set(key,files);}
  renderChat();throw e;
 }},'');
};
$('#message').addEventListener('input',resizeComposer);
$('#message').addEventListener('keydown',event=>{if(event.key!=='Enter'||event.shiftKey||event.isComposing)return;event.preventDefault();if(event.repeat||busy||voiceSession)return;$('#chat-form').requestSubmit();});
$('#send').title='Send message (Enter; Shift+Enter for a new line)';$('#send').setAttribute('aria-keyshortcuts','Enter');
$('#reviews').onclick=e=>{if(busy)return;const section=e.target.closest('[data-run]');if(!section)return;const id=section.dataset.run;if(e.target.closest('[data-save]'))action(()=>api('/api/conversation/'+id+'/approve','POST',{}),'Tasks added. You can edit them on the dashboard.');else if(e.target.closest('[data-reject]'))action(()=>api('/api/runs/'+id+'/reject','POST'),'Earlier plan dismissed.');};
function openEditor(id){const t=state.tasks.find(t=>t.id===id);if(!t)return;editVersion=t.version;$('#edit-id').value=t.id;$('#edit-horizon').value=taskHorizon(t);$('#edit-importance').value=level(t)||'medium';$('#edit-dialog').showModal();$('#edit-horizon').focus();}
function patchCompletionView(task){
 const canvas=$('#canvas'),done=task.status==='completed',root=handoffRoot(task);if(!root)return;
 canvas.querySelectorAll('[data-step-id]').forEach(row=>{
  if(row.dataset.stepId!==task.id)return;row.classList.toggle('is-done',done);
  const check=row.querySelector('[data-complete]');check.checked=done;check.setAttribute('aria-label',`Mark ${task.title} ${done?'pending':'complete'}`);
  row.querySelector('.step-title')?.classList.toggle('done',done);
 });
 canvas.querySelectorAll('[data-task-name],[data-task-id]').forEach(input=>{if((input.dataset.taskName||input.dataset.taskId)===task.id)input.dataset.version=String(task.version);});
 canvas.querySelectorAll('[data-assessment-id]').forEach(el=>{if(el.dataset.assessmentId===task.id)el.innerHTML=handoffButton(task,false);});
 const steps=leafSteps(root.id),progress=`${steps.filter(t=>t.status==='completed').length} / ${steps.length} completed`;
 canvas.querySelectorAll('[data-plan-id],[data-backlog-id]').forEach(card=>{if((card.dataset.planId||card.dataset.backlogId)===root.id)card.querySelectorAll('.focus-fraction,.detail-progress').forEach(el=>el.textContent=progress);});
 canvas.querySelectorAll('[data-handoff]').forEach(button=>{const target=state.tasks.find(t=>t.id===button.dataset.handoff);if(target&&(target.id===task.id||target.id===root.id))button.disabled=!canHandoff(target);});
 if(hasNextAction(root))return;
 // Only the finished plan leaves the active surface; other DOM and bubble positions stay mounted.
 canvas.querySelectorAll('[data-plan-id]').forEach(el=>{if(el.dataset.planId===root.id&&!el.closest('#past-tasks'))el.remove();});
 canvas.querySelectorAll('[data-bubble]').forEach(el=>{if(el.dataset.bubble===root.id)el.remove();});
 if(bubbleWorld)bubbleWorld.bodies=bubbleWorld.bodies.filter(body=>body.id!==root.id);
 if(selectedBubble===root.id){selectedBubble=null;$('#bubble-details').outerHTML='<div id="bubble-details" hidden></div>';}
 const groups=dashboardGroups(state.tasks.filter(t=>!t.parent_task_id),state.tasks),past=$('#past-tasks');
 past.querySelector('.past-groups,.muted')?.remove();past.insertAdjacentHTML('beforeend',`<div class="past-groups">${renderPastGroups(groups.past,state.tasks)}</div>`);
 canvas.querySelectorAll('.focus-item').forEach((el,i)=>{el.dataset.focusRank=String(i);el.querySelector('.focus-rank').textContent=String(i+1);});
 if(!groups.short.length)$('.focus-list').innerHTML='<div class="quiet-empty"><strong>Add your next task.</strong><button class="chat-entry" type="button" data-open-muse>Plan with Muse</button></div>';
 if(!groups.long.length)$('.goal-list').innerHTML='<p class="direction-empty">Add a goal you want to work toward.</p>';
 if(!groups.active.length){stopBubbleWorld();const field=$('.bubble-field');field.style.height='280px';field.innerHTML='<p class="muted">Your tasks will find a place here.</p>';}
 syncFocusHeights();
}
async function complete(id,value){
 if(busy)return;
 const task=state.tasks.find(t=>t.id===id);if(!task)return;
 const transition=completionTarget(id),checks=[...$('#canvas').querySelectorAll('[data-complete]')].filter(el=>el.dataset.complete===id),toggles=[...$('#canvas').querySelectorAll('[data-toggle]')].filter(el=>el.dataset.toggle===id);
 busy=true;$('#error').hidden=true;checks.forEach(el=>{el.checked=value;el.disabled=true;el.setAttribute('aria-busy','true');});toggles.forEach(el=>el.disabled=true);
 const optimistic={...task,status:value?'completed':'pending'};state.tasks=state.tasks.map(t=>t.id===id?optimistic:t);
 try{
  const saved=await api('/api/tasks/'+id,'PATCH',{expected_version:task.version,status:value?'completed':'pending'});
  if(saved?.id!==id||saved.status!==(value?'completed':'pending'))throw Error('Could not confirm the task update. Refresh to check its saved state.');
  state.tasks=state.tasks.map(t=>t.id===id?saved:t);patchCompletionView(saved);
 }catch(e){
  const restore=state.tasks.includes(optimistic);state.tasks=state.tasks.map(t=>t===optimistic?task:t);checks.forEach(el=>el.checked=task.status==='completed');if(restore)patchCompletionView(task);error(e);
 }finally{
  checks.forEach(el=>{el.removeAttribute('aria-busy');el.disabled=false;});toggles.forEach(el=>el.disabled=false);busy=false;restoreCompletionFocus(transition,id);
 }
}
$('#canvas').addEventListener('click',event=>{if(event.target.closest('input,textarea,select,button'))return;const summary=event.target.closest('summary');if(summary?.parentElement?.tagName!=='DETAILS')return;event.preventDefault();animateDisclosure(summary.parentElement);},true);
// Keep a description click intact while an inline field is awaiting blur-save.
$('#canvas').addEventListener('pointerdown',event=>{if(!busy&&event.target.closest('[data-toggle-subtasks]')&&document.activeElement?.matches('[data-task-name],[data-task-field]'))event.preventDefault();});
$('#canvas').onclick=e=>{const remove=e.target.closest('[data-delete-task]');if(remove){trashTask(remove.dataset.deleteTask);return;}const subtasks=e.target.closest('[data-toggle-subtasks]');if(subtasks){if(!busy){const field=document.activeElement;toggleTaskSubtasks(subtasks);if(field?.matches('[data-task-name],[data-task-field]'))field.blur();}return;}const addStep=e.target.closest('[data-add-subtask]');if(addStep){openAddSubtask(addStep.dataset.addSubtask);return;}const add=e.target.closest('[data-add-task]');if(add){openAddTask(add.dataset.addTask);return;}const reopen=e.target.closest('[data-reopen]');if(reopen){reopenTask(reopen.dataset.reopen);return;}const date=e.target.closest('[data-task-field="deadline"]');if(date){try{date.showPicker?.();}catch{}return;}const chat=e.target.closest('[data-task-chat]');if(chat){openTaskChat(chat.dataset.taskChat);return;}if(handleOverviewClick(e))return;if(busy)return;const assess=e.target.closest('[data-assess-handoff]');if(assess){assessSubtasks([state.tasks.find(t=>t.id===assess.dataset.assessHandoff)]);return;}const handoff=e.target.closest('[data-handoff]');if(handoff){handoffToMuse(handoff.dataset.handoff);return;}const edit=e.target.closest('[data-edit]'),toggle=e.target.closest('[data-toggle]');if(edit)openEditor(edit.dataset.edit);if(toggle)complete(toggle.dataset.toggle,state.tasks.find(t=>t.id===toggle.dataset.toggle).status!=='completed');};
// Manual tasks: one saved task, no model request or generated steps.
function manualSubtaskValues(){return [...$('#add-subtasks').querySelectorAll('[data-manual-subtask]')].map(input=>input.value);}
function renderManualSubtasks(values=[]){
 $('#add-subtasks').innerHTML=values.map((value,index)=>`<div class="manual-subtask"><span class="manual-step-number" aria-hidden="true">${index+1}</span><input data-manual-subtask required maxlength="300" aria-label="Subtask ${index+1}" placeholder="What needs to be done?" value="${esc(value)}"><button type="button" class="small ghost" data-remove-manual-step="${index}" aria-label="Remove subtask ${index+1}" >×</button></div>`).join('');
 $('#add-subtask').disabled=values.length>=20;
}
function openAddTask(horizon){
 if(busy)return;
 $('#add-form').reset();$('#add-error').hidden=true;$('#add-horizon').value=horizon;
 const short=horizon==='short_term';
 renderManualSubtasks([]);
 $('#add-title').textContent=`Add ${short?'short-term':'long-term'} task`;
 $('#add-dialog').showModal();$('#add-name').focus();
}
$('#add-subtask').onclick=()=>{if(busy)return;const values=manualSubtaskValues();if(values.length>=20)return;renderManualSubtasks([...values,'']);$('#add-subtasks').querySelectorAll('[data-manual-subtask]').item(values.length)?.focus();};
$('#add-subtasks').onclick=event=>{const button=event.target.closest('[data-remove-manual-step]');if(!button||busy)return;const values=manualSubtaskValues();values.splice(Number(button.dataset.removeManualStep),1);renderManualSubtasks(values);};
async function createManualTask(event){
 event.preventDefault();if(busy)return;
 const title=$('#add-name').value.trim();if(!title){$('#add-name').setCustomValidity('Enter a task name.');$('#add-name').reportValidity();return;}
 const horizon=$('#add-horizon').value,steps=manualSubtaskValues().map(title=>({title:title.trim()}));
 if(steps.some(step=>!step.title)){$('#add-error').textContent='Enter a name for each subtask.';$('#add-error').hidden=false;return;}
 const body={title,description:'',deadline:$('#add-deadline').value||null,user_importance_level:$('#add-importance').value||null,time_horizon:horizon,...(steps.length?{subtasks:steps}:{})};
 setBusy(true);$('#add-error').hidden=true;
 try{
  const saved=await api('/api/tasks','POST',body);
  if(!saved?.id||saved.title!==body.title||saved.time_horizon!==body.time_horizon)throw Error('Could not confirm the saved task. Refresh your workspace before trying again.');
  const {subtasks:children=[],...parent}=saved;
  if(children.length!==steps.length||children.some((child,index)=>!child.id||child.parent_task_id!==parent.id||child.title!==steps[index].title||child.position!==index))throw Error('Could not confirm the saved subtasks. Refresh your workspace before trying again.');
  state.tasks.push(parent,...children);
  openPlans.add(saved.id);$('#add-dialog').close();renderOverview();renderChat();
  assessSubtasks(children);
 }catch(e){$('#add-error').textContent=e.message;$('#add-error').hidden=false;}
 finally{setBusy(false);$('#add-subtask').disabled=manualSubtaskValues().length>=20;}
}
$('#add-form').onsubmit=createManualTask;
$('#add-name').oninput=()=>$('#add-name').setCustomValidity('');
$('#close-add').onclick=$('#cancel-add').onclick=()=>{if(!busy)$('#add-dialog').close();};
function openAddSubtask(id){
 if(busy)return;const task=state.tasks.find(t=>t.id===id);if(!task||task.status==='completed'||task.completed)return;
 $('#subtask-form').reset();$('#subtask-parent').value=id;$('#subtask-error').hidden=true;
 $('#subtask-dialog').showModal();$('#subtask-name').focus();
}
async function createSubtask(event){
 event.preventDefault();if(busy)return;
 const title=$('#subtask-name').value.trim(),parentId=$('#subtask-parent').value;
 if(!title){$('#subtask-name').setCustomValidity('Enter a subtask name.');$('#subtask-name').reportValidity();return;}
 const body={title,parent_task_id:parentId},parent=state.tasks.find(t=>t.id===parentId);if(!parent)return;
 const horizon=taskHorizon(parent,state.tasks);setBusy(true);$('#subtask-error').hidden=true;
 try{
  // Keep a task in its current section when its first subtask is added.
  if(!parent.time_horizon){const pinned=await api('/api/tasks/'+parentId,'PATCH',{expected_version:parent.version,time_horizon:horizon});if(pinned?.id!==parentId||pinned.time_horizon!==horizon)throw Error('Could not confirm the task focus. Refresh before adding the subtask.');state.tasks=state.tasks.map(task=>task.id===parentId?pinned:task);}
  const saved=await api('/api/tasks','POST',body);
  if(!saved?.id||saved.title!==title||saved.parent_task_id!==parentId)throw Error('Could not confirm the saved subtask. Refresh before adding it again.');
  state.tasks.push(saved);
  openPlans.add(parentId);$('#subtask-dialog').close();renderOverview();renderChat();assessSubtasks([saved]);
 }catch(e){$('#subtask-error').textContent=e.message;$('#subtask-error').hidden=false;}finally{setBusy(false);}
}
$('#subtask-form').onsubmit=createSubtask;
$('#subtask-name').oninput=()=>$('#subtask-name').setCustomValidity('');
$('#close-subtask').onclick=$('#cancel-subtask').onclick=()=>{if(!busy)$('#subtask-dialog').close();};
async function reopenTask(id){
 if(busy)return;
 const task=state.tasks.find(t=>t.id===id);if(!task)return;
 const steps=leafSteps(id,state.tasks),status=steps.length&&steps.every(t=>t.status==='completed')?'in_progress':'pending';
 await action(()=>api('/api/tasks/'+id,'PATCH',{expected_version:task.version,status}),'Task reopened.');
}
// End manual tasks.
async function saveTaskName(input){return saveTaskField(input,'title',input.dataset.taskName);}
async function saveTaskField(input,field,id){
 if(busy)return;
 const task=state.tasks.find(t=>t.id===id);if(!task)return;
 const value=input.value.trim(),normalized=field==='deadline'?(value||null):value;
 input.setCustomValidity(field==='title'&&!value?'Enter a task name.':'');
 if(!input.reportValidity()||normalized===(task[field]??(field==='deadline'?null:'')))return;
 setBusy(true);$('#error').hidden=true;
 try{
  const saved=await api('/api/tasks/'+task.id,'PATCH',{expected_version:Number(input.dataset.version),[field]:normalized});
  if(saved?.id!==task.id||saved[field]!==normalized)throw Error('Could not confirm the saved task field.');
  state.tasks=state.tasks.map(t=>t.id===saved.id?saved:t);
  renderOverview();
 }catch(e){error(e);}finally{setBusy(false);}
}
$('#canvas').addEventListener('focusout',event=>{
 const name=event.target.closest('[data-task-name]'),field=event.target.closest('[data-task-field]');
 if(name)saveTaskName(name);else if(field)saveTaskField(field,field.dataset.taskField,field.dataset.taskId);
});
$('#canvas').addEventListener('input',event=>{if(event.target.matches('[data-task-name],[data-task-field]'))event.target.setCustomValidity('');});
$('#canvas').addEventListener('keydown',event=>{
 const input=event.target.closest('[data-task-name],[data-task-field]');if(!input||event.isComposing)return;
 if(event.key==='Enter'&&(input.tagName!=='TEXTAREA'||event.ctrlKey||event.metaKey)){event.preventDefault();input.blur();}
 if(event.key==='Escape'){
  event.preventDefault();const field=input.dataset.taskField||'title',id=input.dataset.taskId||input.dataset.taskName;
  const task=state.tasks.find(t=>t.id===id);
  input.value=task?.[field]??'';input.setCustomValidity('');input.blur();
 }
});
$('#canvas').onchange=e=>{
 const field=e.target.closest('[data-task-field="deadline"]');if(field){saveTaskField(field,'deadline',field.dataset.taskId);return;}
 const el=e.target.closest('[data-complete]');if(!el)return;const checked=el.checked;el.checked=!checked;complete(el.dataset.complete,checked);
};
$('#edit-form').onsubmit=e=>{e.preventDefault();action(async()=>{await api('/api/tasks/'+$('#edit-id').value,'PATCH',{expected_version:editVersion,time_horizon:$('#edit-horizon').value,user_importance_level:$('#edit-importance').value});$('#edit-dialog').close();},'Your correction is saved. Muse will use it next time.');};$('#close-edit').onclick=()=>$('#edit-dialog').close();
$('#refresh').onclick=()=>action(async()=>{},'Saved state refreshed.');$('#access-form').onsubmit=e=>{e.preventDefault();const token=$('#token').value;action(async()=>{await api('/api/session','POST',{token});newChat();$('#token').value='';},'Connected.');};
$('#signout').onclick=async()=>{if(busy)return;endVoice({discard:true});setBusy(true);$('#error').hidden=true;try{await api('/api/session','DELETE');newChat();state={tasks:[],messages:[],runs:[]};pending=null;$('#chat-form').reset();$('#edit-form').reset();$('#edit-dialog').close();$('#add-form').reset();$('#add-dialog').close();$('#subtask-form').reset();$('#subtask-dialog').close();render();$('#access').hidden=false;$('#signout').hidden=true;}catch(e){error(e);}finally{setBusy(false);}};
// Reversible trash: version-checked writes and an Undo stack per workspace visit.
let trashUndo=[],trashOwner=null,trashToastTimer=null;
const trashRequests=new Map();
function saveTrashUndo(show=false){try{sessionStorage.setItem('second-brain-trash:'+state.user_id,JSON.stringify(trashUndo));}catch{}renderTrashUndo(show);}
function loadTrashUndo(){
 if(trashOwner===state.user_id)return;trashOwner=state.user_id;
 try{trashUndo=JSON.parse(sessionStorage.getItem('second-brain-trash:'+state.user_id)||'[]');if(!Array.isArray(trashUndo))trashUndo=[];}catch{trashUndo=[];}
 renderTrashUndo();
}
function dismissTrashNotice(){clearTimeout(trashToastTimer);trashToastTimer=null;$('#trash-undo').hidden=true;}
function renderTrashUndo(show=false){
 const latest=trashUndo.at(-1);$('#undo-trash-menu').hidden=!latest;
 if(!show||!latest){dismissTrashNotice();return;}
 clearTimeout(trashToastTimer);$('#trash-label').textContent='Deleted '+latest.title;$('#trash-undo').hidden=false;
 trashToastTimer=setTimeout(dismissTrashNotice,8000);
}
$('#dismiss-trash').onclick=dismissTrashNotice;
async function trashTask(id){
 if(busy)return;const task=state.tasks.find(t=>t.id===id);if(!task)return;
 const old=trashRequests.get(id),request=old?.expected_version===task.version?old:{request_id:crypto.randomUUID(),expected_version:task.version};trashRequests.set(id,request);
 setBusy(true);$('#error').hidden=true;
 try{
  const result=await api('/api/tasks/'+encodeURIComponent(id),'DELETE',request);trashRequests.delete(id);
  if(!trashUndo.some(t=>t.deletion_id===result.deletion_id))trashUndo.push({id,title:task.title,deletion_id:result.deletion_id});trashUndo=trashUndo.slice(-20);saveTrashUndo(true);
  if(result.task_ids.includes(chatTaskId)){chatDrafts.set(chatTaskId,$('#message').value);chatTaskId=null;chatWorkId=null;delegatedTaskId=null;pending=chatRequests.get('')||null;$('#message').value=chatDrafts.get('')||'';setMuseOpen(false);}
  await refresh();
 }catch(e){error(e);}finally{setBusy(false);}
}
$('#undo-trash').onclick=async()=>{
 if(busy||!trashUndo.length)return;const item=trashUndo.at(-1);setBusy(true);$('#error').hidden=true;
 try{await api('/api/tasks/'+encodeURIComponent(item.id)+'/restore','POST',{deletion_id:item.deletion_id});trashUndo.pop();saveTrashUndo();await refresh();}catch(e){error(e);}finally{setBusy(false);}
};
$('#undo-trash-menu').onclick=()=>{$('.workspace-menu').open=false;return $('#undo-trash').onclick();};
// End reversible trash.
// Machine handoff: delegated work stays in internet-enabled Muse task chat.
const assessmentPending=new Set(),assessmentErrors=new Map(),assessmentRequests=new Map();
function handoffButton(task,disabledByBusy=busy){
  const root=handoffRoot(task);if(root&&taskHorizon(root)==='long_term')return '';
 const pending=assessmentPending.has(task.id),done=task.status==='completed';
 if(!task.handoff&&!done)return `<button type="button" class="small ghost" data-assess-handoff="${esc(task.id)}" ${disabledByBusy||pending?'disabled':''} title="${esc(assessmentErrors.get(task.id)||'Muse will assess whether it can help with this subtask in chat.')}">${pending?'Assessing…':assessmentErrors.has(task.id)?'Retry assessment':'Assess with Muse'}</button>`;
 const eligible=canHandoff(task);
 return `<button type="button" class="small ghost" data-handoff="${esc(task.id)}" ${disabledByBusy||!eligible?'disabled':''} aria-label="Hand off ${esc(task.title)} to Muse" title="${esc(done?'Already completed':eligible?'Hand off to Muse in this task’s chat.':'Needs you: '+(task.handoff?.reason||'A human action is required.'))}">Hand off</button>`;
}
function agentActions(task){const control=handoffButton(task);return control?`<div class="agent-actions" data-assessment-id="${esc(task.id)}">${control}</div>`:'';}
function updateHandoffControls(){
 document.querySelectorAll('.handoff-whole').forEach(el=>{el.disabled=busy||!canHandoff(state.tasks.find(t=>t.id===el.dataset.handoff));});
 document.querySelectorAll('[data-assessment-id]').forEach(el=>{const task=state.tasks.find(t=>t.id===el.dataset.assessmentId);if(task)el.innerHTML=handoffButton(task);});
}
async function assessSubtasks(items){
 const selected=items.filter(t=>t&&!t.handoff&&!assessmentPending.has(t.id)&&t.status!=='completed');if(!selected.length)return;
 const ids=selected.map(t=>t.id).sort(),key=ids.join(','),owner=state.user_id;
 const request=assessmentRequests.get(key)||{request_id:crypto.randomUUID(),task_ids:ids};assessmentRequests.set(key,request);
 ids.forEach(id=>{assessmentPending.add(id);assessmentErrors.delete(id);});updateHandoffControls();
 try{
  const result=await api('/api/handoff/assess','POST',request);if(state.user_id!==owner)return;
  if(result.status!=='running')assessmentRequests.delete(key);
  if(result.status!=='answered')throw Error(result.error||'The assessment is still pending. Retry to check its result.');
  if(!Array.isArray(result.tasks)||result.tasks.length!==ids.length||result.tasks.some(t=>!ids.includes(t.id)||!['muse','user'].includes(t.handoff?.handler)))throw Error('Could not confirm the handoff assessment. Refresh before retrying.');
  result.tasks.forEach(saved=>{
   const previous=state.tasks.find(t=>t.id===saved.id);if(!previous||previous.version>saved.version)return;
   state.tasks=state.tasks.map(t=>t.id===saved.id?saved:t);
   if(previous.title===saved.title&&previous.deadline===saved.deadline&&previous.status===saved.status)document.querySelectorAll('[data-task-name],[data-task-id]').forEach(input=>{if((input.dataset.taskName||input.dataset.taskId)===saved.id&&Number(input.dataset.version)===previous.version)input.dataset.version=String(saved.version);});
  });
 }catch(e){if(state.user_id===owner)ids.forEach(id=>assessmentErrors.set(id,e.message));}
 finally{ids.forEach(id=>assessmentPending.delete(id));updateHandoffControls();}
}
function handoffToMuse(id){
 if(busy)return;const task=state.tasks.find(t=>t.id===id);
 if(!canHandoff(task))return;
 openTaskChat(id);delegatedTaskId=id;
 const name=task.parent_task_id?'subtask':'task',draft=$('#message').value;
 $('#message').value=`Work on this ${name}: ${task.title}. Use the saved task context and the web when useful. Give me the result you can produce, and ask if essential information is missing.`;
 const sent=$('#message').value;$('#chat-form').requestSubmit();if(draft&&draft.trim()!==sent)$('#message').value=draft;resizeComposer();
}
// End machine handoff.

// Muse disclosure: keep the existing DOM, conversation, and unsent draft mounted.
const generalChatHome=$('#muse-chat').parentElement;
function setMuseOpen(open,{focus=true}={}){
 closeAttachmentMenu();
 const panel=$('#muse-chat'),launcher=$('#muse-launcher'),dialog=$('#task-chat-dialog'),host=$('#task-chat-host'),taskMode=!!chatTaskId;
 if(open&&taskMode){
  if(panel.parentElement!==host)host.appendChild(panel);panel.classList.add('is-task-chat');if(!dialog.open)dialog.showModal();
 }else if(!taskMode){
  if(panel.parentElement!==generalChatHome)generalChatHome.appendChild(panel);panel.classList.remove('is-task-chat');if(dialog.open)dialog.close();
 }
 panel.classList.toggle('is-open',open);panel.inert=!open;panel.setAttribute('aria-hidden',String(!open));
 if(!open&&dialog.open)dialog.close();
 launcher.setAttribute('aria-expanded',String(open&&!taskMode));launcher.setAttribute('aria-label',open&&!taskMode?'Close Muse chat':'Open Muse chat');
 if(!open&&voiceSession)endVoice({discard:true,message:'Voice input stopped when chat closed. Your typed draft is kept.'});
 if(open)requestAnimationFrame(()=>{if(!panel.classList.contains('is-open'))return;resizeComposer();const history=$('#conversation');history.scrollTop=history.scrollHeight;if(focus)(busy?$('#close-muse'):$('#message')).focus({preventScroll:true});});else if(focus)launcher.focus({preventScroll:true});
}
$('#muse-launcher').onclick=()=>{if(!chatTaskId&&$('#muse-chat').classList.contains('is-open'))setMuseOpen(false);else openTaskChat(null);};
$('#close-muse').onclick=()=>setMuseOpen(false);
$('#task-chat-dialog').addEventListener('close',()=>{if($('#muse-chat').parentElement===$('#task-chat-host')&&!$('#task-chat-dialog').open)setMuseOpen(false,{focus:false});});
document.addEventListener('click',event=>{if(event.target.closest('[data-open-muse]'))openTaskChat(null);});
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&$('#muse-chat').classList.contains('is-open')&&!$('#task-chat-dialog').open&&!$('#edit-dialog').open&&!$('#add-dialog').open&&!$('#subtask-dialog').open){event.preventDefault();setMuseOpen(false);}});
$('#review-link').onclick=()=>{setMuseOpen(false,{focus:false});$('#reviews').focus({preventScroll:true});};
// End Muse disclosure.
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
 const label=phase==='requesting'?'Starting microphone…':phase==='transcribing'?'Transcribing…':active?'Stop & transcribe':'Record voice message';
 const icon=phase==='requesting'||phase==='transcribing'?'<path d="M20 12a8 8 0 1 1-8-8"/>':active?'<rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor" stroke="none"/>':'<rect x="9" y="3" width="6" height="12" rx="3"/><path d="M5 11v1a7 7 0 0 0 14 0v-1M12 19v3M9 22h6"/>';
 $('#voice').innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true">'+icon+'</svg>';
 $('#voice').setAttribute('aria-label',label);$('#voice').setAttribute('title',label);$('#voice').setAttribute('data-phase',phase||'idle');
 $('#voice').setAttribute('aria-pressed',String(active));
 $('#voice-cancel').hidden=!active&&!voiceRecording;$('#voice-cancel').disabled=busy;
 $('#voice-retry').hidden=active||!voiceRecording;$('#voice-retry').disabled=busy;
 $('#message').readOnly=active;$('#send').disabled=busy||active||draftFiles().some(file=>file.uploading||file.error);$('#attach').disabled=busy||active;if(active)closeAttachmentMenu();resizeComposer();
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
  for(let index=voiceRecording.transcripts.length;index<voiceRecording.parts.length;index++){
  clearTimeout(session.timer);session.timer=setTimeout(()=>{if(voiceSession===session)endVoice({message:'Transcription timed out. Your draft and recording are kept. Retry transcription or continue typing.'});},55000);
  $('#voice-status').textContent=voiceRecording.parts.length>1?`Transcribing part ${index+1} of ${voiceRecording.parts.length}…`:'Transcribing your recording with Meta…';
  const response=await fetch('/api/voice/transcribe',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'audio/wav'},body:voiceRecording.parts[index],signal:session.controller.signal});
  let data;try{data=await response.json();}catch{throw Error('The server returned an unreadable transcription response.');}
  if(voiceSession!==session)return;
  if(!response.ok){
   if(voiceRecording.parts.length>1&&response.status===422&&data.error?.message?.startsWith('No speech was transcribed.')){voiceRecording.transcripts.push('');continue;}
   if(response.status===401){endVoice({discard:true,message:'Your demo session expired. Reconnect before recording again.'});api('/api/dashboard').catch(error);return;}
   throw Error(data.error?.message||'Voice transcription failed.');
  }
  if(typeof data.transcript!=='string'||!data.transcript.trim()||data.transcript.length>10000)throw Error('The server returned an invalid transcript.');
  voiceRecording.transcripts.push(data.transcript.trim());
  }
  const transcript=voiceRecording.transcripts.filter(Boolean).join(' ');
  if(!transcript)throw Error('No speech was transcribed. Try speaking closer to the microphone.');
  $('#message').value=session.base+(session.base?' ':'')+transcript;resizeComposer();
  endVoice({discard:true});$('#voice-status').textContent=$('#message').value.length>10000?'Transcript kept. Shorten your message to 10,000 characters before sending.':'';
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
 const samples=new Float32Array(session.samples);let offset=0;for(const chunk of session.chunks){samples.set(chunk,offset);offset+=chunk.length;}
 const parts=[];for(let offset=0;offset<samples.length;){const end=samples.length-(offset+session.rate*60)<session.rate/4?samples.length:offset+session.rate*60;const chunk=samples.subarray(offset,end);parts.push(encodeWav({rate:session.rate,samples:chunk.length,chunks:[chunk]}));offset=end;}
 voiceRecording={parts,transcripts:[]};session.chunks=[];
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
   const remaining=session.rate*180-session.samples,chunk=event.data.slice(0,remaining);
   if(!chunk.length)return;session.chunks.push(chunk);session.samples+=chunk.length;
   const seconds=Math.floor(session.samples/session.rate);
   if(seconds!==session.seconds){session.seconds=seconds;$('#voice-preview').textContent=`Recorded ${seconds}s / 180s`;}
  };
  stream.getTracks().forEach(track=>track.onended=()=>{if(voiceSession===session&&session.phase==='recording')endVoice({discard:true,message:'The microphone disconnected. Your typed draft is kept. Connect it and try again.'});});
  await session.context.resume();
  if(voiceSession!==session)return;
  clearTimeout(session.timer);session.phase='recording';syncVoice();
  $('#voice-preview').textContent='Recorded 0s / 180s';$('#voice-preview').hidden=false;
  $('#voice-status').textContent='Recording… Stop & transcribe when you’re ready.';
  session.timer=setTimeout(()=>{if(voiceSession!==session)return;session.phase='recorded';releaseCapture(session);syncVoice();$('#voice-status').textContent='Three-minute limit reached. Choose Stop & transcribe, or Cancel.';},180000);
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
$('#voice-status').textContent=voiceAvailable?'':!window.isSecureContext?'Voice input needs HTTPS or localhost. You can still type your message.':'Microphone recording is unavailable in this browser. You can still type your message.';
syncVoice();
// End voice input.

// WebMCP: browser-agent access to persisted dashboard actions.
let webMCPController=null;
async function registerWebMCP(){
 if(!window.isSecureContext||!document.modelContext?.registerTool||webMCPController)return;
 const controller=new AbortController();webMCPController=controller;
 const emptySchema={type:'object',properties:{},additionalProperties:false};
 function validate(input,keys=[]){
  if(!input||typeof input!=='object'||Array.isArray(input)||Object.keys(input).some(key=>!keys.includes(key)))return {error:'Pass an object with only the documented fields.'};
 }
 function uiBlocked(){
  if(!$('#access').hidden)return {error:'Connect using the visible demo access form first.'};
  if(busy||voiceSession)return {error:'Wait for the current request or stop voice capture before changing the interface.'};
  if($('#subtask-dialog')?.open)return {error:'Save or close the new subtask form first; its unsaved changes are preserved.'};
  if($('#add-dialog')?.open)return {error:'Save or close the new task form first; its unsaved changes are preserved.'};
  if($('#edit-dialog').open)return {error:'Save or close the open task editor first; its unsaved changes are preserved.'};
  if([...document.querySelectorAll('[data-task-field]')].some(input=>(input.value||'')!==(state.tasks.find(task=>task.id===input.dataset.taskId)?.[input.dataset.taskField]||'')))return {error:'Save or cancel the inline task edit first; its unsaved text is preserved.'};
  if([...document.querySelectorAll('[data-task-name]')].some(input=>input.value!==state.tasks.find(task=>task.id===input.dataset.taskName)?.title))return {error:'Save or cancel the inline task-name edit first; its unsaved text is preserved.'};
 }
 const uuid={type:'string',format:'uuid',pattern:'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'};
 const isUUID=value=>typeof value==='string'&&new RegExp(uuid.pattern).test(value);
 const handoffSchema={type:['object','null'],properties:{handler:{type:'string',enum:['muse','user']},reason:{type:'string',minLength:1,maxLength:1000},requirements:{type:'array',maxItems:10,items:{type:'string',minLength:1,maxLength:500}},done_when:{type:'string',minLength:1,maxLength:2000}},required:['handler','reason','requirements','done_when'],additionalProperties:false};
 const taskFields={time_horizon:{type:['string','null'],enum:['short_term','long_term',null]},title:{type:'string',minLength:1,maxLength:300},description:{type:'string',maxLength:10000},deadline:{type:['string','null'],format:'date',description:'YYYY-MM-DD, or null to clear. Never invent a deadline.'},user_importance_level:{type:['string','null'],enum:['very_low','low','medium','high','very_high',null]},handoff:handoffSchema};
 function taskError(input){
  if('time_horizon' in input&&input.time_horizon!==null&&!['short_term','long_term'].includes(input.time_horizon))return {error:'Choose short_term, long_term, or null for automatic grouping.'};
  if('title' in input&&(typeof input.title!=='string'||!input.title.trim()||input.title.trim().length>300))return {error:'Provide a task title of 1–300 characters.'};
  if('description' in input&&(typeof input.description!=='string'||input.description.length>10000))return {error:'Provide details of at most 10,000 characters.'};
  if('deadline' in input&&input.deadline!==null&&(typeof input.deadline!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(input.deadline)||!Number.isFinite(Date.parse(input.deadline))||new Date(input.deadline).toISOString().slice(0,10)!==input.deadline))return {error:'Provide a real deadline as YYYY-MM-DD, or null.'};
  if('user_importance_level' in input&&!['very_low','low','medium','high','very_high',null].includes(input.user_importance_level))return {error:'Choose one of the five importance levels, or null.'};
  if('handoff' in input&&input.handoff!==null){
   const h=input.handoff;
   if(validate(h,['handler','reason','requirements','done_when'])||!['muse','user'].includes(h.handler)||typeof h.reason!=='string'||!h.reason.trim()||h.reason.length>1000||typeof h.done_when!=='string'||!h.done_when.trim()||h.done_when.length>2000||!Array.isArray(h.requirements)||h.requirements.length>10||h.requirements.some(r=>typeof r!=='string'||!r.trim()||r.length>500))return {error:'Provide a complete handoff assessment with handler, reason, requirements, and done_when, or null.'};
  }
 }
 function publicTask({id,parent_task_id,title,description,deadline,time_horizon,user_importance_level,status,version,handoff,handoff_source}){return {id,parent_task_id,title,description,deadline,time_horizon,user_importance_level,status,version,handoff,handoff_source};}
 function savedTask(task){if(!isUUID(task?.id)||!Number.isInteger(task.version)||typeof task.title!=='string')throw Error('Invalid saved task response');return {status:'saved',task:publicTask(task)};}
 function publicProposal(proposal){return proposal?{reply:proposal.reply,chat_task_id:proposal.chat_task_id||null,tasks:proposal.tasks.map(({task_id,title,description,deadline,time_horizon,handoff,subtasks})=>({task_id,title,description,deadline,time_horizon,handoff,subtasks:subtasks.map(({title,description,handoff})=>({title,description,handoff}))}))}:null;}
 function publicRun(run){if(!isUUID(run?.id)||typeof run.status!=='string')throw Error('Invalid run response');return {id:run.id,request_id:run.request_id,status:run.status,reply:run.proposal?.reply||null,error:run.error||null};}
 async function mutate(path,method,body,signal,project){
  const blocked=uiBlocked();if(blocked)return blocked;
  signal?.throwIfAborted();
  setBusy(true);$('#error').hidden=true;
  let result;
  try{
   const response=await fetch(path,{method,credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal});
   const data=await response.json();
   if(!response.ok){
    result={error:data.error?.message||'Request failed.',status:response.status,outcome:'rejected',next_step:response.status===409?'Call get_dashboard and use the current version before trying again.':response.status===401?'Connect using the demo access form.':'Correct the request or retry when the service is available.'};
   }else{
    result=project(data);
    // A refresh failure does not change the authoritative mutation result.
    try{await refresh();}catch{result.ui_warning='The server replied, but the dashboard could not refresh. Call get_dashboard to verify saved state.';}
   }
  }catch(e){
   result={error:'The request was interrupted or its response was unreadable. It may have reached the server.',outcome:'unknown',...(body.request_id?{request_id:body.request_id}:{}),next_step:'Call get_dashboard before retrying (pass request_id for a Muse message). Retry a Muse message with the same request_id and message in this page visit. After reload, inspect its run status first. Do not blindly retry task creation.'};
  }finally{setBusy(false);}

  return result;
 }
 const tools=[
  {
   name:'get_dashboard',
   description:'Read saved tasks, handoff assessments, pending proposals, and current-chat run statuses from this browser workspace. Pass request_id to look up a specific Muse request even after reloading. Returns real saved state for verifying writes; unsaved edits are excluded. Handoff uses Muse task chat with web search.',
   inputSchema:{type:'object',properties:{request_id:{...uuid,description:'Optional Muse request UUID to check after an interrupted response or page reload.'}},additionalProperties:false},annotations:{readOnlyHint:true,untrustedContentHint:true},
   async execute(input,{signal}={}){
    const invalid=validate(input,['request_id']);if(invalid)return invalid;
    if('request_id' in input&&!isUUID(input.request_id))return {error:'Provide a request_id UUID, or omit it.'};
    try{
     const response=await fetch('/api/dashboard',{credentials:'same-origin',signal});
     if(!response.ok)return {error:response.status===401?'Connect using the visible demo access form first.':'Could not load saved state. Retry when the server is available.',status:response.status};
     const data=await response.json();signal?.throwIfAborted();
     return {tasks:data.tasks.map(publicTask),reviews:data.runs.filter(run=>run.task_id===null&&run.status==='awaiting_review').map(run=>({id:run.id,status:run.status,proposal:publicProposal(run.proposal)})),runs:data.runs.filter(run=>input.request_id?run.request_id===input.request_id:(!run.chat_hidden&&run.task_id===null&&runChatScope(run,data.tasks,data.events)===chatTaskId)).map(publicRun),execution:{connected:false,status:'unavailable',reason:'Browser control has been removed. Hand off uses internet-enabled Muse task chat.'},source:'Saved server state; unsaved interface edits are not included.'};
    }catch(e){if(signal?.aborted)throw e;return {error:'Could not read saved state. Retry when the server is available.'};}
   }
  },
  {
   name:'create_task',
   description:'Save a task or subtask directly in this workspace. Supply parent_task_id for a subtask. Returns the saved task ID and version. Creates real records; use only for work the user requested. On uncertain results, read the dashboard before retrying to avoid duplicates.',
   inputSchema:{type:'object',properties:{...taskFields,parent_task_id:{...uuid,type:['string','null']},subtasks:{type:'array',maxItems:20,items:{type:'object',properties:{title:{type:'string',minLength:1,maxLength:300}},required:['title'],additionalProperties:false}}},required:['title'],additionalProperties:false},
   annotations:{readOnlyHint:false,untrustedContentHint:true},
   async execute(input,{signal}={}){
    const invalid=validate(input,[...Object.keys(taskFields),'parent_task_id','subtasks']);if(invalid)return invalid;
    if(!('title' in input))return {error:'Provide a task title.'};
    const invalidTask=taskError(input);if(invalidTask)return invalidTask;
    if('subtasks' in input&&(!Array.isArray(input.subtasks)||input.subtasks.length>20||input.subtasks.some(step=>validate(step,['title'])||typeof step.title!=='string'||!step.title.trim()||step.title.trim().length>300)))return {error:'Provide at most 20 subtasks, each with a title.'};
    if(input.subtasks?.length&&input.parent_task_id)return {error:'Add a batch of subtasks with a root task only.'};
    if(input.parent_task_id!==undefined&&input.parent_task_id!==null&&!isUUID(input.parent_task_id))return {error:'Provide a saved parent task UUID, or null.'};
    const result=await mutate('/api/tasks','POST',input,signal,savedTask);if(result.status==='saved'){const candidates=input.parent_task_id?[state.tasks.find(t=>t.id===result.task.id)]:input.subtasks?.length?state.tasks.filter(t=>t.parent_task_id===result.task.id):[];assessSubtasks(candidates);}return result;
   }
  },
  {
   name:'update_task',
   description:'Save changes to a task or subtask by ID: rename, details, deadline, importance, handoff assessment, or status. Set status=completed only when the work is actually done; pending reopens it. Use expected_version from get_dashboard. Only supplied fields change. Returns the saved task and new version; a 409 requires a fresh read.',
   inputSchema:{type:'object',properties:{task_id:uuid,expected_version:{type:'integer',minimum:1},...taskFields,status:{type:'string',enum:['pending','in_progress','completed']}},required:['task_id','expected_version'],additionalProperties:false},
   annotations:{readOnlyHint:false,untrustedContentHint:true},
   async execute(input,{signal}={}){
    const invalid=validate(input,['task_id','expected_version',...Object.keys(taskFields),'status']);if(invalid)return invalid;
    if(!isUUID(input.task_id)||!Number.isInteger(input.expected_version)||input.expected_version<1)return {error:'Provide a saved task UUID and positive integer expected_version from get_dashboard.'};
    if(Object.keys(input).length<3)return {error:'Provide at least one task field to change.'};
    const invalidTask=taskError(input);if(invalidTask)return invalidTask;
    if('status' in input&&!['pending','in_progress','completed'].includes(input.status))return {error:'Choose pending, in_progress, or completed.'};
    const {task_id,...body}=input;
    return mutate('/api/tasks/'+task_id,'PATCH',body,signal,savedTask);
   }
  },
  {
   name:'send_muse_message',
   description:'Send a message to Muse now; validated task updates save directly and the reply appears in chat. This invokes the configured model. Provide a new request_id UUID for new work; reuse the exact request_id and message after an uncertain response in this page visit. Returns actual run status and reply. failed or stale means task updates were not applied; a revised request needs a new UUID. running means processing, not success; check get_dashboard. Matching composer text can be sent; different unsent text is preserved.',
   inputSchema:{type:'object',properties:{request_id:uuid,message:{type:'string',minLength:1,maxLength:10000}},required:['request_id','message'],additionalProperties:false},
   annotations:{readOnlyHint:false,untrustedContentHint:true},
   async execute(input,{signal}={}){
    const invalid=validate(input,['request_id','message']);if(invalid)return invalid;
    if(!isUUID(input.request_id)||typeof input.message!=='string'||!input.message.trim()||input.message.length>10000)return {error:'Provide a request_id UUID and a nonempty message of at most 10,000 characters.'};
    const draft=$('#message').value;
    if(draft&&draft.trim()!==input.message.trim())return {error:'The composer contains different unsent text. It has been preserved; send that exact message or let the user finish it first.'};
    if(pending&&(pending.request_id!==input.request_id||pending.message!==input.message))return {error:'Another message has an uncertain pending request. Preserve it and check its request_id before sending new work.'};
    const previous=state.runs.find(r=>r.request_id===input.request_id);
    const result=await mutate('/api/conversation','POST',{request_id:input.request_id,message:input.message,conversation_id:previous?(previous.input_payload?.conversation_id||null):conversationId,chat_task_id:previous?(previous.input_payload?.chat_task_id||null):chatTaskId,apply_immediately:true,keep_chat_scope:previous?!!previous.input_payload?.keep_chat_scope:true,web_enabled:previous?!!previous.input_payload?.web_enabled:true,delegated_task_id:previous?(previous.input_payload?.delegated_task_id||null):null},signal,run=>({...publicRun(run),...(['failed','stale'].includes(run.status)?{error:run.error||'Task updates were not applied.'}:{})}));
    if(['applied','answered'].includes(result.status)){
     if($('#message').value===draft)$('#message').value='';
     if(pending?.request_id===input.request_id)pending=null;
     followTaskChat(state.runs.find(r=>r.request_id===input.request_id)||{status:result.status});renderChat();
    }
    return result;
   }
  },
  {
   name:'resolve_pending_review',
   description:'Apply or dismiss an earlier unsaved conversation plan by run ID. Read its proposal in get_dashboard first. New chat messages already save directly. Server revision checks reject stale plans. Applying persists the plan; dismissing preserves existing tasks.',
   inputSchema:{type:'object',properties:{run_id:uuid,decision:{type:'string',enum:['apply','dismiss']}},required:['run_id','decision'],additionalProperties:false},
   annotations:{readOnlyHint:false,untrustedContentHint:true},
   async execute(input,{signal}={}){
    const invalid=validate(input,['run_id','decision']);if(invalid)return invalid;
    if(!isUUID(input.run_id)||!['apply','dismiss'].includes(input.decision))return {error:'Provide a run UUID and decision apply or dismiss.'};
    const path=input.decision==='apply'?'/api/conversation/'+input.run_id+'/approve':'/api/runs/'+input.run_id+'/reject';
    return mutate(path,'POST',{},signal,publicRun);
   }
  },
  {
   name:'draft_muse_message',
   description:'Place a message in the Muse composer and open chat for the user to review and send. Existing unsent text is preserved.',
   inputSchema:{type:'object',properties:{message:{type:'string',minLength:1,maxLength:10000,description:'The message to stage for user review.'}},required:['message'],additionalProperties:false},
   execute(input){
    const invalid=validate(input,['message']);if(invalid)return invalid;
    if(typeof input.message!=='string'||!input.message.trim()||input.message.length>10000)return {error:'Provide a nonempty message of at most 10,000 characters.'};
    const blocked=uiBlocked();if(blocked)return blocked;
    if($('#message').value)return {error:'The composer already has unsent text. Ask the user to send or clear it first.'};
    $('#message').value=input.message;setMuseOpen(true);
    return {status:'drafted',next_step:'Review the message and choose Send. No model request or task change has been made.'};
   }
  },
  {
   name:'open_task_editor',
   description:'Open a saved task in the visible editor so the user can review and change it.',
   inputSchema:{type:'object',properties:{task_id:{type:'string',minLength:1,description:'A saved task ID from get_dashboard.'}},required:['task_id'],additionalProperties:false},
   execute(input){
    const invalid=validate(input,['task_id']);if(invalid)return invalid;
    if(typeof input.task_id!=='string'||!input.task_id)return {error:'Provide a saved task ID.'};
    const blocked=uiBlocked();if(blocked)return blocked;
    if(!state.tasks.some(task=>task.id===input.task_id))return {error:'Task is not in the loaded workspace. Refresh the dashboard and try again.'};
    openEditor(input.task_id);return {status:'editor_open',next_step:'Review and edit the task, then choose Save changes.'};
   }
  },
  {
   name:'show_pending_reviews',
   description:'Bring pending Muse proposals into view so the user can correct and save them.',
   inputSchema:emptySchema,
   execute(input){
    const invalid=validate(input);if(invalid)return invalid;
    const blocked=uiBlocked();if(blocked)return blocked;
    if(!state.runs.some(run=>run.task_id===null&&run.status==='awaiting_review'))return {error:'No pending proposal is loaded. Refresh the dashboard to check for new proposals.'};
    setMuseOpen(false,{focus:false});$('#reviews').scrollIntoView({block:'start'});$('#reviews').focus({preventScroll:true});
    return {status:'review_visible',next_step:'Inspect the earlier plan and choose Add these tasks, or dismiss it. New chat requests save tasks directly.'};
   }
  }
 ];
 try{for(const tool of tools){controller.signal.throwIfAborted();await document.modelContext.registerTool(tool,{signal:controller.signal});}}
 catch(e){controller.abort();if(webMCPController===controller)webMCPController=null;if(e.name!=='AbortError')console.warn('WebMCP registration failed; dashboard controls remain available.',e);}
}
window.addEventListener('pagehide',()=>{webMCPController?.abort();webMCPController=null;});
window.addEventListener('pageshow',()=>{registerWebMCP();});
registerWebMCP();
// End WebMCP.

let bubbleResizeFrame=null;
window.addEventListener('pagehide',stopBubbleWorld);
document.addEventListener('visibilitychange',()=>{if(document.hidden)stopBubbleWorld();else layoutBubbles();});
window.addEventListener('resize',()=>{cancelAnimationFrame(bubbleResizeFrame);bubbleResizeFrame=requestAnimationFrame(()=>{layoutBubbles();syncFocusHeights();resizeComposer();});});
refresh().catch(error);
window.addEventListener('pageshow',event=>{if(event.persisted)refresh().catch(error);});
setInterval(()=>{if(busy&&pending)api('/api/dashboard').then(data=>{$('#status').textContent=data.runs.some(r=>r.status==='running')?'Muse is planning…':'';}).catch(()=>{});},4000);
</script></body></html>"""
