import re
import runpy
import shutil
import subprocess
from pathlib import Path

import pytest


def test_enter_sends_and_shift_enter_preserves_multiline_input(tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node required")
    page = runpy.run_path(
        str(Path(__file__).resolve().parents[2] / "frontend/dashboard.py")
    )["PAGE"]
    handler = re.search(r"\$\('#message'\)\.addEventListener\('keydown'.*?;\n", page)[0]
    script = r"""
const assert=require('node:assert/strict');
let callback,sends=0,busy=false,voiceSession=null;
const $=key=>key==='#message'?{addEventListener:(type,fn)=>callback=fn}:{requestSubmit:()=>sends++};
HANDLER
const send=(overrides={})=>{let prevented=false;callback({key:'Enter',ctrlKey:false,metaKey:false,shiftKey:false,isComposing:false,repeat:false,preventDefault(){prevented=true;},...overrides});return prevented;};
assert.equal(send({shiftKey:true}),false);assert.equal(sends,0);
assert.equal(send(),true);assert.equal(sends,1);
assert.equal(send({metaKey:true}),true);assert.equal(sends,2);
send({ctrlKey:true,repeat:true});send({ctrlKey:true,isComposing:true});busy=true;send({ctrlKey:true});busy=false;voiceSession={};send({ctrlKey:true});assert.equal(sends,2);
""".replace("HANDLER", handler)
    path = tmp_path / "shortcut.cjs"
    path.write_text(script, encoding="utf-8")
    result = subprocess.run(
        [node, str(path)], check=False, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert "aria-keyshortcuts','Enter" in page
    assert "Bigger means more important</span>" not in page
    assert '<span class="brand-mark"' not in page


def test_bubble_reveal_aligns_the_bottom_and_respects_reduced_motion(tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node required")
    page = runpy.run_path(
        str(Path(__file__).resolve().parents[2] / "frontend/dashboard.py")
    )["PAGE"]
    reveal = (
        "function revealBubbleDetails(){"
        + page.split("function revealBubbleDetails(){", 1)[1].split(
            "// Completion feedback", 1
        )[0]
    )
    script = r"""
const assert=require('node:assert/strict');let selectedBubble='one',reduced=false,callback;const calls=[];
const panel={hidden:false,scrollIntoView:args=>calls.push(args)};const $=()=>panel;const requestAnimationFrame=fn=>callback=fn;const motionAllowed=()=>!reduced;
REVEAL
revealBubbleDetails();callback();assert.deepEqual(calls.at(-1),{block:'end',inline:'nearest',behavior:'smooth'});
reduced=true;revealBubbleDetails();callback();assert.equal(calls.at(-1).behavior,'instant');
revealBubbleDetails();selectedBubble='two';callback();assert.equal(calls.length,2);
panel.hidden=true;revealBubbleDetails();callback();assert.equal(calls.length,2);
""".replace("REVEAL", reveal)
    path = tmp_path / "bubble-scroll.cjs"
    path.write_text(script, encoding="utf-8")
    result = subprocess.run(
        [node, str(path)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
