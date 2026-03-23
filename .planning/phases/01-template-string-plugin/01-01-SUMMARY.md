---
phase: 01-template-string-plugin
plan: "01"
subsystem: testing
tags: [vitest, tdd, unit-tests, template-resolver, linked-template-string]

# Dependency graph
requires: []
provides:
  - vitest test runner installed and configured in webapps/main
  - RED test scaffold for templateResolver (slugify, encodeExpression, decodeExpression, resolveExpression)
  - RED test scaffold for linkedTemplateString plugin (defaultSchema.linkType, templateExpression, pdf)
affects: [01-02, 01-03]

# Tech tracking
tech-stack:
  added: [vitest@4.1.0]
  patterns: [TDD RED-GREEN-REFACTOR, vitest ESM config with node environment]

key-files:
  created:
    - webapps/main/vitest.config.js
    - webapps/main/src/lib/print/templateResolver.test.js
    - webapps/main/src/lib/print/plugins/linkedTemplateString.test.js
  modified:
    - webapps/main/package.json
    - webapps/main/yarn.lock

key-decisions:
  - "Used yarn (not npm) to install vitest — project uses yarn lockfile"
  - "vitest.config.js uses node environment with src/**/*.test.js glob"
  - "Test stubs intentionally import non-existent modules to establish RED state"

patterns-established:
  - "TDD Pattern: Test files created before implementation modules exist"
  - "Import pattern: named exports from ./templateResolver.js and ./linkedTemplateString.js"
  - "Mock context pattern: getPresetValue and getCustomFieldValue on ctx object"

requirements-completed: [TMPL-02, TMPL-03]

# Metrics
duration: 14min
completed: 2026-03-12
---

# Phase 1 Plan 01: Test Scaffold Summary

**vitest@4.1.0 installed and configured with 13 failing RED test stubs covering templateResolver (slugify/encode/decode/resolve) and linkedTemplateString plugin schema**

## Performance

- **Duration:** 14 min
- **Started:** 2026-03-12T15:25:53Z
- **Completed:** 2026-03-12T15:39:19Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Installed vitest@4.1.0 as devDependency and created `vitest.config.js` with node environment
- Created `templateResolver.test.js` with 10 test cases in RED state (module-not-found)
- Created `linkedTemplateString.test.js` with 3 test cases in RED state (module-not-found)

## Task Commits

Each task was committed atomically:

1. **Task 1: Install vitest and write vitest config** - `5a913dd1` (chore)
2. **Task 2: Write failing test stubs** - `152a3d02` (test)

**Plan metadata:** `[pending]` (docs: complete plan)

## Files Created/Modified
- `webapps/main/vitest.config.js` - Vitest config pointing at src/**/*.test.js with node environment
- `webapps/main/src/lib/print/templateResolver.test.js` - 10 failing tests for slugify, encodeExpression, decodeExpression, resolveExpression
- `webapps/main/src/lib/print/plugins/linkedTemplateString.test.js` - 3 failing tests for createLinkedTemplateString plugin schema
- `webapps/main/package.json` - Added vitest@^4.1.0 as devDependency
- `webapps/main/yarn.lock` - Updated with vitest dependency tree

## Decisions Made
- Used yarn instead of npm (project has yarn.lock, npm install failed due to rolldown peer dependency conflict)
- vitest@4.1.0 installed (latest at time of execution)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Switched from npm to yarn for vitest installation**
- **Found during:** Task 1 (Install vitest)
- **Issue:** `npm install -D vitest` failed with ETARGET error on rolldown@1.x peer dependency; project uses yarn lockfile
- **Fix:** Used `yarn add -D vitest` instead
- **Files modified:** package.json, yarn.lock
- **Verification:** `npx vitest --version` printed `vitest/4.1.0`
- **Committed in:** 5a913dd1 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Package manager switch was necessary for installation to succeed. No scope creep.

## Issues Encountered
- yarn install took ~325 seconds due to downloading rolldown and lightningcss native binaries for arm64

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Test scaffold is in place — implementation plans (01-02, 01-03) can proceed
- Both test files parseable by vitest without configuration errors
- RED state confirmed: both suites fail with `Cannot find module` errors

---
*Phase: 01-template-string-plugin*
*Completed: 2026-03-12*
