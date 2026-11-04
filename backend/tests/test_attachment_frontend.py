"""Exercise the shipped upload controller with simulated browser/file APIs."""

import runpy
import shutil
import subprocess
from pathlib import Path

import pytest


def test_upload_failure_remove_retry_and_per_chat_drafts(tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required")
    page = runpy.run_path(
        str(Path(__file__).resolve().parents[2] / "frontend/dashboard.py")
    )["PAGE"]
    controller = (
        "// General file attachments;"
        + page.split("// General file attachments;", 1)[1].split(
            "// End file attachments.", 1
        )[0]
    )
    script = r"""
const assert=require('node:assert/strict'),vm=require('node:vm');
const els=new Map(),$=key=>{if(!els.has(key))els.set(key,{value:'',innerHTML:'',hidden:false,disabled:false,files:[],setAttribute(k,v){this[k]=v;},focus(){document.activeElement=this;},querySelector(){return options[0];},querySelectorAll(){return options;},click(){this.clicked=true;}});return els.get(key);};
const document={activeElement:null,addEventListener(){}};const options=Array.from({length:4},()=>({focus(){document.activeElement=this;}}));
const esc=s=>String(s).replaceAll('<','&lt;').replaceAll('>','&gt;');
const attachmentDrafts=new Map(),chatFiles=new Map();let chatTaskId=null,busy=false,voiceSession=null,next=0,mode='offline',resolveRequest;
const errors=[],requests=[];const error=e=>errors.push(e.message),crypto={randomUUID:()=>String(++next)};
const fetch=async(path,options)=>{requests.push({path,options});if(mode==='offline')throw new TypeError('offline');if(mode==='deferred')return new Promise(resolve=>resolveRequest=resolve);return {ok:true,json:async()=>({id:path.split('/').at(-1).split('?')[0],filename:'notes.txt',size:25})};};
CONTROLLER
const flush=()=>new Promise(resolve=>setImmediate(resolve));
const choose=(...files)=>{$('#file-input').files=files;$('#file-input').onchange();};
const target=(dataset)=>({closest:selector=>selector.includes('remove')&&dataset.removeFile||selector.includes('retry')&&dataset.retryFile?{dataset}:null});
(async()=>{
 // Paperclip opens the type menu before any native picker; every option filters it.
 $('#attachment-menu').hidden=true;$('#attach').onclick();assert.equal($('#attachment-menu').hidden,false);assert.equal($('#file-input').clicked,undefined);
 for(const [kind,accept] of Object.entries({pdf:'.pdf',txt:'.txt',word:'.docx',image:'.png,.jpg,.jpeg,.webp,.gif'})){
  $('#attachment-menu').onclick({target:{closest:()=>({dataset:{fileKind:kind}})}});
  assert.equal($('#file-input').accept,accept);assert.equal($('#file-input').clicked,true);assert.equal($('#attachment-menu').hidden,true);
 }
 $('#attach').onclick();$('#attachment-picker').onkeydown({key:'ArrowDown',preventDefault(){}});assert.equal(document.activeElement,options[1]);
 let stopped=false;$('#attachment-picker').onkeydown({key:'Escape',preventDefault(){},stopPropagation(){stopped=true;}});assert.equal(stopped,true);assert.equal($('#attachment-menu').hidden,true);
 choose({name:'notes.txt',size:25});await flush();assert.match(draftFiles()[0].error,/connection/);assert.equal($('#send').disabled,true);
 const first=requests[0].path;mode='ok';$('#draft-attachments').onclick({target:target({retryFile:'1'})});await flush();
 assert.equal(requests[1].path,first);assert.equal($('#send').disabled,false);assert.equal(draftFiles()[0].source,undefined);
 chatTaskId='task-a';renderAttachments();assert.equal(draftFiles().length,0);assert.equal($('#draft-attachments').hidden,true);
 choose({name:'task-only.txt',size:20});await flush();assert.equal(draftFiles().length,1);
 chatTaskId=null;renderAttachments();assert.equal(draftFiles()[0].id,'1');assert.equal(draftFiles().length,1);
 $('#draft-attachments').onclick({target:target({removeFile:'1'})});assert.equal(draftFiles().length,0);
 // Removing during upload must not resurrect a late result.
 mode='deferred';choose({name:'pending.txt',size:20});assert.equal($('#send').disabled,true);
 $('#draft-attachments').onclick({target:target({removeFile:'3'})});resolveRequest({ok:true,json:async()=>({id:'3',filename:'pending.txt',size:20})});await flush();
 assert.equal(draftFiles().length,0);assert.equal(chatFiles.has('3'),false);
 choose({name:'large.pdf',size:4000001});assert.match(errors.at(-1),/4 MB/);
 choose(...Array(6).fill({name:'small.txt',size:20}));assert.match(errors.at(-1),/5 files/);
 assert.doesNotMatch(fileLinks([{id:'safe-id',filename:'<script>.txt',size:20}]),/<script>/);
})().catch(e=>{console.error(e);process.exitCode=1;});
""".replace("CONTROLLER", controller)
    path = tmp_path / "uploads.cjs"
    path.write_text(script, encoding="utf-8")
    result = subprocess.run(
        [node, str(path)], capture_output=True, text=True, timeout=15, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert ".pdf,.txt,.docx,.png,.jpg,.jpeg,.webp,.gif" in page
    assert 'required placeholder="Message Muse' not in page
