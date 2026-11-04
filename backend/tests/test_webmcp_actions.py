"""Execute shipped browser tools against the real API using a JSON fetch bridge.

Browser discovery is simulated; authentication, validation, persistence, audits,
and model-run orchestration use FastAPI and SQLite. Muse is an explicit fixture.
"""

import json
import re
import runpy
import shutil
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest


@pytest.mark.parametrize("decision", ["apply", "dismiss"])
def test_agent_journey_without_browser_controls(setup, decision):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required for WebMCP action checks")
    clients, muse, _ = setup
    client = clients(token="test-token")
    assert client.post("/api/session", json={"token": "test-token"}).status_code == 200
    model_calls = []
    handoff = {
        "handler": "muse",
        "reason": "Can prepare a document",
        "requirements": ["Meeting notes"],
        "done_when": "Agenda is ready",
    }

    def respond(snapshot, message):
        model_calls.append((snapshot, message))
        if message == "fail":
            return {"invalid": True}
        return {
            "reply": "Plan saved for " + message,
            "tasks": [
                {
                    "task_id": None,
                    "title": message,
                    "description": "",
                    "deadline": None,
                    "importance_score": 65,
                    "handoff": handoff,
                    "subtasks": [],
                }
            ],
        }

    muse.converse = respond
    review = client.post(
        "/api/conversation",
        json={
            "request_id": str(uuid4()),
            "message": "Earlier plan",
        },
    ).json()
    assert review["status"] == "awaiting_review"
    foreign = clients("bob").post("/api/tasks", json={"title": "Private"}).json()
    page = runpy.run_path(
        str(Path(__file__).resolve().parents[2] / "frontend/dashboard.py")
    )["PAGE"]
    controller = (
        "// WebMCP:" + page.split("// WebMCP:", 1)[1].split("// End WebMCP.", 1)[0]
    )
    helpers = "\n".join(
        re.search(pattern, page)[0]
        for pattern in [
            r"function rootTaskId.*?\n",
            r"function runChatScope.*?\n",
            r"(?s)function followTaskChat\(run\).*?\n}",
        ]
    )
    controller = helpers + controller
    script = (
        r"""
const assert=require('node:assert/strict'),vm=require('node:vm'),{randomUUID}=require('node:crypto');
const lines=require('node:readline').createInterface({input:process.stdin});
let receive;lines.on('line',line=>receive(JSON.parse(line)));
const tools=new Map(),elements=new Map(),requests=[];
const $=key=>{if(!elements.has(key))elements.set(key,{hidden:true,value:'',open:false});return elements.get(key);};
let state={tasks:[],runs:[]},busy=false,voiceSession=null,pending=null,dirty=[],mode='normal',refreshFailed=false,refreshes=0;
let conversationId=null,chatTaskId=null;
const document={querySelectorAll:()=>dirty,modelContext:{async registerTool(tool){tools.set(tool.name,tool);}}};
const window={isSecureContext:true,addEventListener(){}};
function setBusy(value){busy=value;}
async function fetch(path,options={}){
 options.signal?.throwIfAborted();
 assert.equal(options.credentials,'same-origin');
 requests.push({path,method:options.method||'GET',body:options.body?JSON.parse(options.body):undefined});
 const response=await new Promise(resolve=>{receive=resolve;process.stdout.write(JSON.stringify(requests.at(-1))+'\n');});
 if(mode==='lost-response'&&options.method){mode='normal';throw Error('Connection lost after sending');}
 return {ok:response.status>=200&&response.status<300,status:response.status,json:async()=>response.body};
}
const chatDrafts=new Map(),chatRequests=new Map();function renderChat(){}function assessSubtasks(){}
async function refresh(){if(refreshFailed)throw Error('Refresh offline');refreshes++;state=await (await fetch('/api/dashboard',{credentials:'same-origin'})).json();}
function openEditor(){throw Error('No browser editor should be needed');}
function setMuseOpen(){throw Error('No browser chat controls should be needed');}
CONTROLLER
const call=(name,input={},options)=>tools.get(name).execute(input,options);
(async()=>{
 await new Promise(resolve=>setImmediate(resolve));assert.equal(tools.size,8);
 let dashboard=await call('get_dashboard');assert.equal(dashboard.reviews.length,1);
 assert.equal(dashboard.reviews[0].proposal.tasks[0].handoff.handler,'muse');
 assert.equal(dashboard.reviews[0].proposal.tasks[0].importance_score,undefined);
 assert.equal((await call('resolve_pending_review',{run_id:dashboard.reviews[0].id,decision:DECISION})).status,DECISION==='apply'?'applied':'rejected');
 const created=await call('create_task',{title:'Meeting',description:'Keep these notes',handoff:HANDOFF});
 assert.equal(created.status,'saved');assert.equal(created.task.user_id,undefined);assert.equal(created.task.importance_score,undefined);
 const child=await call('create_task',{title:'Draft agenda',parent_task_id:created.task.id});
 assert.equal(child.task.parent_task_id,created.task.id);
 let updated=await call('update_task',{task_id:created.task.id,expected_version:created.task.version,title:'Launch review',deadline:'2026-11-04',user_importance_level:'high'});
 assert.equal(updated.task.title,'Launch review');assert.equal(updated.task.description,'Keep these notes');assert.deepEqual(updated.task.handoff,HANDOFF);
 const stale=await call('update_task',{task_id:created.task.id,expected_version:created.task.version,title:'Stale overwrite'});
 assert.equal(stale.status,409);assert.equal(stale.outcome,'rejected');
 assert.equal((await call('update_task',{task_id:FOREIGN,expected_version:1,status:'completed'})).status,404);
 updated=await call('update_task',{task_id:child.task.id,expected_version:child.task.version,status:'completed'});assert.equal(updated.task.status,'completed');
 updated=await call('update_task',{task_id:child.task.id,expected_version:updated.task.version,status:'pending'});assert.equal(updated.task.status,'pending');
 // Bad inputs never reach the backend.
 const before=requests.length;
 for(const input of [{title:''},{title:'x',deadline:'2026-02-30'},{title:'x',user_importance_level:'urgent'},{title:'x',handoff:{}},{title:'x',parent_task_id:'bad'},{title:'x',unexpected:true}])assert.ok((await call('create_task',input)).error);
 for(const input of [{task_id:child.task.id,expected_version:1},{task_id:child.task.id,expected_version:1,status:null},{task_id:child.task.id,expected_version:true,status:'completed'}])assert.ok((await call('update_task',input)).error);
 assert.equal(requests.length,before);
 // User drafts, sample fixtures, and in-flight work are preserved.
 for(const setup of [()=>busy=true,()=>voiceSession={},()=>$('#edit-dialog').open=true,()=>dirty=[{value:'Unsaved',dataset:{taskName:created.task.id}}]]){
  setup();assert.ok((await call('create_task',{title:'Blocked'})).error);
  busy=false;voiceSession=null;$('#edit-dialog').open=false;dirty=[];
 }
 assert.equal(requests.length,before);
 const request_id=randomUUID();$('#message').value='User draft';assert.ok((await call('send_muse_message',{request_id,message:'Plan my day'})).error);assert.equal($('#message').value,'User draft');$('#message').value='';
 $('#message').value='Plan my day';const run=await call('send_muse_message',{request_id,message:'Plan my day'});assert.equal($('#message').value,'');assert.equal(run.status,'applied');assert.match(run.reply,/Plan my day/);assert.equal(run.user_id,undefined);
 const retry=await call('send_muse_message',{request_id,message:'Plan my day'});assert.equal(retry.id,run.id);
 const failed=await call('send_muse_message',{request_id:randomUUID(),message:'fail'});assert.equal(failed.status,'failed');assert.ok(failed.error);
 // A lost write response is uncertain, never claimed as unsaved or successful.
 mode='lost-response';const uncertain=await call('create_task',{title:'Verify before retry'});assert.equal(uncertain.outcome,'unknown');assert.equal(busy,false);
 dashboard=await call('get_dashboard');assert.equal(dashboard.tasks.filter(t=>t.title==='Verify before retry').length,1);
 // The saved write result survives a failed UI refresh.
 refreshFailed=true;const saved=await call('create_task',{title:'Saved while refresh offline'});assert.equal(saved.status,'saved');assert.ok(saved.ui_warning);refreshFailed=false;
 const controller=new AbortController();controller.abort();const count=requests.length;
 await assert.rejects(call('create_task',{title:'Cancelled'},{signal:controller.signal}),{name:'AbortError'});assert.equal(requests.length,count);
 dashboard=await call('get_dashboard');assert.equal(dashboard.tasks.find(t=>t.id===created.task.id).title,'Launch review');assert.equal(dashboard.tasks.find(t=>t.id===child.task.id).status,'pending');assert.equal(dashboard.execution.connected,false);
 assert.equal(dashboard.runs.find(r=>r.id===run.id).status,'applied');assert.ok(refreshes>0);
 conversationId=null;assert.ok((await call('get_dashboard')).runs.length>0);assert.equal((await call('get_dashboard',{request_id})).runs[0].id,run.id);
 const inFlight=call('create_task',{title:'First request'});assert.ok((await call('create_task',{title:'Concurrent request'})).error);assert.equal((await inFlight).status,'saved');
 process.stdout.write(JSON.stringify({done:true})+'\n');lines.close();
})().catch(e=>{console.error(e);lines.close();process.exitCode=1;});
""".replace("CONTROLLER", controller)
        .replace("DECISION", json.dumps(decision))
        .replace("HANDOFF", json.dumps(handoff))
        .replace("FOREIGN", json.dumps(foreign["id"]))
    )
    process = subprocess.Popen(
        [node, "-e", script],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        for line in process.stdout:
            request = json.loads(line)
            if request.get("done"):
                break
            response = client.request(
                request["method"],
                request["path"],
                json=request.get("body"),
                headers={"Origin": "http://testserver"},
            )
            process.stdin.write(
                json.dumps(
                    {
                        "status": response.status_code,
                        "body": response.json(),
                    }
                )
                + "\n"
            )
            process.stdin.flush()
        _, stderr = process.communicate(timeout=15)
        assert process.returncode == 0, stderr
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate()
    assert [message for _, message in model_calls].count("Plan my day") == 1
    snapshot = next(s for s, message in model_calls if message == "Plan my day")
    assert any(t["title"] == "Launch review" for t in snapshot["tasks"])
    # The client retains browser cookies; a fresh app client sees saved records.
    reloaded = clients(token="test-token", cookies=client.cookies).get("/api/dashboard")
    assert any(t["title"] == "Launch review" for t in reloaded.json()["tasks"])
