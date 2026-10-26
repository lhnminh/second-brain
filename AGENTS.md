# Agent instructions

## Collaborate step by step

- The user wants to understand all changes. Explain the intended change and its purpose before editing, provide updates at meaningful steps, and summarize what changed and how it was checked.
- Make focused, reviewable changes. Explain consequential product or architecture choices in plain language.
- Preserve existing user work. Clearly distinguish established decisions, working proposals, and assumptions.

## Project purpose

This project is Visual Second Brain, a hosted daily dashboard that helps the user free up time and mental space, especially at the start of the day.

Read `visual_second_brain_spec.md` before making product or architecture changes. It contains the current product direction and unresolved decisions. This file guides delivery toward the hackathon; it does not settle those open decisions.

- Make priorities, work to do, work currently underway, current focus, and next actions easy to understand visually.
- Prefer direct dashboard interaction, with conversation available when useful.
- Preserve useful context and user corrections between visits.
- Choose scope from a concrete daily scenario. Avoid adding features solely because they demonstrate an AI capability.

## Hackathon context and evidence

The project is intended for the Meta Global AI Developer Hackathon, October 26–November 4, 2026. The event description supplied by the user lists a submission deadline of November 4 at 9:00 PM ET and says dates may change.

Treat that supplied description as planning context, not the complete official rules. Verify current official rules, deadlines, required model use, eligibility, and submission requirements before relying on them for submission decisions. Do not invent scoring weights or mandatory deliverables.

The supplied description distinguishes application selection from project judging:

- Application selection: project clarity, feasibility, and theme fit; demonstrated technical skill. These two criteria are equally weighted for applications only.
- Indie developer project judging: creativity, technical ambition, and whether it works.
- Startup project judging: technical execution and whether it holds up in production.

The entry track is not yet confirmed. Do not silently select one or apply the application weights to final project judging.

## Build toward the judging criteria

The current product naturally aligns with **Build for Your World**: solve a firsthand problem and free up time and mental space. Do not force a second theme or expand scope to appear more ambitious.

When proposing substantial work, explain:

1. Which concrete user problem it addresses.
2. How it improves the daily dashboard experience.
3. What technical capability or judging criterion it demonstrates.
4. How we can verify that it works within the remaining time.

Favor a complete, reliable user journey over a wide collection of disconnected features. Aim for a distinctive visual experience with an observable benefit and enough technical depth to explain convincingly.

## Model integration

- Plan for a meaningful Meta model contribution to the core user journey. Make it possible to explain what the model contributes and why it helps.
- The supplied event description mentions Muse Spark, Muse Wonder, Muse Image, SAM 3.1, and Meta open weights models. Verify availability, API contracts, access, and official requirements before choosing an integration; the list does not imply every model must be used.
- Select models and providers based on the demonstrated user need, available access, latency, cost, and reliability. Partner credits are conditional, not assumed resources.
- Keep model calls behind a clear boundary, validate model output before changing dashboard state, and keep credentials server-side.
- Distinguish real model behavior from fixtures or simulated results in development and demonstrations. Never present a mock as a working integration.

## Delivery and verification

- Start with a concrete morning scenario and implement an end-to-end slice: provide context, view useful dashboard state, make a correction or choose an action, and return with that state preserved.
- Keep the stack proportional to that slice. The Python scaffold exists; frontend, storage, hosting, and agent runtime choices remain open. Explain substantial additions or replacements before implementing them.
- Preserve user corrections and distinguish observed facts, inferred recommendations, and stale or unavailable information.
- A suggested next action is not authorization to execute it. Showing work as running requires a reliable source for that status.
- Handle model failures visibly and preserve user state when a request fails. Never manufacture successful results.
- Run checks appropriate to each change. Prioritize verification of persistence, model-output validation, user corrections, and the main demo journey as those capabilities are implemented.
- For the startup track, if selected, add evidence appropriate to production claims, such as access isolation, failure recovery, and measured latency. Do not claim production readiness without evidence.

## Demo and submission readiness

As implementation progresses, keep setup instructions and the demo scenario reproducible. Record required configuration without secrets, actual model/provider usage, and known limitations.

Build toward a demonstration that shows the firsthand problem, the useful dashboard, the model's contribution, a user correction, and preserved context on return. Measure any claimed improvement using an explicit baseline; label unmeasured benefits as hypotheses.

Before submission, check the current official requirements and map each required artifact to real implementation evidence. Clearly state what works, what is simulated, and what remains incomplete. Do not invent results or submit/publish externally without user authorization.

## Code Map

- `backend/second_brain` - Python application source, managed by the root uv project

## Conventions

- Keep source files with `.py` extensions.
