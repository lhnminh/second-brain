# Visual Second Brain — Daily Dashboard

**Status:** Revised product direction; details open for discussion  
**Version:** 0.4  
**Date:** October 26, 2026  
**Format:** Hosted web application  
**Working name:** Visual Second Brain (temporary)

## 1. Product direction

Visual Second Brain is a visual dashboard you open daily, especially at the start of your day, to **free up time and mental space**.

The product should help the user begin their day with less effort spent gathering context, holding things in their head, and figuring out what needs attention. These are working interpretations of the desired benefit, to validate through concrete examples.

Seeing current focus and deciding the next action are useful capabilities within that experience. They do not define the whole product.

The motivation also includes dissatisfaction with interacting with agents primarily through text. The dashboard should provide useful visual interaction directly, with conversation available when helpful.

**Positioning:** A daily starting point that helps you reclaim time and mental space.

## 2. Established direction and working proposals

### Established direction

- The product is something the user opens daily, especially at the start of the day.
- Its intended benefit is freeing up time and mental space.
- A dashboard is the central interface.
- The experience should be more visual and less dependent on text conversation.
- The dashboard should communicate the user's current focus.
- It should help the user identify their next action.
- It should show priorities across short-term and long-term horizons.
- It should show what needs to be done.
- It should show what is currently running or in progress.

### Working proposals to validate

- Surface the context that helps the user start their day with less effort.
- Make current focus easy to see when useful, without assuming it always dominates the screen.
- Show a concrete recommended next action with enough context to understand it.
- Let the user correct the focus and accept, adjust, or dismiss a suggestion directly.
- Show relevant progress, blockers, and recent changes when they help the user act.
- Persist the dashboard so the user can return without rebuilding context.

These proposals are starting points, not settled requirements.

## 3. Target experience

A user opens the app at the start of their day. The dashboard helps them get oriented and reduces the effort needed to begin. It carries useful context forward so the user has less to reconstruct or remember.

The intended outcome is that the user leaves with more time and mental space for their day. Finding a next action can contribute to that outcome, but the experience should be evaluated more broadly.

### Daily overview

The dashboard brings together:

- **Priorities:** What matters most, across short-term needs and long-term direction.
- **Work to do:** What needs to be done, with enough context to understand its importance.
- **Work currently running:** What is already underway and its current status.
- **Current focus and next actions:** Where to put attention and how to move forward.

Together these should help the user understand their situation without checking several places or reconstructing it from a conversation.

## 4. Dashboard content and proposed interactions

The content categories below reflect the current product direction. Their layout and specific interactions remain proposals.

| Area | Question it answers | Proposed interaction |
|---|---|---|
| Priorities | What deserves attention most? | Review and adjust priority |
| Short-term view | What needs attention soon? | Inspect upcoming work and choose an action |
| Long-term view | What am I working toward? | Review goals and their related work |
| Work to do | What needs to be done? | Add, revise, defer, or complete work |
| Currently running | What is already underway, and how is it going? | Inspect status and relevant details |
| Current focus and next action | Where should my attention go now? | Select focus or adjust a suggestion |

A proposed relationship is to connect near-term work to longer-term priorities so the user can see why it matters. How those relationships are created remains open.

“Currently running” is intentionally broad. It may include the user's ongoing work, agent runs, background processes, or some combination. The exact scope needs definition. Showing an item here does not itself authorize the agent to start or control it.

The visual hierarchy should make the overall situation easy to scan and let the user inspect details as needed. These content categories do not require six separate panels. The dashboard should reduce the effort of tracking work rather than add another surface to maintain.

The layout remains open. A freeform canvas, draggable blocks, graphs, and a permanent chat sidebar are no longer assumed requirements.

## 5. Role of the agent

The agent helps reduce the effort of starting and navigating the day. Maintaining context and suggesting next actions are possible ways to do that; its broader responsibilities remain to be defined.

Potential responsibilities:

