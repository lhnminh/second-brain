"""Exercise the shipped browser-panel controller across retries and workspace changes."""

import runpy
import shutil
import subprocess
from pathlib import Path

import pytest


def test_browser_panel_retries_controls_history_and_late_results(tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required")
    page = runpy.run_path(
        str(Path(__file__).resolve().parents[2] / "frontend/dashboard.py")
    )["PAGE"]
    controller = page.split("// Browser execution:", 1)[1].split(
        "// End browser execution.", 1
    )[0]
    controller = controller[controller.index("let browserState=") :]
    script = r"""
const assert=require('node:assert/strict');const crypto=require('node:crypto');
let state={user_id:'workspace',tasks:[{id:'task',title:'Research',version:3}]},busy=false,chatTaskId=null;function renderChat(){}
const elements=new Map(),$=id=>{if(!elements.has(id))elements.set(id,{hidden:false,value:'',innerHTML:'',textContent:'',open:true,disabled:false,src:'',getAttribute(key){return this[key]},reset(){},addEventListener(name,fn){this[name]=fn}});return elements.get(id)};
const esc=s=>String(s??'').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
let timer=null;const setTimeout=fn=>{timer=fn;return 1},clearTimeout=()=>{timer=null};
let records=[],requests=[],offline=false,delayStart=false,releaseStart;
const sample={id:'run',task_id:'task',request_id:'request',status:'running',summary:'Working',steps:[],downloads:[],frame:1,created_at:'2026-11-03T12:00:00Z'};
async function api(path,method,body){
 requests.push({path,method,body});
 if(path==='/api/browser')return {connected:true,runs:records,reason:'Screenshots go to Meta'};
 if(path==='/api/browser/runs'){
  if(offline)throw Error('Offline');if(delayStart)await new Promise(resolve=>releaseStart=resolve);
  records=[sample];return {...sample};
 }
 if(path.endsWith('/control')){sample.status=body.action==='pause'?'paused':body.action==='stop'?'stopped':'running';return {...sample};}
 return {...sample};
}
CONTROLLER
(async()=>{
 await openBrowserHandoff(state.tasks[0]);assert.equal($('#browser-form').hidden,false);
 $('#browser-url').value='https://example.com/';$('#browser-instructions').value='Only read';
 offline=true;await $('#browser-form').onsubmit({preventDefault(){}});const original=requests.find(r=>r.path==='/api/browser/runs').body;
 assert.equal($('#browser-url').value,'https://example.com/');assert.equal($('#browser-error').hidden,false);
 offline=false;delayStart=true;const pending=$('#browser-form').onsubmit({preventDefault(){}});
 await $('#browser-form').onsubmit({preventDefault(){}});
 assert.equal(requests.filter(r=>r.path==='/api/browser/runs').length,2);releaseStart();await pending;delayStart=false;
 const retry=requests.filter(r=>r.path==='/api/browser/runs').at(-1).body;
 assert.equal(original.request_id,retry.request_id);assert.equal(retry.expected_version,3);
 assert.equal($('#browser-frame').src,'/api/browser/runs/run/frames/1');assert.equal($('#browser-frame-link').href,$('#browser-frame').src);
 assert.equal($('#browser-start').disabled,false);
 await controlBrowser('pause');assert.equal($('#browser-resume').hidden,false);assert.equal($('#browser-pause').hidden,true);
 await controlBrowser('resume');assert.equal($('#browser-pause').hidden,false);
 await controlBrowser('stop');assert.equal($('#browser-stop').hidden,true);assert.equal($('#browser-again').hidden,false);
 sample.status='finished';sample.summary='<script>not HTML</script>';sample.downloads=[{id:'file',name:'<unsafe>.txt',bytes:2}];
 await openBrowserHandoff(state.tasks[0]);assert.equal($('#browser-form').hidden,true);
 assert.equal($('#browser-summary').textContent,sample.summary);assert.match($('#browser-downloads').innerHTML,/&lt;unsafe&gt;/);
 assert.match($('#browser-history').innerHTML,/finished/);
 // A late start response cannot populate a different workspace or task dialog.
 $('#browser-again').onclick();delayStart=true;const old=$('#browser-form').onsubmit({preventDefault(){}});
 state={user_id:'other',tasks:[]};releaseStart();await old;assert.equal(browserRun,null);
 $('#handoff-dialog').close();
})().catch(e=>{console.error(e);process.exitCode=1});
""".replace("CONTROLLER", controller)
    # The mock's close event follows the browser's dialog close lifecycle.
    script = script.replace(
        "$('#handoff-dialog').close();", "$('#handoff-dialog').close?.();"
    )
    path = tmp_path / "browser-panel.cjs"
    path.write_text(script, encoding="utf-8")
    result = subprocess.run(
        [node, str(path)], capture_output=True, text=True, timeout=15, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "button[data-handoff]:disabled{cursor:default}" in page
