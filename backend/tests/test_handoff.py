"""The disconnected handoff must never manufacture execution or send requests."""

import json
import runpy
import shutil
import subprocess
from pathlib import Path

import pytest


def test_handoff_placeholder_leaves_work_and_chat_unchanged():
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
const original=structuredClone(state);
const elements=new Map();
const $=selector=>{if(!elements.has(selector))elements.set(selector,{textContent:'',value:'',focus(){this.focused=true;},scrollIntoView(){this.scrolled=true;}});return elements.get(selector);};
$('#message').value='Unsent message';
function esc(value){return String(value).replaceAll('<','&lt;').replaceAll('>','&gt;');}
function motionAllowed(){return false;}
function api(){throw Error('Handoff must not call the API');}
function fetch(){throw Error('Handoff must not make network requests');}
CONTROLLER
assert.match(agentActions(state.tasks[0]),/Hand off to Muse/);
assert.doesNotMatch(agentActions(state.tasks[1]),/data-handoff=/);
assert.match(agentActions(state.tasks[1]),/For you/);
assert.doesNotMatch(agentActions(state.tasks[2]),/data-handoff=/);
assert.match(agentActions(state.tasks[2]),/Not assessed/);
assert.match(agentActions(state.tasks[0]),/Needs: Notes/);
assert.match(agentActions(state.tasks[0]),/Done when: An outline/);
assert.equal(agentActions({id:'done',status:'completed'}),'');
assert.equal(agentActions({id:'done-sample',completed:true}),'');
handoffToMuse('live');
assert.match($('#notice').textContent,/No computer connected/);
assert.match($('#notice').textContent,/Nothing has been started/);
assert.equal($('#notice').focused,true);assert.equal($('#notice').scrolled,true);
assert.deepEqual(state,original);assert.equal($('#message').value,'Unsent message');
samplePreview=true;handoffToMuse('sample');assert.match($('#notice').textContent,/Sample task/);
const previous=$('#notice').textContent;handoffToMuse('missing');assert.equal($('#notice').textContent,previous);
samplePreview=false;handoffToMuse('human');handoffToMuse('unknown');assert.equal($('#notice').textContent,previous);
const proposal={title:'A step'};
setProposalField(proposal,'handoff.handler','muse');
setProposalField(proposal,'handoff.reason','Computer work');
setProposalField(proposal,'handoff.requirements',' Notes\n\nBrowser ');
setProposalField(proposal,'handoff.done_when','A useful result');
assert.deepEqual(proposal.handoff.requirements,['Notes','Browser']);assert.ok(validHandoff(proposal.handoff));
assert.match(handoffFields(proposal,'test'),/value="muse" selected/);
assert.match(handoffFields({handoff:{...assessment,reason:'<script>'}},'test'),/&lt;script&gt;/);
setProposalField(proposal,'handoff.handler','user');assert.equal(proposal.handoff.handler,'user');
setProposalField(proposal,'handoff.handler','');assert.equal(proposal.handoff,null);
busy=true;samplePreview=false;handoffToMuse('live');assert.equal($('#notice').textContent,previous);
assert.deepEqual(state,original);
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
