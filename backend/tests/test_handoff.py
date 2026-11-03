"""Ask Muse reuses a saved task scope without starting execution or sending a message."""

import json
import runpy
import shutil
import subprocess
from pathlib import Path

import pytest


def test_ask_muse_opens_existing_task_scope_without_sending_or_executing():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required for the handoff UI harness")
    page = runpy.run_path(
        str(Path(__file__).resolve().parents[2] / "frontend/dashboard.py")
    )["PAGE"]
    controller = (
        "// Machine handoff:"
        + page.split("// Machine handoff:", 1)[1].split("// End machine handoff.", 1)[0]
    )
    full_js = page.split("<script>", 1)[1].split("</script>", 1)[0]
    script = r"""
const assert=require('node:assert/strict'),vm=require('node:vm');
new vm.Script(FULL_JS);
let busy=false,samplePreview=false;
const assessment={handler:'muse',reason:'Computer work',requirements:['Notes'],done_when:'An outline is ready'};
const state={tasks:[{id:'live',title:'Prepare <proposal>',status:'pending',handoff:assessment},{id:'human',title:'Choose a color',status:'pending',handoff:{...assessment,handler:'user'}},{id:'unknown',title:'Old task',status:'pending'}],runs:[],messages:[]};
const samplePlans=[{id:'sample',title:'Sample task',completed:false,handoff:assessment}],sampleSteps=[];
const original=structuredClone(state),opened=[];
function openTaskChat(id){opened.push(id);}
const elements=new Map();
const $=selector=>{if(!elements.has(selector))elements.set(selector,{textContent:'',value:'',focus(){this.focused=true;},scrollIntoView(){this.scrolled=true;}});return elements.get(selector);};
$('#message').value='Unsent message';
function esc(value){return String(value).replaceAll('<','&lt;').replaceAll('>','&gt;');}
function motionAllowed(){return false;}
function api(){throw Error('Handoff must not call the API');}
function fetch(){throw Error('Handoff must not make network requests');}
CONTROLLER
assert.match(agentActions(state.tasks[0]),/Ask Muse about Prepare/);
assert.doesNotMatch(agentActions(state.tasks[1]),/data-handoff=/);
assert.equal(agentActions(state.tasks[1]),'');
assert.doesNotMatch(agentActions(state.tasks[2]),/data-handoff=/);
assert.match(agentActions(state.tasks[2]),/Not assessed/);
assert.doesNotMatch(agentActions(state.tasks[0]),/For Muse|Why\?|handoff-details/);
assert.doesNotMatch(agentActions(state.tasks[0]),/Rename/);
assert.equal(agentActions({id:'done',title:'Done',status:'completed'}),'');
samplePreview=true;assert.equal(agentActions({id:'done-sample',completed:true}),'');samplePreview=false;
handoffToMuse('live');
assert.deepEqual(opened,['live']);handoffToMuse('live');assert.deepEqual(opened,['live','live']);
assert.equal($('#notice').textContent,'');
assert.deepEqual(state,original);assert.equal($('#message').value,'Unsent message');
samplePreview=true;handoffToMuse('sample');assert.match($('#notice').textContent,/Sample tasks have no saved chat/);
const previous=$('#notice').textContent;handoffToMuse('missing');assert.equal($('#notice').textContent,previous);
samplePreview=false;handoffToMuse('human');handoffToMuse('unknown');assert.equal($('#notice').textContent,previous);
$('#edit-handoff-handler').value='muse';$('#edit-handoff-reason').value='Computer work';
$('#edit-handoff-requirements').value=' Notes\n\nBrowser ';$('#edit-handoff-done').value='A useful result';
const handoff=readEditorHandoff();
assert.deepEqual(handoff.requirements,['Notes','Browser']);assert.ok(validHandoff(handoff));
assert.match(handoffFields({handoff},'test'),/value="muse" selected/);
assert.match(handoffFields({handoff:{...assessment,reason:'<script>'}},'test'),/&lt;script&gt;/);
$('#edit-handoff-handler').value='user';assert.equal(readEditorHandoff().handler,'user');
$('#edit-handoff-handler').value='';assert.equal(readEditorHandoff(),null);
busy=true;samplePreview=false;handoffToMuse('live');assert.equal($('#notice').textContent,previous);
assert.deepEqual(state,original);assert.deepEqual(opened,['live','live']);
""".replace("CONTROLLER", controller).replace("FULL_JS", json.dumps(full_js))
    result = subprocess.run(
        [node, "-e", script], capture_output=True, text=True, check=False, timeout=15
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'id="draft-dialog"' not in page
    assert 'id="task-chat-context"' not in page
    assert "Draft with Muse" not in page


def test_legacy_drafting_endpoints_are_no_longer_exposed(setup):
    clients, _, _ = setup
    paths = clients().get("/openapi.json").json()["paths"]
    assert "/api/tasks/{task_id}/drafts" not in paths
    assert "/api/tasks/{task_id}/draft" not in paths
    assert "/api/conversation" in paths
