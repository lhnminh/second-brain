"""One mounted composer, a general launcher and root-scoped task dialogs."""

import re
import runpy
import shutil
import subprocess
from pathlib import Path

import pytest


def test_launcher_task_dialog_handoff_and_optional_browser(tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required")
    page = runpy.run_path(
        str(Path(__file__).resolve().parents[2] / "frontend/dashboard.py")
    )["PAGE"]
    root = re.search(r"function rootTaskId.*?\n", page)[0]
    opener = (
        "function openTaskChat("
        + page.split("function openTaskChat(", 1)[1].split(
            "$('#chat-scope').onchange", 1
        )[0]
    )
    surface = page.split("// Muse disclosure:", 1)[1].split(
        "// End Muse disclosure.", 1
    )[0]
    surface = surface[surface.index("const generalChatHome=") :]
    handoff = (
        "function handoffToMuse("
        + page.split("function handoffToMuse(", 1)[1].split("$('#close-handoff')", 1)[0]
    )
    script = (
        r"""
const assert=require('node:assert/strict');const requestAnimationFrame=fn=>fn();
let busy=false,voiceSession=null,pending=null,chatTaskId=null,chatWorkId=null,delegatedTaskId=null;
const chatDrafts=new Map(),chatRequests=new Map(),els=new Map(),events={};
function element(){const classes=new Set();return {value:'',textContent:'',hidden:false,open:false,inert:true,attrs:{},listeners:{},parentElement:null,
 classList:{add:v=>classes.add(v),remove:v=>classes.delete(v),contains:v=>classes.has(v),toggle(v,on){on?classes.add(v):classes.delete(v)}},
 appendChild(child){child.parentElement=this},getAttribute(key){return this.attrs[key]},setAttribute(key,v){this.attrs[key]=v},focus(){},showModal(){this.open=true},close(){this.open=false;this.listeners.close?.()},addEventListener(key,fn){this.listeners[key]=fn}};}
const $=id=>{if(!els.has(id))els.set(id,element());return els.get(id)};
const home=element();home.appendChild($('#muse-chat'));
const state={user_id:'owner',tasks:[{id:'root',title:'Main work',status:'pending'},{id:'child',parent_task_id:'root',title:'Research sources',status:'pending',handoff:{handler:'muse'}},{id:'other',title:'Other task',status:'pending'}]};
const document={addEventListener:(key,fn)=>events[key]=fn};const localStorage={setItem(){}};
let rendered=[],browserOpened=[],sent=[];function renderChat(){rendered.push(chatTaskId)};function endVoice(){voiceSession=null}
function canHandoff(t){return !!t&&t.status!=='completed'&&(t.handoff?.handler==='muse'||!t.parent_task_id)}
function openBrowserHandoff(task){browserOpened.push(task.id)}
$('#chat-form').requestSubmit=()=>{sent.push({scope:chatTaskId,task:delegatedTaskId,message:$('#message').value});$('#message').value=''};
ROOT
OPENER
SURFACE
HANDOFF
$('#message').value='My general draft';$('#muse-launcher').onclick();assert.equal(chatTaskId,null);assert.equal($('#muse-chat').parentElement,home);
openTaskChat('child');assert.equal(chatTaskId,'root');assert.equal(chatWorkId,'child');assert.equal($('#task-chat-dialog').open,true);assert.equal($('#muse-chat').parentElement,$('#task-chat-host'));assert.equal($('#message').value,'');
$('#message').value='My task draft';handoffToMuse('child');assert.equal(sent.length,1);assert.equal(sent[0].scope,'root');assert.equal(sent[0].task,'child');assert.equal($('#message').value,'My task draft');assert.equal($('#handoff-dialog').open,false);
$('#use-task-browser').onclick();assert.deepEqual(browserOpened,['child']);assert.equal($('#handoff-dialog').open,true);$('#handoff-dialog').close();
$('#close-muse').onclick();assert.equal($('#task-chat-dialog').open,false);
$('#muse-launcher').onclick();assert.equal(chatTaskId,null);assert.equal($('#muse-chat').parentElement,home);assert.equal($('#message').value,'My general draft');assert.equal($('#task-chat-dialog').open,false);
openTaskChat('root');assert.equal($('#message').value,'My task draft');openTaskChat('other');assert.equal($('#message').value,'');openTaskChat('root');assert.equal($('#message').value,'My task draft');
$('#use-task-browser').onclick();assert.equal(browserOpened.at(-1),'root');
$('#handoff-dialog').close();pending={request_id:'uncertain',delegated_task_id:'child'};$('#message').value='Retry child question';openTaskChat(null);openTaskChat('root');assert.equal(pending.request_id,'uncertain');assert.equal(delegatedTaskId,'child');assert.equal($('#message').value,'Retry child question');
""".replace("ROOT", root)
        .replace("OPENER", opener)
        .replace("SURFACE", surface)
        .replace("HANDOFF", handoff)
    )
    path = tmp_path / "surfaces.cjs"
    path.write_text(script, encoding="utf-8")
    result = subprocess.run(
        [node, str(path)], capture_output=True, text=True, timeout=15, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert '<select id="chat-scope" hidden' in page
    assert "Transcript ready. Review or edit it, then Send." not in page


def test_chat_renderer_formats_links_without_injecting_html(tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required")
    page = runpy.run_path(
        str(Path(__file__).resolve().parents[2] / "frontend/dashboard.py")
    )["PAGE"]
    helpers = (
        "function safeChatUrl"
        + page.split("function safeChatUrl", 1)[1].split("function renderChat(){", 1)[0]
    )
    script = r"""
const assert=require('node:assert/strict');const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
HELPERS
assert.equal(safeChatUrl('javascript:alert(1)'),null);assert.equal(safeChatUrl('https://user:pass@example.com'),null);
const out=chatContent('**Answer** <img src=x onerror=bad> [IANA](https://www.iana.org/help/example-domains) `code`');
assert.match(out,/<strong>Answer<\/strong>/);assert.doesNotMatch(out,/<img/);assert.match(out,/&lt;img/);assert.match(out,/rel="noopener noreferrer"/);assert.match(out,/<code>code<\/code>/);
const recipe=chatContent('## Dinner\n\n**Serves 4** 【4311417271938779975†L40-L44】\n\n- Chicken\n- Tomatoes');assert.doesNotMatch(recipe,/4311417271938779975|【|†/);assert.match(recipe,/<h4>Dinner<\/h4>/);assert.match(recipe,/<ul><li>Chicken<\/li><li>Tomatoes<\/li><\/ul>/);
""".replace("HELPERS", helpers)
    path = tmp_path / "format.cjs"
    path.write_text(script, encoding="utf-8")
    result = subprocess.run(
        [node, str(path)], capture_output=True, text=True, timeout=15, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_deletion_toast_expires_and_recovery_remains_available(tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required")
    page = runpy.run_path(
        str(Path(__file__).resolve().parents[2] / "frontend/dashboard.py")
    )["PAGE"]
    controller = page.split("// Reversible trash:", 1)[1].split(
        "// End reversible trash.", 1
    )[0]
    controller = controller[controller.index("let trashUndo=") :]
    script = r"""
const assert=require('node:assert/strict');const els=new Map();const $=key=>{if(!els.has(key))els.set(key,{hidden:true,textContent:''});return els.get(key)};
const state={user_id:'workspace'};let timer=null,delay=null;const setTimeout=(fn,ms)=>{timer=fn;delay=ms;return 1},clearTimeout=()=>{timer=null};
const sessionStorage={setItem(){},getItem(){return '[]'}};
CONTROLLER
trashUndo=[{id:'first',title:'First task',deletion_id:'one'}];saveTrashUndo(true);
assert.equal($('#trash-undo').hidden,false);assert.equal(delay,8000);assert.equal($('#undo-trash-menu').hidden,false);
timer();assert.equal($('#trash-undo').hidden,true);assert.equal(trashUndo.length,1);assert.equal($('#undo-trash-menu').hidden,false);
trashUndo.push({id:'second',title:'Second task',deletion_id:'two'});saveTrashUndo(true);assert.equal($('#trash-label').textContent,'Deleted Second task');$('#dismiss-trash').onclick();assert.equal($('#trash-undo').hidden,true);assert.equal(trashUndo.length,2);
renderTrashUndo();assert.equal($('#trash-undo').hidden,true);assert.equal($('#undo-trash-menu').hidden,false);
""".replace("CONTROLLER", controller)
    path = tmp_path / "trash-toast.cjs"
    path.write_text(script, encoding="utf-8")
    result = subprocess.run(
        [node, str(path)], capture_output=True, text=True, timeout=15, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
