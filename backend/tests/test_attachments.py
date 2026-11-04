"""Real parsers/storage plus a simulated Muse response, with no network calls."""

import base64
import io
import json
import zipfile
from uuid import uuid4

import httpx
import pytest
from PIL import Image
from pypdf import PdfWriter
from sqlalchemy import select

from second_brain.attachments import MAX_FILE_BYTES, model_file, validate_file
from second_brain.config import Settings
from second_brain.db import attachments
from second_brain.muse import Muse, MuseFailure


def document(text="A general document with a table cell."):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as archive:
        archive.writestr(
            "word/document.xml",
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>'
            + text
            + "</w:t></w:r></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>Blue</w:t></w:r></w:p></w:tc></w:tr></w:tbl></w:body></w:document>",
        )
    return out.getvalue()


def pdf(pages=1):
    out = io.BytesIO()
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=200, height=200)
    writer.write(out)
    return out.getvalue()


def picture(format="PNG"):
    out = io.BytesIO()
    Image.new("RGB", (32, 32), "red").save(out, format=format)
    return out.getvalue()


def upload(client, name="notes.txt", data=b"Remember the blue notebook.", file_id=None):
    return client.put(
        "/api/attachments/" + (file_id or str(uuid4())),
        params={"filename": name},
        content=data,
        headers={"Content-Type": "application/octet-stream"},
    )


def send(client, files=(), message="What does this file say?", **values):
    return client.post(
        "/api/conversation",
        json={
            "request_id": str(uuid4()),
            "message": message,
            "attachment_ids": list(files),
            "apply_immediately": True,
            **values,
        },
    )


@pytest.mark.parametrize(
    "name,data",
    [
        ("notes.txt", b"Hello"),
        ("unicode.txt", "Olá".encode("utf-16")),
        ("plan.docx", document()),
        ("scan.pdf", pdf()),
        ("image.png", picture()),
        ("image.jpg", picture("JPEG")),
        ("image.webp", picture("WEBP")),
        ("image.gif", picture("GIF")),
    ],
)
def test_supported_files_are_persisted_and_downloadable(setup, name, data):
    clients, _, engine = setup
    client = clients()
    file = upload(client, name, data).json()
    assert file["filename"] == name and file["size"] == len(data)
    assert "data" not in file and "text" not in file
    download = client.get("/api/attachments/" + file["id"])
    assert download.status_code == 200 and download.content == data
    assert download.headers["cache-control"] == "no-store"
    assert download.headers["x-content-type-options"] == "nosniff"
    assert download.headers["content-disposition"].startswith("attachment;")
    returning = clients(cookies=client.cookies)
    assert returning.get("/api/attachments/" + file["id"]).content == data
    with engine.connect() as c:
        stored = dict(
            c.execute(select(attachments).where(attachments.c.id == file["id"]))
            .mappings()
            .one()
        )
    block = model_file(stored)
    if name.endswith((".txt", ".docx")):
        assert block["type"] == "input_text"
        if name.endswith("docx"):
            assert "Blue" in block["text"]
    else:
        encoded = block.get("image_url") or block["file_data"]
        assert base64.b64decode(encoded.split(",", 1)[1]) == data


def test_owned_upload_retry_and_cross_workspace_isolation(setup):
    clients, muse, _ = setup
    first, other = clients(), clients()
    file_id = str(uuid4())
    file = upload(first, file_id=file_id).json()
    assert upload(first, file_id=file_id).json() == file
    assert upload(first, data=b"Different", file_id=file_id).status_code == 409
    assert upload(other, file_id=file_id).status_code == 404
    assert other.get("/api/attachments/" + file_id).status_code == 404
    muse.converse = lambda *_: pytest.fail(
        "An unowned attachment must never reach Muse"
    )
    assert send(other, [file_id]).status_code == 404
    assert other.get("/api/dashboard").json()["messages"] == []
    assert upload(first, file_id=str(uuid4())).status_code == 201
    assert (
        first.put(
            "/api/attachments/" + str(uuid4()),
            params={"filename": "x.txt"},
            content=b"data",
            headers={"Origin": "https://evil.example"},
        ).status_code
        == 403
    )


