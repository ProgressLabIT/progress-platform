# Testing

> Test frameworks, structure, patterns, and coverage.
> Updated: 2026-03-12

---

## Test Frameworks

| Framework | Layer | Location |
|-----------|-------|----------|
| **Mocha + Supertest + Chai** | API integration tests | `testing/` |
| **Cypress** | E2E browser tests | `testing/cypress/` |
| **Robot Framework** | BDD integration tests | `testing/robot-test/` |
| **Faker.js** | Test data generation | Used in Mocha/Cypress tests |

**Frontend unit tests:** No active unit test framework. `test` script exits 0 (no-op).

---

## Test Structure

Tests are **not co-located** with source code. All tests live in `testing/`:

```
testing/
├── cypress/
│   ├── e2e/
│   │   ├── 01 - login page/        # Login flow tests
│   │   └── 02 - traceability/      # Traceability feature tests
│   ├── fixtures/                   # Test data fixtures
│   └── support/                    # Cypress commands and helpers
├── robot-test/
│   ├── tests/
│   │   ├── authentication/         # Auth flow tests
│   │   └── events/                 # Event processing tests
│   └── resources/
│       ├── commons/                # Shared Robot resources
│       ├── keywords/               # Custom Robot keywords
│       └── utils/                  # Robot utility helpers
├── features/                       # BDD .feature files
├── test-data/                      # Shared test fixtures
├── test-fakerest-api/              # Fake REST API for testing
└── test-reqres-api/                # Reqres API test examples
```

---

## API Integration Tests (Mocha)

- **Framework:** Mocha with Chai assertions and Supertest for HTTP
- **Data:** Faker.js for generating realistic test data
- **State passing:** Auth tokens and state extracted from responses and passed between tests
- **Pattern:** Sequential tests that build on prior state (not fully isolated)

```javascript
// Example pattern
const response = await request(app)
  .post('/api/endpoint')
  .send({ data: faker.lorem.word() })
  .expect(200)

// Extract token/id for next test
const { id } = response.body
```

---

## E2E Tests (Cypress)

- **Location:** `testing/cypress/e2e/`
- **Organization:** Numbered folders by feature (`01 - login page`, `02 - traceability`)
- **Fixtures:** Static test data in `testing/cypress/fixtures/`
- **Custom commands:** Defined in `testing/cypress/support/`

---

## Integration Tests (Robot Framework)

- **BDD-style** tests with `.robot` files
- Python resources for API interactions
- **Keywords** in `testing/robot-test/resources/keywords/`
- Tests cover: authentication flows, event processing

---

## Coverage Gaps

- **No frontend unit tests** — Vue components untested at unit level
- **No utility function unit tests** — `backend/api/utils/` has no unit test coverage
- **No event handler isolation tests** — event handlers not tested in isolation
- **No load/concurrency tests** — concurrent scenarios not covered
- **No job queue race condition tests**

---

## Running Tests

```bash
# Cypress E2E (from testing/ directory)
npx cypress run

# Robot Framework
robot testing/robot-test/tests/

# Mocha API tests
npm test  # (from testing/ directory)
```

---

## Test Data

- **Faker.js**: Used for generating dynamic test data in JS tests
- **Fixtures**: Static data in `testing/cypress/fixtures/` and `testing/test-data/`
- **State**: Tests pass state (tokens, IDs) through response extraction — tests can be order-dependent
