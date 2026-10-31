import json

import httpx
import pytest

from second_brain.config import Settings
from second_brain.muse import Muse, MuseFailure

VALID = {"reply": "Review", "importance_score": 70, "subtasks": []}


def configure(monkeypatch, handler):
    original_client = httpx.Client
    monkeypatch.setattr(
        "second_brain.muse.httpx.Client",
        lambda **kw: original_client(
            transport=httpx.MockTransport(handler),
            **kw,
        ),
    )
    return Muse(Settings(_env_file=None, meta_api_key="test-secret", vercel=None))


def test_meta_request_contract(monkeypatch):
    def handler(request):
        assert str(request.url) == "https://api.meta.ai/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-secret"
        body = json.loads(request.content)
        assert body["model"] == "muse-spark-1.3"
        assert body["response_format"]["type"] == "json_schema"
        assert body["store"] is False
        assert json.loads(body["messages"][1]["content"])["state"] == {
            "task": {"title": "Homework"}
        }
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"finish_reason": "stop", "message": {"content": json.dumps(VALID)}}
                ]
            },
        )

    muse = configure(monkeypatch, handler)
    assert muse.plan({"task": {"title": "Homework"}}, "plan").importance_score == 70


@pytest.mark.parametrize(
    "case",
    [
        "401",
        "429",
        "500",
        "redirect",
        "malformed",
        "truncated",
        "invalid_schema",
        "timeout",
    ],
)
def test_meta_failure_is_safe(monkeypatch, case):
    def handler(request):
        if case == "timeout":
            raise httpx.ReadTimeout("test-secret provider details", request=request)
        if case.isdigit():
            return httpx.Response(int(case), text="test-secret provider details")
        if case == "redirect":
            return httpx.Response(302, headers={"Location": "https://other.example/"})
        if case == "malformed":
            return httpx.Response(200, text="not JSON test-secret")
        proposal = VALID if case == "truncated" else {**VALID, "importance_score": True}
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "length" if case == "truncated" else "stop",
                        "message": {"content": json.dumps(proposal)},
                    }
                ]
            },
        )

    with pytest.raises(MuseFailure) as error:
        configure(monkeypatch, handler).plan({}, "plan")
    assert "test-secret" not in str(error.value)


def test_no_key_no_network(monkeypatch):
    monkeypatch.delenv("META_API_KEY", raising=False)
    with pytest.raises(MuseFailure):
        Muse(Settings(_env_file=None, meta_api_key=None)).plan({}, "plan")


def test_hosted_demo_requires_persistence_and_token():
    with pytest.raises(ValueError):
        Settings(
            _env_file=None,
            vercel="1",
            database_url="sqlite:///./test.db",
            mock_auth_token="token",
        ).validate_hosted()
    with pytest.raises(ValueError):
        Settings(
            _env_file=None,
            vercel="1",
            database_url="postgresql://unused/db",
            mock_auth_token=None,
        ).validate_hosted()
    Settings(
        _env_file=None,
        vercel="1",
        database_url="postgresql://unused/db",
        mock_auth_token="token",
    ).validate_hosted()


def test_blank_env_uses_defaults(tmp_path):
    env = tmp_path / ".env"
    env.write_text("META_BASE_URL=\nMETA_MODEL=\nDATABASE_URL=\n")
    settings = Settings(_env_file=env)
    assert settings.meta_model == "muse-spark-1.3"
    assert settings.meta_base_url == "https://api.meta.ai/v1"
    assert settings.database_url.startswith("sqlite:")


def test_conversation_uses_structured_objects(monkeypatch):
    def handler(request):
        body = json.loads(request.content)
        contract = body["response_format"]["json_schema"]
        assert contract["name"] == "conversation_plan"
        assert "tasks" in contract["schema"]["properties"]
        assert contract["strict"] is True
        assert "task_id=null" in body["messages"][0]["content"]
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "content": json.dumps(
                                {"reply": "What subject?", "tasks": []}
                            )
                        },
                    }
                ]
            },
        )

    assert configure(monkeypatch, handler).converse({}, "Homework").tasks == []


