# Visual Second Brain — Quiet workspace

## Direction

Keep the dashboard simple and useful at a glance: short-term focus on the left,
long-term focus on the right, and draggable task bubbles below. On narrow screens,
stack those sections in the same order. Conversation stays in a floating panel.

The user's reference collection is
[Awesome DESIGN.md](https://github.com/VoltAgent/awesome-design-md).
The [Linear analysis](https://github.com/VoltAgent/awesome-design-md/blob/main/design-md/linear.app/DESIGN.md)
informed the restrained hierarchy and spacing; the
[Notion analysis](https://github.com/VoltAgent/awesome-design-md/blob/main/design-md/notion/DESIGN.md)
informed soft surfaces and consistent controls. This is a custom light theme,
not a reproduction of either brand or its marketing layout.

## Tokens

| Role | Value |
| --- | --- |
| Page | `#f7f8fa` |
| Surface | `#ffffff` |
| Primary text | `#242b3b` |
| Secondary text | `#626b7d` |
| Border | `#e3e6ed` |
| Action | `#435ac6` |
| Long-term surface | `#f0f2fa` |
| Font | Segoe UI / system sans serif; no remote font requests |
| Body / controls | 14–15px |
| Section title | 19px |
| Task title | 21px |
| Page title | 30–40px |
| Spacing | 8, 12, 16, 24, 32, 40px |

## Interaction rules

- Show the task outcome first. Overview subtasks use one closed-by-default
  disclosure; bubble details show subtasks or the description directly, with no nested disclosure.
- Keep completion beside the step it changes. A step never completes its parent.
- Show one readable progress fraction ending in “completed” and a deadline when present; avoid repeated
  captions, decorative icons, and tiny uppercase labels.
- Use **Subtasks** for the complete ordered leaf-step list, including struck-through completed steps. Count only those displayed steps.
- Use **Ask Muse** beside eligible work. This opens the existing persistent
  chat for that exact saved task or subtask. It sends nothing automatically.
- Use the date as the main heading; keep only the app name in the top bar, without
  a logo or tagline. Chevrons identify actual disclosure controls.
- Provide persistent general and task chats; Ctrl+Enter sends, Enter adds a line.
- Use explicit task counts. Do not show a workspace summary in long-term focus.
- Show each task's own deadline, including subtasks and dated bubbles. Do not
  inherit deadlines for display or invent missing dates.
- Keep scrolling natural through textareas, chat history, and task descriptions;
  allow the outer surface to scroll when an inner surface reaches its boundary.
- A separate right-hand chevron opens long-term descriptions; task names only edit. List all entries together
  in one scrollable area, without a separate “more” group.
- Bubble selection and switching preserve the page position. Keep keyboard focus
  on the bubble with preventScroll; show details below with opacity-only motion.
- All short-term index badges share the same neutral style; rank 1 is not a status.
- Keep Complete task last and aligned right in every action group.
- Past tasks show a read-only name/status and one Reopen task action; no child,
  editing, or chat controls. Group rows under Short-term and Long-term using the
  same classification as active tasks. Reopening preserves completed steps.
- Place + Add task immediately before each focus section's count. Create one task
  with a saved section choice. Short-term creation has numbered subtask rows;
  long-term creation has a description. Both offer optional date and importance.
  Save the short-term root and entered steps together, without a model call.
- Names, descriptions and dates are editable in place. Enter/blur saves names;
  Ctrl/Cmd+Enter or blur saves descriptions; Escape cancels. Editing a long-term
  name never opens or closes its description. Derived counts and interface labels are not content.
- Use one persistent, labeled **Talk to Muse** button. Workspace utilities live
  together in the header menu.
- Keep focus rings, keyboard bubble controls, native disclosures, reduced motion,
  failure feedback, and inline task-name editing.
- Color and bubble size supplement accessible importance labels.
- Sample mode must be visibly labeled and must never write fixture tasks.

An explicit time_horizon pins the task to its chosen section. For unselected
legacy/model tasks, dated tasks or saved plans appear in short-term focus;
remaining undated tasks appear in long-term focus. Short-term ordering is by
earliest deadline, undated plans last, then importance. The panels never overlap. Deadline badges run from red (overdue or due within one day), through orange
(two to three days) and yellow (four to seven days), to green (more than a week).
The sample-workspace label belongs in the header. Workspace and the voice note
use small, vertically centered chevrons that turn when expanded. The bubble map still includes all active tasks.
A simple chat task must stay one task unless the user explicitly requests or
supplies subtasks; missing details belong in chat or the description.
