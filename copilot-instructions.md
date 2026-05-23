# Personal Copilot CLI instructions (@masonmem)
#
# This file is loaded by Copilot CLI globally, regardless of which repo I'm
# in. Treat it as user-scoped guidance about *me as a developer* and my
# workflow — not as a place for model-runtime hacks (e.g. don't put Qwen
# `/no_think` soft switches here; those don't reliably work via Ollama and
# belong at the API/CLI layer via `--think=false` or `"think": false`).
#
# Suitable content:
#   - Communication style preferences (tone, verbosity)
#   - Workflow conventions (commit style, branch naming, lint/test habits)
#   - Tools I expect to be available locally
#   - Defaults to assume when a repo doesn't specify

## Tool use

- Only call tools that appear in the current session's tool catalog. If a
  tool name like `google_search`, `web_search`, `view_directory`, or
  `view_file_list_` is not in the provided list, do not call it. Use the
  tools that ARE provided instead.
- After a tool error of the form "Tool X does not exist", do not retry the
  same nonexistent name. Switch to a tool that IS in the catalog, or
  answer the user directly.
- Common task → tool mapping (when these tools are available):
  - List files in a directory → `glob` (pattern `*` or `**/*`), or `bash`
    with `ls`.
  - Search file contents → `grep`.
  - Read a file → `view`.
  - Run a shell command → `bash`.
- In non-interactive (`-p`) sessions, after performing the requested work,
  reply with the result and stop. Do not loop calling more tools "just in
  case".

