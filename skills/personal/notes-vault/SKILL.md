---
name: notes-vault
description: "Use when the user mentions \"my notes\", \"the inbox\", \"what did I write about X\", asks to save or draft a note, or anything else implying the personal Obsidian vault at ~/notes. Not for project docs or repo READMEs — those live in their repos."
---

# notes-vault

- `~/notes` is the Obsidian vault (journal, inbox, projects, writing).
  OpenCode uses its native file/search tools for the vault; Open WebUI
  exposes the same files through its `notes` tool server.
- When the user mentions "my notes", "the inbox", "what did I write
  about X", or anything implying the personal vault, USE the available
  native file/search or available notes tools rather than refusing. Don't
  reply with "I don't have access to your personal notes" — you do.
- Latest-by-mtime: start with `~/notes/00-inbox/` or the most recent
  dated subfolder; fall back to a search by query for topical asks.
- Treat the vault as **read-only by default**. Only write under
  `~/notes/00-inbox/agent-drafts/` (matches the OWUI airlock), and
  only when the user explicitly asks you to save / draft something.
