# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Read these first

- **`.github/copilot-instructions.md`** — the canonical conventions (code style, naming, architecture patterns, "Do Not" list). Treat it as authoritative; everything here is a supplement, not a replacement.
- **`PLAN.md`** — the v1 execution roadmap with task-level progress checkboxes. Read it to know exactly where we are; **check off tasks as their PRs merge** so it always reflects reality.
- **`docs/STATUS.md`** — current milestone, architecture decisions, key concepts. Update at the end of a session that changes an architecture decision or milestone status.
- **`docs/VISION.md`** — long-term "why", including the egalitarian power model (users sovereign over their own experience; admins are infrastructure only). Rarely changes, but every design decision must respect it.
- **`docs/DESIGN.md`** — the UI design language (mobile-first inline disclosure, dense-page legibility, tasteful flourishes). Every screen must follow it; it's the basis for the Showcase/theming work too.

## Working agreements

- **One task = one GitHub issue = one PR** (branch `pr-<issue#>-<desc>`), individually CI-green, merged before dependents build on it. Prefer small durable increments over large interdependent batches — work must survive an interrupted session and be resumable from the repo alone.
- **Doc coherence**: VISION, STATUS, PLAN.md, this file, and copilot-instructions describe one system. Any doc change considers the whole picture — no drift, no slop, no duplicated half-truths across files.
- **Craftsmanship bar**: clean, elegant, well-organized TypeScript that feels crafted with love — clear naming, no redundancy, tests and Storybook stories landing *with* the code. Prefer proven open source for infrastructure; build-to-learn applies to product mechanics.
- If a convention or lesson will matter to future sessions, encode it here (or in a skill) rather than leaving it in conversation history.

## Commands

```bash
docker compose up -d        # Start PostgreSQL (required before dev / db / test against db)
pnpm dev                    # Dev server at http://localhost:3000
pnpm build                  # Production build
pnpm check                  # Biome lint + format (run before committing)
pnpm test                   # Run all tests (vitest)
pnpm storybook              # Component dev at :6006
```

- **Single test:** `pnpm vitest run src/lib/relative-time.test.ts` (or `pnpm vitest <pattern>` for watch mode).
- **DB workflow:** edit `src/db/schema.ts` → `pnpm db:push` (dev) or `pnpm db:generate` + `pnpm db:migrate` (versioned). `pnpm db:seed` loads sample data; `pnpm db:studio` opens the GUI.

Package manager is **pnpm** (`packageManager: pnpm@10.19.0`). Use `pnpx shadcn@latest add <component>` to add shadcn/ui components.

## Architecture

TanStack Start app (SSR + server functions in one Vite process). Path alias `@/` → `src/` (via `vite-tsconfig-paths`).

**Layered data flow — never collapse these layers:**

```
route/component → server function (transport only) → service layer (business logic) → Drizzle → Postgres
```

Server functions (`createServerFn`, see `src/services/health.ts`) are transport-only and return structured results, not throws. Real logic lives in the service layer so the transport can be swapped later.

**Building-block post model** — the central extensibility mechanism:

- DB (`src/db/schema.ts`): `posts` + `post_blocks`. A block has `block_type`, JSONB `content`, optional JSONB `layout`. New block types need **no migration** — they're conventions inside JSONB.
- App types (`src/db/block-types.ts`): `BlockContent` is a discriminated union on `blockType` (`text-short` | `text-long` | `image`), each with a runtime type guard. `content` crosses the DB boundary as `unknown`; narrow it with these guards before use.
- Rendering (`src/components/blocks/registry.ts`): `getBlockRenderer(blockType)` maps type → React component, falling back to `UnknownBlock` for unknown types. Register new block components here. This is how contributed block types will plug in.
- Layout (`src/lib/group-blocks.ts`): `groupBlocksIntoRows` packs adjacent `half`/`third`-width blocks into flex rows.

**Feed pipeline:** feed fetching follows `fetch → filter → sort → return` even though filter is currently a passthrough and sort is chronological — keep the structure so plugin algorithms slot in.

**DB connection** (`src/db/index.ts`): singleton `postgres` client (guarded against Vite HMR duplication) requiring `DATABASE_URL`; `db` is the Drizzle instance with the full schema.

## Conventions that bite

- **Biome formatting:** tabs, double quotes, auto-organized imports. `src/routeTree.gen.ts` and `src/styles.css` are excluded — never hand-edit the generated route tree.
- **Testing scope:** test pure logic / utilities colocated as `*.test.ts`; presentational React components get Storybook stories instead, not unit tests. Import `describe`/`it`/`expect` explicitly from `vitest`.
- **`src/db/index.ts` is lazy** — `db`/`sqlClient` are proxies that connect on first *use*, not at import, so importing a module that merely *references* the DB (a component → `*-api` → `auth` → `db` chain) no longer throws when `DATABASE_URL` is unset. This used to break CI (which has no `DATABASE_URL`) for any test that transitively reached the DB module — it bit A1, F5, I2 before the lazy fix. Still good practice: keep pure logic in DB-free modules (`*-pipeline.ts` / `*-rules.ts`) and **run `env -u DATABASE_URL pnpm test` before pushing** (a real *query* without `DATABASE_URL` still throws, so a test that actually hits the DB will still fail — correctly).
- **Build it to learn:** no auth libraries (auth is from-scratch argon2 + sessions), no cloud services. See the "Do Not" list in copilot-instructions.

## Deployment

Dockerfile + `server.production.mjs` serve the build. Images publish to `ghcr.io/masonmem/lines` (release workflow); deployment is a Komodo-managed compose stack in `masonmem/homelab` (hyperion, behind Caddy at `lines.hyperionx.dev`). No paid cloud — and never design host-tied; the platform must stay portable (see PLAN.md Wave H for node replication/migration). CI (`.github/workflows/ci.yml`) runs lint/build/test.
