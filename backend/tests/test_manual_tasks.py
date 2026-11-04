"""Manual tasks retain their selected focus section and user content."""

import re
import runpy
import shutil
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError

from second_brain.db import tasks
from second_brain.service import planning_tasks


@pytest.mark.parametrize("horizon", ["short_term", "long_term"])
def test_manual_plan_saves_exact_steps_atomically_and_in_order(setup, horizon):
    clients, muse, _ = setup
    client = clients()
    response = client.post(
        "/api/tasks",
        json={
            "title": "Prepare workshop",
            "time_horizon": horizon,
            "deadline": "2026-11-10",
            "subtasks": [{"title": "Choose a topic"}, {"title": "Prepare slides"}],
        },
    )
    assert response.status_code == 201
    root = response.json()
    children = root.pop("subtasks")
    assert [step["title"] for step in children] == ["Choose a topic", "Prepare slides"]
    assert [step["position"] for step in children] == [0, 1]
    assert all(step["parent_task_id"] == root["id"] for step in children)
    assert all(
        step["deadline"] is None and step["handoff"] is None for step in children
    )
    saved = clients(cookies=client.cookies).get("/api/dashboard").json()
    assert sorted(saved["tasks"], key=lambda task: task["id"]) == sorted(
        [root, *children], key=lambda task: task["id"]
    )
    assert (
        len([event for event in saved["events"] if event["kind"] == "task.created"])
        == 3
    )
    assert muse.calls == 0 and saved["messages"] == [] and saved["runs"] == []


@pytest.mark.parametrize(
    "changes",
    [
        {"subtasks": [{"title": "   "}]},
        {"subtasks": [{"title": "Step"}] * 21},
        {"parent_task_id": str(uuid4()), "subtasks": [{"title": "Nested"}]},
        {"subtasks": [{"title": "Step", "unexpected": True}]},
    ],
)
def test_invalid_manual_steps_never_save_a_partial_plan(setup, changes):
    clients, _, _ = setup
    client = clients()
    assert (
        client.post(
            "/api/tasks",
            json={"title": "Plan", "time_horizon": "short_term", **changes},
        ).status_code
        == 422
    )
    assert client.get("/api/dashboard").json()["tasks"] == []


def test_manual_plan_rolls_back_parent_and_steps_if_audit_write_fails(
    setup, monkeypatch
):
    clients, _, _ = setup
    client = clients()
    client.get("/api/dashboard")

    def fail_audit(*args, **kwargs):
        raise RuntimeError("Test audit failure")

    monkeypatch.setattr("second_brain.service.audit", fail_audit)
    with pytest.raises(RuntimeError, match="Test audit failure"):
        client.post(
            "/api/tasks",
            json={
                "title": "Plan",
                "time_horizon": "short_term",
                "subtasks": [{"title": "First"}, {"title": "Second"}],
            },
        )
    saved = client.get("/api/dashboard").json()
    assert saved["tasks"] == [] and saved["events"] == []


@pytest.mark.parametrize("horizon", ["short_term", "long_term"])
def test_manual_task_persists_selection_and_edits_without_muse(setup, horizon):
    clients, muse, engine = setup
    client = clients()
    task = client.post(
        "/api/tasks",
        json={
            "title": "My task",
            "description": "My own context",
            "time_horizon": horizon,
        },
    ).json()
    assert task["time_horizon"] == horizon
    assert task["deadline"] is None
    assert muse.calls == 0
    edited = client.patch(
        "/api/tasks/" + task["id"],
        json={
            "expected_version": task["version"],
            "title": "A clearer name",
            "description": "Updated context",
            "deadline": "2026-12-20",
        },
    ).json()
    returning = clients(cookies=client.cookies)
    data = returning.get("/api/dashboard").json()
    assert len(data["tasks"]) == 1
    assert data["tasks"][0] == edited
    assert edited["time_horizon"] == horizon
    assert edited["description"] == "Updated context"
    assert data["messages"] == [] and data["runs"] == []
    assert (
        clients()
        .patch(
            "/api/tasks/" + task["id"],
            json={"expected_version": edited["version"], "time_horizon": "long_term"},
        )
        .status_code
        == 404
    )
    assert (
        client.patch(
            "/api/tasks/" + task["id"],
            json={"expected_version": task["version"], "time_horizon": None},
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/tasks", json={"title": "Invalid", "time_horizon": "someday"}
        ).status_code
        == 422
    )
    automatic = client.patch(
        "/api/tasks/" + task["id"],
        json={"expected_version": edited["version"], "time_horizon": None},
    ).json()
    assert automatic["time_horizon"] is None
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            update(tasks).where(tasks.c.id == task["id"]).values(time_horizon="invalid")
        )


def test_reopening_a_finished_plan_keeps_done_steps_and_restores_active_context(setup):
    clients, muse, _ = setup
    client = clients()
    task = client.post(
        "/api/tasks", json={"title": "Plan", "time_horizon": "short_term"}
    ).json()
    step = client.post(
        "/api/tasks", json={"title": "Finished step", "parent_task_id": task["id"]}
    ).json()
    client.patch(
        "/api/tasks/" + step["id"],
        json={"expected_version": step["version"], "status": "completed"},
    )
    active, history = planning_tasks(client.get("/api/dashboard").json()["tasks"])
    assert active == [] and len(history) == 2
    client.patch(
        "/api/tasks/" + task["id"],
        json={"expected_version": task["version"], "status": "in_progress"},
    )
    saved = client.get("/api/dashboard").json()["tasks"]
    active, history = planning_tasks(saved)
    assert [t["id"] for t in active] == [task["id"]]
    assert history[0]["id"] == step["id"] and history[0]["status"] == "completed"
    snapshots = []
    muse.converse = lambda state, message: (
        snapshots.append(state) or {"reply": "Ready to continue.", "tasks": []}
    )
    run = client.post(
        "/api/conversation",
        json={
            "request_id": str(uuid4()),
            "message": "Continue this task",
            "chat_task_id": task["id"],
        },
    ).json()
    assert run["status"] == "answered"
    assert any(t["id"] == task["id"] for t in snapshots[0]["tasks"])


