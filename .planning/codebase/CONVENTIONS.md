# Coding Conventions

**Analysis Date:** 2026-04-15

## Naming Patterns

**Files:**
- Backend Python: `snake_case.py` -- one file per domain (`production.py`, `inventory.py`, `counting.py`)
- Backend models: `snake_case.py` matching endpoint domain (`backend/api/models/production.py`)
- Frontend Vue components: `PascalCase.vue` (`PrintTemplateCard.vue`, `BaseAutocompleteProduct.vue`)
- Frontend composables: mixed -- `use{Name}.js` for newer (`useSSE.js`, `usePrefectAPI.js`) and plain `camelCase.js` for older (`event.js`, `drawer.js`, `warehouse.js`)
- Pinia stores: `camelCase.js` (`config.js`, `countSession.js`, `task.js`)
- Vuex store modules: `camelCase.js` (`product.js`, `session.js`, `traceability.js`)

**Functions:**
- Backend: `snake_case` (`create_work_order`, `get_positions`, `_generate_counter`)
- Frontend: `camelCase` (`showFieldDetail`, `getFieldIcon`, `sendEvent`)
- Private/internal backend helpers: underscore prefix (`_key()`, `_now()`, `_event_payload()`)

**Variables:**
- Backend: `snake_case` (`new_wo`, `wo_code_in_use`, `bind_vars`)
- Frontend template refs: `snake_case` in templates (`search_text`, `splitter_model`, `selected_field_key`)
- Frontend JS: `camelCase` in `<script setup>` (`isLoading`, `configDefaults`)
- NOTE: Frontend has inconsistent casing -- templates use `snake_case` while modern JS uses `camelCase`

**Types/Models:**
- Backend Pydantic: `PascalCase` (`WorkOrderNew`, `PositionSearchParams`, `EventInfoModel`)
- Backend Enums: `PascalCase` class, `UPPER_SNAKE_CASE` values (`EventType.JOB_STARTED`, `WorkStatus.CREATED`)
- Frontend: no TypeScript -- plain JavaScript throughout

**Component Prefixes:**
- `Base*` prefix for reusable UI primitives: `BaseDialog.vue`, `BaseConfirmationDialog.vue`, `BaseDatePicker.vue`
- `BaseAutocomplete*` prefix for autocomplete variants: `BaseAutocompleteProduct.vue`, `BaseAutocompleteUser.vue`

## Code Style

**Formatting:**
- Frontend: Prettier with `singleQuote: true` -- config at `webapps/main/.prettierrc.json`
- Backend: PEP 8 (no formatter config detected -- likely manual or editor-based)

**Linting:**
- ESLint with `plugin:vue/vue3-recommended` + `plugin:import/recommended` + `prettier`
- Config at `webapps/main/.eslintrc.js`
- Key enforced rules:
  - `vue/eqeqeq: 'error'` -- strict equality in templates
  - `curly: 'error'` -- always use braces
  - `no-unused-vars: ['error', { argsIgnorePattern: '^_' }]` -- prefix unused args with `_`
  - `import/order: 'warn'` -- alphabetized, grouped by type
  - `vue/prop-name-casing: 'off'` -- intentionally disabled (TODO to enable after migration)
  - `vue/no-unused-properties: 'warn'` -- warns on unused props/setup returns
- No Python linter config detected (no ruff.toml, pyproject.toml lint section, etc.)

## Import Organization

**Backend:**
- Standard library first, then FastAPI/framework, then internal modules
- Wildcard imports from models are common and accepted: `from models.production import *`
- Relative imports not used -- all imports are absolute from `backend/api/` root (set via `pythonpath` in pytest config)
- Example pattern from `backend/api/endpoints/production.py`:
  ```python
  import traceback
  from datetime import datetime
  from typing import List

  from fastapi import APIRouter, Body, HTTPException, Query, Depends
  from utils import auth

  from models.production import *
  from utils.api import APIResponse
  from utils.db import db
  from utils.production import Queries, create_job_record
  ```

