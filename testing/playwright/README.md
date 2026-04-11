# Playwright E2E Tests — Progress Platform

Manual-run E2E tests for the 3 critical user journeys. Requires full backend+frontend stack at localhost.

## Prerequisites

1. Full stack running (docker-compose up)
2. Playwright browsers installed:
   ```bash
   npm run install-browsers
   ```
3. Environment variables:
   ```bash
   export PLAYWRIGHT_USERNAME=admin
   export PLAYWRIGHT_PASSWORD=admin
   export PLAYWRIGHT_BASE_URL=http://localhost  # optional, default
   ```

## Run

```bash
# All journeys
npm test

# Individual journey
npm run test:login       # E2E-01: Login → batch complete
npm run test:workorder   # E2E-02: Work order creation
npm run test:stock       # E2E-03: Stock receipt

# Headed mode (see browser)
npx playwright test --headed

# Debug mode
npx playwright test --debug
```

## Journeys

| File | Requirement | Journey |
|------|-------------|---------|
| `login_to_batch_complete.spec.js` | E2E-01 | Login → job list → batch complete |
| `work_order_creation.spec.js` | E2E-02 | Work orders → create → verify |
| `stock_receipt.spec.js` | E2E-03 | Inventory → stock receipt movement |

## Notes

- Tests are **not CI-automated** — they require a running stack (same pattern as Locust load tests)
- `workers: 1` — tests run sequentially to avoid state conflicts
- Screenshots saved to `test-results/` on failure
- Tests validate journey reachability and absence of JS errors, not pixel-perfect UI
