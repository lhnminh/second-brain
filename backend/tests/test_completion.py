"""Completion uses the saved task response without reloading workspace history."""

import json
import runpy
import shutil
import subprocess
from pathlib import Path

import pytest
from sqlalchemy import event


def test_task_patch_returns_saved_row_with_one_task_read(setup):
    clients, _, engine = setup
    client = clients()
    task = client.post("/api/tasks", json={"title": "Complete this step"}).json()
    statements = []

    def record(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", record)
    try:
        response = client.patch(
            "/api/tasks/" + task["id"],
            json={
                "expected_version": task["version"],
                "status": "completed",
            },
        )
    finally:
        event.remove(engine, "before_cursor_execute", record)
    assert response.status_code == 200
    saved = response.json()
    assert saved["status"] == "completed" and saved["version"] == task["version"] + 1
    assert sum(s.lstrip().upper().startswith("SELECT") for s in statements) == 1
    assert len(statements) == 6
    data = client.get("/api/dashboard").json()
    assert data["tasks"] == [saved]
    assert data["events"][-1]["kind"] == "task.edited"
    assert (
        client.patch(
            "/api/tasks/" + task["id"],
            json={
                "expected_version": task["version"],
                "status": "pending",
            },
        ).status_code
        == 409
    )
    assert (
        clients("bob")
        .patch(
            "/api/tasks/" + task["id"],
            json={
                "expected_version": saved["version"],
                "status": "pending",
            },
        )
        .status_code
        == 404
    )


def test_browser_completion_feedback_confirmation_and_failure():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required for the completion browser harness")
    page = runpy.run_path(
        str(Path(__file__).resolve().parents[2] / "frontend/dashboard.py")
    )["PAGE"]
    function = (
        "async function complete("
        + page.split("async function complete(", 1)[1].split(
            "$('#canvas').addEventListener", 1
        )[0]
    )
    full_js = page.split("<script>", 1)[1].split("</script>", 1)[0]
    script = r"""
const assert=require('node:assert/strict'),vm=require('node:vm');new vm.Script(FULL_JS);
let busy=false,renders=0,exits=0,entries=0,resolvePatch,rejectPatch;
let state={tasks:[{id:'a',status:'pending',version:1},{id:'b',status:'pending',version:5}],messages:[{content:'Keep this'}],runs:[]};
const requests=[],errors=[],classes=new Set(),row={classList:{add:c=>classes.add(c),remove:c=>classes.delete(c)}};
const checkbox={dataset:{complete:'a'},checked:false,attrs:{},closest:()=>row,setAttribute(k,v){this.attrs[k]=v;},removeAttribute(k){delete this.attrs[k];}};
const toggle={dataset:{toggle:'a'},textContent:'Complete plan'};
const elements=new Map(),$=key=>{if(!elements.has(key))elements.set(key,{textContent:'',hidden:false});return elements.get(key);};
$('#canvas').querySelectorAll=selector=>selector==='[data-complete]'?[checkbox]:selector==='[data-toggle]'?[toggle]:[];
function setBusy(value){busy=value;}
function refresh(){throw Error('Completion must not refetch the dashboard');}
function render(){throw Error('Completion must preserve chat and proposal drafts');}
function renderOverview(){renders++;}
async function animateTaskExit(){exits++;return {planId:'plan'};}
function animateTaskEntry(value){if(value)entries++;}
function error(e){errors.push(e.message);}
function api(path,method,body){requests.push({path,method,body});return new Promise((resolve,reject)=>{resolvePatch=resolve;rejectPatch=reject;});}
FUNCTION
(async()=>{
 const saving=complete('a',true);
 assert.equal(checkbox.checked,true);assert.equal(classes.has('is-saving'),true);assert.equal(checkbox.attrs['aria-busy'],'true');
 assert.equal(state.tasks[0].status,'pending');assert.equal(busy,true);assert.equal(exits,0);assert.equal(renders,0);
 assert.match($('#notice').textContent,/Saving/);assert.equal(toggle.textContent,'Saving…');
 assert.deepEqual(requests,[{path:'/api/tasks/a',method:'PATCH',body:{expected_version:1,status:'completed'}}]);
 resolvePatch({id:'a',status:'completed',version:2});await saving;
 assert.equal(state.tasks[0].status,'completed');assert.equal(state.tasks[0].version,2);assert.equal(state.tasks[1].version,5);
 assert.equal(requests.length,1);assert.equal(renders,1);assert.equal(exits,1);assert.equal(entries,1);
 assert.equal(busy,false);assert.equal(classes.size,0);assert.equal(checkbox.attrs['aria-busy'],undefined);
 assert.equal(state.messages[0].content,'Keep this');assert.equal(toggle.textContent,'Complete plan');
 // Undo also responds immediately and uses the current saved version.
 const undo=complete('a',false);assert.equal(checkbox.checked,false);assert.equal(state.tasks[0].status,'completed');
 resolvePatch({id:'a',status:'pending',version:3});await undo;assert.equal(exits,1);assert.equal(state.tasks[0].status,'pending');
 // A failed or conflicting save restores the checkbox without changing task state.
 for(const message of ['Offline','Task changed; reload before editing']){
  const count=renders,attempt=complete('a',true);assert.equal(checkbox.checked,true);
  rejectPatch(Error(message));await attempt;
  assert.equal(checkbox.checked,false);assert.equal(state.tasks[0].status,'pending');assert.equal(state.tasks[0].version,3);
  assert.equal(renders,count);assert.equal(errors.at(-1),message);assert.equal(busy,false);assert.equal(classes.size,0);
 }
 // An unexpected response cannot manufacture successful completion.
 const unexpected=complete('a',true);resolvePatch({id:'a',status:'pending',version:3});await unexpected;
 assert.equal(checkbox.checked,false);assert.equal(state.tasks[0].status,'pending');assert.match(errors.at(-1),/Could not confirm/);
 // Access expiry clears private state in api(); completion must not resurrect it.
 const expiry=complete('a',true);state={tasks:[],messages:[],runs:[]};rejectPatch(Error('Access expired'));await expiry;
 assert.deepEqual(state.tasks,[]);assert.equal(busy,false);
 const count=requests.length;await complete('missing',true);assert.equal(requests.length,count);
})().catch(e=>{console.error(e);process.exitCode=1;});
""".replace("FUNCTION", function).replace("FULL_JS", json.dumps(full_js))
    result = subprocess.run(
        [node, "-e", script], capture_output=True, text=True, check=False, timeout=15
    )
    assert result.returncode == 0, result.stdout + result.stderr
