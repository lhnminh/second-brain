"""Run the shipped recorder/controller against browser and network test doubles."""

import json
import re
import runpy
import shutil
import subprocess
from pathlib import Path

import pytest


def test_voice_lifecycle_and_conversation_submission():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required to exercise the browser voice controller")
    page = runpy.run_path(
        str(Path(__file__).resolve().parents[2] / "frontend" / "dashboard.py")
    )["PAGE"]
    voice = (
        "// Voice input:"
        + page.split("// Voice input:", 1)[1].split("// End voice input.", 1)[0]
    )
    submit = re.search(r"\$\('#chat-form'\)\.onsubmit=.*?;\n", page)[0]
    full_js = page.split("<script>")[1].split("</script>")[0]
    harness = r"""
const assert=require('node:assert/strict'),vm=require('node:vm');
new vm.Script(FULL_JS);
const flush=()=>new Promise(resolve=>setImmediate(resolve));
function browser({supported=true,secure=true,permissionError=false,deferPermission=false,network='ok'}={}){
 const elements=new Map(),events={},timers=new Map();let nextTimer=0,resolvePermission;
 const $=selector=>{if(!elements.has(selector))elements.set(selector,{value:'',textContent:'',hidden:false,disabled:false,readOnly:false,setAttribute(k,v){this[k]=v;}});return elements.get(selector);};
 const track={stop(){this.stopped=true;}};
 const stream={getTracks:()=>[track]};
 class Node {constructor(){this.port={onmessage:null};}connect(){}disconnect(){this.disconnected=true;}}
 class Context {
  static instances=[];
  constructor(){this.sampleRate=24000;this.audioWorklet={addModule:async()=>{}};this.destination={};Context.instances.push(this);}
  createMediaStreamSource(){return new Node();}
  createGain(){const n=new Node();n.gain={value:1};return n;}
  resume(){return Promise.resolve();}
  close(){this.closed=true;return Promise.resolve();}
 }
 class Worklet extends Node {static instances=[];constructor(){super();Worklet.instances.push(this);}}
 const window={isSecureContext:secure,AudioContext:supported?Context:undefined,AudioWorkletNode:Worklet,addEventListener:(event,fn)=>events[event]=fn};
 const navigator={mediaDevices:{getUserMedia:async()=>{
  if(permissionError)throw Object.assign(Error('denied'),{name:'NotAllowedError'});
  if(deferPermission)return new Promise(resolve=>resolvePermission=resolve);
  return stream;
 }}};
 const document={hidden:false,addEventListener:(event,fn)=>events[event]=fn};
 const sent=[],uploads=[],urls={revoked:[],createObjectURL:()=> 'blob:recorder',revokeObjectURL(url){this.revoked.push(url);}};
 const context=vm.createContext({$,window,navigator,document,AudioWorkletNode:Worklet,Blob,URL:urls,AbortController,TypeError,busy:false,
 setTimeout:fn=>{timers.set(++nextTimer,fn);return nextTimer;},clearTimeout:id=>timers.delete(id),
 conversationId:'chat-1',chatRuns:()=>[],state:{runs:[]},pending:null,drafts:new Map(),crypto:{randomUUID:()=> 'request-1'},structuredClone,
 action:async fn=>fn(),api:async(path,method,body)=>{sent.push({path,body});return {status:'answered'};},refresh:async()=>{},error:e=>$('#error').textContent=e.message,
 fetch:async(path,options)=>{
  uploads.push({path,...options});
  if(network==='hang')return new Promise(()=>{});
  if(network==='fail')throw new TypeError('offline');
  return {ok:true,json:async()=>({transcript:'Finish my math homework.'})};
 }});
 vm.runInContext(VOICE+'\n'+SUBMIT,context);
 return {$,track,sent,uploads,events,document,timers,urls,Context,Worklet,run:code=>vm.runInContext(code,context),
 allow:()=>resolvePermission(stream),async start(){await $('#voice').onclick();},
 samples(n=12000){Worklet.instances.at(-1).port.onmessage({data:new Float32Array(n).fill(0.5)});},
 submit:()=>$('#chat-form').onsubmit({preventDefault(){}})};
}
(async()=>{
 // Record locally; nothing is uploaded or sent until the explicit stop action.
 let b=browser();b.$('#message').value='Today:';await b.start();
 assert.equal(b.$('#send').disabled,true);assert.equal(b.$('#message').readOnly,true);
 b.samples();assert.equal(b.uploads.length,0);b.submit();assert.equal(b.sent.length,0);
 b.$('#voice').onclick();await flush();
 assert.equal(b.uploads.length,1);assert.equal(b.uploads[0].path,'/api/voice/transcribe');
 assert.equal(b.uploads[0].headers['Content-Type'],'audio/wav');assert.equal(b.track.stopped,true);
 const buffer=await b.uploads[0].body.arrayBuffer(),view=new DataView(buffer);
 assert.equal(view.getUint32(24,true),24000);assert.equal(view.getUint16(22,true),1);
 assert.equal(view.getUint32(40,true),24000);assert.equal(view.getInt16(44,true),16384);
 assert.equal(b.$('#message').value,'Today: Finish my math homework.');assert.equal(b.sent.length,0);
 assert.equal(b.$('#send').disabled,false);assert.equal(b.$('#message').readOnly,false);
 b.$('#message').value='Today: Finish biology homework.';await b.submit();await flush();
 assert.equal(b.sent[0].path,'/api/conversation');assert.equal(b.sent[0].body.message,'Today: Finish biology homework.');
 // Cancel releases all resources and keeps the original typed draft.
 b=browser();b.$('#message').value='Keep this';await b.start();b.samples();b.$('#voice-cancel').onclick();
 assert.equal(b.$('#message').value,'Keep this');assert.equal(b.track.stopped,true);
 assert.equal(b.Context.instances[0].closed,true);assert.equal(b.uploads.length,0);
 assert.equal(b.Worklet.instances[0].port.onmessage,null);assert.equal(b.urls.revoked.length,1);
 // A late microphone grant after cancellation cannot restart recording.
 b=browser({deferPermission:true});const starting=b.start();b.$('#voice-cancel').onclick();b.allow();await starting;
 assert.equal(b.track.stopped,true);assert.equal(b.Context.instances.length,0);assert.equal(b.$('#send').disabled,false);
 // Unsupported/insecure browsers and denied permission still permit typing.
 for(const opts of [{supported:false},{secure:false},{permissionError:true}]){
  b=browser(opts);b.$('#message').value='Typed';await b.start();
  assert.equal(b.$('#send').disabled,false);assert.equal(b.$('#message').value,'Typed');assert.equal(b.uploads.length,0);
 }
 // Page hiding and navigation stop capture and do not upload automatically.
 for(const event of ['pagehide','visibilitychange']){
  b=browser();await b.start();b.samples();b.document.hidden=true;b.events[event]();
  assert.equal(b.track.stopped,true);assert.equal(b.$('#send').disabled,false);assert.equal(b.uploads.length,0);
 }
 // Failed transcription preserves draft + in-memory audio for an explicit retry.
 b=browser({network:'fail'});b.$('#message').value='Typed';await b.start();b.samples();b.$('#voice').onclick();await flush();
 assert.equal(b.$('#message').value,'Typed');assert.equal(b.$('#voice-retry').hidden,false);assert.equal(b.$('#send').disabled,false);
 b.$('#voice-retry').onclick();await flush();assert.equal(b.uploads.length,2);assert.equal(b.uploads[0].body,b.uploads[1].body);
 b.$('#voice-cancel').onclick();assert.equal(b.$('#voice-retry').hidden,true);
 // Cancelling in-flight transcription aborts the request without changing text.
 b=browser({network:'hang'});b.$('#message').value='Typed';await b.start();b.samples();b.$('#voice').onclick();
 b.$('#voice-cancel').onclick();assert.equal(b.uploads[0].signal.aborted,true);assert.equal(b.$('#message').value,'Typed');
 // Transcription timeout permits retry, while the one-minute limit stops capture only.
 b=browser({network:'hang'});await b.start();b.samples();b.$('#voice').onclick();[...b.timers.values()][0]();
 assert.equal(b.$('#voice-retry').hidden,false);assert.equal(b.$('#send').disabled,false);
 b=browser();await b.start();b.samples();[...b.timers.values()][0]();assert.equal(b.track.stopped,true);
 assert.equal(b.uploads.length,0);b.$('#voice').onclick();await flush();assert.equal(b.uploads.length,1);
 // Too-short recordings never reach the server, and message limits still apply.
 b=browser();await b.start();b.$('#voice').onclick();await flush();assert.equal(b.uploads.length,0);
 b.$('#message').value='x'.repeat(10001);b.submit();assert.equal(b.sent.length,0);assert.match(b.$('#error').textContent,/Shorten/);
 console.log('Recorder lifecycle, WAV encoding, retry, and reviewed submission passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
"""
    script = (
        f"const VOICE={json.dumps(voice)},SUBMIT={json.dumps(submit)},FULL_JS={json.dumps(full_js)};\n"
        + harness
    )
    result = subprocess.run(
        [node, "-e", script], check=False, capture_output=True, text=True, timeout=15
    )
    assert result.returncode == 0, result.stdout + result.stderr
