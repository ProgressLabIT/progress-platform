# Codebase Structure

> Directory layout, key file locations, and naming conventions.
> Updated: 2026-03-12

---

## Top-Level Layout

```
progress-platform/
├── backend/              # All backend services
│   ├── api/              # Main FastAPI application
│   ├── commons/          # Shared backend utilities/models
│   ├── lte/              # LTE-specific backend service
│   ├── mock/             # Mock services for development
│   ├── reports/          # Streamlit reports service
│   ├── scripts/          # Utility/migration scripts
│   └── workflow/         # Workflow engine (Prefect flows)
├── webapps/              # Frontend applications
│   ├── main/             # Primary MES web app (Vue3/Quasar)
│   └── warehouse/        # Warehouse operations app (Vue3/Quasar)
├── deploy/               # Infrastructure and deployment
│   ├── compose/          # Docker Compose files
│   ├── config/           # Service configuration files
│   ├── dashboards/       # Monitoring dashboards (ArangoDB)
│   ├── artifacts/        # Build artifacts
│   └── scripts/          # Deployment helper scripts
├── testing/              # All test suites (separate from source)
│   ├── cypress/          # E2E browser tests
│   ├── robot-test/       # Robot Framework integration tests
│   ├── features/         # BDD feature files
│   ├── test-data/        # Test fixtures and data
│   ├── test-fakerest-api/
│   └── test-reqres-api/
├── db/                   # Database definitions and migrations
│   ├── migrations/       # DB migration scripts
│   ├── scripts/          # DB utility scripts
│   ├── backup/           # DB backups (by date/tenant)
│   └── Data Architecture/ # Data model documentation
├── km/                   # Knowledge management docs
│   ├── architecture/     # Architecture docs
│   ├── auth/             # Auth documentation
│   ├── domains/          # Domain-specific docs
│   └── guides/           # How-to guides
├── cli/                  # CLI tools
├── files/                # Local file storage (MinIO data)
└── .planning/            # GSD planning documents
    └── codebase/         # Codebase map documents
```

---

## Backend API (`backend/api/`)

```
backend/api/
├── endpoints/            # Route handlers (one file per domain)
│   ├── admin.py
│   ├── auth.py
│   ├── events.py
│   ├── inventory.py
│   ├── production.py
│   └── ...
├── events/               # Event handlers (domain event processing)
├── managers/             # Business logic managers
├── models/               # Pydantic request/response models
├── middlewares/          # FastAPI middleware
├── commons/              # Shared API utilities
├── utils/                # Utility modules
│   ├── auth.py           # JWT auth utilities ⚠️ hardcoded secret
│   └── dhr.py            # DHR logic ⚠️ 1297 lines, debug prints
├── media/                # Media file handling
└── main.py               # FastAPI app entry point
```

Key naming conventions:
- Files: `snake_case.py`
- Endpoint files named after domain (e.g., `production.py`, `inventory.py`)
- Models use PascalCase classes

---

## Frontend Apps (`webapps/main/`, `webapps/warehouse/`)

Both apps share the same structure (Quasar/Vue3):

```
webapps/main/src/
├── pages/               # Route-level page components
├── components/          # Reusable UI components
├── views/               # View components (larger than components)
├── layouts/             # App layout wrappers
├── composables/         # Vue composition functions
│   └── event.js         # sendEvent() - event logging composable
├── store/               # Vuex store (legacy)
├── stores/              # Pinia stores (newer)
├── router/              # Vue Router configuration
├── boot/                # Quasar boot files (plugins, init)
├── lib/                 # Third-party lib wrappers
├── mixins/              # Vue mixins (legacy pattern)
├── utils/               # Frontend utility functions
├── types/               # TypeScript type definitions
├── i18n/                # Internationalization strings
├── assets/              # Static assets
└── css/                 # Global styles
```

Key naming conventions:
- Components: `PascalCase.vue`
- Composables: `use{Name}.js` or `{name}.js` in `composables/`
- Pages: `{Domain}Page.vue` or domain-named `.vue` files
- Stores: camelCase, e.g., `auth.js`

---

## Deployment (`deploy/`)

```
deploy/
├── compose/
│   ├── docker-compose.yml         # Base compose
│   ├── docker-compose.dev.yml     # Dev overrides
│   └── docker-compose.prod.yml    # Production overrides
├── config/                        # Per-service config files
│   ├── nginx/
│   ├── kafka/
│   └── arangodb/
├── dashboards/
│   └── ArangoDB/                  # ArangoDB monitoring views
└── scripts/                       # Deploy helper scripts
```

---

## Testing (`testing/`)

Tests are **not co-located** with source code — all in dedicated `testing/` directory.

```
testing/
├── cypress/e2e/
│   ├── 01 - login page/           # Login flow E2E tests
│   └── 02 - traceability/         # Traceability E2E tests
├── robot-test/
│   ├── tests/
│   │   ├── authentication/        # Auth integration tests
│   │   └── events/                # Event integration tests
│   └── resources/
│       ├── commons/
│       ├── keywords/              # Robot Framework keywords
│       └── utils/
├── features/                      # BDD .feature files
└── test-data/                     # Shared test fixtures
```

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/api/main.py` | FastAPI app entry point |
| `backend/commons/` | Shared models, executors, kafka utils |
| `webapps/main/src/boot/` | App initialization (axios, auth, plugins) |
| `webapps/main/src/router/index.js` | Route definitions |
| `deploy/compose/docker-compose.yml` | Service orchestration |
| `db/migrations/` | Database migration scripts |
| `km/architecture/` | Architecture decision docs |
