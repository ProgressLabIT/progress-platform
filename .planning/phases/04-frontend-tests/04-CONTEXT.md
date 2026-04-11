# Phase 4: Frontend Tests - Context

**Gathered:** 2026-04-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver automated tests for two target Vue components and three Playwright E2E journeys:
1. Vitest component tests for `ProgressBtn.vue` — 6 behavioral states with user interaction simulation (click/dblclick triggers)
2. Vitest component tests for `WorkSessionSteps.vue` — avatar styling, step navigation, component type selection
3. Playwright E2E scripts targeting localhost — 3 journeys (login→batch complete, work order creation, stock receipt)

No changes to production components. No new infrastructure beyond test tooling additions.

</domain>

<decisions>
## Implementation Decisions

### Vitest Configuration
- **D-01:** Add a SEPARATE `vitest.component.config.js` alongside the existing `vitest.config.js` — do NOT modify the existing config (keeps `src/lib/print/*.test.js` running in `node` environment unchanged)
- **D-02:** New config: environment `happy-dom`, `@vitejs/plugin-vue` for SFC transformation, includes `src/**/*.component.test.js` (or similar glob distinct from existing `src/**/*.test.js`)
- **D-03:** Component tests run via `vitest --config vitest.component.config.js`
- **D-04:** Both configs coexist — existing print utility tests unaffected

### Quasar Mock Strategy
- **D-05:** Stub Quasar components manually via `@vue/test-utils` stubs option: `{ 'q-btn': true, 'q-icon': true, 'q-avatar': true, 'q-toolbar': true }` etc.
- **D-06:** Mock `$t()` as identity function: `global.config.globalProperties.$t = (key) => key`
- **D-07:** Mock `$theme` as a simple object: `global.config.globalProperties.$theme = { green: '#4CAF50', grey: '#9E9E9E', ... }`
- **D-08:** No `@quasar/testing-unit-vitest` — manual stubs are sufficient for logic/behavior tests
- **D-09:** Test behavioral correctness (what actions fire, what conditions enable/disable, what renders conditionally) not rendering fidelity (pixel-perfect Quasar output)

### ProgressBtn Test Approach
- **D-10:** Use `wrapper.trigger('click')` and `wrapper.trigger('dblclick')` for interaction simulation
- **D-11:** Do NOT test `v-touch-hold` directive (Quasar touch directive — too complex to simulate in jsdom/happy-dom)
- **D-12:** 6 behavioral states to cover:
  - `step_check` mode: renders differently (icon/text reflects step check state)
  - `completeStep` call: click in non-last-step mode emits/calls complete step
  - `declareBatch` call: click in last-step mode emits/calls declare batch
  - `edit_mode` state: q-btn swapped for save/cancel buttons (template branch)
  - disabled state: `!job.active` disables the button
  - mandatory field validation: if mandatory fields unfilled, click blocked/warned
- **D-13:** Test via `mount` (not `shallowMount`) but with all Quasar components stubbed

### WorkSessionSteps Test Approach
- **D-14:** Cover: avatar step styling (active vs inactive via `stepStyle()`), step click navigation (`stepClick()`), component type selection (if applicable)
- **D-15:** Interaction simulation via `wrapper.trigger('click')` on avatar elements
- **D-16:** Assertions on computed styles or CSS classes for active step highlighting

### E2E Playwright
- **D-17:** Target: `http://localhost` (or configurable via `PLAYWRIGHT_BASE_URL` env var)
- **D-18:** Playwright tests are standalone scripts NOT integrated into Vitest — live in `testing/playwright/`
- **D-19:** "Can be executed" = scripts exist, run without crashing when backend+frontend stack is running at localhost
- **D-20:** Not CI-automated (requires full stack) — same pattern as Locust. Documented as manual-run tools.
- **D-21:** Three journeys:
  - `login_to_batch_complete.spec.js` — login → select work order → start batch → complete batch
  - `work_order_creation.spec.js` — navigate to work orders → create new → verify created
  - `stock_receipt.spec.js` — navigate to inventory → create stock receipt movement

### Plan Split
- **D-22:** Plan 04-01: Vitest config setup + ProgressBtn component tests (6 behavioral states, user interaction simulation)
- **D-23:** Plan 04-02: WorkSessionSteps component tests (avatar styling, step navigation, component type selection)
- **D-24:** Plan 04-03: Playwright E2E scripts (3 journeys, localhost target, documented as manual)

### Claude's Discretion
- Exact glob pattern for component test files (`.component.test.js` vs `.spec.js` vs `__tests__/*.js`)
- Specific `@vue/test-utils` version compatibility with the installed Vue 3.4.18 — researcher to verify
- Which Pinia/Vuex stores ProgressBtn depends on — researcher to check component's `setup()` or `props` for required store injections
- Exact Playwright version and whether `@playwright/test` is already in package.json

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `webapps/main/src/components/ProgressBtn.vue` — target component, 18.4K, Quasar + $t + $theme
- `webapps/main/src/views/WorkSessionSteps.vue` — target component, Quasar q-avatar, stepStyle/stepClick
- `webapps/main/vitest.config.js` — existing config (node env, print tests) — must NOT be modified
- `webapps/main/package.json` — check for @vue/test-utils, playwright, vitest version compatibility
- `webapps/main/src/lib/print/zpl.test.js` — example of existing test pattern (utility, node env)

</canonical_refs>

<code_context>
## Existing Code Insights

- Vitest already installed (vitest.config.js exists), environment: 'node', targets `src/**/*.test.js`
- 3 existing utility tests in `src/lib/print/` — all pure logic, no Vue component rendering
- `ProgressBtn.vue` (18.4K): uses `q-btn`, `q-icon`, `v-touch-hold.mouse`, `$t()`, `$theme`, Options API or Composition API (needs verification)
- `WorkSessionSteps.vue`: uses `q-avatar`, `q-toolbar`, `$t()`, template `v-for` over steps
- No existing Playwright setup in webapps/main
- Vue 3.4.18 installed, Quasar 2.16.0

</code_context>

<specifics>
## Specific Ideas

- ProgressBtn test file: `src/components/ProgressBtn.component.test.js`
- WorkSessionSteps test file: `src/views/WorkSessionSteps.component.test.js`
- Component test run command: `yarn vitest --config vitest.component.config.js run`
- Playwright journey files: `testing/playwright/login_to_batch_complete.spec.js`, `testing/playwright/work_order_creation.spec.js`, `testing/playwright/stock_receipt.spec.js`

</specifics>

<deferred>
## Deferred Ideas

- **Touch-hold directive testing** — `v-touch-hold.mouse` on ProgressBtn is Quasar-specific and not testable in happy-dom without significant mocking. Deferred.
- **CI integration for E2E** — Playwright running against a Dockerized stack in CI is a valid future phase. Deferred.
- **Visual regression testing** — Screenshot comparison for component rendering. Deferred.

</deferred>
