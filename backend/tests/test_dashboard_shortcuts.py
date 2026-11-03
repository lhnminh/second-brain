import re
import runpy
import shutil
import subprocess
from pathlib import Path

import pytest


def test_ctrl_enter_sends_and_plain_enter_preserves_multiline_input(tmp_path):
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
const send=(overrides={})=>{let prevented=false;callback({key:'Enter',ctrlKey:false,metaKey:false,isComposing:false,repeat:false,preventDefault(){prevented=true;},...overrides});return prevented;};
assert.equal(send(),false);assert.equal(sends,0);
assert.equal(send({ctrlKey:true}),true);assert.equal(sends,1);
assert.equal(send({metaKey:true}),true);assert.equal(sends,2);
send({ctrlKey:true,repeat:true});send({ctrlKey:true,isComposing:true});busy=true;send({ctrlKey:true});busy=false;voiceSession={};send({ctrlKey:true});assert.equal(sends,2);
""".replace("HANDLER", handler)
    path = tmp_path / "shortcut.cjs"
    path.write_text(script, encoding="utf-8")
    result = subprocess.run(
        [node, str(path)], check=False, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert "Control+Enter Meta+Enter" in page
    assert "Bigger means more important</span>" not in page
    assert '<span class="brand-mark"' not in page
