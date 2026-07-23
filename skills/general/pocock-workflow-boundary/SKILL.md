---
name: pocock-workflow-boundary
description: Apply the external-state and permission boundary whenever using Matt Pocock workflow skills, CONTEXT/ADR/spec/ticket/research outputs, or ask-matt routing.
---

# Personal Pocock workflow boundary

Use the upstream skills unchanged. This skill is a policy overlay, not a fork or
an alternate router. `/ask-matt` routes only to upstream skills.

Before running a workflow skill, obtain the external state directory:

```sh
ai-project-state --ensure
```

Store personal context, ADR drafts, specifications, ticket drafts, research,
handoffs, and evaluation results there. Do not create `CONTEXT.md`, ADRs,
specifications, `.scratch`, or similar AI artifacts in a work repository unless
Mason explicitly opts in for that task.

Apply these mappings:

- `/grill-with-docs`: keep its context and decision outputs in external state.
- `/to-spec`: keep local drafts in external state; publishing to an issue
  tracker is a separate explicit action.
- `/to-tickets`: keep local ticket drafts in external state; creating tracker
  tickets is a separate explicit action.
- `/research` and `/teach`: write requested artifacts to external state.
- `/handoff`: use its OS-temporary handoff, then copy a retained result to
  external state only when requested.
- `/implement`: start a fresh session in the intended linked worktree and use
  `/tdd` as the inner discipline.

Never run `/setup-matt-pocock-skills` in a real work repository. Skills that
require repository-resident artifacts, branch creation, merge-conflict
operations, or parallel agents are opt-in and must be tested in disposable
scratch state first. Parallel agents still require an explicit maximum count.
