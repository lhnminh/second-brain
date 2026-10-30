"""Exercise shipped WebMCP tools with browser and authenticated-fetch doubles."""

import json
import runpy
import shutil
import subprocess
from pathlib import Path

import pytest


def test_webmcp_tools_and_lifecycle():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required to exercise WebMCP tools")
    page = runpy.run_path(
        str(Path(__file__).resolve().parents[2] / "frontend" / "dashboard.py")
    )["PAGE"]
    script = "// WebMCP:" + page.split("// WebMCP:", 1)[1].split(
        "// End WebMCP.", 1
    )[0]
    harness = r"""
const assert=require('node:assert/strict'),vm=require('node:vm');
const flush=()=>new Promise(resolve=>setImmediate(resolve));
function browser({supported=true,secure=true,registrationFailure=false}={}){
 const elements=new Map(),events={},tools=new Map(),calls=[],editors=[],opens=[];
 const $=selector=>{if(!elements.has(selector))elements.set(selector,{hidden:true,value:'',open:false,focus(){this.focused=true;},scrollIntoView(){this.scrolled=true;}});return elements.get(selector);};
 const state={tasks:[{id:'task-1',title:'Homework',version:2,description:'Saved',user_id:'private-owner',importance_score:75}],runs:[{id:'run-1',task_id:null,status:'awaiting_review'}]};
 let response={ok:true,json:async()=>structuredClone(state)};
 const document=supported?{modelContext:{async registerTool(tool,{signal}){
  if(registrationFailure&&tools.size===1)throw Error('unsupported');
  assert.equal(tools.has(tool.name),false);tools.set(tool.name,tool);
  signal.addEventListener('abort',()=>tools.delete(tool.name),{once:true});
 }}}:{};
 const context=vm.createContext({document,window:{isSecureContext:secure,addEventListener:(name,fn)=>events[name]=fn},
  $,state,busy:false,voiceSession:null,AbortController,console:{warn(){}},
  setMuseOpen:(...args)=>opens.push(args),openEditor:id=>{editors.push(id);$('#edit-dialog').open=true;},
  fetch:async(path,options)=>{calls.push({path,...options});options.signal?.throwIfAborted();return response;}});
 vm.runInContext(SCRIPT,context);
 return {$,events,tools,calls,editors,opens,state,run:code=>vm.runInContext(code,context),
  respond:value=>response=value,call:(name,input={},options)=>tools.get(name).execute(input,options)};
}
(async()=>{
 for(const opts of [{supported:false},{secure:false}]){
  const b=browser(opts);await flush();assert.equal(b.tools.size,0);
 }
 let b=browser();await flush();assert.equal(b.tools.size,4);
 const result=await b.call('get_dashboard');assert.equal(result.tasks[0].title,'Homework');
 assert.equal(result.tasks[0].user_id,undefined);assert.equal(result.tasks[0].importance_score,undefined);
 assert.equal(result.reviews[0].id,'run-1');assert.equal(b.calls[0].credentials,'same-origin');
 assert.equal(b.tools.get('get_dashboard').annotations.readOnlyHint,true);
 // Read from the server each time, and never return cached records on failure.
 b.respond({ok:false,status:401});assert.match((await b.call('get_dashboard')).error,/Connect/);
 b.respond({ok:false,status:503});assert.equal((await b.call('get_dashboard')).tasks,undefined);
 b.respond({ok:true,json:async()=>{throw Error('invalid JSON');}});
 assert.match((await b.call('get_dashboard')).error,/Could not read/);
 const controller=new AbortController();controller.abort();
 await assert.rejects(b.call('get_dashboard',{}, {signal:controller.signal}),{name:'AbortError'});
 // All tool inputs are validated by the app, including unknown properties.
 for(const name of b.tools.keys()){
  assert.ok((await b.call(name,null)).error);assert.ok((await b.call(name,{unexpected:true})).error);
 }
 assert.ok((await b.call('draft_muse_message',{message:' '})).error);
 assert.ok((await b.call('draft_muse_message',{message:'x'.repeat(10001)})).error);
 assert.ok((await b.call('open_task_editor',{task_id:2})).error);
 // Drafting stages visible text, does not send it, and preserves user text.
 assert.equal((await b.call('draft_muse_message',{message:'Plan homework'})).status,'drafted');
 assert.equal(b.$('#message').value,'Plan homework');assert.deepEqual(b.opens.at(-1),[true]);
 assert.ok((await b.call('draft_muse_message',{message:'Replace draft'})).error);
 assert.equal(b.$('#message').value,'Plan homework');
 b.$('#access').hidden=false;assert.ok((await b.call('open_task_editor',{task_id:'task-1'})).error);
 b.$('#access').hidden=true;
 for(const assignment of ['busy=true','busy=false;voiceSession={}']){
  b.run(assignment);assert.ok((await b.call('show_pending_reviews')).error);
 }
 b.run('voiceSession=null');
 assert.ok((await b.call('open_task_editor',{task_id:'missing'})).error);
 assert.equal((await b.call('open_task_editor',{task_id:'task-1'})).status,'editor_open');
 assert.deepEqual(b.editors,['task-1']);
 assert.ok((await b.call('open_task_editor',{task_id:'task-1'})).error);
 assert.ok((await b.call('show_pending_reviews')).error);
 b.$('#edit-dialog').open=false;
 assert.equal((await b.call('show_pending_reviews')).status,'review_visible');
 assert.equal(b.$('#reviews').scrolled,true);assert.equal(b.$('#reviews').focused,true);
 b.state.runs=[];assert.ok((await b.call('show_pending_reviews')).error);
 assert.ok(b.calls.every(call=>call.path==='/api/dashboard'&&!call.method));
 // Navigation unregisters tools; BFCache restoration registers exactly once.
 b.events.pagehide();assert.equal(b.tools.size,0);
 b.events.pageshow();await flush();assert.equal(b.tools.size,4);
 b.events.pageshow();await flush();assert.equal(b.tools.size,4);
 b=browser({registrationFailure:true});await flush();assert.equal(b.tools.size,0);
 // Navigation during asynchronous registration cannot leave partial tools behind.
 b=browser();b.events.pagehide();await flush();assert.equal(b.tools.size,0);
})().catch(error=>{console.error(error);process.exitCode=1;});
"""
    subprocess.run(
        [node, "-e", "const SCRIPT=" + json.dumps(script) + ";\n" + harness],
        check=True,
        capture_output=True,
        text=True,
    )
