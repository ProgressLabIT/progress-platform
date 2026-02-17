# Testing Patterns

**Analysis Date:** 2026-02-13

## Test Framework

**Runner:**
- None configured for webapps (main and warehouse)
- Config: `package.json` script `"test": "echo \"No test specified\" && exit 0"`
- No pytest configuration found for backend

**Assertion Library:**
- Not applicable (no test framework configured)

**Run Commands:**
```bash
# Frontend testing (not implemented)
yarn test                              # Returns "No test specified"

# Backend testing (not configured)
# No test runner configured
```

## Test File Organization

**Location (When Tests Exist):**
- Backend: Ad-hoc test files at `utils/api_auth_manager_test.py` and `scripts/OAuth2_test.py`
- Frontend: No test files found in codebase
- Pattern: Co-located with source (test in same directory as code)

**Naming (Observed):**
- Backend: `*_test.py` suffix (e.g., `api_auth_manager_test.py`)
- Pattern would be: `test_*.py` or `*_test.py` (currently inconsistent)

**Structure:**
```
backend/
├── api/
│   ├── utils/
│   │   └── api_auth_manager_test.py     # Manual test file
└── scripts/
    └── OAuth2_test.py                    # Manual test file
```

## Test Structure

**Current Manual Testing Pattern:**
```python
# backend/api/utils/api_auth_manager_test.py
import httpx
from api_auth_manager import APIAuthManager

client = httpx.Client()
APIAuthManager.getInstance().setAPIToken('...')
response = client.get('http://localhost:8000/api/whoami',
                      headers=APIAuthManager.getInstance().getAuthHeader())
print(response.json())
client.close()
```

**Characteristics:**
- No test framework structure (no describe/test blocks)
- Direct imports and manual execution
- Used for verifying API authentication workflow
- Not integrated into CI/CD pipeline
- Would be run manually by developer

**Recommended Setup (for future implementation):**

For backend (Python) - would use pytest:
```python
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from api.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_authentication_flow(client):
    # Arrange
    token = "eyJ..."

    # Act
    response = client.get(
        "/api/whoami",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Assert
    assert response.status_code == 200
```

For frontend (JavaScript) - would use Vitest or Jest:
```javascript
import { describe, it, expect, vi } from 'vitest'
import { useTaskStore } from '@/stores/task'
import { setActivePinia, createPinia } from 'pinia'

describe('useTaskStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should fetch tasks', async () => {
    const store = useTaskStore()
    // Mock API call
    vi.mock('@/boot/axios')
    await store.fetchTasks()
    expect(store.tasks.length).toBeGreaterThan(0)
  })
})
```

## Mocking

**Framework:**
- Not configured in codebase
- Manual mocking could use: `unittest.mock` in Python or `vitest` mocks in JavaScript

**Patterns (If Implemented):**

Python backend example (hypothetical based on code structure):
```python
# Mock ArangoDB transaction
from unittest.mock import Mock, MagicMock

def test_batch_created_event():
    mock_tx = Mock()
    mock_collection = Mock()
    mock_tx.collection.return_value = mock_collection
    mock_collection.insert.return_value = {'new': {...}}

    event = BatchCreatedEvent(tx=mock_tx, info={...})
    event.apply()

    assert event.response is not None
```

JavaScript frontend example (hypothetical based on code structure):
```javascript
// Mock API calls
import { vi } from 'vitest'
import { api } from '@/boot/axios'

vi.mock('@/boot/axios', () => ({
  api: {
    get: vi.fn(() => Promise.resolve({ data: [...] })),
    post: vi.fn(() => Promise.resolve({ data: {...} }))
  }
}))
```

**What to Mock:**
- External service calls (API, Kafka, ArangoDB - via abstraction layer)
- Timer functions (setTimeout, setInterval)
- HTTP requests (use mocking library)
- Date/time functions if testing time-dependent logic

**What NOT to Mock:**
- Core business logic (event processing, validation)
- Framework functionality (Pinia stores, Vue composables)
- Database queries within event `apply()` methods (use transaction-based testing)
- Component rendering (use component testing instead)

## Fixtures and Factories

**Test Data (Not Currently Implemented):**

Would typically be organized as:
```python
# backend/tests/fixtures/models.py
import pytest

@pytest.fixture
def sample_batch_created_event():
    return {
        'job_key': 'Job/12345',
        'phase_key': 'Phase/1',
        'work_order_key': 'WorkOrder/100',
        'product_key': 'Product/ABC',
        'new_batch_serials': [],
        'timestamp': datetime.utcnow()
    }

@pytest.fixture
def mock_arangodb_transaction():
    tx = Mock()
    tx.collection.return_value = Mock()
    tx.commit_transaction = Mock()
    tx.abort_transaction = Mock()
    return tx
```

**Location (Recommended):**
- Backend: `backend/tests/fixtures/` for fixture definitions
- Frontend: `webapps/main/src/__tests__/fixtures/` for test data factories
- Or inline in test files for simple cases

## Coverage

**Requirements:**
- Not enforced (no coverage configuration found)
- No CI pipeline checks for code coverage