**Frontend:**
- ESLint enforces `import/order` with alphabetization
- Groups: builtin -> external -> internal -> parent -> sibling -> index
- Path alias `@/` maps to `src/` -- use for all internal imports
- Example from `webapps/main/src/composables/event.js`:
  ```javascript
  import { Notify } from 'quasar';
  import { timestamp } from '@/lib/TimeHandling.js';
  import store from '@/store';
  import { useTaskStore } from '@/stores/task.js';
  import { api } from '../boot/axios';
  ```

## Component Patterns

**Vue SFC Style -- Two patterns coexist:**
- `<script setup>` (Composition API): ~101 components -- use for all new code
- `export default {}` (Options API): ~100 components -- legacy, do not convert unless modifying
- Total .vue files: ~204 in main webapp

**New Component Template (use this for new components):**
```vue
<template>
  <!-- template content -->
</template>

<script setup>
import { ref, computed } from 'vue';
import { api } from '@/boot/axios';

const props = defineProps({
  // props here
});

const emit = defineEmits(['event-name']);

// reactive state
const loading = ref(false);
</script>
```

**Legacy Options API pattern (do not add new code in this style):**
```vue
<script>
export default {
  name: 'ComponentName',
  props: { /* ... */ },
  data() { return { /* ... */ }; },
  computed: { /* ... */ },
  methods: { /* ... */ },
};
</script>
```

## State Management

**Pinia stores (newer -- use for new state):**
- Location: `webapps/main/src/stores/`
- 4 stores: `config.js`, `countSession.js`, `task.js`, `taskType.js`
- Pattern: `defineStore` with setup function syntax (not options syntax)
- Example from `webapps/main/src/stores/config.js`:
  ```javascript
  import { defineStore } from 'pinia';
  import { reactive, ref } from 'vue';
  import { api } from '@/boot/axios';

  export const useConfigStore = defineStore('config', () => {
    const isLoading = ref(true);
    const config = reactive({ ...configDefaults });
    // ...
  });
  ```

**Vuex store (legacy -- avoid adding to this):**
- Location: `webapps/main/src/store/`
- 14 modules: `product.js`, `session.js`, `traceability.js`, `warehouse.js`, etc.
- Root store at `webapps/main/src/store/index.js` -- imports all modules
- Still used for session management, product state, and many domain areas
- Mutations use `UPPER_SNAKE_CASE` (`TOGGLE_SESSION_LOCK`, `CLOSE_SESSION`)

## API Call Patterns

**Frontend -> Backend:**
- All HTTP via `api` axios instance from `webapps/main/src/boot/axios.js`
- Auth: JWT token injected via axios request interceptor from Vuex getter `getToken`
- 401 responses trigger automatic logout (except `whoami` and `session` endpoints)
- Event dispatching: use `sendEvent()` composable from `webapps/main/src/composables/event.js`
- SSE for real-time updates: use `useSSE()` composable from `webapps/main/src/composables/useSSE.js`

**Backend Endpoint Pattern:**
- One `router = APIRouter()` per domain file in `backend/api/endpoints/`
- Auth via `dependencies=[Depends(auth.verify_token)]` on each route
- Response model: `APIResponse` wrapper from `utils.api`
- Transaction management: manual `db.begin_transaction()` / `tx.abort_transaction()` in endpoint body
- Error pattern: try/except with `traceback.format_exc()` in HTTPException detail

## Event System Pattern

**Event class structure** (all events follow this pattern):
```python
# Location: backend/api/events/{domain}/{event_name}.py
class SomeEvent(BaseProductionEvent):  # or BaseEvent

    class InfoModel(EventInfoModel):
        # Event-specific fields as Pydantic model
        job_key: str
        batch_key: str | None = None

    @classmethod
    def get_event_type(cls) -> EventType:
        return EventType.SOME_EVENT

    @classmethod
    def get_tx_collections(cls) -> list[str]:
        return ['Job', 'Batch', 'WorkOrder']  # collections this event writes

    def apply(self):
        # Business logic -- all DB mutations here, within the transaction
        pass
```

