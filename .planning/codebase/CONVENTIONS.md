# Coding Conventions

**Analysis Date:** 2026-02-13

## Naming Patterns

**Files (Python Backend):**
- Snake case with underscores: `api_auth_manager.py`, `base_event.py`, `kafka_consumer.py`
- Event classes: `{domain}_{event}.py` (e.g., `batch_created.py`, `issue_updated.py`, `serial_booked.py`)
- Exception classes follow pattern: `{Action}Error` suffix (e.g., `SerialNotUpdatedError`, `SerialCodeAlreadyPresent`, `SerialNotCreatedError`)

**Files (JavaScript/Vue Frontend):**
- Composables use `use` prefix followed by camelCase: `useFormFields.js`, `usePrefectAPI.js`, `useCountRecordExport.js`
- Store files (Pinia): lowercase domain names: `task.js`, `product.js`, `job.js`
- Components: PascalCase: `JobCard.vue`, `TaskNew.vue`, `MessageThread.vue`, `BaseTooltipIcon.vue`
- Utility files: camelCase: `apiCall.js`, `dateUtils.js`, `xlsxDownload.js`, `loadScript.js`
- Routes: descriptive camelCase: `productionRoutes.js`, `adminRoutes.js`, `taskRoutes.js`

**Functions (Python):**
- Snake case: `create_job_record()`, `_update_job_progress()`, `verify_password()`, `get_user()`
- Private functions prefixed with underscore: `_generate_counter()`, `_get_job_data()`, `_update_job_progress()`
- Async functions (FastAPI): regular snake case with `async def`: `async def create_work_order()`, `async def get_issue_type()`

**Functions (JavaScript):**
- camelCase: `getFieldByType()`, `getTaskByKey()`, `getTasksByStatus()`, `fetchTasks()`
- Event handlers: `handle{Action}` or `on{Event}`: common Vue pattern
- Getters in Pinia: `get{Entity}` (e.g., `getTaskByKey`, `getActiveTask`, `getTasksByStatus`)

**Variables:**
- snake_case in Python: `wo_code`, `product_key`, `qt_planned`, `serial_key`, `batch_qt`
- camelCase in JavaScript: `activeTaskKey`, `ignoredEntities`, `isEntityIgnored`, `taskData`
- Boolean prefixes: `is`, `has` in both languages: `is_active`, `has_items`, `isLoading`, `hasError`

**Types & Classes (Python):**
- PascalCase: `WorkOrderNew`, `ProductDetails`, `Batch`, `FlexModel`, `ArangoDocument`, `ArangoEdge`
- Pydantic model suffix not required but pattern is domain-based: `IssueType`, `IssueTypeFull`, `IssueTypeUpdate`
- Event classes: PascalCase ending with `Event`: `BatchCreatedEvent`, `WIPBookedEvent`, `IssueUpdatedEvent`
- Base classes prefixed with `Base`: `BaseEvent`, `BaseProductionEvent`, `BaseSe-rial`, `BaseCollaboration`

**Types & Classes (JavaScript):**
- Store name pattern: `use{Domain}Store`: `useTaskStore`, `useCountSessionStore`
- No explicit TypeScript in code (using JSDoc when needed)

**Database/Constants:**
- Collection names: PascalCase for Document collections (`Event`, `Batch`, `WorkOrder`, `Job`, `Queue`, `Product`, `Phase`), snake_case for edge collections (`requires`, `is_in_position`, etc.)
- Field names in documents: snake_case: `wo_code`, `product_key`, `qt_planned`, `_key`, `_id`, `_rev`
- Enum values: UPPER_SNAKE_CASE: `EventType.BATCH_CREATED`, `WorkStatus.COMPLETED`
- API event types: UPPER_SNAKE_CASE: `TASK_CREATED`, `ISSUE_CREATED`, `BATCH_COMPLETED`

## Code Style

**Formatting:**
- ESLint: eslint-plugin-vue v9.19.2 with Vue 3 recommended rules
- Prettier: v3.1.1 configured with single quotes only (`.prettierrc.json`: `{"singleQuote": true}`)
- Python: No explicit formatter configuration found; follows PEP 8 conventions observed in code

**Linting (Frontend - JavaScript/Vue):**
- Tool: ESLint v8.57.0
- Config: `.eslintrc.js` at root of each webapp
- Extensions: eslint-plugin-vue, eslint-plugin-import
- Key Rules:
  - `vue/eqeqeq`: enforced (error) - strict equality checking
  - `curly`: enforced (error) - require curly braces for all control structures
  - `no-unused-vars`: enforced (error) with pattern `^_` for intentional unused (e.g., `_unusedParam`)
  - `no-debugger`: error in production, off in development
  - `vue/no-empty-component-block`: warning
  - `vue/padding-line-between-blocks`: warning
  - `import/order`: warning with alphabetical alphabetization - groups: [builtin, external, internal, parent, sibling, index, object, type]

**Linting (Backend - Python):**
- No explicit linter config file found
- Code follows PEP 8 style
- Uses type hints throughout (Python 3.11)
- Union types: `str | None` (PEP 604 style, not `Optional[str]` or `Union[str, None]`)

## Import Organization

**Order (Backend - Python):**
1. Standard library: `import os`, `import traceback`, `from datetime import`, `from typing import`
2. Third-party: `from fastapi import`, `from pydantic import`, `from arango import`
3. Relative application imports: `from utils import`, `from models import`, `from events import`

