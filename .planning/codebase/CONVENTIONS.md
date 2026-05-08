# Coding Conventions

**Analysis Date:** 2026-05-08

## Naming Patterns

**Files:**
- Backend Python: `snake_case.py` -- one file per domain (`production.py`, `inventory.py`, `counting.py`)
- Backend models: `snake_case.py` matching endpoint domain (`backend/api/models/production.py`)
- Frontend Vue components: `PascalCase.vue` (`PrintTemplateCard.vue`, `BaseAutocompleteProduct.vue`)
- Frontend composables: mixed -- `use{Name}.js` for newer (`useSSE.js`, `usePrefectAPI.js`) and plain `camelCase.js` for older (`event.js`, `drawer.js`, `warehouse.js`)
- Pinia stores: `camelCase.js` (`config.js`, `countSession.js`, `task.js`)
- Vuex store modules: `camelCase.js` (`product.js`, `session.js`, `traceability.js`)
- Test files: `test_*.py` for pytest; `*.component.test.js` for Vitest

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
- Frontend: Prettier 3.1.1 with `singleQuote: true` -- config at `webapps/main/.prettierrc.json`
  ```json
  {
    "singleQuote": true
  }
  ```
- Backend: PEP 8 (no formatter config detected -- likely manual or editor-based)

**Linting:**
- ESLint with `plugin:vue/vue3-recommended` + `plugin:import/recommended` + `prettier`
- Config at `webapps/main/.eslintrc.js` (119 lines)
- Key enforced rules:
  - `vue/eqeqeq: 'error'` -- strict equality in templates
  - `curly: 'error'` -- always use braces
  - `no-unused-vars: ['error', { argsIgnorePattern: '^_' }]` -- prefix unused args with `_`
  - `import/order: ['warn', {alphabetize: {order: 'asc'}, groups: [builtin, external, internal, parent, sibling, index]}]` -- enforces import grouping and alphabetization
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

**Pinia stores (modern -- use for new state):**
- Location: `webapps/main/src/stores/`
- Stores: `config.js`, `countSession.js`, `task.js`, `taskType.js`, `rightDrawer.js`, `userHub.js`
- Pattern: `defineStore(storeName, { state, getters, actions })` with options syntax
- Example from `webapps/main/src/stores/task.js`:
  ```javascript
  export const useTaskStore = defineStore('task', {
    state: () => ({
      tasks: [],
      activeTaskKey: null,
      loading: false,
    }),

    getters: {
      getTaskByKey: (state) => (key) => {
        return state.tasks.find((task) => task._key === key)
      },
    },

    actions: {
      async fetchTasks(searchParams = {}) {
        this.loading = true
        try {
          const { data } = await api.get('/task', { params: searchParams })
          this.tasks = data
          return data
        } finally {
          this.loading = false
        }
      },
    },
  })
  ```

**Vuex store (legacy -- avoid adding to this):**
- Location: `webapps/main/src/store/`
- 14+ modules: `product.js`, `session.js`, `traceability.js`, `warehouse.js`, etc.
- Root store at `webapps/main/src/store/index.js` -- imports all modules
- Still used for session management, product state, and many domain areas
- Mutations use `UPPER_SNAKE_CASE` (`TOGGLE_SESSION_LOCK`, `CLOSE_SESSION`)
- **DO NOT ADD new state to Vuex.** Use Pinia instead.

## API Call Patterns

**Frontend -> Backend:**
- All HTTP via `api` axios instance from `webapps/main/src/boot/axios.js`
- Auth: JWT token injected via axios request interceptor from Vuex getter `getToken`
- 401 responses trigger automatic logout (except `whoami` and `session` endpoints)
- Event dispatching: use `sendEvent()` composable from `webapps/main/src/composables/event.js` (3.1KB)
- SSE for real-time updates: use `useSSE()` composable from `webapps/main/src/composables/useSSE.js`

**sendEvent() Composable Pattern:**
- Signature: `async sendEvent({ event_type, event_data })`
- Automatically attaches: user context from Vuex store, task context from Pinia task store (if task active), timestamp
- Example usage from `webapps/main/src/stores/task.js`:
  ```javascript
  const response = await sendEvent({
    event_type: 'TASK_CREATED',
    event_data: {
      task_type_key: taskData.type,
      title: taskData.title,
      description: taskData.description,
    }
  })
  ```

**Backend Endpoint Pattern:**
- One `router = APIRouter()` per domain file in `backend/api/endpoints/`
- Auth via `dependencies=[Depends(auth.verify_token)]` on each route
- Response model: `APIResponse` wrapper from `utils.api`
- Transaction management: manual `db.begin_transaction()` / `tx.abort_transaction()` in endpoint body
- Error pattern: try/except with `traceback.format_exc()` in HTTPException detail

## i18n (Internationalization)

**Framework:** Vue I18n 9.0.0

**Discipline:** Every user-facing string must have i18n entries.

**Pattern:**
- Strings stored in `webapps/main/src/i18n/en.js` (59.7KB) and `it.js` (64.7KB)
- Hierarchical keys for organization: `bom.add_line`, `errors.field_required`
- Access via `$t('key')` in templates or `t('key')` in scripts

