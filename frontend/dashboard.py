"""Buildless conversation canvas served by FastAPI."""

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Visual Second Brain</title><style>

/* Shared palette and controls. No external fonts or asset requests. */
:root{--paper:#f6f5f0;--panel:#fffefa;--ink:#283c32;--muted:#647269;--line:#dddfd5;--green:#315b43;--soft:#edf1e6;--accent:#dce9b5;--red:#973e32;font-family:ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink);background:var(--paper);font-synthesis:none}

*{box-sizing:border-box}
body{margin:0}
button,input,textarea,select{font:inherit;color:inherit}
button,a,input,textarea,select{outline-offset:4px}
button{cursor:pointer;border:1px solid var(--line);border-radius:9px;padding:10px 15px;background:var(--panel);font-size:13px;font-weight:600;transition:background .15s,border-color .15s}
button:hover{border-color:#9aaa98;background:var(--soft)}
button:disabled{opacity:.55;cursor:wait}
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
.chat{position:fixed;z-index:20;right:28px;bottom:104px;width:400px;max-width:calc(100vw - 56px);max-height:calc(100dvh - 132px);overflow-y:auto;overscroll-behavior:contain;min-width:0;background:linear-gradient(160deg,#fffefa,#f0f3e9);border:1px solid #d7decf;border-radius:24px;padding:22px;box-shadow:0 24px 80px #233c3226,0 4px 16px #233c3210;transform-origin:calc(100% - 24px) bottom;opacity:0;visibility:hidden;pointer-events:none;transform:translateY(16px) scale(.94);transition:opacity .2s ease,transform .24s cubic-bezier(.2,.8,.2,1),visibility .24s}
.chat.is-open{visibility:visible;opacity:1;pointer-events:auto;transform:translateY(0) scale(1);transition-delay:0s}
.muse-launcher{position:fixed;z-index:21;right:28px;bottom:24px;bottom:max(24px,env(safe-area-inset-bottom));display:grid;place-items:center;width:64px;height:64px;padding:0;border-radius:50%;color:#e9f3ce;background:radial-gradient(circle at 30% 20%,#5d8062,#315b43 65%,#244432);border:1px solid #456d4e;box-shadow:0 7px 24px #233c3230,inset 0 1px 1px #ffffff40;transition:transform .2s,box-shadow .2s}
.muse-launcher:hover{color:#f3f9e5;background:radial-gradient(circle at 30% 20%,#6c8c6a,#315b43 65%);transform:translateY(-3px);box-shadow:0 12px 28px #233c3238}
.muse-launcher[aria-expanded="true"]{box-shadow:0 0 0 5px #dfe8d5,0 7px 24px #233c3220}
.muse-launcher svg{width:32px;height:32px;filter:drop-shadow(0 2px 3px #173d2733)}
.launcher-caption{position:absolute;right:76px;white-space:nowrap;background:var(--panel);color:var(--green);border:1px solid var(--line);border-radius:8px;padding:7px 11px;font-size:11px;box-shadow:0 3px 12px #233c3208;pointer-events:none}
.muse-launcher[aria-expanded="true"] .launcher-caption{display:none}
.chat-head-copy{flex:1}.chat-close{width:32px;height:32px;padding:0;border:0;border-radius:50%;background:#e8eddf;font-size:19px;font-weight:400}
.chat-entry{display:inline-block;margin-top:16px;color:var(--green);font-size:12px;background:transparent;border:0;padding:0;text-decoration:underline;text-underline-offset:4px}
.chat-head{margin-bottom:18px;padding-bottom:16px;border-bottom:1px solid #d9ded1}
.muse-mark{display:grid;place-items:center;width:36px;height:36px;background:var(--panel);border:1px solid var(--line);border-radius:50%;font-size:23px;color:var(--green)}
.chat h2{font-size:15px;letter-spacing:-.2px}
.chat-head p{font-size:11px;color:var(--muted);margin-top:3px}
.chat-welcome{padding:8px 2px 22px}
.chat-welcome h3{font-size:20px;font-weight:500;letter-spacing:-.5px;line-height:1.4}
.chat-welcome p{font-size:13px;color:var(--muted);margin-top:10px}
.history{max-height:28vh;overflow:auto;overscroll-behavior:contain}
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
.composer #voice{display:grid;place-items:center;flex:none;width:34px;height:34px;padding:0;border-radius:50%;background:#f2f5ed;border-color:transparent;color:#536b56}.composer #voice svg{width:18px;height:18px}.composer #voice[data-phase="requesting"] svg,.composer #voice[data-phase="transcribing"] svg{animation:mic-spin 1s linear infinite}@keyframes mic-spin{to{transform:rotate(360deg)}}
.composer #voice:hover{background:#e7eedf}
.composer #voice[aria-pressed="true"]{background:#e0ead5;border-color:#8ba687;color:var(--green)}
.voice-note{margin:10px 3px 0;color:var(--muted);font-size:10px;line-height:1.6}
.voice-note summary{cursor:pointer;list-style:none;color:#758071}
.voice-note summary::-webkit-details-marker{display:none}
.voice-note summary::after{content:' ⌄';padding-left:3px}
.voice-note[open] summary::after{content:' ⌃'}
.voice-note .voice-status{margin-top:6px}
.voice-status:empty{display:none}
.status{font-size:12px;color:var(--muted);margin:10px 0;line-height:1.6}
.status:empty{display:none}
.save-hint{font-size:10px;color:var(--muted);margin-top:13px;text-align:center}
.voice-preview{font-size:12px;color:var(--green);margin-top:10px}
.voice-status{font-size:10px;line-height:1.6;margin-top:10px;color:var(--muted);overflow-wrap:anywhere}
#voice[aria-pressed="true"]{background:var(--soft);border-color:var(--green)}
#review-link{display:block;padding:11px 13px;margin-bottom:16px;border:1px solid #c5d2b0;border-radius:9px;background:#e3ebd6;font-size:12px;text-decoration:none}

/* Review uses the wider canvas and keeps approval explicit. */
#reviews{scroll-margin-top:24px}
#reviews:empty{display:none}
.review-heading{font-size:11px;color:var(--green);margin:0 0 12px;font-weight:650;letter-spacing:.2px}
.proposal{border:1px solid #b9cba6;background:#f2f5e9;border-radius:16px;padding:24px;margin-bottom:24px}
.proposal-step{padding-top:18px;border-top:1px solid #d4ddc8;margin-top:18px}
.proposal>.proposal-step:first-child{padding-top:0;border-top:0;margin-top:0}
.proposal .field{margin-top:16px}
.proposal h3{font-size:14px}
.proposal-step .proposal-step{padding:16px;background:#fffefa80;border:1px solid var(--line);border-radius:10px}
.proposal-step textarea{font-size:12px;min-height:65px;margin-top:8px}
.proposal input{font-size:13px}
.proposal .row{flex-wrap:wrap}
.review-actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:22px;padding-top:18px;border-top:1px solid #d4ddc8}
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
.overview-toolbar{display:flex;align-items:center;gap:12px}.draft-label{font-size:11px;color:#735d32;background:#f4ead4;padding:6px 10px;border-radius:20px}
.overview-grid{display:grid;grid-template-columns:1.15fr 1fr;gap:22px}.overview-panel{background:var(--panel);border:1px solid var(--line);border-radius:22px;padding:26px;min-width:0}
.panel-top{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:24px}.panel-top h2{font-size:18px;letter-spacing:-.5px}.panel-kicker{font-size:10px;letter-spacing:1.6px;text-transform:uppercase;color:var(--muted);margin-bottom:6px}
.panel-icon{display:grid;place-items:center;width:38px;height:38px;border-radius:12px;background:var(--soft);font-size:21px;color:var(--green)}
.focus-list{display:grid;gap:12px}.focus-item{padding:18px;background:#f5f5ef;border:1px solid transparent;border-radius:14px;min-width:0}.focus-item:first-child{background:#ecf1df;border-color:#dce5c9}
.focus-context{display:flex;align-items:center;gap:10px;margin-bottom:12px;min-width:0}.focus-rank{font-size:10px;color:var(--muted)}.focus-plan{font-size:11px;color:var(--muted);flex:1;overflow-wrap:anywhere}.focus-fraction{font-size:10px;color:var(--muted);white-space:nowrap}.focus-context progress{width:52px;flex:none}
.next-steps{display:grid;gap:10px}.step-line{display:flex;align-items:flex-start;gap:10px;min-width:0}.step-title{flex:1;min-width:0;text-align:left;padding:0;border:0;background:none;font-size:14px;font-weight:500;line-height:1.6;overflow-wrap:anywhere}.step-title:hover{background:none;text-decoration:underline}.step-title.done{text-decoration:line-through;color:var(--muted)}.step-line .check{margin-top:4px;width:17px;height:17px}.step-state{font-size:10px;color:var(--muted);white-space:nowrap;padding-top:4px}.steps-finished{font-size:12px;color:var(--muted)}.sample-check{padding:0;width:18px;flex:none;border:0;background:transparent;font-size:19px;line-height:23px;font-weight:400}
.focus-details{margin-top:14px;border-top:1px solid #dce2d1;padding-top:10px}.focus-details>summary,.completed-steps>summary{cursor:pointer;font-size:11px;color:var(--muted);list-style:none}.focus-details>summary::after{content:' ＋';float:right}.focus-details[open]>summary::after{content:' −'}.focus-details summary::-webkit-details-marker{display:none}.plan-info{margin-top:12px}.plan-info p{font-size:12px;color:var(--muted);margin-top:10px;white-space:pre-wrap;overflow-wrap:anywhere;max-width:65ch}.focus-meta{display:flex;align-items:center;gap:10px;flex-wrap:wrap;font-size:10px;color:var(--muted)}.focus-details .card-actions{margin-top:12px;padding-top:10px;gap:8px}.focus-details .step-title{font-size:12px}.remaining-steps{display:grid;gap:10px;margin-top:14px}.completed-steps{margin-top:14px}.completed-steps .step-line{margin-top:10px}
.plan-notes{margin:10px 0 0}.plan-step{padding:12px 0;border-bottom:1px solid var(--line)}.plan-step:last-child{border-bottom:0}.step-notes,.step-children{margin:6px 0 0 27px;font-size:11px;color:var(--muted)}.step-notes summary,.step-children summary{cursor:pointer}.step-notes p{margin:8px 0;white-space:pre-wrap;overflow-wrap:anywhere}.step-children .plan-step{padding:10px 0}.all-plans>.plan-step{padding:14px 0}
.panel-foot{margin-top:20px;font-size:11px;color:var(--muted)}.all-plans{margin-top:18px}.all-plans>summary{font-size:12px;cursor:pointer;color:var(--green)}.all-plans .task{padding:12px 0}.quiet-empty{display:flex;flex-direction:column;align-items:flex-start;justify-content:center;min-height:222px;gap:12px;color:var(--muted)}.quiet-empty strong{font-size:17px;font-weight:500;color:var(--ink)}.quiet-empty p{font-size:12px;max-width:260px}.quiet-empty .chat-entry{margin-top:0}
.direction-panel{background:linear-gradient(135deg,#f1f3e9,#f8f8f1)}.goal-item{padding:12px 0;border-bottom:1px solid #dce2d1;display:flex;align-items:center;gap:16px}.goal-item:last-of-type{border-bottom:0}.goal-symbol{width:48px;height:48px;display:grid;place-items:center;border-radius:50%;background:#e1e9d2;color:#496641;font-size:24px;flex:none}.goal-item:nth-child(3) .goal-symbol{background:#eee4d4;color:#886d49}.goal-item:nth-child(4) .goal-symbol{background:#dce7e6;color:#4b706d}.goal-title{font-weight:500;font-size:17px;line-height:1.4}.goal-note{font-size:11px;color:var(--muted);margin-top:5px}.direction-caption{font-size:11px;color:var(--muted);margin-top:22px}
.progress-panel{grid-column:1/-1}.progress-layout{display:grid;grid-template-columns:minmax(0,1fr) 260px;gap:30px}.month-control{display:flex;align-items:center;gap:14px}.month-control strong{font-size:13px;font-weight:500;min-width:112px;text-align:center}.month-control button{padding:4px 9px;background:transparent}.calendar-week,.calendar-grid{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:7px}.calendar-week{margin-bottom:8px}.calendar-week span{font-size:10px;color:var(--muted);padding-left:12px}.calendar-day{height:42px;border-radius:10px;text-align:left;padding:8px 11px;position:relative;background:#f5f5ef;border:1px solid transparent;font-size:11px;font-weight:400}.calendar-day:hover{border-color:#9aaa98}.calendar-day[data-count="1"]{background:#e3eccf}.calendar-day[data-count="2"]{background:#c7d9a6}.calendar-day[data-count="3"]{background:#9bb97a}.calendar-day.is-today{border:1px solid var(--green);font-weight:700}.calendar-day.is-selected{outline:2px solid var(--green);outline-offset:2px}.day-dots{display:block;font-size:13px;letter-spacing:2px;line-height:14px;color:#42613e}.calendar-blank{height:42px}.calendar-day.is-future{background:transparent;color:#92988d}.calendar-legend{display:flex;align-items:center;gap:7px;font-size:10px;color:var(--muted);margin-top:16px}.legend-swatch{width:12px;height:12px;border-radius:3px;background:#f5f5ef}.legend-swatch.mid{background:#e3eccf}.legend-swatch.full{background:#9bb97a}.calendar-note{margin-left:auto}.day-detail{border-left:1px solid var(--line);padding-left:26px}.day-detail h3{font-size:14px;font-weight:500;margin-bottom:8px}.day-total{font-size:38px;letter-spacing:-2px;line-height:1.2}.day-total small{font-size:11px;letter-spacing:0;color:var(--muted);margin-left:7px}.completed-list{list-style:none;padding:0;margin:18px 0 0}.completed-list li{display:flex;gap:9px;align-items:flex-start;font-size:12px;margin-bottom:14px;line-height:1.5}.completed-list li span{color:#648446}.day-detail .muted{font-size:12px;margin-top:16px}
@media(max-width:900px){.overview-grid{gap:16px}.overview-panel{padding:20px}.progress-layout{grid-template-columns:minmax(0,1fr) 190px;gap:20px}.day-detail{padding-left:20px}.canvas{max-width:100%}}
@media(max-width:650px){.overview-grid{grid-template-columns:1fr}.progress-panel{grid-column:auto}.progress-layout{grid-template-columns:1fr}.day-detail{border-left:0;border-top:1px solid var(--line);padding:20px 0 0}.overview-toolbar{align-items:flex-start;gap:8px;flex-wrap:wrap}.calendar-day{height:47px;padding:6px}.calendar-blank{height:47px}.calendar-week span{padding-left:6px}.calendar-grid,.calendar-week{gap:5px}.calendar-note{display:none}.panel-top{flex-wrap:wrap}.month-control{gap:7px}.goal-title{font-size:16px}}

</style></head><body>
<header class="topbar row between"><div class="row"><span class="brand-mark" aria-hidden="true">✳</span><span class="brand">Visual Second Brain</span></div><nav class="row"><button id="refresh" class="small ghost">Refresh</button><a href="/dev">Dev ↗</a><button id="signout" class="small ghost" hidden>Sign out</button></nav></header>
<main><div id="error" class="error" role="alert" hidden></div><div id="notice" class="notice" role="status" aria-live="polite"></div>
<section id="access" class="panel" hidden style="margin-bottom:24px"><form id="access-form" class="panel-body"><h2>Demo access</h2><p class="muted">Enter the app’s demo access token. Access lasts eight hours. Your workspace belongs to this browser; clearing cookies starts a new one.</p><div class="row" style="margin-top:12px"><input id="token" type="password" aria-label="Demo access token" autocomplete="off" maxlength="4096" required><button class="primary">Connect</button></div></form></section>
<div id="layout" class="canvas-layout"><section class="canvas" aria-label="Your saved tasks"><div class="intro row between wrap"><div><h1 class="eyebrow">Your daily overview</h1><time id="workspace-date" class="workspace-date"></time></div><div class="overview-toolbar"><span id="draft-label" class="draft-label" hidden>Design draft · sample data</span><button id="preview-toggle" class="small ghost" type="button">Preview sample day</button></div></div><div id="reviews" tabindex="-1"></div><div id="canvas" aria-live="polite"><div class="canvas-state"><p>Loading your workspace…</p></div></div></section>
<aside id="muse-chat" class="chat" aria-labelledby="muse-title" aria-hidden="true" inert><div class="chat-head row"><span class="muse-mark" aria-hidden="true">✳</span><div class="chat-head-copy"><h2 id="muse-title">Muse</h2><p>A little help finding your next step.</p></div><button id="close-muse" class="chat-close" type="button" data-chat-control aria-label="Close Muse chat">×</button></div><a id="review-link" href="#reviews" hidden>Review proposed changes ↗</a><div id="chat-welcome" class="chat-welcome" hidden><h3>Start with what’s on your mind.</h3><p>A deadline, a project, or a few loose thoughts. Tell Muse what needs doing, and work out a plan together.</p></div><div id="conversation" class="history" aria-live="polite"></div><div id="status" class="status" role="status" aria-live="polite"></div>
<form id="chat-form" class="composer"><label for="message">What’s on your mind?</label><textarea id="message" maxlength="10000" required placeholder="Message Muse…"></textarea><div class="row between"><div class="row wrap" style="margin:0"><button id="voice" class="small" type="button" aria-pressed="false" aria-label="Record voice message" title="Record voice message" aria-describedby="voice-status voice-privacy"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><rect x="9" y="3" width="6" height="12" rx="3"/><path d="M5 11v1a7 7 0 0 0 14 0v-1M12 19v3M9 22h6"/></svg></button><button id="voice-retry" class="small ghost" type="button" hidden>Retry transcription</button><button id="voice-cancel" class="small ghost" type="button" hidden>Cancel</button></div><button id="send" class="primary" type="submit" aria-label="Send message" title="Send message">↑</button></div></form><p id="voice-status" class="voice-status" role="status" aria-live="polite"></p><p id="voice-preview" class="voice-preview" hidden></p><details class="voice-note"><summary>Voice uses Meta transcription</summary><p id="voice-privacy" class="voice-status">Record up to one minute. Stop &amp; transcribe sends audio to Meta for transcription. Review the text before sending. This app does not save audio.</p></details><p class="save-hint">Muse proposes. You review and save.</p></aside></div></main>
<button id="muse-launcher" class="muse-launcher" type="button" data-chat-control aria-label="Open Muse chat" aria-expanded="false" aria-controls="muse-chat"><svg viewBox="0 0 40 40" fill="none" aria-hidden="true"><path d="M20 3C22 14 26 18 37 20C26 22 22 26 20 37C18 26 14 22 3 20C14 18 18 14 20 3Z" fill="currentColor"/><circle cx="31" cy="8" r="2.5" fill="currentColor" opacity=".65"/></svg><span class="launcher-caption" aria-hidden="true">Talk to Muse</span></button>
<dialog id="edit-dialog"><form id="edit-form"><div class="row between" style="margin-bottom:20px"><h2 style="margin:0">Edit task</h2><button type="button" id="close-edit" class="small" aria-label="Close editor">✕</button></div><input id="edit-id" type="hidden"><div class="field"><label for="edit-title">Task</label><input id="edit-title" required maxlength="300"></div><div class="field"><label for="edit-description">Details</label><textarea id="edit-description" maxlength="10000"></textarea></div><div class="grid2"><div class="field"><label for="edit-deadline">Due date</label><input id="edit-deadline" type="date"></div><div class="field"><label for="edit-importance">Importance</label><select id="edit-importance" data-level-select></select></div></div><div class="field"><label for="edit-status">Status</label><select id="edit-status"><option value="pending">Pending</option><option value="in_progress">In progress</option><option value="completed">Completed</option></select></div><button class="primary" type="submit">Save changes</button></form></dialog>
<script>
'use strict';
const $=s=>document.querySelector(s),esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels={very_low:'Very low',low:'Low',medium:'Medium',high:'High',very_high:'Very high'};
let state={tasks:[],messages:[],runs:[]},ranges={},busy=false,pending=null,editVersion=null;
const drafts=new Map();
// A visit owns its chat in memory; saved dashboard records stay in the workspace.
let conversationId=crypto.randomUUID();
function newChat(){conversationId=crypto.randomUUID();pending=null;$('#chat-form').reset();}
function chatRuns(){return state.runs.filter(r=>r.input_payload?.conversation_id===conversationId);}
const today=new Date();$('#workspace-date').dateTime=[today.getFullYear(),String(today.getMonth()+1).padStart(2,'0'),String(today.getDate()).padStart(2,'0')].join('-');$('#workspace-date').textContent=today.toLocaleDateString(undefined,{weekday:'long',month:'short',day:'numeric'});
document.querySelectorAll('[data-level-select]').forEach(el=>el.innerHTML='<option value="">Let Muse assess</option>'+Object.entries(labels).map(([k,v])=>`<option value="${k}">${v}</option>`).join(''));
function level(t){return t.user_importance_level||Object.keys(ranges).find(k=>t.importance_score!==null&&t.importance_score>=ranges[k].min&&t.importance_score<=ranges[k].max)||'';}
function badge(t){return `<span class="pill ${esc(level(t))}">${esc(labels[level(t)]||'Unassessed')}</span>`;}
function error(e){$('#error').textContent=e.message||'Something went wrong. Your draft is still here.';$('#error').hidden=false;}
async function api(path,method='GET',body){let r;try{r=await fetch(path,{method,credentials:'same-origin',headers:{'Content-Type':'application/json'},...(body===undefined?{}:{body:JSON.stringify(body)})});}catch{throw Error('Could not reach the server. Your draft is preserved; try again.');}let data;try{data=await r.json();}catch{throw Error('The server returned an unreadable response. Your draft is preserved.');}if(!r.ok){if(r.status===401){endVoice({discard:true});$('#access').hidden=false;$('#signout').hidden=true;newChat();state={tasks:[],messages:[],runs:[]};render();}throw Error((data.error?.message||'Request failed')+(r.status===409?' Refresh to see the latest state.':''));}return data;}
function setBusy(value){if(value)endVoice({discard:true});busy=value;document.querySelectorAll('button:not([data-chat-control]),input,textarea,select').forEach(el=>el.disabled=value);$('#send').textContent=value?'…':'↑';syncVoice();}
async function refresh(){const [data,levels,health]=await Promise.all([api('/api/dashboard'),api('/api/importance-levels'),api('/health')]);state=data;const runIds=new Set(chatRuns().map(r=>r.id));state.messages=state.messages.filter(m=>runIds.has(m.run_id));ranges=levels;$('#access').hidden=true;$('#signout').hidden=!health.demo_access_required;render();}
async function action(work,success){if(busy)return;setBusy(true);$('#error').hidden=true;$('#notice').textContent='';try{await work();await refresh();if(success)$('#notice').textContent=success;}catch(e){$('#status').textContent='';error(e);}finally{setBusy(false);}}
function stepProgress(task){const steps=state.tasks.filter(t=>t.parent_task_id===task.id);if(!steps.length)return '';const done=steps.filter(t=>t.status==='completed').length;return `<div class="task-progress"><progress value="${done}" max="${steps.length}" aria-label="Completed steps for ${esc(task.title)}"></progress><span>${done} of ${steps.length} steps complete</span></div>`;}
function taskRow(t){
 const children=orderedChildren(t.id),details=t.description||t.deadline;
 return `<div class="plan-step"><div class="step-line"><input class="check" type="checkbox" data-complete="${esc(t.id)}" aria-label="Mark ${esc(t.title)} ${t.status==='completed'?'pending':'complete'}" ${t.status==='completed'?'checked':''}><button class="step-title ${t.status==='completed'?'done':''}" data-edit="${esc(t.id)}">${esc(t.title)}</button>${t.status==='in_progress'?'<span class="step-state">In progress</span>':''}</div>${details?`<details class="step-notes"><summary>Details</summary>${t.description?`<p>${esc(t.description)}</p>`:''}${t.deadline?`<span>Due ${esc(t.deadline)}</span>`:''}</details>`:''}${children.length?`<details class="step-children"><summary>${children.filter(c=>c.status==='completed').length}/${children.length} steps</summary>${children.map(taskRow).join('')}</details>`:''}</div>`;
}
// Sample mode is an isolated visual draft. It never replaces API state or writes records.
let samplePreview=new URLSearchParams(window.location.search).get('draft')==='1';
const overviewToday=new Date();overviewToday.setHours(0,0,0,0);
let calendarMonth=new Date(overviewToday.getFullYear(),overviewToday.getMonth(),1),selectedDay=localDay(overviewToday);
function localDay(d){return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;}
const sampleFocus=[
 {id:'sample-1',title:'Finish the homework outline',note:'Due Sunday',done:2,total:4},
 {id:'sample-2',title:'Polish the dashboard',note:'In progress',done:1,total:3},
 {id:'sample-3',title:'Make time for a walk',note:'A little space for yourself',done:0,total:1}
];
const sampleGoals=[{symbol:'↗',title:'Build something useful',note:'A product that gives time back'},{symbol:'◎',title:'Keep learning, every week',note:'Make curiosity a habit'},{symbol:'♧',title:'A calmer, healthier routine',note:'Leave room for life outside work'}];
const sampleHistory={};
for(let day=1;day<=overviewToday.getDate();day++){
 const date=new Date(overviewToday.getFullYear(),overviewToday.getMonth(),day);
 const count=[0,2,1,3,0,1,2][date.getDay()];
 sampleHistory[localDay(date)]=['Review assignment brief','Sketch the dashboard','Read one chapter'].slice(0,count);
}
sampleHistory[localDay(overviewToday)]=['Review assignment brief','Sketch the dashboard'];
function orderedChildren(id,tasks=state.tasks){return tasks.filter(t=>t.parent_task_id===id).sort((a,b)=>(a.position??0)-(b.position??0));}
function leafSteps(id,tasks=state.tasks){return orderedChildren(id,tasks).flatMap(t=>orderedChildren(t.id,tasks).length?leafSteps(t.id,tasks):[t]);}
function focusStep(t,sample=false){
 const done=t.status==='completed';
 return `<div class="step-line ${done?'is-done':''}">${sample?`<button class="sample-check" data-sample-step="${esc(t.id)}" aria-label="${done?'Reopen':'Complete'} sample step ${esc(t.title)}">${done?'✓':'○'}</button>`:`<input class="check" type="checkbox" data-complete="${esc(t.id)}" aria-label="Mark ${esc(t.title)} ${done?'pending':'complete'}" ${done?'checked':''}>`}${sample?`<span class="step-title ${done?'done':''}">${esc(t.title)}</span>`:`<button class="step-title ${done?'done':''}" data-edit="${esc(t.id)}">${esc(t.title)}</button>`}</div>`;
}
function overviewFocus(t,i,tasks=state.tasks,sample=false){
 const steps=leafSteps(t.id,tasks),unfinished=steps.filter(c=>c.status!=='completed'),visible=unfinished.slice(0,3),done=steps.filter(c=>c.status==='completed').length;
 const actions=steps.length?visible:[t],completeSteps=steps.filter(c=>c.status==='completed');
 return `<article class="focus-item"><div class="focus-context"><span class="focus-rank">0${i+1}</span><span class="focus-plan">${esc(t.title)}</span>${steps.length?`<span class="focus-fraction">${done}/${steps.length}</span><progress value="${done}" max="${steps.length}" aria-label="Completed steps for ${esc(t.title)}"></progress>`:''}</div><div class="next-steps">${actions.map(c=>focusStep(c,sample)).join('')||'<span class="steps-finished">All steps checked off · finish the plan when ready.</span>'}</div><details class="focus-details"><summary>${unfinished.length>3?`All ${steps.length} steps`:'Plan details'}</summary><div class="plan-info"><div class="focus-meta">${sample?'<span>Sample plan</span>':badge(t)}${t.deadline?`<span>Due ${esc(t.deadline)}</span>`:''}${t.status==='in_progress'?'<span>In progress</span>':''}</div>${t.description?`<details class="step-notes plan-notes"><summary>Notes</summary><p>${esc(t.description)}</p></details>`:''}</div>${unfinished.length>3?`<div class="remaining-steps">${unfinished.slice(3).map(c=>focusStep(c,sample)).join('')}</div>`:''}${completeSteps.length?`<details class="completed-steps"><summary>Completed · ${completeSteps.length}</summary>${completeSteps.map(c=>focusStep(c,sample)).join('')}</details>`:''}<div class="card-actions">${sample?`<button class="small ghost" data-sample-complete="${esc(t.id)}">${t.completed?'Reopen plan':'Complete plan'}</button>`:`<button class="small ghost" data-edit="${esc(t.id)}">Edit plan</button><button class="small ghost" data-toggle="${esc(t.id)}">Complete plan</button>`}</div></details></article>`;
}
const sampleStepNames=[['Read the assignment brief','Collect references','Write the outline','Review the outline'],['Sketch the layout','Refine the priority cards','Check the mobile layout'],['Walk around the neighborhood']];
const sampleSteps=sampleFocus.flatMap((t,i)=>sampleStepNames[i].map((title,j)=>({id:`${t.id}-step-${j}`,parent_task_id:t.id,title,position:j,status:j<t.done?'completed':'pending'})));
function renderOverview(){
 $('#draft-label').hidden=!samplePreview;$('#preview-toggle').textContent=samplePreview?'Back to my workspace':'Preview sample day';$('#preview-toggle').setAttribute('aria-pressed',String(samplePreview));
 const roots=state.tasks.filter(t=>!t.parent_task_id),active=roots.filter(t=>t.status!=='completed').sort((a,b)=>(b.importance_score??-1)-(a.importance_score??-1));
 const focus=samplePreview?sampleFocus.map((t,i)=>overviewFocus({...t,status:t.completed?'completed':'pending'},i,sampleSteps,true)).join(''):active.slice(0,3).map((t,i)=>overviewFocus(t,i)).join('');
 const allPlans=!samplePreview&&roots.length?`<details class="all-plans"><summary>All saved plans · ${roots.length}</summary>${roots.map(taskRow).join('')}</details>`:'';
 const goals=samplePreview?sampleGoals.map(g=>`<div class="goal-item"><span class="goal-symbol" aria-hidden="true">${g.symbol}</span><div><div class="goal-title">${esc(g.title)}</div><div class="goal-note">${esc(g.note)}</div></div></div>`).join(''):`<div class="quiet-empty"><span class="goal-symbol" aria-hidden="true">↗</span><strong>What are you working toward?</strong><p>Your bigger goals will live here.</p><span class="panel-foot">Goal data isn’t connected in this draft.</span></div>`;
 $('#canvas').innerHTML=`<div class="overview-grid"><section class="overview-panel" aria-labelledby="focus-title"><div class="panel-top"><div><p class="panel-kicker">Make room for these</p><h2 id="focus-title">Your top 3</h2></div><span class="panel-icon" aria-hidden="true">◎</span></div><div class="focus-list">${focus||`<div class="quiet-empty"><strong>${roots.length?'A little breathing room.':'One thing at a time.'}</strong><p>${roots.length?'All your saved plans are complete.':'Tell Muse what needs doing to find your first priorities.'}</p><button class="chat-entry" type="button" data-open-muse>Talk to Muse ↗</button></div>`}</div>${allPlans}<p class="panel-foot">${samplePreview?'Sample priorities · try checking one off':active.length?'Ranked by importance':''}</p></section><section class="overview-panel direction-panel" aria-labelledby="direction-title"><div class="panel-top"><div><p class="panel-kicker">The bigger picture</p><h2 id="direction-title">Long-term focus</h2></div><span class="panel-icon" aria-hidden="true">↗</span></div>${goals}${samplePreview?'<p class="direction-caption">A direction to grow in. No deadline needed.</p>':''}</section><section class="overview-panel progress-panel" aria-labelledby="progress-title"><div class="panel-top"><div><p class="panel-kicker">Small steps add up</p><h2 id="progress-title">Your progress</h2></div><div class="month-control"><button type="button" data-month="-1" aria-label="Previous month">‹</button><strong>${calendarMonth.toLocaleDateString(undefined,{month:'long',year:'numeric'})}</strong><button type="button" data-month="1" aria-label="Next month">›</button></div></div><div class="progress-layout"><div>${renderCalendar()}<div class="calendar-legend"><span>Less</span><i class="legend-swatch"></i><i class="legend-swatch mid"></i><i class="legend-swatch full"></i><span>More completed</span><span class="calendar-note">${samplePreview?'Sample completion history':'Completion history not connected'}</span></div></div><aside class="day-detail" aria-label="Selected day">${renderDayDetail()}</aside></div></section></div>`;
}
function renderCalendar(){
 const year=calendarMonth.getFullYear(),month=calendarMonth.getMonth(),offset=(calendarMonth.getDay()+6)%7,days=new Date(year,month+1,0).getDate();
 let cells='<div class="calendar-blank" aria-hidden="true"></div>'.repeat(offset);
 for(let day=1;day<=days;day++){
  const date=new Date(year,month,day),key=localDay(date),items=samplePreview?(sampleHistory[key]||[]):[],today=key===localDay(overviewToday),future=date>overviewToday;
  const description=samplePreview?`${items.length} completed`:'completion history unavailable';
  cells+=`<button type="button" class="calendar-day ${today?'is-today':''} ${key===selectedDay?'is-selected':''} ${future?'is-future':''}" data-day="${key}" data-count="${Math.min(items.length,3)}" aria-label="${date.toLocaleDateString(undefined,{month:'long',day:'numeric',year:'numeric'})}, ${description}" aria-pressed="${key===selectedDay}" ${today?'aria-current="date"':''}>${day}<span class="day-dots" aria-hidden="true">${'•'.repeat(Math.min(items.length,3))}</span></button>`;
 }
 return `<div class="calendar-week" aria-hidden="true">${['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].map(d=>`<span>${d}</span>`).join('')}</div><div class="calendar-grid" role="group" aria-label="Completion calendar">${cells}</div>`;
}
function renderDayDetail(){
 const date=new Date(selectedDay+'T00:00:00'),title=selectedDay===localDay(overviewToday)?'Today':date.toLocaleDateString(undefined,{month:'short',day:'numeric'}),items=samplePreview?(sampleHistory[selectedDay]||[]):[];
 return `<h3>${title}</h3>${samplePreview?`<div class="day-total">${items.length}<small>completed</small></div>${items.length?`<ul class="completed-list">${items.map(t=>`<li><span aria-hidden="true">✓</span>${esc(t)}</li>`).join('')}</ul>`:'<p class="muted">No sample completions.</p>'}`:'<p class="muted">Completed work will appear here once history is connected.</p>'}`;
}
function handleOverviewClick(e){
 const day=e.target.closest('[data-day]'),month=e.target.closest('[data-month]'),sample=e.target.closest('[data-sample-complete]'),step=e.target.closest('[data-sample-step]');
 if(day){selectedDay=day.dataset.day;renderOverview();$('#canvas').querySelector(`[data-day="${selectedDay}"]`)?.focus();return true;}
 if(month){const direction=Number(month.dataset.month);calendarMonth=new Date(calendarMonth.getFullYear(),calendarMonth.getMonth()+direction,1);selectedDay=localDay(calendarMonth);renderOverview();$('#canvas').querySelector(`[data-month="${direction}"]`)?.focus();return true;}
 if(step&&samplePreview){const task=sampleSteps.find(t=>t.id===step.dataset.sampleStep);task.status=task.status==='completed'?'pending':'completed';const key=localDay(overviewToday);sampleHistory[key]=sampleHistory[key].filter(t=>t!==task.title);if(task.status==='completed')sampleHistory[key].push(task.title);renderOverview();return true;}
 if(sample&&samplePreview){const task=sampleFocus.find(t=>t.id===sample.dataset.sampleComplete);task.completed=!task.completed;const key=localDay(overviewToday);sampleHistory[key]=sampleHistory[key].filter(t=>t!==task.title);if(task.completed)sampleHistory[key].push(task.title);renderOverview();$('#canvas').querySelector(`[data-sample-complete="${task.id}"]`)?.focus();return true;}
 return false;
}
$('#preview-toggle').onclick=()=>{samplePreview=!samplePreview;calendarMonth=new Date(overviewToday.getFullYear(),overviewToday.getMonth(),1);selectedDay=localDay(overviewToday);renderOverview();};

function render(){
 $('#chat-welcome').hidden=state.messages.length>0;
 renderOverview();
 $('#conversation').innerHTML=state.messages.slice(-40).map(m=>{const run=state.runs.find(r=>r.id===m.run_id),status=run?.status;const label=m.role==='user'?'YOU':status==='awaiting_review'?'MUSE · PROPOSAL, NOT SAVED':status==='superseded'?'MUSE · EARLIER PROPOSAL':status==='stale'?'MUSE · OUTDATED PROPOSAL':'MUSE';return `<div class="chat-message ${m.role==='user'?'user':''}"><small>${label}</small>${esc(m.content)}</div>`;}).join('');$('#conversation').scrollTop=$('#conversation').scrollHeight;
 const running=chatRuns().some(r=>r.status==='running');$('#status').textContent=running?'Muse is planning…':chatRuns().at(-1)?.status==='failed'?'The last request failed. Your saved work is unchanged.':'';
 const reviews=state.runs.filter(r=>r.task_id===null&&r.status==='awaiting_review');
 $('#review-link').hidden=!reviews.length;$('#review-link').textContent=reviews.length===1?'A proposal is ready to review ↗':reviews.length+' proposals ready to review ↗';
 $('#reviews').innerHTML=reviews.map(r=>{if(!drafts.has(r.id))drafts.set(r.id,structuredClone(r.proposal));const p=drafts.get(r.id);return `<div class="review-heading">Proposed changes · not saved yet</div><section class="proposal" data-run="${r.id}">${p.tasks.map((t,i)=>`<div data-object="${i}" class="proposal-step"><div class="row between"><h3>${t.task_id?'Update task':'New task'}</h3>${badge(t)}<button class="small ghost" data-remove-task="${i}">Remove</button></div><div class="field"><label for="title-${r.id}-${i}">Task</label><input id="title-${r.id}-${i}" data-key="title" maxlength="300" value="${esc(t.title)}"></div><div class="field"><label for="desc-${r.id}-${i}">Details</label><textarea id="desc-${r.id}-${i}" data-key="description" maxlength="10000">${esc(t.description)}</textarea></div><div class="field"><label for="date-${r.id}-${i}">Due date · confirm before saving</label><input id="date-${r.id}-${i}" data-key="deadline" type="date" value="${esc(t.deadline||'')}"></div>${t.subtasks.map((c,j)=>`<div class="proposal-step" data-child="${j}"><div class="row between"><label for="step-${r.id}-${i}-${j}">Step ${j+1}</label><button class="small ghost" data-remove-step="${j}">Remove</button></div><input id="step-${r.id}-${i}-${j}" data-key="title" maxlength="300" value="${esc(c.title)}"><textarea data-key="description" aria-label="Step ${j+1} details" maxlength="10000">${esc(c.description)}</textarea></div>`).join('')}${t.task_id&&t.subtasks.length?'<p class="muted">These steps will be added to the existing plan.</p>':''}</div>`).join('')}<div class="review-actions"><button class="primary small" data-save="${r.id}">Save reviewed plan</button><button class="small" data-reject="${r.id}">Dismiss</button></div></section>`;}).join('');
}
$('#chat-form').onsubmit=e=>{e.preventDefault();if(voiceSession||busy)return;const message=$('#message').value.trim();if(!message)return;if(message.length>10000){error(Error('Shorten your message to 10,000 characters before sending. Your transcript is preserved.'));return;}const latest=chatRuns().filter(r=>r.task_id===null&&r.status==='awaiting_review').at(-1),review_draft=latest?(drafts.get(latest.id)||latest.proposal):null;const input={message,review_draft};if(!pending||JSON.stringify({message:pending.message,review_draft:pending.review_draft})!==JSON.stringify(input))pending={request_id:crypto.randomUUID(),conversation_id:conversationId,...structuredClone(input)};const request=pending;action(async()=>{$('#status').textContent='Muse is planning…';const run=await api('/api/conversation','POST',request);if(run.status==='running')throw Error('Muse is still planning. Refresh to check, or retry the same message.');pending=null;await refresh();if(run.status==='failed')throw Error(run.error||'Muse could not reply. Try again.');if(run.status==='stale')throw Error('Your workspace changed during planning. Send again for a fresh proposal.');$('#message').value='';},'');};
$('#message').addEventListener('keydown',event=>{if(event.key!=='Enter'||!event.metaKey||event.isComposing)return;event.preventDefault();if(event.repeat||busy||voiceSession)return;$('#chat-form').requestSubmit();});
$('#send').title='Send message (⌘ Enter)';$('#send').setAttribute('aria-keyshortcuts','Meta+Enter');
$('#reviews').oninput=e=>{const section=e.target.closest('[data-run]'),object=e.target.closest('[data-object]');if(!section||!object||!e.target.dataset.key)return;let item=drafts.get(section.dataset.run).tasks[+object.dataset.object];const child=e.target.closest('[data-child]');if(child)item=item.subtasks[+child.dataset.child];item[e.target.dataset.key]=e.target.dataset.key==='deadline'?(e.target.value||null):e.target.value;};
$('#reviews').onclick=e=>{if(busy)return;const section=e.target.closest('[data-run]');if(!section)return;const id=section.dataset.run,p=drafts.get(id),object=e.target.closest('[data-object]');if(e.target.closest('[data-remove-task]')){p.tasks.splice(+object.dataset.object,1);render();}else if(e.target.closest('[data-remove-step]')){p.tasks[+object.dataset.object].subtasks.splice(+e.target.dataset.removeStep,1);render();}else if(e.target.closest('[data-save]')){if(!p.tasks.length||p.tasks.some(t=>!t.title.trim()||t.subtasks.some(c=>!c.title.trim()))){error(Error('Keep at least one task and give each task and step a title.'));return;}action(()=>api('/api/conversation/'+id+'/approve','POST',{proposal:p}),'Your reviewed plan is saved.');}else if(e.target.closest('[data-reject]'))action(()=>api('/api/runs/'+id+'/reject','POST'),'Proposal dismissed.');};
function openEditor(id){const t=state.tasks.find(t=>t.id===id);editVersion=t.version;$('#edit-id').value=t.id;$('#edit-title').value=t.title;$('#edit-description').value=t.description;$('#edit-deadline').value=t.deadline||'';$('#edit-importance').value=t.user_importance_level||'';$('#edit-status').value=t.status;$('#edit-dialog').showModal();}
function complete(id,value){const t=state.tasks.find(t=>t.id===id);action(()=>api('/api/tasks/'+id,'PATCH',{expected_version:t.version,status:value?'completed':'pending'}),'Task updated.');}
$('#canvas').onclick=e=>{if(handleOverviewClick(e)||samplePreview)return;if(busy)return;const edit=e.target.closest('[data-edit]'),toggle=e.target.closest('[data-toggle]');if(edit)openEditor(edit.dataset.edit);if(toggle)complete(toggle.dataset.toggle,state.tasks.find(t=>t.id===toggle.dataset.toggle).status!=='completed');};
$('#canvas').onchange=e=>{if(samplePreview)return;const el=e.target.closest('[data-complete]');if(!el)return;const checked=el.checked;el.checked=!checked;complete(el.dataset.complete,checked);};
$('#edit-form').onsubmit=e=>{e.preventDefault();action(async()=>{await api('/api/tasks/'+$('#edit-id').value,'PATCH',{expected_version:editVersion,title:$('#edit-title').value,description:$('#edit-description').value,deadline:$('#edit-deadline').value||null,user_importance_level:$('#edit-importance').value||null,status:$('#edit-status').value});$('#edit-dialog').close();},'Your correction is saved. Muse will use it next time.');};$('#close-edit').onclick=()=>$('#edit-dialog').close();
$('#refresh').onclick=()=>action(async()=>{},'Saved state refreshed.');$('#access-form').onsubmit=e=>{e.preventDefault();const token=$('#token').value;action(async()=>{await api('/api/session','POST',{token});newChat();$('#token').value='';},'Connected.');};
$('#signout').onclick=async()=>{if(busy)return;endVoice({discard:true});setBusy(true);$('#error').hidden=true;try{await api('/api/session','DELETE');newChat();state={tasks:[],messages:[],runs:[]};drafts.clear();pending=null;$('#chat-form').reset();$('#edit-form').reset();$('#edit-dialog').close();render();$('#access').hidden=false;$('#signout').hidden=true;$('#notice').textContent='Signed out.';}catch(e){error(e);}finally{setBusy(false);}};
// Muse disclosure: keep the existing DOM, conversation, and unsent draft mounted.
function setMuseOpen(open,{focus=true}={}){
 const panel=$('#muse-chat'),launcher=$('#muse-launcher');
 panel.classList.toggle('is-open',open);panel.inert=!open;panel.setAttribute('aria-hidden',String(!open));
 launcher.setAttribute('aria-expanded',String(open));launcher.setAttribute('aria-label',open?'Close Muse chat':'Open Muse chat');
 if(!open&&voiceSession)endVoice({discard:true,message:'Voice input stopped when chat closed. Your typed draft is kept.'});
 if(focus){if(open)(busy?$('#close-muse'):$('#message')).focus({preventScroll:true});else launcher.focus({preventScroll:true});}
}
$('#muse-launcher').onclick=()=>setMuseOpen($('#muse-launcher').getAttribute('aria-expanded')!=='true');
$('#close-muse').onclick=()=>setMuseOpen(false);
document.addEventListener('click',event=>{if(event.target.closest('[data-open-muse]'))setMuseOpen(true);});
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&$('#muse-launcher').getAttribute('aria-expanded')==='true'&&!$('#edit-dialog').open){event.preventDefault();setMuseOpen(false);}});
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
$('#voice-status').textContent=voiceAvailable?'':!window.isSecureContext?'Voice input needs HTTPS or localhost. You can still type your message.':'Microphone recording is unavailable in this browser. You can still type your message.';
syncVoice();
// End voice input.

// WebMCP: browser-agent access to saved state and reviewable UI actions.
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
  if($('#edit-dialog').open)return {error:'Save or close the open task editor first; its unsaved changes are preserved.'};
 }
 const tools=[
  {
   name:'get_dashboard',
   description:'Read the current saved tasks and proposal statuses from this browser workspace. Use to understand the user’s plans before offering a next step.',
   inputSchema:emptySchema,annotations:{readOnlyHint:true},
   async execute(input,{signal}={}){
    const invalid=validate(input);if(invalid)return invalid;
    try{
     const response=await fetch('/api/dashboard',{credentials:'same-origin',signal});
     if(!response.ok)return {error:response.status===401?'Connect using the visible demo access form first.':'Could not load saved state. Retry when the server is available.',status:response.status};
     const data=await response.json();signal?.throwIfAborted();
     return {tasks:data.tasks.map(({id,parent_task_id,title,description,deadline,user_importance_level,status,version})=>({id,parent_task_id,title,description,deadline,user_importance_level,status,version})),reviews:data.runs.filter(run=>run.task_id===null&&run.status==='awaiting_review').map(run=>({id:run.id,status:run.status})),source:'Saved server state; unsaved interface edits are not included.'};
    }catch(e){if(signal?.aborted)throw e;return {error:'Could not read saved state. Retry when the server is available.'};}
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
    return {status:'review_visible',next_step:'Review the proposal and choose Save reviewed plan when ready.'};
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

if(samplePreview)renderOverview();
refresh().catch(error);
window.addEventListener('pageshow',event=>{if(event.persisted)refresh().catch(error);});
setInterval(()=>{if(busy&&pending)api('/api/dashboard').then(data=>{$('#status').textContent=data.runs.some(r=>r.status==='running')?'Muse is planning…':'';}).catch(()=>{});},4000);
</script></body></html>"""