- Interpret the focus and context provided by the user.
- Help organize short-term and long-term priorities.
- Keep work to do and work already underway understandable from available information.
- Distinguish observed status from inferred status; show uncertainty or stale information when relevant.
- Suggest a specific, feasible next action.
- Give a brief explanation when useful.
- Incorporate corrections, completed actions, and changes in focus.
- Ask for missing information when it materially affects a recommendation.

The user controls their focus and which action to take. A suggested action is separate from authorization to execute it.

Automatic context gathering, proactive behavior, and action execution remain unresolved product decisions.

## 6. Interaction principles

1. **Time and mental space.** Judge features by whether they reduce effort and free the user to get on with their day.
2. **Dashboard first.** Opening the app reveals useful state immediately.
3. **Visual clarity.** Layout, hierarchy, and status cues make the situation understandable at a glance.
4. **Actionable suggestions.** Recommend a concrete next step with a clear purpose.
5. **Direct control.** Users can update focus and action state from the dashboard.
6. **Conversation when useful.** Discussion helps refine the dashboard or resolve uncertainty.
7. **Visible rationale.** Explain recommendations briefly and distinguish known context from assumptions.
8. **Persistent context.** Preserve intentional user updates for subsequent recommendations.

## 7. Candidate MVP

The MVP scope should follow a concrete daily scenario. A candidate prototype could demonstrate:

1. The user provides enough context for a representative day.
2. The dashboard shows short-term and long-term priorities, work to do, and what is currently running.
3. The user can understand what needs attention, inspect ongoing work, and take or choose a useful action.
4. Direct corrections update the dashboard and inform subsequent agent suggestions.
5. Returning preserves useful context and reflects recorded changes.

User-entered context is one possible starting point. Connected sources and automatic preparation remain open decisions.

### Prototype success questions

- Can the user distinguish short-term priorities, long-term direction, work to do, and work already underway?
- Does opening the dashboard save effort at the start of the day?
- Does it reduce what the user has to remember or reconstruct?
- Does it help the user get on with their day sooner?
- Can the user understand and correct it without a lengthy conversation?
- Is there a useful reason to return the following morning?

## 8. Engineering implications

The earlier design centered on an agent composing arrangements of typed blocks. Implementation should now follow the daily dashboard experience and its intended benefit of freeing time and mental space once its shape is clearer.

Useful principles from the earlier design:

- Store canonical dashboard state so user edits and agent suggestions share context.
- Validate model output before applying changes.
- Preserve user corrections and handle stale updates.
- Keep enough history to explain or undo meaningful agent changes.
- Keep credentials server-side and authorize access to user data.

Previous stack suggestions—Next.js/TypeScript, Supabase, React Flow, and an optional Python agent runtime—remain provisional. React Flow may be unnecessary for a dashboard. The repository currently has a Python package scaffold; this document does not commit to replacing it.

Meta model requirements, WebMCP support, research integrations, and hosting choices should be revisited against the revised product needs and actual hackathon constraints. They do not define the dashboard experience.

## 9. Open product decisions

1. **What would free up time and mental space in a real morning?** Identify the context gathering, remembering, decisions, or work the product could help with.
2. **Where does current focus come from?** Explicit user selection, inference from connected activity, or a combination?
3. **How many focuses are visible?** One active focus, several parallel areas, or an overview with one selected area?
4. **What does next action mean?** A recommendation for the user, an action the agent can offer to execute, or both?
5. **What context is needed?** User notes, existing tasks, calendar events, project activity, or other sources?
6. **When should recommendations change?** On request, after a state change, or through proactive updates?
7. **What counts as currently running?** User projects and tasks, agent activity, background processes, or a combination? Where does reliable status come from?
8. **How are priorities set?** User-defined, agent-suggested, or both? What distinguishes the short-term and long-term horizons?
9. **Which real situation should the first prototype serve?** Choose a concrete example before finalizing the layout.

## 10. Immediate design priority

Walk through a real start of day: what the user currently checks, remembers, decides, and does. Use that example to design a dashboard that frees up time and mental space. Choose features and layout from that evidence.
