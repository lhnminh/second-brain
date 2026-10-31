"""Keep a stated outcome visible while gathering missing details in chat."""

import json
import runpy
import shutil
import subprocess
from pathlib import Path
from uuid import uuid4

import httpx
import pytest

from second_brain.config import Settings
from second_brain.muse import Muse

MESSAGE = "I have a Duolingo Takehome assessment need to be done by next week"
HANDOFF = {
    "handler": "user",
    "reason": "The user owns the assessment.",
    "requirements": ["Current brief"],
    "done_when": "The required assessment work is complete.",
}


def test_assessment_outcome_and_work_scaffold_survive_adapter_and_persistence(
    setup, monkeypatch
):
    clients, muse, _ = setup
    value = {
        "reply": "What is in the current brief, and what is the exact due date?",
        "tasks": [
            {
                "task_id": None,
                "title": "Complete Duolingo take-home assessment",
                "description": "Due next week; exact date and brief needed.",
                "deadline": None,
                "importance_score": 70,
                "handoff": HANDOFF,
                "subtasks": [
                    {
                        "title": title,
                        "description": detail,
                        "importance_score": 70,
                        "handoff": HANDOFF,
                    }
                    for title, detail in [
                        (
                            "Review the current assessment requirements",
                            "Read the current brief and identify what is required.",
                        ),
                        (
                            "Complete the work required by the assessment",
                            "Follow the current brief; implementation details remain unknown.",
                        ),
                        (
                            "Check the work against the requirements",
                            "Compare the result with the current brief.",
                        ),
                    ]
                ],
            }
        ],
    }

    def handler(request):
        body = json.loads(request.content)
        instructions = body["messages"][0]["content"]
        assert body["max_completion_tokens"] == 8192
        assert "Root tasks must name the user's intended outcome" in instructions
        assert "Ask for missing inputs in reply" in instructions
        assert "checking the result against those requirements" in instructions
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"finish_reason": "stop", "message": {"content": json.dumps(value)}}
                ]
            },
        )

    original_client = httpx.Client
    monkeypatch.setattr(
        "second_brain.muse.httpx.Client",
        lambda **kw: original_client(transport=httpx.MockTransport(handler), **kw),
    )
    muse.converse = Muse(
        Settings(_env_file=None, meta_api_key="test-secret", vercel=None)
    ).converse
    client = clients()
    result = client.post(
        "/api/conversation",
        json={
            "request_id": str(uuid4()),
            "message": MESSAGE,
            "apply_immediately": True,
        },
    ).json()
    assert result["status"] == "applied"
    saved = clients(cookies=client.cookies).get("/api/dashboard").json()
    parent = next(t for t in saved["tasks"] if t["parent_task_id"] is None)
    children = sorted(
        (t for t in saved["tasks"] if t["parent_task_id"] == parent["id"]),
        key=lambda t: t["position"],
    )
    assert parent["title"] == "Complete Duolingo take-home assessment"
    assert parent["deadline"] is None
    assert [t["title"] for t in children] == [
        t["title"] for t in value["tasks"][0]["subtasks"]
    ]
    assert (
        next(m for m in saved["messages"] if m["role"] == "assistant")["content"]
        == value["reply"]
    )


