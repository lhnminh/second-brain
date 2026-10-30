"""Fresh visits keep workspace data while scoping conversational context."""

import re
import runpy
import shutil
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest


def test_new_chat_excludes_prior_messages_but_keeps_saved_work(setup):
    clients, muse, _ = setup
    client = clients()
    snapshots = []

    def respond(snapshot, message):
        snapshots.append(snapshot)
        return {"reply": "Understood.", "tasks": []}

    muse.converse = respond
    task = client.post("/api/tasks", json={"title": "Saved work"}).json()
    first_chat, next_chat = str(uuid4()), str(uuid4())

    def send(chat, message):
        return client.post(
            "/api/conversation",
            json={
                "request_id": str(uuid4()),
                "conversation_id": chat,
                "message": message,
            },
        )

    first = send(first_chat, "First visit").json()
    assert send(first_chat, "Follow up").status_code == 200
    assert [m["content"] for m in snapshots[-1]["recent_messages"]] == [
        "First visit",
        "Understood.",
    ]
    assert snapshots[-1]["recent_runs"][0]["id"] == first["id"]
    assert send(next_chat, "New visit").status_code == 200
    assert snapshots[-1]["recent_messages"] == []
    assert snapshots[-1]["recent_runs"] == []
    assert snapshots[-1]["tasks"][0]["id"] == task["id"]
    assert len(client.get("/api/dashboard").json()["messages"]) == 6
    retry = {**first["input_payload"], "conversation_id": next_chat}
    assert client.post("/api/conversation", json=retry).status_code == 409


def test_browser_chat_filters_reload_and_resets_login():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required for the chat lifecycle browser harness")
    page = runpy.run_path(
        str(Path(__file__).resolve().parents[2] / "frontend/dashboard.py")
    )["PAGE"]
    functions = "\n".join(
        re.search(pattern, page)[0]
        for pattern in [
            r"let conversationId=.*?;\n",
            r"function newChat\(\).*?\n",
            r"function chatRuns\(\).*?\n",
            r"async function refresh\(\).*?\n",
        ]
    )
    script = r"""
const assert=require('node:assert/strict');
let id=0;const crypto={randomUUID:()=>String(++id)};
let state={tasks:[],messages:[],runs:[]},pending={},ranges;
const elements=new Map();
const $=key=>{if(!elements.has(key))elements.set(key,{reset(){this.didReset=true;}});return elements.get(key);};
let renders=0;function render(){renders++;}
let data={tasks:[{id:'saved'}],runs:[{id:'old',input_payload:{conversation_id:'previous'}}],messages:[{run_id:'old',content:'Old message'}]};
async function api(path){return path==='/api/dashboard'?structuredClone(data):{};}
FUNCTIONS
(async()=>{
 await refresh();assert.equal(state.messages.length,0);assert.equal(state.tasks.length,1);
 data.runs.push({id:'current',input_payload:{conversation_id:conversationId}});
 data.messages.push({run_id:'current',content:'Current message'});
 await refresh();assert.deepEqual(state.messages.map(m=>m.content),['Current message']);
 const prior=conversationId;newChat();assert.notEqual(conversationId,prior);
 assert.equal(pending,null);assert.equal($('#chat-form').didReset,true);
 await refresh();assert.equal(state.messages.length,0);assert.equal(state.tasks.length,1);
})().catch(e=>{console.error(e);process.exit(1);});
""".replace("FUNCTIONS", functions)
    result = subprocess.run(
        [node, "-e", script], check=False, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