**Example from `endpoints/product.py`:**
```python
import os
import traceback

from fastapi import APIRouter, Form, File, HTTPException, UploadFile, Body, Query, Depends
from utils import auth
from fastapi.encoders import jsonable_encoder
from typing import Annotated

from utils.kpi import Queries as ProductStatQueries
from models.product import *
from models.process import PhaseData
from utils.api import APIResponse
from utils.db import db
from utils.dt import timestamp
from utils.file import FileHandler
from utils.product import *
from utils.process import Queries as ProcessQueries
```

**Order (Frontend - JavaScript):**
1. Vue/Framework: `import { defineStore } from 'pinia'`
2. External libraries: `import { Notify, Dialog } from 'quasar'`, `import axios from 'axios'`
3. Internal composables/utils: `import { useI18n } from 'vue-i18n'`, `import { computed } from 'vue'`
4. Application modules: `import { api } from '@/boot/axios.js'`, `import { sendEvent } from '@/composables/event.js'`

**Path Aliases:**
- Frontend: `@/` resolves to `src/` directory (Vue path alias configured in jsconfig.json)
- Backend: Relative imports without path prefixes; Python path includes backend root

## Error Handling

**Patterns (Python Backend):**
- HTTPException from FastAPI for API errors:
  ```python
  raise HTTPException(
    status_code=409,
    detail="An issue type with the same code already exists"
  )
  ```
- Custom exceptions defined in `utils/exceptions.py`: `HTTPError`, `SerialCodeAlreadyPresent`, `SerialNotUpdatedError`
- Try/except blocks wrap database operations and external service calls
- ValueError for validation failures within event logic:
  ```python
  raise ValueError("Quantity cannot be zero or negative")
  raise ValueError("You must provide serials to be linked to this new batch")
  ```
- Transaction abort on error:
  ```python
  try:
    # ... logic
  except Exception:
    tx.abort_transaction()
    raise HTTPException(...)
  ```
- traceback.format_exc() captured in error responses for debugging

**Patterns (JavaScript Frontend):**
- Try/catch blocks for async operations:
  ```javascript
  try {
    const { data } = await api.get('/task', { params: searchParams })
    // success handling
  } catch (error) {
    console.error('Error fetching tasks:', error)
    throw error
  } finally {
    this.loading = false
  }
  ```
- console.error() for logging: `console.error('Error fetching tasks:', error)`
- console.warn() for non-critical issues: `console.warn('API_CONFIG not found, using default configuration')`
- Quasar Notify for user-facing errors (from `quasar` imports)
- Dialog for confirmations and alerts

## Logging

**Framework:**
- Python: Uses `traceback.format_exc()` for exception details; console output via standard print (no logger import)
- JavaScript: Uses native `console` object

**Patterns:**
- Python: Errors logged with full traceback included in HTTPException detail
- JavaScript: `console.error('Context: <error>')` for exceptions in try/catch blocks
- No structured logging framework found; relies on console output and traceback strings

## Comments

**When to Comment:**
- Comments used selectively for complex business logic
- Section dividers using dashes: `# ----------` (seen in endpoints for grouping related routes)
- Commented-out code kept for reference in some cases (e.g., `# TODO:` comments)

**JSDoc/TSDoc:**
- Minimal JSDoc usage observed
- Example: `@see` reference in `src/composables/form.js`:
  ```javascript
  /**
   * @see {@link ../mixins/form.js}
   */
  export function useFormFields() {
  ```
- No formal TypeScript (JavaScript with JSDoc for type hints where needed)

**Python Docstrings:**
- Docstrings present in base classes (ABC classes describe abstract methods):
  ```python
  @classmethod
  @abstractmethod
  def get_event_type(cls) -> EventType:
    """
    Returns the event type. Must be implemented by the subclass.
    """
    pass
  ```
- Event classes document their purpose implicitly through naming and implementation

## Function Design

**Size:**
- Backend: Functions typically 10-50 lines; complex event handlers can be 80+ lines
- Frontend: Composable functions 30-70 lines; component methods variable length based on feature

**Parameters:**
- Python: Type hints required (Pydantic models preferred for complex data)
- Python event handlers: Require InfoModel inner class for event data validation
- JavaScript: No type enforcement; documented through usage patterns

**Return Values:**
- Python: Explicit returns; event `apply()` methods store responses in `self.response`
- JavaScript: Async functions return Promises; Pinia actions return data for composition
- Python: Functions that spawn events return list or single response from `self.response`

**Async Handling:**
- Python: FastAPI async def for route handlers; no explicit async/await in library calls (ArangoDB client is blocking)
- JavaScript: Explicit async/await for API calls; computed() for reactive data

## Module Design

**Exports:**
- Python: Event classes exported via __init__ imports; utils functions exported directly
- JavaScript:
  - Named exports preferred: `export function getFieldByType() {}`
  - Store exports: `export const useTaskStore = defineStore(...)`
  - No default exports in most modules

**Barrel Files:**
- Python: Minimal use; imports done from specific modules
- JavaScript: Router files act as barrel exports (e.g., `router/index.js` imports all route files)
- Frontend: Stores imported individually from `src/stores/` or `src/store/`

**Architecture Patterns:**
- Backend: Event-sourced domain events; each event class encapsulates business logic in `apply()` method
- Frontend: Pinia stores with actions for API calls; composables for reusable logic; Vue 3 Composition API patterns

---

*Convention analysis: 2026-02-13*
