# Copilot Instructions — Lines

## GitHub

- **Owner**: masonmem
- **Repo**: lines

When interacting with GitHub (issues, PRs, etc.), always use these values.

## Project Overview

Lines is a self-hosted, distributed social platform. See `docs/VISION.md` for the long-term vision and `README.md` for tech stack and setup.

**v0.9.0 is released and live** (Milestones 1–10 + Wave P, including multi-node replication and the full plugin system); v1.0.0 is in progress (UI-refinement waves). We build frontend-first: each milestone is UI with mock data → backend → wire together. See `docs/STATUS.md` / `PLAN.md` for exactly where we are.

## Key Files

| File                              | Purpose                                                                    | Keep Updated?                                                           |
| --------------------------------- | -------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `PLAN.md`                         | **v1 execution roadmap with task-level progress checkboxes**               | **Yes — check off tasks as their PRs merge**                            |
| `docs/STATUS.md`                  | **Current milestone, architecture decisions, issue tracker, key concepts** | **Yes — update after every architectural decision or milestone change** |
| `docs/VISION.md`                  | Long-term vision, principles, future ideas                                 | Rarely — only when the vision evolves                                   |
| `README.md`                       | Tech stack, setup instructions, project structure, scripts                 | When dev setup or project structure changes                             |
| `.github/copilot-instructions.md` | This file — agent context and guidelines                                   | When conventions or patterns change                                     |
| `.cursorrules`                    | Cursor-specific instructions (shadcn usage)                                | As needed                                                               |
| `biome.json`                      | Linting and formatting config                                              | Rarely                                                                  |

**At the start of a session**, read `docs/STATUS.md` and `PLAN.md` to understand what's in progress and what decisions have been made. Check GitHub Issues for detailed task tracking.

**Docs are one system**: VISION, STATUS, PLAN.md, CLAUDE.md, and this file must stay coherent as a whole — any doc change considers the full picture.

**At the end of a session** that changes architecture decisions, completes issues, or shifts milestone status, update `docs/STATUS.md` accordingly. Keep it concise — it's a reference, not a journal.

## Tech Stack

- **Framework**: TanStack Start (SSR + server functions)
- **Routing**: TanStack Router (file-based, `src/routes/`)
- **Data fetching**: TanStack Query
- **Styling**: Tailwind CSS v4
- **UI components**: shadcn/ui (`pnpx shadcn@latest add <component>`)
- **Database**: PostgreSQL (via Docker Compose)
- **ORM**: Drizzle
- **Build**: Vite
- **Linting/Formatting**: Biome
- **Testing**: Vitest
- **Component dev**: Storybook

## Architecture Patterns

### API Layer

Server functions call a **service layer**. Never put business logic directly in server functions — they are transport only.

```
route/component → server function → service → database
```

The service layer is the real API boundary. If we swap server functions for REST routes later, only the transport changes.

### Post Model — Building Blocks

Posts are containers of ordered blocks. See `docs/STATUS.md` for the full concept.

- Schema: `posts` table + `post_blocks` table (JSONB `content` and `layout` fields)
- Frontend: Block renderer registry maps `block_type` → React component
- Always handle unknown block types with a graceful fallback

### Feed Pipeline

Feed fetching follows a pipeline pattern:

```
fetchPosts() → applyFilters() → applySorting() → return
```

Even when filters are a passthrough, maintain this structure so plugin algorithms slot in cleanly.

### Storage Abstraction

Media storage goes through an interface: `save()`, `get()`, `delete()`. Local filesystem today, distributed later. Never access storage directly — always go through the interface.

## Code Style

### General

- Write clean, idiomatic TypeScript
- Prefer explicit types over `any` — use `unknown` when the type is genuinely not known
- Use discriminated unions for variant types (block content, API responses, etc.)
- Keep functions small and single-purpose
- Colocate related code — tests next to source, stories next to components

### Formatting (enforced by Biome)

- **Indentation**: tabs
- **Quotes**: double quotes
- **Imports**: auto-organized by Biome
- Run `pnpm check` before committing

### Naming

- **Files**: kebab-case for utilities (`feed-service.ts`), PascalCase for React components (`PostCard.tsx`)
- **Variables/functions**: camelCase
- **Types/interfaces**: PascalCase
- **Database columns**: snake_case
- **Constants**: UPPER_SNAKE_CASE for true constants, camelCase for derived values

### React & Components

- Functional components only
- Prefer named exports over default exports (exception: route components required by TanStack Router)
- Props types defined as `interface` next to the component
- Every UI component gets a Storybook story
- Keep components presentational where possible — data fetching happens in routes or hooks

### Database & Backend

- Schema defined in Drizzle (TypeScript, not raw SQL)
- Migrations managed by `drizzle-kit`
- Use parameterized queries — never interpolate user input into SQL
- Service functions are `async` and return typed results
- Seed data scripts go in `src/db/seed.ts`

### Error Handling

- Server functions should return structured errors, not throw
- Frontend should always handle loading and error states
- Log errors with context (what operation failed, what input was given)

### Testing

- Use Vitest with `describe`/`it` pattern
- Colocate test files next to source: `relative-time.ts` → `relative-time.test.ts`
- Test pure logic and utility functions — not presentational React components (those get Storybook stories)
- Import `describe`, `expect`, `it`, and lifecycle hooks (`beforeEach`, `afterEach`) explicitly from `vitest`
- Use `vi.spyOn` for mocking; restore mocks in `afterEach`
- Keep tests focused: one behavior per `it` block
- Extract testable logic out of components into utility files when it has meaningful branching or algorithmic complexity
- Run `pnpm test` before committing

### Git

- Use [Conventional Commits](https://www.conventionalcommits.org/): `type(scope): description`
- Common types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `style`
- Reference GitHub issues where appropriate: `feat(db): add connection module (#1)`
- Keep commits focused — one logical change per commit
- Branch naming: `pr-<issue#>-<short-description>` (e.g., `pr-01-infra-setup`)

## Project Structure

```
src/
├── routes/           # File-based routing (TanStack Router)
├── components/       # UI components + Storybook stories
│   └── storybook/    # shadcn component stories
├── services/         # Business logic layer (called by server functions)
├── db/               # Schema, migrations, seed data
├── integrations/     # Third-party integration setup
├── lib/              # Shared utilities
└── mocks/            # Mock data for development and Storybook
docs/
├── VISION.md         # Long-term vision (the "why")
├── STATUS.md         # Current status and decisions (the "what now")
├── DESIGN.md         # UI design language (mobile-first; every screen follows it)
├── PLUGINS.md        # Plugin developer guide (manifests, templates, DSL, themes)
├── SHOWCASE.md       # Showcase / theming-v2 / demo-content design (Wave Q)
├── GETTING-STARTED.md# End-user guide
├── SECURITY.md       # Threat model
├── MODERATION.md     # Moderation philosophy
└── MIGRATION.md      # Multi-node migration runbook
```

## Do Not

- Add cloud services (AWS, Vercel, Supabase, etc.) — everything runs on hardware you control
- Use auth libraries — auth is built from scratch as a learning exercise
- Skip Storybook stories for new UI components
- Put business logic in route components or server functions
- Use `any` type without a comment explaining why
- Create documentation files to summarize work unless explicitly asked
