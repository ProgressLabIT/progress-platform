# Codebase Concerns

> Technical debt, known issues, and areas of concern.
> Updated: 2026-03-12

---

## Critical Security Issues

### Hardcoded JWT Secret
- **File:** `backend/api/utils/auth.py:37`
- **Issue:** JWT secret hardcoded in source code
- **Impact:** Full authentication bypass if source is leaked
- **Fix:** Move to environment variable, rotate in production

### Unvalidated File Paths
- **File:** `backend/api/utils/dhr.py`
- **Issue:** No input validation on file paths
- **Impact:** Potential path traversal vulnerability
- **Fix:** Sanitize and validate all path inputs

### Secret Management
- **Issue:** Inconsistent secret management between dev and production environments
- **Fix:** Standardize on environment variables with documented required vars

---

## Technical Debt

### Oversized Files (Complexity Risk)
| File | Lines | Concern |
|------|-------|---------|
| `backend/api/utils/dhr.py` | 1297 | Mixed concerns, needs splitting |
| `backend/api/routes/production.py` | 862 | Too large, mixed concerns |
| Data import logic file | 636 | Tight coupling, complex logic |

### Debug Code Left in Production
- **File:** `backend/api/utils/dhr.py`
- **Issue:** 30+ debug `print()` statements
- **Impact:** Performance degradation + log noise
- **Fix:** Replace with proper logger calls, remove debug prints

### Silent Error Suppression
- **Pattern:** Bare `except:` clauses throughout endpoint files
- **Impact:** Errors silently swallowed, debugging becomes very difficult
- **Fix:** Catch specific exception types, log errors properly

### Wildcard Imports
- **Pattern:** `from module import *` across ~10 endpoint files
- **Impact:** Hides undefined references, namespace pollution
- **Fix:** Replace with explicit imports

---

## Known Bugs

### Undefined Variable in Admin Endpoint
- **File:** `backend/api/endpoints/admin.py:98`
- **Issue:** Transaction abort references undefined variable
- **Impact:** Runtime error in certain admin operations
- **Fix:** Identify and define the missing variable

### Unvalidated Job Updates
- **Location:** Work order rebalancing logic
- **Issue:** Job updates processed without validating constraints
- **Impact:** Potential data corruption on rebalancing
- **Fix:** Add pre-validation before applying job updates

---

## Performance Bottlenecks

### Synchronous PDF Generation
- **Location:** Request handler (WeasyPrint)
- **Issue:** PDF generation blocks the request thread
- **Impact:** Long response times, potential timeouts under load
- **Fix:** Offload to background task/queue

### Unoptimized AQL Queries
- **Location:** Event handlers
- **Issue:** No index strategy documented or enforced
- **Impact:** Slow queries at scale
- **Fix:** Profile queries, add ArangoDB indexes

### In-Memory PDF Attachment Processing
- **Issue:** All PDF attachments processed in memory
- **Impact:** Memory pressure with large/many attachments
- **Fix:** Stream processing or chunked handling

---

## Fragile Areas

### Event Sourcing Idempotency
- **Issue:** Idempotency verification gaps in event handlers
- **Impact:** Duplicate event processing can cause data inconsistency
- **Risk:** HIGH — silent data corruption possible

### Data Import Logic
- **File:** ~636-line import file
- **Issue:** Tightly coupled, complex import logic
- **Impact:** Hard to test, easy to break with changes
- **Fix:** Decompose into smaller, testable units

### Job Queue Management
- **Issue:** Job queue state split across multiple collections
- **Impact:** Race condition risks with concurrent queue operations
- **Fix:** Implement proper locking or atomic operations

### Work Order Quantity Rebalancing
- **Issue:** Quantity rebalancing logic with unvalidated constraints
- **Impact:** Invalid states possible if constraints violated
- **Fix:** Add constraint validation before rebalancing

---

## Test Coverage Gaps

- No unit tests for utility functions: inventory, production, serial modules
- Limited isolation testing for event handlers
- No load/concurrency tests for simultaneous operations
- No tests for the job queue race condition scenarios

---

## Areas to Watch

- `backend/api/utils/dhr.py` — high complexity, debug code, security concerns
- `backend/api/endpoints/admin.py` — known bug, needs attention
- Event sourcing layer — idempotency gaps are high-risk
- PDF generation pipeline — blocking + memory issues
