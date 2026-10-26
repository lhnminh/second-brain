# Visual Second Brain — Product Spec

**Status:** MVP product scope defined; technical integration and implementation details open  
**Version:** 0.11  
**Date:** October 26, 2026  
**Format:** Hosted web application  
**Working name:** Visual Second Brain

## 1. Product vision

**A daily starting point that frees up time and mental space.**

Visual Second Brain is a visual dashboard you open daily, especially at the start of your day. It brings together priorities, work that needs doing, and work already underway so you can understand where things stand and get on with your day.

The experience combines three parts:

- **Daily dashboard:** See short-term and long-term priorities, current focus, and next actions.
- **Agent activity:** See subtask creation and importance-scoring activity. The broader vision adds steps and screenshots for screen-based execution.
- **Corner pet:** Open text or voice interaction with the agent whenever you want to ask, discuss, or steer work.

The dashboard provides useful context at a glance. Conversation supports the experience without requiring the user to reconstruct their situation from a message history.

**Agent platform:** Muse. Users can provide voice or text input, and the agent can reply in text chat and update the dashboard. Spoken agent replies are outside the MVP scope.

## 2. Users and onboarding

The application supports multiple users. Each signed-in user has their own dashboard, priorities, tasks, conversation history, and agent runs. Saved data and any connected accounts must be scoped to that user.

### Voice-first onboarding

The intended onboarding experience is open-ended voice input with text chat replies from Muse. The user can talk freely about who they are, what they are involved in, and their general focus. The agent should accommodate an unstructured explanation rather than require a detailed form or a polished plan.

A proposed flow:

1. Invite the user to talk about themselves and what is currently on their mind.
2. Let them explain in their own words; Muse can ask brief follow-up questions in text chat when needed.
3. Extract an initial understanding of their context, broad focus, and any priorities or goals they mention.
4. Present that understanding for correction or confirmation.
5. Use the confirmed context to populate their first dashboard.

Specific tasks, deadlines, and priorities should only be populated when supported by what the user says or subsequently confirms. Broad aspirations can remain broad; onboarding does not need to produce a complete task list.

The Muse integration details for voice input, transcription, and audio retention remain to be defined. Text input is also available; spoken replies are not required. Microphone use should have clear listening controls. The context carried forward from onboarding should be visible and editable by the user.

## 3. Daily dashboard

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

### Importance: simple user choice, granular agent scoring

**Decision:** Users choose one of five importance levels. The agent maintains an internal integer `importance_score` from 0–100 for finer ranking.

- The user interface shows five choices, with no slider or numeric entry.
- Each level maps to a score range. A user-selected level constrains the agent's score to that range.
- The agent can refine the score within the selected range to distinguish similarly important items without overriding the user's choice.
- The dashboard displays the importance level rather than the internal score.
- Importance stays separate from deadline and urgency. An approaching deadline may raise priority without changing importance.

This keeps fine-grained scoring with the agent and reduces the user's decision burden. The five labels and their exact score ranges remain to be defined.

## 4. Agent activity

For the MVP, agent work consists of creating subtasks and assigning importance scores. Activity should show that work's status and resulting changes. Completing a planning run does not mean the user's task is complete.

### Broader vision: screen-based activity

The following screen and screenshot experience applies when the agent later performs work with a visual surface; it is not required for subtask creation or scoring.

The user can open a running agent task to see what is happening and how it is progressing.

The task view should include:

- The task and its current status.
- The current step and a history of steps taken.
- Screenshots associated with relevant steps.
- Results and any point where user input is needed.

A screen view may also show the task as it runs. Whether this uses live viewing, periodic screenshots, or step-linked captures remains open.

Steps describe observable actions and results. Tasks without a screen should still expose useful progress. Status should reflect actual execution and indicate when information is stale or unavailable.

## 5. Corner pet and conversation

A small pet sits in a corner of the application. Activating it opens text chat with optional voice input to Muse. Voice input is available throughout daily use, including after onboarding. The agent replies in text chat; it does not speak back in the MVP.

The user can speak naturally or type to ask questions, discuss priorities, update their context, request work, or steer an ongoing task. Conversation should share the dashboard's context, including relevant user edits and task state.

The dashboard remains useful with conversation closed. The pet's appearance, animation, and any activity indicators are design decisions. Voice input should have explicit listening controls and a visible listening state.

## 6. Role of the agent

The MVP agent has two core capabilities:

1. **Create subtasks:** Break a task into concrete steps that help complete it.
2. **Score importance:** Assign or refine internal 0–100 importance scores using available context and respecting any user-selected importance level.

The user can edit the breakdown and choose among five importance levels. Suggestions should reflect the latest user changes. Deadlines must come from user-provided or confirmed context rather than being invented during decomposition.

External task execution and broader autonomous behavior are outside this initial capability set.

### Core task model

Tasks and subtasks use the same structure. A subtask references its parent through `parent_task_id`; a top-level task has no parent.

| Field | Purpose |
|---|---|
| `id` | Identify the task |
| `user_id` | Scope the task to its owner |
| `parent_task_id` | Link a subtask to its parent; empty for a top-level task |
| `title` | Describe the work to complete |
| `description` | Optional supporting context |
| `deadline` | Optional deadline; empty when unknown or not set |
| `importance_score` | Internal integer from 0–100; empty until assessed |
| `user_importance_level` | Optional user-selected level, constraining the agent's score |
| `status` | Track pending, in-progress, or completed work |
| `created_at`, `updated_at` | Track creation and changes |