**Child event spawning:**
```python
self.batch = BatchCreatedEvent.create_as_child(self, dict(
    job_key=self.info.job_key,
    phase_key=self.info.phase_key,
))
```

**Event lifecycle:** `__init__` -> `pre_processing()` -> `apply()` -> `post_processing()` -> `store_event()` -> commit

**Event types registry:** `backend/api/models/event.py` -- `EventType` enum with 50+ event types organized by domain (Production, Collaboration, Admin, Inventory, Serial, Work Session, WIP).

## Error Handling

**Backend -- Current state (problematic):**
- 62 bare `except:` clauses across 14 endpoint files
- Common anti-pattern: catch-all with `traceback.format_exc()` returned in HTTP 500
- Example from `backend/api/endpoints/production.py`:
  ```python
  try:
      # ... business logic
  except:
      tx.abort_transaction()
      raise HTTPException(status_code=500, detail=traceback.format_exc())
  ```

**Backend -- Preferred pattern for new code:**
- Catch specific exceptions
- Use custom exception classes from `backend/api/utils/exceptions.py` (e.g., `JobIsStartedError`, `JobHasNoAssigneeError`)
- Event system: transactions auto-abort in `finally` block of `BaseEvent.save()` if still running

**Frontend:**
- Composable-level error handling with Quasar `Notify.create()` for user-facing errors
- Pattern from `sendEvent()`: catch error, show notification, re-throw

## Logging

**Backend:**
- Use Python `logging` module: `logger = logging.getLogger("module_name")`
- `print()` statements exist in legacy code -- do not add more
- Logger used in `backend/api/events/base_event.py` for NATS publish failures

**Frontend:**
- `console.error()` for caught exceptions (e.g., SSE listener errors in `useSSE.js`)
- `console.warn()` for configuration fallbacks (e.g., missing `API_CONFIG` in `axios.js`)
- No structured logging framework

## Comments

**Backend:**
- Section separators common: `# ===============================================`
- Numbered comments for workflow steps: `# 0. Handle Work Order Code`, `# 1. Fetch product data`
- TODO comments present but sparse
- Docstrings: present on event classes and utility functions, absent on most endpoints

**Frontend:**
- JSDoc on composables (e.g., `useSSE()` in `webapps/main/src/composables/useSSE.js` has `@param` and `@returns`)
- Inline comments in templates are rare
- ESLint TODO comments in `.eslintrc.js` for future rule enablement

## Function Design

**Backend endpoints:**
- Async functions (`async def`) even when no await is used (FastAPI convention)
- Parameters: Pydantic models for body, `Query()` for query params, `Depends()` for injection
- Inner helper functions defined within endpoint scope (e.g., `enrich_with_media` in `process.py`)

**Frontend composables:**
- Return object with exposed API: `return { subscribe }` pattern
- Auto-cleanup via `onBeforeUnmount()` lifecycle hook
- Factory function pattern: composable returns a factory (`auth_headers` returns `_make_headers`)

## Module Design

**Exports:**
- Backend: no `__all__` declarations, wildcard imports from models accepted
- Frontend: named exports for composables (`export function useSSE`), default export for boot files

**Barrel Files:**
- Backend `backend/api/events/__init__.py` registers event classes
- Frontend: no barrel files -- direct imports to specific files

## Patterns to Follow

1. `<script setup>` with Composition API for new Vue components
2. Pinia with setup function syntax for new stores
3. `sendEvent()` composable for event dispatching from frontend
4. `useSSE()` for real-time data subscriptions
5. Pydantic models for all backend data validation
6. Specific exception types from `utils/exceptions.py`
7. `logging` module (not `print()`) in backend
8. `@/` path alias for all frontend internal imports

## Patterns to Avoid

- Wildcard imports (`from module import *`) -- use explicit imports in new code
- Debug `print()` statements -- use logger
- Bare `except:` clauses -- catch specific exceptions
- Adding to legacy Vuex store at `webapps/main/src/store/` -- use Pinia instead
- Options API for new components -- use Composition API with `<script setup>`
- Direct axios calls in components -- go through store actions or composables

---

*Convention analysis: 2026-04-15*
