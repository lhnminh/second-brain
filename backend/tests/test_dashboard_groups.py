"""Exercise the shipped grouping/rendering code with saved-task-shaped data."""

import runpy
import shutil
import subprocess
from pathlib import Path

import pytest


def test_deadline_order_separate_goals_and_accessible_past_tasks(tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node required")
    page = runpy.run_path(
        str(Path(__file__).resolve().parents[2] / "frontend/dashboard.py")
    )["PAGE"]
    helpers = (
        "function orderedChildren("
        + page.split("function orderedChildren(", 1)[1].split("// Focus grouping.", 1)[
            0
        ]
    )
    overview = (
        "function handoffRoot("
        + page.split("function handoffRoot(", 1)[1].split(
            "function renderOverview(", 1
        )[0]
    )
    script = r"""
const assert=require('node:assert/strict');
const esc=value=>String(value??'').replaceAll('<','&lt;').replaceAll('>','&gt;');
const busy=false,state={tasks:[]},openPlans=new Set();function agentActions(t){return t.handoff?'<div class="agent-actions"><button>Ask Muse</button></div>':'';}
HELPERS
OVERVIEW
const roots=[
 {id:'later',title:'Later',deadline:'2026-12-20',importance_score:100},
 {id:'early',title:'Earlier',deadline:'2026-11-01',importance_score:20},
 {id:'goal',title:'Learn pottery',description:'Explore shapes and clay.'},
 {id:'plan',title:'Undated plan'},
 {id:'done',title:'Finished',status:'completed',updated_at:'2026-11-03'},
 {id:'steps-done',title:'Steps done',status:'pending',updated_at:'2026-11-02'}
];
const tasks=[...roots,{id:'step',parent_task_id:'plan',title:'First step',status:'pending'},
 {id:'finished-step',parent_task_id:'steps-done',title:'Done step',status:'completed'}];
state.tasks=tasks;
const grouped=dashboardGroups(roots,tasks);
assert.deepEqual(grouped.short.map(t=>t.id),['early','later','plan']);
assert.deepEqual(grouped.long.map(t=>t.id),['goal']);
assert.deepEqual(grouped.past.map(t=>t.id),['done','steps-done']);
assert.equal(new Set([...grouped.short,...grouped.long].map(t=>t.id)).size,grouped.active.length);
const longHtml=longTermEntry(roots[2]);assert.doesNotMatch(longHtml,/data-handoff=/);
assert.doesNotMatch(sectionTaskControls('short_term'),/section-count|tasks<\/span>/);
const whole={id:'whole',time_horizon:'short_term',status:'pending'},one={id:'one',parent_task_id:'whole',status:'pending',handoff:{handler:'muse'}},two={id:'two',parent_task_id:'whole',status:'pending',handoff:{handler:'user'}};state.tasks.push(whole,one,two);assert.equal(canHandoff(whole),false);assert.match(taskDeadlineRow(whole),/disabled/);two.handoff.handler='muse';assert.equal(canHandoff(whole),true);whole.time_horizon='long_term';assert.equal(canHandoff(whole),false);assert.equal(canHandoff(one),false);assert.doesNotMatch(taskDeadlineRow(whole),/data-handoff=/);whole.time_horizon='short_term';

assert.match(longHtml,/<div class="goal-heading"><input[^>]*data-task-name="goal"[^>]*value="Learn pottery"/);assert.match(longHtml,/data-toggle-subtasks="goal"[^>]*aria-expanded="false"/);assert.match(longHtml,/id="goal-subtasks-goal"[^>]*hidden/);assert.doesNotMatch(longHtml,/<summary|<details/);
assert.doesNotMatch(longHtml,/Explore shapes and clay|<textarea|Description/);assert.match(longHtml,/data-add-subtask="goal"/);assert.ok(longHtml.indexOf('Ask Muse')<longHtml.indexOf('Edit task'));assert.doesNotMatch(longHtml,/Go to task chat/);
const stepHtml=focusStep({id:'empty-step',title:'Review layout',description:'Preserved note',handoff:true});assert.doesNotMatch(stepHtml,/<textarea|Add description|Preserved note/);assert.match(stepHtml,/Review layout/);

assert.doesNotMatch(longHtml,/data-bubble=|Show .* more/);
const groupedPast=renderPastGroups([{...roots[4],time_horizon:'long_term',deadline:'2026-11-01'},roots[5]],tasks);
assert.match(groupedPast,/Past short-term tasks/);assert.match(groupedPast,/Past long-term tasks/);assert.ok(groupedPast.indexOf('Steps done')<groupedPast.indexOf('Past long-term tasks'));assert.ok(groupedPast.indexOf('Finished')>groupedPast.indexOf('Past long-term tasks'));
const pastHtml=pastTask(roots[4],tasks);
assert.match(pastHtml,/Completed/);assert.match(pastHtml,/Reopen task/);assert.doesNotMatch(pastHtml,/data-task-chat=|data-edit=|data-complete=|<details|<input|<textarea/);assert.equal((pastHtml.match(/<button/g)||[]).length,1);assert.match(pastHtml,/data-reopen="done"/);
assert.match(pastTask(roots[5],tasks),/All subtasks completed/);
assert.equal(roots[5].status,'pending');
const pinned=[{id:'manual-short',time_horizon:'short_term'},{id:'manual-long',time_horizon:'long_term',deadline:'2026-11-01'}];
assert.deepEqual(dashboardGroups(pinned,pinned).short.map(t=>t.id),['manual-short']);assert.deepEqual(dashboardGroups(pinned,pinned).long.map(t=>t.id),['manual-long']);
assert.equal(dashboardGroups([{...roots[5],status:'in_progress'}],tasks).active.length,1);
const actions=taskActions({...roots[0],handoff:true});
assert.ok(actions.indexOf('Ask Muse')<actions.indexOf('Edit task'));
assert.ok(actions.indexOf('Edit task')<actions.indexOf('Complete task'));
assert.match(taskDeadline({deadline:'2000-01-01'}),/data-urgency="overdue"/);
const now=new Date(),date=[now.getFullYear(),String(now.getMonth()+1).padStart(2,'0'),String(now.getDate()).padStart(2,'0')].join('-');
assert.match(taskDeadline({deadline:date}),/data-urgency="urgent">Due today/);
assert.match(taskDeadline({deadline:'2099-01-01'}),/data-urgency="later">Due/);
assert.equal(taskDeadline({}), '');
// Reopening a saved step restores its original task to the active group.
tasks.find(t=>t.id==='finished-step').status='pending';assert.deepEqual(dashboardGroups(roots,tasks).past.map(t=>t.id),['done']);
assert.ok(dashboardGroups(roots,tasks).short.some(t=>t.id==='steps-done'));
""".replace("HELPERS", helpers).replace("OVERVIEW", overview)
    path = tmp_path / "dashboard.cjs"
    path.write_text(script, encoding="utf-8")
    result = subprocess.run(
        [node, str(path)], capture_output=True, text=True, check=False, timeout=15
    )
    assert result.returncode == 0, result.stdout + result.stderr