**Structure from en.js:**
```javascript
export default {
  add: 'add',
  batch: 'batch',
  bom: {
    add_line: 'add line',
    delete_selected: 'delete selected',
    alerts: {
      line_exists: 'Item already used in this phase',
      quantity_negative: 'Item quantity must be positive',
    },
  },
  errors: {
    field_required: 'Field is required',
    status_update_err: 'Error updating status',
  },
}
```

**Usage in templates:**
```vue
<template>
  <q-input
    :label="$capitalize($t('title'))"
    :rules="[val => !!val || $t('errors.field_required')]"
  />
</template>
```

**Usage in script:**
```javascript
Notify.create({
  message: t('task_complete_success'),
  color: 'theme-green',
})
```

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
- Bare `except:` clauses found across endpoint files (e.g., `production.py:64`, `auth.py:171,213,276`, `admin.py:90,132,243`)
- Common anti-pattern: catch-all with `traceback.format_exc()` returned in HTTP 500
- Silent error swallowing: exceptions caught and ignored without logging
- Example from `backend/api/endpoints/production.py`:
  ```python
  try:
      # ... business logic
  except:
      tx.abort_transaction()
      raise HTTPException(status_code=500, detail=traceback.format_exc())
  ```

**Backend -- Preferred pattern for new code:**
1. Catch specific exceptions (not bare `except:`)
2. Log the error with context using `logging` module (see Logging section below)
3. Raise HTTPException with appropriate status code and detail
4. Never swallow exceptions silently

**Example of preferred pattern:**
```python
import logging
from fastapi import HTTPException
from utils.exceptions import JobIsStartedError

logger = logging.getLogger(__name__)

try:
    # Do work
    result = db.collection('Job').find({"_key": job_key}).next()
except StopIteration:
    logger.warning(f"Job not found: {job_key}")
    raise HTTPException(status_code=404, detail="Job not found")
except JobIsStartedError as e:
    logger.warning(f"Job already started: {job_key}")
    raise HTTPException(status_code=409, detail="Job is already started")
except Exception as e:
    logger.error(f"Unexpected error fetching job: {str(e)}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")
```

**Frontend:**
- Composable-level error handling with Quasar `Notify.create()` for user-facing errors
- Pattern from `sendEvent()`: catch error, show notification, re-throw

## Logging

**Backend:**
- Use Python `logging` module: `logger = logging.getLogger(__name__)`
- Logger initialized at module level
- Use logger methods: `logger.debug()`, `logger.info()`, `logger.warning()`, `logger.error()`
- Never use `print()` for debug output

**Current legacy issues (do NOT replicate):**
- `backend/api/endpoints/process.py:246`: `print(f'WARNING: ...')`
- `backend/api/endpoints/product.py:47`: `print(params.model_dump())`
- `backend/api/endpoints/traceability.py:87,172,185`: bare `print(e)`
- `backend/api/utils/auth.py:257–283`: multiple `print()` statements in token verification

**Do NOT add more print statements.** Convert existing ones to logger calls when touching those files.

**Frontend:**
- `console.error()` for caught exceptions (e.g., SSE listener errors in `useSSE.js`)
- `console.warn()` for configuration fallbacks (e.g., missing `API_CONFIG` in `axios.js`)
- No structured logging framework

## Comments & Documentation

**Backend:**
- Section separators common: `# ===============================================`
- Numbered comments for workflow steps: `# 0. Handle Work Order Code`, `# 1. Fetch product data`
- TODO comments present but sparse
- Docstrings: present on event classes and utility functions, absent on most endpoints

**Frontend:**
- JSDoc on composables (e.g., `useSSE()` in `webapps/main/src/composables/useSSE.js` has `@param` and `@returns`)
- Inline comments in templates are rare
- ESLint TODO comments in `.eslintrc.js` for future rule enablement

**Test Docstrings (pytest):**
- BDD-style docstrings describing the scenario
- Pattern: "Given X, when Y, then Z"
- Example from `testing/pytest/tests/collaboration/test_issues.py`:
  ```python
  async def test_01_create_critical_issue(self, client, auth_headers):
      """Given a product context,
      when an ISSUE_CREATED event is sent with critical=True,
      then the issue is persisted with critical flag and returns issue_key.
      migrated from: collaborations.robot 'Send critical product issue created event'.
      """
  ```

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
2. Pinia with options syntax (`defineStore(name, { state, getters, actions })`) for new stores
3. `sendEvent()` composable for event dispatching from frontend
4. `useSSE()` for real-time data subscriptions
5. Pydantic models for all backend data validation
6. Specific exception types from `utils/exceptions.py`
7. `logging` module (not `print()`) in backend
8. `@/` path alias for all frontend internal imports
9. i18n entries (`webapps/main/src/i18n/`) for every user-facing string
10. Docstrings in test functions describing the scenario in BDD-style

## Patterns to Avoid

- Wildcard imports (`from module import *`) -- use explicit imports in new code
- Debug `print()` statements -- use logger
- Bare `except:` clauses -- catch specific exceptions
- Adding to legacy Vuex store at `webapps/main/src/store/` -- use Pinia instead
- Options API for new components -- use Composition API with `<script setup>`
- Direct axios calls in components -- go through store actions or composables
- Hardcoded user-facing strings in templates -- always use i18n keys
- Silent error handling (catching exceptions without logging)

---

*Convention analysis: 2026-05-08*
