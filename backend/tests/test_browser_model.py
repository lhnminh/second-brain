import json

import httpx
import pytest
from pydantic import ValidationError

from second_brain.browser_driver import BrowserDriver, public_url, safe_filename
from second_brain.browser_model import ACTIONS, BROWSER_ACTION, BrowserMuse
from second_brain.config import Settings
from second_brain.muse import MuseFailure


def test_muse_browser_contract_is_validated_and_server_side(monkeypatch):
    requests = []

    def post(self, url, **kwargs):
        requests.append((url, kwargs))
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "status": "completed",
                "output": [
                    {
                        "type": "function_call",
                        "call_id": "one",
                        "name": "browser_action",
                        "arguments": json.dumps(
                            {
                                "actions": [
                                    {
                                        "type": "click",
                                        "button": "left",
                                        "x": 20,
                                        "y": 30,
                                    }
                                ]
                            }
                        ),
                    }
                ],
            },
        )

    monkeypatch.setattr(httpx.Client, "post", post)
    model = BrowserMuse(Settings(_env_file=None, meta_api_key="fake-test-key"))
    result = model.turn([{"role": "user", "content": "test"}])
    assert result["call"]["actions"][0]["x"] == 20
    url, request = requests[0]
    assert url.endswith("/responses")
    assert (
        request["json"]["store"] is False
        and request["json"]["parallel_tool_calls"] is False
    )
    assert [t["name"] for t in request["json"]["tools"]] == [
        "browser_action",
        "open_url",
        "pause_for_user",
    ]
    assert '"oneOf"' not in json.dumps(BROWSER_ACTION)
    assert '"discriminator"' not in json.dumps(BROWSER_ACTION)


@pytest.mark.parametrize(
    "output",
    [
        [
            {
                "type": "function_call",
                "call_id": "1",
                "name": "run_shell",
                "arguments": "{}",
            }
        ],
        [
            {
                "type": "function_call",
                "call_id": "1",
                "name": "browser_action",
                "arguments": '{"actions":[{"type":"click","x":true,"y":20}]}',
            }
        ],
        [
            {
                "type": "function_call",
                "call_id": "1",
                "name": "browser_action",
                "arguments": '{"actions":[{"type":"type","text":"x","shell":"bad"}]}',
            }
        ],
        [{"type": "computer_call", "actions": [{"type": "click", "x": 1, "y": 2}]}],
    ],
)
def test_invalid_or_unadvertised_model_actions_fail_closed(monkeypatch, output):
    monkeypatch.setattr(
        httpx.Client,
        "post",
        lambda self, url, **kwargs: httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={"status": "completed", "output": output},
        ),
    )
    with pytest.raises(MuseFailure):
        BrowserMuse(Settings(_env_file=None, meta_api_key="fake-test-key")).turn([])


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "http://127.0.0.1/",
        "http://[::1]/",
        "http://169.254.169.254/",
        "https://localhost/",
        "https://host.local/",
        "https://user:pass@example.com/",
        "https://example.com:8000/",
    ],
)
def test_local_and_nonwebsite_addresses_are_rejected(url):
    with pytest.raises(ValueError):
        public_url(url, resolve=False)


def test_driver_cannot_use_local_clipboard_or_browser_file_shortcuts():
    driver = BrowserDriver("unused")
    for keys in [
        ["Control", "v"],
        ["Control", "o"],
        ["Meta", "r"],
        ["Control+v"],
        ["F12"],
    ]:
        with pytest.raises(ValueError):
            driver.perform({"type": "keypress", "keys": keys})
    with pytest.raises(ValueError):
        driver.perform({"type": "click", "button": "left", "x": 1280, "y": 30})
    assert safe_filename("../../a\\b.txt") == "b.txt"
    assert "/" not in safe_filename("../evil.txt")
    assert ACTIONS.validate_python({"type": "screenshot"}).type == "screenshot"
    with pytest.raises(ValidationError):
        ACTIONS.validate_python({"type": "shell", "command": "bad"})
