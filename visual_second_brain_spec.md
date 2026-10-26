# Visual Second Brain — Product Spec

**Status:** Product concept; layout and implementation to be defined  
**Version:** 0.6  
**Date:** October 26, 2026  
**Format:** Hosted web application  
**Working name:** Visual Second Brain

## 1. Product vision

**A daily starting point that frees up time and mental space.**

Visual Second Brain is a visual dashboard you open daily, especially at the start of your day. It brings together priorities, work that needs doing, and work already underway so you can understand where things stand and get on with your day.

The experience combines three parts:

- **Daily dashboard:** See short-term and long-term priorities, current focus, and next actions.
- **Agent activity:** See running agent tasks and inspect their progress through steps and screenshots.
- **Corner pet:** Open text or voice interaction with the agent whenever you want to ask, discuss, or steer work.

The dashboard provides useful context at a glance. Conversation supports the experience without requiring the user to reconstruct their situation from a message history.

## 2. Daily dashboard

| Content | Purpose |
|---|---|
| Priorities | Understand what matters most |
| Short-term view | See what needs attention soon |
| Long-term view | Keep larger goals and direction visible |
| Work to do | Understand what needs to be done |
| Currently running | See agent tasks underway and their status |
| Current focus and next actions | Decide where to put attention and how to move forward |

These are content needs, not a prescribed set of panels. The layout should make the overall situation easy to scan, with details available when needed.

Proposed interactions include adjusting priorities, editing work, choosing a focus, and accepting or revising suggested next actions. Connecting near-term work to long-term goals could help explain why an action matters.

Useful context should persist between visits. User corrections and completed work should inform subsequent suggestions.

## 3. Agent activity

The user can open a running agent task to see what is happening and how it is progressing.

The task view should include:

- The task and its current status.
- The current step and a history of steps taken.
- Screenshots associated with relevant steps.
- Results and any point where user input is needed.

A screen view may also show the task as it runs. Whether this uses live viewing, periodic screenshots, or step-linked captures remains open.

Steps describe observable actions and results. Tasks without a screen should still expose useful progress. Status should reflect actual execution and indicate when information is stale or unavailable.

## 4. Corner pet and conversation

A small pet sits in a corner of the application. Activating it opens text chat or voice interaction with the agent.

The user can ask questions, discuss priorities, request work, or steer an ongoing task. Conversation should share the dashboard's context, including relevant user edits and task state.

The dashboard remains useful with conversation closed. The pet's appearance, animation, and any activity indicators are design decisions. Voice should have explicit listening controls and a visible listening state.

## 5. Role of the agent

The agent supports the broader goal of saving time and reducing mental load. Its responsibilities include:

- Helping organize short-term and long-term priorities from available context.
- Keeping work to do and work underway understandable.
- Suggesting concrete next actions with a brief rationale when useful.
- Incorporating user corrections, completed work, and changes in focus.
- Making running tasks inspectable through progress and visual evidence.

The user controls priorities and actions. Recommendations, observed facts, and assumptions should be distinguishable. The scope of execution, automatic context gathering, and proactive behavior still needs definition.

## 6. Experience principles

1. **Save time and mental space.** Each feature should reduce effort or the need to remember and reconstruct context.
2. **Make the situation visible.** Use visual hierarchy and clear status to support a quick daily overview.
3. **Support direct interaction.** Let the user correct and update information where it appears.
4. **Keep conversation accessible.** Text and voice are available through the pet when useful.
5. **Make agent work inspectable.** Show progress, steps, evidence, and outcomes.
6. **Carry context forward.** Preserve useful state and intentional user changes between visits.

## 7. Candidate prototype

Use one concrete daily scenario to demonstrate the complete experience:

1. Open the dashboard with saved context for the day.
2. Review short-term and long-term priorities, work to do, and running agent tasks.
3. Adjust a priority or focus directly.
4. Activate the pet and interact through text or voice using the updated context.
5. Open a running agent task and inspect its progress, steps, and screenshots.
6. Return to the dashboard and see the updated state persist.

Context sources, the task the agent performs, and the implementation scope of voice and screen viewing must be chosen before building the prototype.

### Success criteria

- The user can quickly understand priorities, pending work, and agent activity.
- The experience reduces the effort of starting the day and keeping track of work.
- Direct edits inform subsequent agent interactions.
- Agent progress is understandable and reflects real execution.
- Useful context persists, giving the user a reason to return the next day.

## 8. Engineering requirements

- Use shared, persistent state for the dashboard, conversation, and agent tasks.
- Validate agent-generated updates before applying them.
- Preserve user corrections and handle conflicting or stale updates.
- Record meaningful changes and task events for inspection and recovery.
- Associate screenshots and progress events with the relevant task and step.
- Authorize data access and agent actions; keep credentials server-side.

The technology stack remains open. The repository currently contains a Python package scaffold. Model providers, integrations, hosting, and any hackathon requirements need verification before implementation choices are finalized.

## 9. Open decisions

| Decision | What needs definition |
|---|---|
| First daily scenario | Whose day are we supporting, and what effort should the product remove? |
| Context sources | What comes from the user, connected tools, or agent inference? |
| Priority and time horizons | How are priorities set, and what counts as short-term or long-term? |
| Dashboard layout | How are the overview, focus, and task activity presented together? |
| Execution and autonomy | What can the agent do, when can it run, and what requires approval? |
| Running work | Should the dashboard include user work and other processes alongside agent tasks? |
| Screen visibility | Live view, periodic screenshots, step-linked captures, or a combination? |
| Pet and voice | How does conversation open, how is voice controlled, and does the pet indicate activity? |

**Next design step:** Walk through a real start of day and use it to sketch the dashboard, agent task view, and pet interaction.
