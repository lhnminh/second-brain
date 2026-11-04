"""Subtask handoff assessments are separate from chat and computer execution."""

import json
import runpy
import shutil
import subprocess
from pathlib import Path

import pytest


def test_handoff_controls_and_background_assessment_preserve_work(tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required")
    page = runpy.run_path(
        str(Path(__file__).resolve().parents[2] / "frontend/dashboard.py")
    )["PAGE"]
    controller = (
        "// Machine handoff:"
        + page.split("// Machine handoff:", 1)[1].split("// End machine handoff.", 1)[0]
    )
    script = r"""
const assert=require('node:assert/strict'),vm=require('node:vm');new vm.Script(FULL_JS);
const crypto=require('node:crypto');let busy=false;
const assessment={handler:'muse',reason:'Computer work',requirements:['Notes'],done_when:'An outline is ready'};
let state={user_id:'workspace',tasks:[{id:'live',parent_task_id:'root',title:'Draft agenda',status:'pending',handoff:assessment},{id:'human',parent_task_id:'root',title:'Move chairs',status:'pending',handoff:{...assessment,handler:'user'}},{id:'unknown',title:'New step',status:'pending',version:1,handoff:null}]};
const elements=new Map(),$=key=>{if(!elements.has(key))elements.set(key,{textContent:'',value:'',showModal(){this.open=true;},close(){this.open=false;}});return elements.get(key);};
const control={dataset:{assessmentId:'unknown'},innerHTML:''},field={dataset:{taskName:'unknown',version:'1'},value:'My unsent title'};
const document={querySelectorAll:selector=>selector==='.handoff-whole'?[]:selector==='[data-assessment-id]'?[control]:[field]};
function handoffRoot(t){return {time_horizon:'short_term'}};function taskHorizon(t){return t.time_horizon};function canHandoff(t){return t?.handoff?.handler==='muse'&&t.status!=='completed'};
const esc=value=>String(value??'').replaceAll('<','&lt;').replaceAll('>','&gt;');
let delegatedTaskId=null,openedChat=null,sent=0;function openTaskChat(id){openedChat=id;}$('#chat-form').requestSubmit=()=>sent++;
let requests=[],resolveRequest,rejectRequest;
async function api(path,method,body){requests.push({path,method,body});return new Promise((resolve,reject)=>{resolveRequest=resolve;rejectRequest=reject;});}
CONTROLLER
(async()=>{
 assert.match(agentActions(state.tasks[0]),/Hand off/);assert.doesNotMatch(agentActions(state.tasks[0]),/Ask Muse/);
 assert.match(agentActions(state.tasks[1]),/disabled/);assert.match(agentActions({...state.tasks[0],status:'completed'}),/disabled/);
 assert.match(agentActions(state.tasks[2]),/Assess with Muse/);
 handoffToMuse('live');assert.equal(openedChat,'live');assert.equal(delegatedTaskId,'live');assert.equal(sent,1);assert.match($('#message').value,/Draft agenda/);assert.equal(requests.length,0);handoffToMuse('human');assert.equal(sent,1);
 const original=structuredClone(state.tasks[2]),pending=assessSubtasks([state.tasks[2]]);assert.match(control.innerHTML,/Assessing/);assert.equal(requests.length,1);
 await assessSubtasks([state.tasks[2]]);assert.equal(requests.length,1);
 resolveRequest({status:'answered',tasks:[{...original,version:2,handoff:assessment,handoff_source:'model'}]});await pending;
 assert.equal(state.tasks[2].handoff.handler,'muse');assert.equal(state.tasks[2].title,'New step');assert.equal(state.tasks[2].status,'pending');assert.equal(field.value,'My unsent title');assert.equal(field.dataset.version,'2');assert.match(control.innerHTML,/Hand off/);
 state.tasks[2]={...original};const failed=assessSubtasks([state.tasks[2]]);resolveRequest({status:'failed',error:'Model unavailable'});await failed;assert.equal(state.tasks[2].handoff,null);assert.match(control.innerHTML,/Retry assessment/);
 const offline=assessSubtasks([state.tasks[2]]),request=requests.at(-1).body;rejectRequest(Error('Offline'));await offline;
 const retry=assessSubtasks([state.tasks[2]]);assert.equal(requests.at(-1).body.request_id,request.request_id);resolveRequest({status:'answered',tasks:[{...original,version:2,handoff:assessment}]});await retry;
 // Finishing in another workspace cannot populate its UI with the old result.
 state.tasks[2]={...original};const old=assessSubtasks([state.tasks[2]]);state={user_id:'different',tasks:[]};resolveRequest({status:'answered',tasks:[{...original,version:2,handoff:assessment}]});await old;assert.deepEqual(state.tasks,[]);
})().catch(e=>{console.error(e);process.exitCode=1;});
""".replace("CONTROLLER", controller).replace(
        "FULL_JS", json.dumps(page.split("<script>", 1)[1].split("</script>", 1)[0])
    )
    path = tmp_path / "handoff.cjs"
    path.write_text(script, encoding="utf-8")
    result = subprocess.run(
        [node, str(path)], capture_output=True, text=True, check=False, timeout=15
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "samplePreview" not in page and "Sample workspace" not in page
    assert "Go to task chat" not in page and 'id="edit-handler"' not in page


def test_legacy_drafting_endpoints_are_no_longer_exposed(setup):
    clients, _, _ = setup
    paths = clients().get("/openapi.json").json()["paths"]
    assert "/api/tasks/{task_id}/drafts" not in paths
    assert "/api/tasks/{task_id}/draft" not in paths
    assert "/api/conversation" in paths
