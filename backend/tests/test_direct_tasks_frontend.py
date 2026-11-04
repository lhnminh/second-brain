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
    helpers = "\n".join(
        re.search(pattern, page)[0]
        for pattern in [
            r"function rootTaskId.*?\n",
            r"function runChatScope.*?\n",
            r"function chatRuns.*?\n",
        ]
    )
    helpers += (
        "\nfunction safeChatUrl"
        + page.split("function safeChatUrl", 1)[1].split("function renderChat(){", 1)[0]
    )
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
let state={tasks:[],runs:[],messages:[]};let chatTaskId=null,delegatedTaskId=null;let refreshFailed=false,responseData=null;
const crypto={randomUUID:()=>String(++nextId)},requests=[],errors=[];
CHAT_HELPERS
function canHandoff(){return true;}let chatWorkId=null;function renderOverview(){}
async function refresh(){refreshes++;if(refreshFailed)throw Error('Refresh failed');if(responseData)state=structuredClone(responseData);}
const chatDrafts=new Map(),chatRequests=new Map();
async function api(path,method,body){
 requests.push({path,method,body:structuredClone(body)});
 assert.equal($('#message').value,'');if(mode==='offline')throw Error('Offline');
 return {id:'run',request_id:body.request_id,message:body.message,status:mode,error:mode==='failed'?'Model failed':null};
}
function error(e){errors.push(e.message);}
function action(work){lastAction=(async()=>{try{await work();await refresh();}catch(e){error(e);}})();return lastAction;}
CHAT_RENDER
SUBMIT
RENDER
(async()=>{
 $('#message').value='Prepare a workshop';$('#chat-form').onsubmit({preventDefault(){}});await lastAction;
 assert.equal(requests.length,1);assert.equal(requests[0].path,'/api/conversation');
 assert.equal(requests[0].body.apply_immediately,true);assert.equal(requests[0].body.review_draft,undefined);
 assert.equal($('#message').value,'',errors.join('; '));assert.equal(pending,null);assert.equal(refreshes,2);
 assert.ok(requests.every(r=>!r.path.includes('/approve')));
 state={tasks:[{id:'saved'}],runs:[{id:'run',task_id:null,status:'applied'}],messages:[{run_id:'run',role:'assistant',content:'Your workshop plan.'}]};
 render();assert.equal($('#reviews').innerHTML,'');assert.match($('#conversation').innerHTML,/MUSE/);
 assert.equal($('#status').textContent,'');
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
 // Saved creation/corrections and task-only answers route to the exact task.
 state={tasks:[{id:'a'},{id:'b'},{id:'child',parent_task_id:'a'}],runs:[{id:'new',status:'applied',related_task_ids:['a']}],messages:[]};
 $('#message').value='General draft';followTaskChat({id:'new',status:'applied'});assert.equal(chatTaskId,'a');assert.equal(chatDrafts.get(''),'General draft');
 chatDrafts.set('b','B draft');state.runs.push({id:'question',status:'answered',proposal:{chat_task_id:'b'}});followTaskChat({id:'question',status:'answered'});assert.equal(chatTaskId,'b');assert.equal($('#message').value,'B draft');
 state.runs.push({id:'ambiguous',status:'applied',related_task_ids:['a','b']});followTaskChat({id:'ambiguous',status:'applied'});assert.equal(chatTaskId,'b');
 followTaskChat({status:'failed'});assert.equal(chatTaskId,'b');
 // General creation exercises the real helper's optional tasks argument, not a stub.
 chatTaskId=null;state={tasks:[],runs:[],messages:[]};mode='applied';
 responseData={tasks:[{id:'created-root'},{id:'created-child',parent_task_id:'created-root'}],runs:[{id:'run',task_id:null,status:'applied',input_payload:{chat_task_id:null},related_task_ids:['created-root','created-child']}],messages:[]};
 $('#message').value='Create the actual task';$('#chat-form').onsubmit({preventDefault(){}});await lastAction;
 assert.equal(chatTaskId,'created-root');assert.equal($('#message').value,'');assert.equal(pending,null);assert.equal(errors.filter(e=>e.includes('tasks.find')).length,0);
 // A successful send stays cleared even when refreshing the UI fails afterward.
 refreshFailed=true;$('#message').value='A saved question';$('#chat-form').onsubmit({preventDefault(){}});await lastAction;assert.equal($('#message').value,'');assert.equal(pending,null);refreshFailed=false;responseData=null;
 // An exchange sent in A and routed to B appears only in B, with both sides together.
 chatDrafts.clear();chatTaskId='a';mode='answered';chatDrafts.set('a','Question about B');
 responseData={tasks:[{id:'a'},{id:'b'}],runs:[{id:'run',task_id:null,status:'answered',message:'Question about B',input_payload:{chat_task_id:'a'},proposal:{chat_task_id:'b'},chat_scope_id:'b'}],messages:[{run_id:'run',role:'user',content:'Question about B'},{run_id:'run',role:'assistant',content:'B answer'}]};
 $('#message').value='Question about B';$('#chat-form').onsubmit({preventDefault(){}});await lastAction;
 assert.equal(chatTaskId,'b');assert.equal($('#message').value,'');assert.match($('#conversation').innerHTML,/B answer/);
 chatTaskId='a';renderChat();assert.doesNotMatch($('#conversation').innerHTML,/Question about B|B answer/);assert.equal(chatDrafts.get('a')||'','');
 chatTaskId='b';renderChat();assert.match($('#conversation').innerHTML,/Question about B/);assert.match($('#conversation').innerHTML,/B answer/);responseData=null;
 // Old stored plans have compact recovery controls, with no draft-editing form.
 state={tasks:[],runs:[{id:'old',task_id:null,status:'awaiting_review',proposal:{tasks:[{title:'Earlier task',subtasks:[]}]}}],messages:[]};
 render();assert.match($('#reviews').innerHTML,/Add these tasks/);assert.doesNotMatch($('#reviews').innerHTML,/<input|<textarea|data-object=/);
})().catch(e=>{console.error(e);process.exitCode=1;});
""".replace("SUBMIT", submit)
        .replace("CHAT_HELPERS", helpers)
        .replace(
            "CHAT_RENDER",
            "function renderChat(){"
            + page.split("function renderChat(){", 1)[1].split(
                "function openTaskChat(", 1
            )[0],
        )
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