**View Coverage (Recommended):**
```bash
# Backend (if pytest installed)
pytest --cov=backend/api --cov-report=html

# Frontend (if vitest configured)
vitest run --coverage
```

## Test Types

**Unit Tests:**
- Scope: Individual functions, event handlers, store actions
- Approach (for backend): Test event `apply()` methods with mocked transactions
- Approach (for frontend): Test Pinia store actions and composable functions
- Example areas:
  - Event validation (Pydantic models)
  - Store getters and actions
  - Utility functions (date handling, formatting, etc.)

**Integration Tests:**
- Scope: Multi-step workflows combining events, API calls, database operations
- Approach: Use test database transactions; mock external services
- Example areas:
  - Work order creation with job generation
  - Task creation and assignment workflow
  - Issue lifecycle (create → update → close)
  - Event spawning (parent → child events)

**E2E Tests:**
- Framework: Not used
- Would test: Full user workflows from API request to database state change
- Would require: Docker environment with services running

**API Tests:**
- Current approach: Manual scripts (`api_auth_manager_test.py`)
- Could use: httpx, requests, or REST client
- Should test: Authorization, error handling, response format

## Common Patterns

**Async Testing (Python FastAPI):**
```python
# Using TestClient (synchronous wrapper around async app)
from fastapi.testclient import TestClient
from api.main import app

def test_create_work_order():
    client = TestClient(app)
    response = client.post(
        "/work-order",
        json={
            "wo_code": "WO-001",
            "product_code": "PROD-A",
            "quantity": 100
        },
        headers={"Authorization": "Bearer token"}
    )
    assert response.status_code == 201
    assert response.json()["status_code"] == 201
```

**Async Testing (JavaScript Frontend):**
```javascript
import { describe, it, expect, vi } from 'vitest'
import { useTaskStore } from '@/stores/task'

describe('useTaskStore async', () => {
  it('should handle fetchTasks with error', async () => {
    const store = useTaskStore()

    // Mock failed API call
    vi.mock('@/boot/axios', () => ({
      api: {
        get: vi.fn(() =>
          Promise.reject(new Error('Network error'))
        )
      }
    }))

    await expect(store.fetchTasks()).rejects.toThrow()
  })
})
```

**Error Testing (Python):**
```python
def test_batch_created_event_validation():
    """Test that batch creation validates input"""
    info = BatchCreatedEvent.InfoModel(
        job_key='',  # Invalid: empty
        phase_key='Phase/1',
        work_order_key='WorkOrder/1',
        product_key='Product/1',
        new_batch_serials=[]
    )

    with pytest.raises(ValueError):
        event = BatchCreatedEvent(info=info, tx=mock_tx)
        event.apply()
```

**Error Testing (JavaScript):**
```javascript
describe('useTaskStore error handling', () => {
  it('should handle create task error gracefully', async () => {
    const store = useTaskStore()

    vi.mock('@/boot/axios', () => ({
      api: {
        post: vi.fn(() =>
          Promise.reject({ response: { status: 400 } })
        )
      }
    }))

    await expect(
      store.createTask({ title: 'Test' })
    ).rejects.toBeDefined()
  })
})
```

**Transaction Testing (Python Backend):**
```python
def test_event_with_transaction():
    """Test event within ArangoDB transaction"""
    tx = db.begin_transaction(write=['Batch', 'Job', 'Event'])

    event = BatchCreatedEvent(
        tx=tx,
        info={'job_key': '...', ...}
    )

    event.apply()

    # Check state within transaction
    batch = tx.collection('Batch').get(event.info.new_batch_key)
    assert batch is not None

    tx.commit_transaction()
```

## Test Data Strategy

**Current State:**
- No organized test data
- Manual test files create data ad-hoc

**Recommended:**
- Fixtures for common entities (Work Orders, Jobs, Products)
- Factory functions for generating test data (factory_boy or custom factories)
- Seed data for integration tests
- Isolated databases per test or transaction rollback

**Example Test Data Structure:**
```python
# backend/tests/factories.py
class WorkOrderFactory:
    @staticmethod
    def create(wo_code='WO-TEST-001', **kwargs):
        return {
            'wo_code': wo_code,
            'product_key': kwargs.get('product_key', 'Product/1'),
            'quantity': kwargs.get('quantity', 100),
            'phase_sequence': kwargs.get('phase_sequence', ['default']),
            **kwargs
        }

class BatchFactory:
    @staticmethod
    def create(job_key='Job/1', **kwargs):
        return {
            'job_key': job_key,
            'qt_total': kwargs.get('qt_total', 50),
            'active': kwargs.get('active', True),
            **kwargs
        }
```

## CI/CD Integration

**Current:**
- No test execution in `.gitlab-ci.yml`
- Pipeline only builds Docker images on version tags

**Recommended (for future):**
```yaml
# In .gitlab-ci.yml
test:backend:
  image: python:3.11
  script:
    - cd backend
    - pip install -r requirements-dev.txt
    - pytest --cov=api tests/
  coverage: '/TOTAL.*?(\d+%)/'

test:frontend:
  image: node:20
  script:
    - cd webapps/main
    - yarn install
    - yarn test --coverage
```

---

*Testing analysis: 2026-02-13*
