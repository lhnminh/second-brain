"""Renames preserve task identity and reach subsequent agent requests."""

import runpy
import shutil
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest


@pytest.mark.parametrize("subtask", [False, True])
def test_rename_persists_and_reaches_muse(setup, subtask):
    clients, muse, _ = setup
    client = clients()
    parent = client.post("/api/tasks", json={"title": "Prepare meeting"}).json()
    task = (
        client.post(
            "/api/tasks",
            json={"title": "Draft agenda", "parent_task_id": parent["id"]},
        ).json()
        if subtask
        else parent
    )
    saved = client.patch(
        "/api/tasks/" + task["id"],
        json={"expected_version": task["version"], "title": "Prepare launch review"},
    )
    assert saved.status_code == 200
    renamed = saved.json()
    assert renamed["id"] == task["id"]
    assert renamed["parent_task_id"] == task["parent_task_id"]
    assert renamed["version"] == task["version"] + 1
    reloaded = clients(cookies=client.cookies).get("/api/dashboard").json()
    assert next(t for t in reloaded["tasks"] if t["id"] == task["id"]) == renamed

    def respond(snapshot, message):
        current = next(t for t in snapshot["tasks"] if t["id"] == task["id"])
        assert current["title"] == "Prepare launch review"
        return {"reply": "I have the updated name.", "tasks": []}

    muse.converse = respond
    run = client.post(
        "/api/conversation",
        json={"request_id": str(uuid4()), "message": "Help with the renamed task"},
    ).json()
    assert run["status"] == "answered"
    # A stale editor cannot undo the rename.
    assert client.patch(
        "/api/tasks/" + task["id"],
        json={"expected_version": task["version"], "title": "Old editor"},
    ).status_code == 409


def test_inline_name_saves_and_preserves_failed_edits():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required for the inline editing harness")
    page = runpy.run_path(
        str(Path(__file__).resolve().parents[2] / "frontend/dashboard.py")
    )["PAGE"]
    controller = "async function saveTaskName(" + page.split(
        "async function saveTaskName(", 1
    )[1].split("$('#canvas').onchange=", 1)[0]
    script = r"""
const assert=require('node:assert/strict');
let busy=false,samplePreview=false,fail=false,renders=0,lastError;
const state={tasks:[{id:'task',title:'Old name',version:3}]};
const listeners={},elements=new Map();
const $=s=>{if(!elements.has(s))elements.set(s,{addEventListener:(event,fn)=>listeners[event]=fn});return elements.get(s);};
function setBusy(value){busy=value;}function error(e){lastError=e.message;}
function renderOverview(){renders++;}
const requests=[];
async function api(path,method,body){requests.push({path,method,body});if(fail)throw Error('Offline');return {...state.tasks[0],title:body.title,version:4};}
CONTROLLER
const input={value:' New name ',dataset:{taskName:'task',version:'3'},setCustomValidity(value){this.validity=value;},reportValidity(){return !this.validity;},closest(){return this;},blur(){this.blurred=true;}};
(async()=>{
 await saveTaskName(input);
 assert.deepEqual(requests[0],{path:'/api/tasks/task',method:'PATCH',body:{expected_version:3,title:'New name'}});
 assert.equal(state.tasks[0].title,'New name');assert.equal(renders,1);assert.equal(busy,false);
 input.value='Unsaved name';input.dataset.version='4';fail=true;
 await saveTaskName(input);assert.equal(input.value,'Unsaved name');assert.equal(state.tasks[0].title,'New name');assert.equal(lastError,'Offline');assert.equal(busy,false);
 input.value='   ';await saveTaskName(input);assert.equal(requests.length,2);assert.match(input.validity,/Enter a task name/);
 listeners.keydown({target:input,key:'Escape',preventDefault(){}});assert.equal(input.value,'New name');assert.equal(input.blurred,true);
 input.blurred=false;listeners.keydown({target:input,key:'Enter',preventDefault(){}});assert.equal(input.blurred,true);
})().catch(e=>{console.error(e);process.exitCode=1;});
""".replace("CONTROLLER", controller)
    result = subprocess.run(
        [node, "-e", script], check=False, capture_output=True, text=True, timeout=15
    )
    assert result.returncode == 0, result.stdout + result.stderr
