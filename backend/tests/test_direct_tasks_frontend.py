"""Run the shipped chat handler with deferred, simulated backend responses."""

import json
import re
import runpy
import shutil
import subprocess
from pathlib import Path

import pytest


def test_chat_saves_without_approval_and_preserves_retry_text():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required for the direct-task browser harness")
    page = runpy.run_path(
        str(Path(__file__).resolve().parents[2] / "frontend/dashboard.py")
    )["PAGE"]
    submit = re.search(r"\$\('#chat-form'\)\.onsubmit=.*?;\n", page)[0]
    render = (
        "function render(){"
        + page.split("function render(){", 1)[1].split("$('#chat-form').onsubmit", 1)[0]
    )
    script = (
        r"""
const assert=require('node:assert/strict'),vm=require('node:vm');
new vm.Script(FULL_JS);
const elements=new Map(),$=key=>{if(!elements.has(key))elements.set(key,{value:'',textContent:'',innerHTML:'',hidden:false,scrollHeight:0});return elements.get(key);};
const esc=value=>String(value??'').replaceAll('<','&lt;').replaceAll('>','&gt;');
let busy=false,voiceSession=null,pending=null,conversationId='visit',nextId=0,mode='applied',refreshes=0,lastAction;
let state={tasks:[],runs:[],messages:[]};
const crypto={randomUUID:()=>String(++nextId)},requests=[],errors=[];
function chatRuns(){return state.runs;}
function renderOverview(){}
async function refresh(){refreshes++;}
async function api(path,method,body){
 requests.push({path,method,body:structuredClone(body)});
 if(mode==='offline')throw Error('Offline');
 return {id:'run',status:mode,error:mode==='failed'?'Model failed':null};
}
function error(e){errors.push(e.message);}
function action(work){lastAction=(async()=>{try{await work();await refresh();}catch(e){error(e);}})();return lastAction;}
SUBMIT
RENDER
(async()=>{
 $('#message').value='Prepare a workshop';$('#chat-form').onsubmit({preventDefault(){}});await lastAction;
 assert.equal(requests.length,1);assert.equal(requests[0].path,'/api/conversation');
 assert.equal(requests[0].body.apply_immediately,true);assert.equal(requests[0].body.review_draft,undefined);
 assert.equal($('#message').value,'');assert.equal(pending,null);assert.equal(refreshes,1);
 assert.ok(requests.every(r=>!r.path.includes('/approve')));
 state={tasks:[{id:'saved'}],runs:[{id:'run',task_id:null,status:'applied'}],messages:[{run_id:'run',role:'assistant',content:'Your workshop plan.'}]};
 render();assert.equal($('#reviews').innerHTML,'');assert.match($('#conversation').innerHTML,/TASKS SAVED/);
 assert.match($('#status').textContent,/Task updates saved/);
 // Network uncertainty keeps the same message and idempotency key for retry.
 mode='offline';$('#message').value='Add a meeting';$('#chat-form').onsubmit({preventDefault(){}});await lastAction;
 const request=requests.at(-1).body;assert.equal($('#message').value,'Add a meeting');assert.equal(pending.request_id,request.request_id);
 $('#chat-form').onsubmit({preventDefault(){}});await lastAction;assert.equal(requests.at(-1).body.request_id,request.request_id);
 mode='applied';$('#chat-form').onsubmit({preventDefault(){}});await lastAction;assert.equal(requests.at(-1).body.request_id,request.request_id);assert.equal($('#message').value,'');
 // Model failures and stale replies retain user input for a fresh request.
 for(const status of ['failed','stale']){
  mode=status;$('#message').value='Keep this text';$('#chat-form').onsubmit({preventDefault(){}});await lastAction;
  assert.equal($('#message').value,'Keep this text');assert.equal(pending,null);
 }
 mode='answered';$('#message').value='What next?';$('#chat-form').onsubmit({preventDefault(){}});await lastAction;assert.equal($('#message').value,'');
 // Old stored plans have compact recovery controls, with no draft-editing form.
 state={tasks:[],runs:[{id:'old',task_id:null,status:'awaiting_review',proposal:{tasks:[{title:'Earlier task',subtasks:[]}]}}],messages:[]};
 render();assert.match($('#reviews').innerHTML,/Add these tasks/);assert.doesNotMatch($('#reviews').innerHTML,/<input|<textarea|data-object=/);
})().catch(e=>{console.error(e);process.exitCode=1;});
""".replace("SUBMIT", submit)
        .replace("RENDER", render)
        .replace(
            "FULL_JS", json.dumps(page.split("<script>", 1)[1].split("</script>", 1)[0])
        )
    )
    result = subprocess.run(
        [node, "-e", script], capture_output=True, text=True, check=False, timeout=15
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Save reviewed plan" not in page
    assert "data-remove-step" not in page
