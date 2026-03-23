# Code Conventions

> Code style, naming patterns, and established patterns in this codebase.
> Updated: 2026-03-12

---

## Naming Conventions

### Backend (Python)
- Files: `snake_case.py`
- Functions/variables: `snake_case`
- Classes/models: `PascalCase` (Pydantic models)
- Constants: `UPPER_SNAKE_CASE`
- Endpoint files named after domain: `production.py`, `inventory.py`

### Frontend (Vue3/JS)
- Vue components: `PascalCase.vue` (e.g., `PrintTemplateCard.vue`)
- Composables: `use{Name}.js` or descriptive name in `composables/`
- Stores (Pinia): `camelCase` module names
- Pages: descriptive PascalCase (e.g., `ProductionPage.vue`)
- Utility files: `camelCase.js`

---

## Backend Patterns

### FastAPI Endpoints
- One file per domain in `backend/api/endpoints/`
- Routes registered via router, imported in `main.py`
- Pydantic models for request/response validation in `backend/api/models/`
- Auth via JWT middleware — see `backend/api/utils/auth.py`

### Event System
- Events processed in `backend/api/events/`
- Business logic in `backend/api/managers/`
- Separation: endpoints call managers, managers emit events

### Error Handling (Current — problematic)
- Bare `except:` clauses common throughout endpoint files (known issue)
- Errors often swallowed silently
- **Preferred pattern** (use this for new code):
  ```python
  try:
      result = some_operation()
  except SpecificError as e:
      logger.error(f"Operation failed: {e}")
      raise HTTPException(status_code=500, detail=str(e))
  ```

### Logging
- Use Python's `logging` module (not `print()`)
- `print()` debug statements exist in legacy code — do not add more

---

## Frontend Patterns

### Vue3 Composition API
- Prefer `<script setup>` with Composition API for new components
- Legacy components use Options API — do not refactor unless changing
- Composables extract reusable logic: `webapps/main/src/composables/`

### Event Logging
- Use the `sendEvent()` composable for user action tracking
- Located at `webapps/main/src/composables/event.js`

### State Management
- **Pinia stores** (newer): `webapps/main/src/stores/` — use for new state
- **Vuex store** (legacy): `webapps/main/src/store/` — avoid adding to this
- Prefer Pinia for any new state management

### API Calls
- Axios configured in boot files: `webapps/main/src/boot/`
- API calls made through store actions or composables, not directly in components

### Import Organization
- ESLint enforces import ordering (configured with `eslint-plugin-import`)
- External deps → internal modules → relative imports
- Use path aliases for internal imports (configured in Quasar)

---

## Code Style

### Backend
- PEP 8 formatting (Python standard)
- FastAPI dependency injection for shared concerns (auth, db)
- Pydantic for all data validation at boundaries

### Frontend
- Prettier for formatting (configured in `.prettierrc` or `package.json`)
- ESLint with `vue/vue3-recommended` ruleset
- No unused imports (enforced by ESLint)

---

## Patterns to Follow

1. **Thin endpoints** — keep route handlers thin, delegate to managers
2. **Pydantic models** — validate all external input with Pydantic
3. **Explicit exceptions** — catch specific exceptions, never bare `except:`
4. **Composables over mixins** — use composables for new shared frontend logic
5. **Pinia over Vuex** — use Pinia for new store modules
6. **Proper logging** — use Python logger, not print statements

---

## Patterns to Avoid

- Wildcard imports (`from module import *`) — use explicit imports
- Debug `print()` statements — use logger
- Bare `except:` clauses — catch specific exceptions
- Adding to legacy Vuex store — use Pinia instead
- Options API for new components — use Composition API
