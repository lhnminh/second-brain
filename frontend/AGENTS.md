# Frontend instructions

These instructions supplement the root `AGENTS.md`. Read it and
`../visual_second_brain_spec.md` before making product or architecture changes.
Explain changes step by step and preserve the other developer's work.

## Ownership

Own the browser experience in `frontend/`:

- Daily dashboard with short-term and long-term priorities, tasks, subtasks,
  deadlines, and activity status.
- Direct task editing, completion controls, and five importance choices.
- Sign-in and onboarding screens, including review of extracted user context.
- Corner pet, text chat, microphone controls, and visible input/processing states.
- Loading, empty, error, and retry states.

The frontend framework is not selected yet. Choose and document the setup before
adding framework-specific scaffolding. Keep setup commands in the root README
accurate as the application becomes runnable.

## Product constraints

- Users can type or provide voice input. Muse replies in text chat; spoken
  replies are outside the MVP scope.
- Users choose one of five importance levels. Do not expose the internal 0–100
  score, a slider, or numeric entry.
- User-selected levels constrain the agent's score. Labels and ranges must agree
  with the shared contract; do not define a competing frontend mapping.
- Show actual planning activity for subtask creation and importance scoring.
  Screen streaming and screenshots are deferred.
- Keep the dashboard useful when chat is closed. Keep user edits intact during
  loading and failures.

## Backend boundary and shared contracts

- Coordinate task, context, message, activity, error, and authentication contracts
  with the backend developer before integrating. Record the agreed shapes and
  endpoints in a shared root-level contract document when they are defined.
- Build against representative fixtures while APIs are being implemented. Label
  simulated behavior clearly; keep fixtures behind the same client boundary used
  for real requests.
- Keep Muse credentials and model calls on the backend. Microphone capture and
  permission controls belong here; the voice transport and processing contract
  must be agreed with the backend developer.
- Server authorization is required even when frontend controls hide an action.
- Own changes inside `frontend/`. Coordinate backend or shared root-file changes
  with the other developer; do not silently change API shapes or task semantics.

## Verification

Check the changed user flow, including loading and failure behavior. As the
features become functional, verify task edits, importance selection, microphone
controls, chat, and saved-state reload against the backend. Report which checks
used fixtures and which used real integration.
