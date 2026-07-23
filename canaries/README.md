# Model canaries

Copy this directory to disposable external state before an evaluation. Install
the pinned dependencies there; do not ask the model to edit `ai-sync`.

```sh
destination="$(ai-project-state --ensure)/canaries/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$destination"
cp -R ~/code/ai-sync/canaries/. "$destination/"
cd "$destination"
npm ci
```

Give the model only one task:

- `typescript/TASK.md`
- `react/TASK.md`
- `security/TASK.md`

Record the run in a copy of `RESULTS.md`. The seeded targeted test should fail
before the task and pass afterward. A run must not modify other canaries.