@pytest.mark.parametrize(
    "name,data,status",
    [
        ("empty.txt", b"", 413),
        ("big.txt", b"x" * (MAX_FILE_BYTES + 1), 413),
        ("file.exe", b"binary", 415),
        ("old.doc", b"binary", 415),
        ("bad.pdf", b"not pdf", 422),
        ("bad.docx", b"not zip", 422),
        ("bad.png", b"not image", 422),
        ("wrong.jpg", picture(), 422),
        ("too-long.txt", b"a" * 100001, 422),
        ("binary.txt", b"a\x00b", 422),
        ("too-many-pages.pdf", pdf(51), 422),
    ],
)
def test_invalid_files_do_not_save(setup, name, data, status):
    clients, _, engine = setup
    client = clients()
    response = upload(client, name, data)
    assert response.status_code == status
    with engine.connect() as c:
        assert not c.execute(select(attachments)).first()


def test_files_remain_in_their_chat_and_survive_failed_runs(setup):
    clients, muse, _ = setup
    client = clients()
    task = client.post("/api/tasks", json={"title": "Task A"}).json()
    child = client.post(
        "/api/tasks", json={"title": "Step A", "parent_task_id": task["id"]}
    ).json()
    other = client.post("/api/tasks", json={"title": "Task B"}).json()
    file = upload(client).json()
    seen = []
    muse.converse = lambda state, message: (
        seen.append(state) or {"reply": "The notebook is blue.", "tasks": []}
    )
    body = {
        "request_id": str(uuid4()),
        "message": "",
        "attachment_ids": [file["id"]],
        "chat_task_id": child["id"],
    }
    first = client.post("/api/conversation", json=body).json()
    assert first["status"] == "answered" and len(seen) == 1
    assert (
        client.post("/api/conversation", json=body).json()["id"] == first["id"]
        and len(seen) == 1
    )
    assert seen[-1]["attachments"][0]["just_attached"] is True
    assert "blue notebook" in seen[-1]["_attachment_content"][0]["text"]
    assert send(client, message="Follow up", chat_task_id=task["id"]).status_code == 200
    assert seen[-1]["attachments"][0]["just_attached"] is False
    assert (
        send(client, message="Other task", chat_task_id=other["id"]).status_code == 200
    )
    assert seen[-1]["_attachment_content"] == []
    assert send(client, message="General").status_code == 200
    assert seen[-1]["_attachment_content"] == []
    data = clients(cookies=client.cookies).get("/api/dashboard").json()
    user = next(
        m
        for m in data["messages"]
        if m["run_id"] == first["id"] and m["role"] == "user"
    )
    assert user["attachments"] == [file]
    assert "blue notebook" not in json.dumps(data)
    muse.converse = lambda *_: (_ for _ in ()).throw(MuseFailure("offline"))
    assert (
        send(client, [file["id"]], chat_task_id=task["id"]).json()["status"] == "failed"
    )
    assert client.get("/api/attachments/" + file["id"]).status_code == 200


def test_message_and_provider_budgets_are_checked_before_model_call(setup):
    clients, muse, _ = setup
    client = clients()
    muse.converse = lambda *_: pytest.fail("Invalid input reached Muse")
    assert send(client, message="").status_code == 422
    file = upload(client, "pages.pdf", pdf(30)).json()
    other = upload(client, "more.pdf", pdf(30)).json()
    assert send(client, [file["id"], other["id"]]).status_code == 422
    assert send(client, [file["id"], file["id"]]).status_code == 422
    assert send(client, [str(uuid4()) for _ in range(6)]).status_code == 422


def test_attachment_uses_real_responses_multimodal_contract(monkeypatch):
    requests = []

    def post(self, url, **kwargs):
        requests.append((url, kwargs["json"]))
        return httpx.Response(
            200,
            json={
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": json.dumps(
                                    {
                                        "reply": "A red square.",
                                        "tasks": [],
                                        "chat_task_id": None,
                                    }
                                ),
                            }
                        ],
                    }
                ],
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx.Client, "post", post)
    image = model_file(validate_file("red.png", picture()))
    muse = Muse(Settings(_env_file=None, meta_api_key="test-secret"))
    result = muse.converse(
        {"tasks": [], "_attachment_content": [image]}, "Describe this"
    )
    assert result.reply == "A red square."
    url, body = requests[0]
    assert url.endswith("/responses") and body["store"] is False
    content = body["input"][0]["content"]
    assert content[1] == image and "_attachment_content" not in content[0]["text"]