This is the core work model, supported by per-user onboarding context, conversation history, and agent activity records. Separate goal and project entities are not required for the initial MVP.

Parent and child tasks must belong to the same user, and parent relationships must not form cycles. Subtask ordering, parent completion behavior, and any propagation of deadlines or importance still need definition.

### Supporting user context

Persist context as structured, user-scoped records that can be queried and updated individually. Markdown summaries may help with reading or agent context, but should not be the sole source of truth.

The working context categories are:

| Category | Examples |
|---|---|
| About the user | Roles, responsibilities, interests, preferences |
| Long-term direction | Aspirations and what matters to the user |
| Current situation | General focus, commitments, constraints |
| Work state | Tasks, subtasks, completion, and agent activity |
| Assistance preferences | How the user wants help and relevant permissions |

These categories do not require separate tables or additional MVP goal and project entities. Concrete work belongs in task records; other context supports interpretation and scoring.

Context should retain its source, update time, and whether it was user-stated, user-confirmed, or agent-inferred. User corrections take precedence over conflicting inferences. Permissions require explicit authorization and must not be inferred from personal context.

A relational database with flexible JSON fields is the proposed storage approach; Postgres was suggested, but the database choice and final supporting schema remain open.

## 7. Experience principles

1. **Save time and mental space.** Each feature should reduce effort or the need to remember and reconstruct context.
2. **Make the situation visible.** Use visual hierarchy and clear status to support a quick daily overview.
3. **Support direct interaction.** Let the user correct and update information where it appears.
4. **Keep conversation accessible.** Text and voice are available through the pet when useful.
5. **Make agent work inspectable.** Show progress, steps, evidence, and outcomes.
6. **Carry context forward.** Preserve useful state and intentional user changes between visits.

## 8. MVP flow

Use one concrete daily scenario to demonstrate the complete experience:

1. Sign in as a new user and talk freely through voice onboarding.
2. Review and correct the agent's understanding, then open the initial dashboard.
3. Add or confirm a task, with an optional deadline and five-level importance choice.
4. Ask the agent through the pet to break it into subtasks and assess importance.
5. See the planning activity and inspect the generated subtasks and importance levels on the dashboard.
6. Edit the breakdown, adjust an importance level, or mark work complete.
7. Return to the dashboard and see the updated state persist for that user.

The MVP proves task decomposition and importance scoring alongside voice onboarding, the dashboard, and pet interaction. Screen streaming, screenshot capture, external integrations, and execution of the underlying work are deferred.

### Success criteria

- A new user can establish useful context by speaking naturally and correct the agent's interpretation.
- The user can quickly understand priorities, pending work, and agent activity.
- The experience reduces the effort of starting the day and keeping track of work.
- Direct edits inform subsequent agent interactions.
- Agent progress is understandable and reflects real execution.
- Useful context persists, giving the user a reason to return the next day.

## 9. Engineering requirements

- Authenticate users and enforce user-scoped access on every data and task operation.
- Use shared, persistent state within each user account for onboarding context, the dashboard, conversation, and agent tasks.
- Validate agent-generated updates before applying them.
- Preserve user corrections and handle conflicting or stale updates.
- Record meaningful changes and task events for inspection and recovery.
- Associate planning activity and resulting changes with the relevant tasks.
- When screen-based execution is added, associate screenshots with the relevant run and step.
- Authorize data access and agent actions; keep credentials server-side.

The technology stack remains open. The repository currently contains a Python package scaffold. Muse is the selected agent platform. Its integration contract, the remaining stack, hosting, and any hackathon requirements need verification before implementation choices are finalized.

### Implementation sequence

1. Verify Muse's integration contract for text and voice input, chat replies, structured task updates, and activity status. This is the first technical dependency to resolve.
2. Finalize the initial schema and implement per-user authentication, isolation, and persistence.
3. Connect onboarding context, subtask creation, and importance scoring through Muse.
4. Build the dashboard and five-level importance control.
5. Add the corner pet with text chat and voice input, without spoken replies.
6. Validate the complete flow, including saved state, user corrections, and isolation between users.

## 10. Open decisions

| Decision | What needs definition |
|---|---|
| First daily scenario | Whose day are we supporting, and what effort should the product remove? |
| Context sources | Voice onboarding supplies initial context; what additional input or connected tools should keep it current? |
| Storage and context schema | Which database and supporting record structures implement the task model and user context? |
| Muse input and chat | How are voice input, transcription, and text chat integrated with Muse? What audio or transcripts are retained? |
| Importance levels | What are the five labels and their score ranges? |
| Priority and time horizons | How do importance, deadlines, and work state determine priority, and what counts as short-term or long-term? |
| Dashboard layout | How are the overview, focus, and task activity presented together? |
| Planning updates | Should generated subtasks apply immediately with undo or be reviewed first? |
| Task relationships | How are subtasks ordered, when is a parent complete, and do deadline or importance values propagate? |
| Running work | Should the dashboard include user work and other processes alongside agent tasks? |
| Future screen visibility | When screen-based execution is added: live view, periodic screenshots, step-linked captures, or a combination? |
| Pet and voice input | How does chat open, how is microphone input controlled, and does the pet indicate activity? |

**Next implementation step:** Verify the Muse integration contract, then validate the initial schema against one onboarding-to-task-breakdown example. No additional product features are needed to start.
