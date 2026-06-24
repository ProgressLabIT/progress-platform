# Shared webapp composables — shaping notes

> **Status: PARKED, nothing to do now.** Not an ADR. Captures a 2026-06-03 discussion about
> de-duplicating composables shared between the two webapps. **Decision: do not pursue.** The two
> apps may converge into a single app in the near future, which would dissolve the duplication
> entirely — so the setup cost isn't worth paying now. Revisit only if convergence stalls *and*
> the shared surface keeps growing.

## Where this came from

While migrating the per-tab SSE multiplex (`useSSE.js`) into both webapps (commits `1401a862` main,
`301d04d2` warehouse), we noticed `useSSE.js` now lives as two identical copies. That raised the
question of a shared package for cross-webapp composables.

## The duplication surface (today)

Four composables exist in both `webapps/main/src/composables/` and `webapps/warehouse/src/composables/`:
`drawer.js`, `event.js`, `theme.js`, `useSSE.js`. Small but creeping.

## Structure facts (so we don't re-discover them)

- Two **independent** Quasar 2.16 / Vue 3.4 apps, each with its own `yarn.lock` (yarn 1.22 classic).
  **No workspaces**; root `yarn.lock` is an empty stub.
- `@` aliases to **each app's own** `./src` (`quasar.config.js`).
- **The two `boot/axios.js` differ** — so the `api` axios instance a shared composable needs is
  genuinely app-specific.

## The one real constraint

Shared composables can't `import { api } from '@/boot/axios'`: there's no single `@` for shared
code, and the `api` instance differs per app. **Shared code must receive `api` by injection, not
import it.** Everything else follows from that.

## Options (if we ever do this)

1. **Lightweight shared source dir (preferred if we proceed).** `webapps/shared/composables/*`,
   referenced via a per-app Vite alias `@shared` → `../shared`. Each composable becomes a factory
   that takes `api` (`createSSE(api) → { useSSE }`), with all module-singleton state moved inside the
   factory closure (each app is a separate bundle, so state is naturally per-app). Keep a one-line
   shim at the old path per app (`export const { useSSE } = createSSE(api)`) so **no importer
   changes**. Gotcha: `webapps/shared/` is outside each Quasar root → Vite dev server needs
   `extendViteConf` to push the path into `server.fs.allow` (build is fine via alias). Neither app's
   eslint lints `shared/` unless configured.
2. **Yarn-workspaces package** (`packages/web-shared`, root `package.json` workspaces, apps depend on
   `workspace:*`). Same factory-DI design. **Skip** — converting two apps with separate lockfiles into
   a hoisted yarn-1 monorepo churns dependency resolution and fights Quasar CLI's per-app
   expectations; far too much for 4 small files.

If we proceed at all, scope it to **all 4 duplicated files at once** (amortize the alias + fs.allow
setup), not `useSSE` alone.

## Until then — drift guard

The two `useSSE.js` copies must stay in sync if touched. Currently guarded only by the project memory
note (`project_sse_connection_budget.md`). No CI check added (solo-maintainer discipline; convergence
likely makes it moot).
