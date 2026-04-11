// @ts-check
import { defineConfig, devices } from '@playwright/test';

/**
 * Progress Platform E2E Test Configuration
 *
 * PREREQUISITES (manual setup required):
 * 1. Full stack running at http://localhost (docker-compose up)
 * 2. PLAYWRIGHT_USERNAME and PLAYWRIGHT_PASSWORD env vars set
 * 3. Playwright browsers installed: npm run install-browsers
 *
 * Run: npm test
 * Run single journey: npm run test:login
 */
export default defineConfig({
  testDir: '.',
  timeout: 60_000,
  retries: 0,
  workers: 1, // Sequential — journeys may share state in a running system
  reporter: 'list',
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost',
    headless: true,
    screenshot: 'only-on-failure',
    video: 'off',
    trace: 'off',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
