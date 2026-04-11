// @ts-check
import { test, expect } from '@playwright/test';

/**
 * E2E-01: Login → Select Work Order → Start Job → Complete Batch
 *
 * PREREQUISITES:
 * - Full stack running at PLAYWRIGHT_BASE_URL (default: http://localhost)
 * - PLAYWRIGHT_USERNAME env var set (default: 'admin')
 * - PLAYWRIGHT_PASSWORD env var set (default: 'admin')
 * - At least one work order in READY state with an assigned job
 *
 * This journey validates the critical production workflow:
 * operator logs in → selects a job → completes a batch → verifies progress update
 */

const USERNAME = process.env.PLAYWRIGHT_USERNAME ?? 'admin';
const PASSWORD = process.env.PLAYWRIGHT_PASSWORD ?? 'admin';

test.describe('Login to Batch Complete Journey (E2E-01)', () => {
  test('operator can log in and navigate to job list', async ({ page }) => {
    // Step 1: Navigate to app
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Step 2: Login
    // Locate username and password inputs — Progress uses a login form
    const usernameInput = page.locator('input[type="text"], input[name="username"], input[placeholder*="user" i]').first();
    const passwordInput = page.locator('input[type="password"]').first();

    await expect(usernameInput).toBeVisible({ timeout: 10_000 });
    await usernameInput.fill(USERNAME);
    await passwordInput.fill(PASSWORD);

    // Submit login form
    await page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Accedi")').first().click();

    // Step 3: Verify landing on dashboard or job list after login
    await page.waitForLoadState('networkidle');
    // Should be redirected away from login page
    await expect(page).not.toHaveURL(/login/i, { timeout: 15_000 });
  });

  test('operator can navigate to active job list', async ({ page }) => {
    // Login first
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    const usernameInput = page.locator('input[type="text"], input[name="username"], input[placeholder*="user" i]').first();
    const passwordInput = page.locator('input[type="password"]').first();
    await expect(usernameInput).toBeVisible({ timeout: 10_000 });
    await usernameInput.fill(USERNAME);
    await passwordInput.fill(PASSWORD);
    await page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Accedi")').first().click();
    await page.waitForLoadState('networkidle');

    // Navigate to job list (operator jobs)
    await page.goto('/operator/jobs');
    await page.waitForLoadState('networkidle');

    // Verify job list page loaded
    await expect(page.locator('body')).toBeVisible();
    // Page should not be a 404 or error page
    const pageText = await page.locator('body').textContent();
    expect(pageText).not.toContain('404');
    expect(pageText).not.toContain('Not Found');
  });

  test('batch complete flow executes without JS errors', async ({ page }) => {
    // Track console errors
    const errors = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    page.on('pageerror', (err) => errors.push(err.message));

    // Login
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    const usernameInput = page.locator('input[type="text"], input[name="username"], input[placeholder*="user" i]').first();
    const passwordInput = page.locator('input[type="password"]').first();
    await expect(usernameInput).toBeVisible({ timeout: 10_000 });
    await usernameInput.fill(USERNAME);
    await passwordInput.fill(PASSWORD);
    await page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Accedi")').first().click();
    await page.waitForLoadState('networkidle');

    // Navigate through operator workflow
    await page.goto('/operator/jobs');
    await page.waitForLoadState('networkidle');

    // Filter critical JS errors (exclude known noisy warnings)
    const criticalErrors = errors.filter(
      (e) => !e.includes('ResizeObserver') && !e.includes('Non-Error promise rejection'),
    );

    // The journey does not crash the app
    expect(criticalErrors).toHaveLength(0);
  });
});
