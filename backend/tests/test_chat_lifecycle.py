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


def test_browser_task_histories_and_unsent_drafts_are_separate(tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node required")
    page = runpy.run_path(
        str(Path(__file__).resolve().parents[2] / "frontend/dashboard.py")
    )["PAGE"]
    functions = "\n".join(
        re.search(pattern, page)[0]
        for pattern in [
            r"let conversationId=.*?;\n",
            r"const chatDrafts=.*?;\n",
            r"function newChat\(\).*?\n",
            r"function rootTaskId.*?\n",
            r"function runChatScope.*?\n",
            r"function chatRuns\(\).*?\n",
            r"async function refresh\(\).*?\n",
        ]
    )
    functions += (
        "\nfunction safeChatUrl"
        + page.split("function safeChatUrl", 1)[1].split("function renderChat(){", 1)[0]
    )
    chat = (
        "function renderChat(){"
        + page.split("function renderChat(){", 1)[1].split(
            "$('#chat-scope').onchange", 1
        )[0]
    )
    script = r"""
const assert=require('node:assert/strict');
let state={tasks:[],messages:[],runs:[]},pending=null,ranges={},busy=false;
const elements=new Map(),$=key=>{if(!elements.has(key))elements.set(key,{reset(){this.value='';},value:'',textContent:'',innerHTML:'',hidden:false});return elements.get(key);};
function canHandoff(){return true;}const esc=String;function refreshBrowserState(){}function loadTrashUndo(){}
function render(){}function setMuseOpen(){}
let data={tasks:[{id:'a',title:'Task A'},{id:'b',title:'Task B'},{id:'child',title:'Subtask',parent_task_id:'a'}],runs:[
{id:'created',task_id:null,input_payload:{conversation_id:'old-visit'},related_task_ids:['a'],status:'applied'},
{id:'a-run',task_id:null,input_payload:{chat_task_id:'a'},status:'answered'},
{id:'b-run',task_id:null,input_payload:{chat_task_id:'b'},status:'answered'}],
messages:[{run_id:'created',role:'user',content:'Create task A'},{run_id:'a-run',role:'user',content:'A private discussion'},{run_id:'b-run',role:'user',content:'B discussion'}]};
async function api(path){return path==='/api/dashboard'?structuredClone(data):{};}
FUNCTIONS
CHAT
(async()=>{
 await refresh();assert.equal(state.messages.length,3);
 openTaskChat('child');assert.equal(chatTaskId,'a');assert.doesNotMatch($('#chat-scope').innerHTML,/Subtask/);assert.match($('#conversation').innerHTML,/Create task A/);assert.match($('#conversation').innerHTML,/A private discussion/);assert.doesNotMatch($('#conversation').innerHTML,/B discussion/);
 $('#message').value='A draft';pending={request_id:'retry-a',message:'A draft'};
 openTaskChat('b');assert.equal($('#message').value,'');assert.equal(pending,null);assert.match($('#conversation').innerHTML,/B discussion/);
 $('#message').value='B draft';openTaskChat('a');assert.equal($('#message').value,'A draft');assert.equal(pending.request_id,'retry-a');
 newChat();await refresh();assert.equal(chatTaskId,null);assert.equal(pending,null);assert.equal(state.messages.length,3);
 openTaskChat('a');assert.match($('#conversation').innerHTML,/A private discussion/);assert.equal($('#message').value,'');
})().catch(e=>{console.error(e);process.exitCode=1;});
""".replace("FUNCTIONS", functions).replace("CHAT", chat)
    script_file = tmp_path / "chat.cjs"
    script_file.write_text(script, encoding="utf-8")
    result = subprocess.run(
        [node, str(script_file)],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert result.returncode == 0, result.stderr