def test_manual_task_form_preserves_failures_and_prevents_double_submission(tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node required")
    page = runpy.run_path(
        str(Path(__file__).resolve().parents[2] / "frontend/dashboard.py")
    )["PAGE"]
    controller = page.split("// Manual tasks:", 1)[1].split("// End manual tasks.", 1)[
        0
    ]
    controller = controller[controller.index("function openAddTask(") :]
    controller = re.search(r"function taskHorizon.*?\n", page)[0] + controller
    script = r"""
const assert=require('node:assert/strict');
let busy=false,renders=0,chats=0,fail=false,resolveRequest;
const state={tasks:[]},openPlans=new Set(),requests=[];
let manualSteps=[];function manualSubtaskValues(){return [...manualSteps];}function renderManualSubtasks(values){manualSteps=[...values];}
const elements=new Map();
const $=s=>{if(!elements.has(s))elements.set(s,{value:'',hidden:false,querySelectorAll(){return [];},reset(){},showModal(){this.open=true;},close(){this.open=false;},focus(){},setCustomValidity(v){this.validity=v;},reportValidity(){return !this.validity;}});return elements.get(s);};
function assessSubtasks(){}function setBusy(value){busy=value;}function renderOverview(){renders++;}function renderChat(){chats++;}
function leafSteps(id,tasks){return tasks.filter(t=>t.parent_task_id===id);}
async function api(path,method,body){requests.push({path,method,body});if(fail)throw Error('Offline');return new Promise(resolve=>resolveRequest=resolve);}
async function action(work){return work();}
CONTROLLER
(async()=>{
 openAddTask('short_term');assert.equal($('#add-dialog').open,true);
 $('#add-name').value='My task';manualSteps=['Read the brief','Write the outline'];
 assert.equal(manualSteps.length,2);
 const event={preventDefault(){}};
 const saving=createManualTask(event);assert.equal(busy,true);await createManualTask(event);assert.equal(requests.length,1);
 assert.deepEqual(requests[0],{path:'/api/tasks',method:'POST',body:{title:'My task',description:'',deadline:null,user_importance_level:null,time_horizon:'short_term',subtasks:[{title:'Read the brief'},{title:'Write the outline'}]}});
 resolveRequest({...requests[0].body,id:'saved',status:'pending',version:1,subtasks:manualSteps.map((title,index)=>({id:'step-'+index,parent_task_id:'saved',title,position:index,status:'pending',version:1}))});await saving;
 assert.equal(state.tasks.length,3);assert.equal($('#add-dialog').open,false);assert.equal(renders,1);assert.equal(chats,1);
 openAddTask('long_term');assert.equal(manualSteps.length,0);$('#add-name').value='Keep my draft';fail=true;await createManualTask(event);
 assert.equal($('#add-dialog').open,true);assert.equal($('#add-name').value,'Keep my draft');assert.equal($('#add-error').textContent,'Offline');assert.equal(busy,false);assert.equal(state.tasks.length,3);
 // Adding a first subtask pins a legacy goal to its current section before saving.
 state.tasks=[{id:'legacy',title:'Legacy goal',time_horizon:null,version:2,description:'Keep old context',status:'pending'}];fail=false;
 openAddSubtask('legacy');$('#subtask-name').value='Choose the first action';const start=requests.length;
 const adding=createSubtask(event);await createSubtask(event);assert.equal(requests.length,start+1);
 assert.deepEqual(requests.at(-1),{path:'/api/tasks/legacy',method:'PATCH',body:{expected_version:2,time_horizon:'long_term'}});
 resolveRequest({...state.tasks[0],time_horizon:'long_term',version:3});await new Promise(resolve=>setImmediate(resolve));
 assert.deepEqual(requests.at(-1),{path:'/api/tasks',method:'POST',body:{title:'Choose the first action',parent_task_id:'legacy'}});
 resolveRequest({id:'new-step',title:'Choose the first action',parent_task_id:'legacy',position:0,status:'pending',version:1});await adding;
 assert.equal(state.tasks[0].time_horizon,'long_term');assert.equal(state.tasks[0].description,'Keep old context');assert.equal(state.tasks[1].parent_task_id,'legacy');assert.equal($('#subtask-dialog').open,false);
 openAddSubtask('legacy');$('#subtask-name').value='Keep this subtask draft';fail=true;await createSubtask(event);
 assert.equal($('#subtask-dialog').open,true);assert.equal($('#subtask-name').value,'Keep this subtask draft');assert.equal(state.tasks.length,2);assert.equal($('#subtask-error').textContent,'Offline');assert.equal(busy,false);
 state.tasks=[{id:'finished',version:4,status:'pending'},{id:'step',parent_task_id:'finished',status:'completed'}];fail=false;
 const reopen=reopenTask('finished');assert.deepEqual(requests.at(-1).body,{expected_version:4,status:'in_progress'});resolveRequest({});await reopen;
 assert.equal(state.tasks[1].status,'completed');
})().catch(e=>{console.error(e);process.exitCode=1;});
""".replace("CONTROLLER", controller)
    path = tmp_path / "manual-tasks.cjs"
    path.write_text(script, encoding="utf-8")
    result = subprocess.run(
        [node, str(path)], capture_output=True, text=True, check=False, timeout=15
    )
    assert result.returncode == 0, result.stdout + result.stderr