def test_priority_heading_preserves_the_task_outcome_above_its_next_action():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required for the priority rendering harness")
    page = runpy.run_path(
        str(Path(__file__).resolve().parents[2] / "frontend/dashboard.py")
    )["PAGE"]
    functions = page.split("function orderedChildren(", 1)[1].split(
        "const sampleStepNames=", 1
    )[0]
    script = r"""
const assert=require('node:assert/strict'),vm=require('node:vm');new vm.Script(FULL_JS);
const state={tasks:[{id:'parent',title:'Complete Duolingo take-home assessment',status:'pending',description:'',deadline:null},{id:'child',parent_task_id:'parent',title:'Review the current requirements',status:'pending',position:0}]};
const esc=value=>String(value??'').replaceAll('<','&lt;').replaceAll('>','&gt;');
function agentActions(){return '';}function badge(){return '';}
function orderedChildren(FUNCTIONS
const html=overviewFocus(state.tasks[0],0);
assert.match(html,/<h3 class="focus-plan"><button type="button" data-edit="parent">Complete Duolingo take-home assessment<\/button><\/h3>/);
assert.ok(html.indexOf('Complete Duolingo take-home assessment')<html.indexOf('Next action'));
assert.ok(html.indexOf('Next action')<html.indexOf('Review the current requirements'));
assert.match(html,/data-complete="child"/);assert.doesNotMatch(html,/data-complete="parent"/);
const sample=overviewFocus(state.tasks[0],0,state.tasks,true);assert.match(sample,/<h3 class="focus-plan">Complete Duolingo take-home assessment<\/h3>/);
const single={id:'single',title:'One task',status:'pending'};
const singleHtml=overviewFocus(single,0,[single]);assert.match(singleHtml,/is-single/);assert.doesNotMatch(singleHtml,/next-action-label/);
assert.equal((singleHtml.match(/>One task<\/button>/g)||[]).length,1);
const unsafe={...state.tasks[0],title:'<script>bad</script>'};assert.doesNotMatch(overviewFocus(unsafe,0),/<script>bad/);
""".replace("FUNCTIONS", functions).replace(
        "FULL_JS", json.dumps(page.split("<script>", 1)[1].split("</script>", 1)[0])
    )
    result = subprocess.run(
        [node, "-e", script], capture_output=True, text=True, check=False, timeout=15
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_clarification_only_plan_is_repaired_by_existing_ids(setup, monkeypatch):
    clients, muse, _ = setup
    client = clients()
    parent = client.post(
        "/api/tasks", json={"title": "Complete Duolingo take-home assessment"}
    ).json()
    old_step = client.post(
        "/api/tasks",
        json={
            "title": "Share current brief and confirm deadline",
            "parent_task_id": parent["id"],
        },
    ).json()
    value = {
        "reply": "What is the current brief and exact due date?",
        "tasks": [
            {
                "task_id": parent["id"],
                "title": parent["title"],
                "description": "Current brief needed",
                "deadline": None,
                "importance_score": 70,
                "handoff": None,
                "subtasks": [
                    {
                        "title": "Complete the required assessment work",
                        "description": "Follow the brief once available.",
                        "importance_score": 70,
                        "handoff": HANDOFF,
                    },
                    {
                        "title": "Check the result against the brief",
                        "description": "Check the required work.",
                        "importance_score": 70,
                        "handoff": HANDOFF,
                    },
                ],
            },
            {
                "task_id": old_step["id"],
                "title": "Review the current assessment requirements",
                "description": "Read the brief and identify what is required.",
                "deadline": None,
                "importance_score": 70,
                "handoff": None,
                "subtasks": [],
            },
        ],
    }

    def handler(request):
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"finish_reason": "stop", "message": {"content": json.dumps(value)}}
                ]
            },
        )

    original_client = httpx.Client
    monkeypatch.setattr(
        "second_brain.muse.httpx.Client",
        lambda **kw: original_client(transport=httpx.MockTransport(handler), **kw),
    )
    muse.converse = Muse(
        Settings(_env_file=None, meta_api_key="test-secret", vercel=None)
    ).converse
    run = client.post(
        "/api/conversation",
        json={
            "request_id": str(uuid4()),
            "message": MESSAGE,
            "apply_immediately": True,
        },
    ).json()
    assert run["status"] == "applied"
    saved = client.get("/api/dashboard").json()["tasks"]
    assert len(saved) == 4
    roots = [t for t in saved if t["parent_task_id"] is None]
    assert len(roots) == 1 and roots[0]["id"] == parent["id"]
    steps = sorted(
        (t for t in saved if t["parent_task_id"] == parent["id"]),
        key=lambda t: t["position"],
    )
    assert steps[0]["id"] == old_step["id"]
    assert steps[0]["title"] == "Review the current assessment requirements"
    assert len(steps) == 3 and all(t["status"] == "pending" for t in saved)