@pytest.mark.parametrize("kind", ["plan", "conversation"])
@pytest.mark.parametrize("classified", [True, False])
def test_classification_is_part_of_the_structured_generation(
    monkeypatch, kind, classified
):
    handoff = {
        "handler": "muse",
        "reason": "Computer work",
        "requirements": ["Notes"],
        "done_when": "An outline is ready",
    }
    child = {
        "title": "Draft an outline",
        "description": "Use the notes",
        "importance_score": 60,
    }
    if classified:
        child["handoff"] = handoff
    result = (
        {"reply": "Review", "importance_score": 60, "subtasks": [child]}
        if kind == "plan"
        else {
            "reply": "Review",
            "tasks": [
                {
                    "task_id": None,
                    "title": "Prepare proposal",
                    "description": "Use the notes",
                    "deadline": None,
                    "importance_score": 60,
                    "handoff": handoff,
                    "subtasks": [child],
                }
            ],
        }
    )

    def handler(request):
        body = json.loads(request.content)
        assert (
            "handoff"
            in body["response_format"]["json_schema"]["schema"]["$defs"][
                "SuggestedTask"
            ]["required"]
        )
        assert (
            "Classify every proposed task and subtask" in body["messages"][0]["content"]
        )
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": json.dumps(result)},
                    }
                ]
            },
        )

    muse = configure(monkeypatch, handler)
    call = muse.plan if kind == "plan" else muse.converse
    if classified:
        response = call({}, "Plan it")
        steps = response.subtasks if kind == "plan" else response.tasks[0].subtasks
        assert steps[0].handoff.handler == "muse"
    else:
        with pytest.raises(MuseFailure):
            call({}, "Plan it")


def test_direct_mode_instructions_and_cleared_assessment_are_preserved(monkeypatch):
    task_id = "3f6c5e94-df91-4734-a67b-71d2ea89f643"

    def handler(request):
        body = json.loads(request.content)
        instructions = body["messages"][0]["content"]
        assert "The app will save" in instructions
        assert "only the user's later approval" not in instructions
        result = {
            "reply": "The task title is updated.",
            "tasks": [
                {
                    "task_id": task_id,
                    "title": "Updated title",
                    "description": "",
                    "deadline": None,
                    "importance_score": 60,
                    "subtasks": [],
                    "handoff": None,
                }
            ],
        }
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": json.dumps(result)},
                    }
                ]
            },
        )

    snapshot = {
        "apply_immediately": True,
        "tasks": [{"id": task_id, "handoff": None, "handoff_source": "user"}],
    }
    result = configure(monkeypatch, handler).converse(snapshot, "Rename the task")
    assert result.tasks[0].handoff is None


def test_finished_assessment_is_not_an_active_duplicate_in_model_context(monkeypatch):
    old_id = "b0842fd6-8cbb-4936-b323-7373b5258c4e"
    snapshot = {
        "apply_immediately": True,
        "tasks": [],
        "completed_tasks": [
            {
                "id": old_id,
                "title": "Duolingo Takehome assessment",
                "status": "completed",
                "completion_reason": "completed",
            }
        ],
    }

    def handler(request):
        body = json.loads(request.content)
        instructions = body["messages"][0]["content"]
        assert "state.tasks list is current work" in instructions
        assert "state.completed_tasks is finished history" in instructions
        assert "completed history is not an active match" in instructions
        assert "Never duplicate saved tasks" not in instructions
        assert json.loads(body["messages"][1]["content"])["state"] == snapshot
        task = {
            "task_id": None,
            "title": "Current Duolingo assessment",
            "description": "Exact due date and brief needed",
            "deadline": None,
            "importance_score": 70,
            "subtasks": [],
            "handoff": {
                "handler": "user",
                "reason": "The user owns the assessment",
                "requirements": ["Current brief"],
                "done_when": "Current assessment completed",
            },
        }
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "content": json.dumps(
                                {
                                    "reply": "Here is the new assessment task.",
                                    "tasks": [task],
                                }
                            )
                        },
                    }
                ]
            },
        )

    result = configure(monkeypatch, handler).converse(
        snapshot, "I have a Duolingo Takehome assessment need to be done by next week."
    )
    assert result.tasks[0].task_id is None


def test_existing_unassessed_task_can_be_updated_without_inventing_classification(
    monkeypatch,
):
    task_id = "92591fe7-3625-48fb-a1a9-5714c714535e"
    result = {
        "reply": "The task now reflects the requested outcome.",
        "tasks": [
            {
                "task_id": task_id,
                "title": "Review the current assessment requirements",
                "description": "Read the requirements in the current brief.",
                "deadline": None,
                "importance_score": 60,
                "handoff": None,
                "subtasks": [],
            }
        ],
    }

    def handler(request):
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": json.dumps(result)},
                    }
                ]
            },
        )

    muse = configure(monkeypatch, handler)
    snapshot = {
        "apply_immediately": True,
        "tasks": [{"id": task_id, "handoff": None, "handoff_source": None}],
    }
    value = muse.converse(snapshot, "Improve the existing step")
    assert str(value.tasks[0].task_id) == task_id and value.tasks[0].handoff is None
