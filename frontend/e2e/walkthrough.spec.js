import { test, expect } from '@playwright/test';
import { switchPersona, resetDemoState } from './helpers.js';

test.describe('Full Role-Based Screen Walkthrough and Console Audit', () => {
  let consoleErrors = [];
  let consoleWarnings = [];
  let unhandledRejections = [];
  let failedRequests = [];

  test.beforeEach(async ({ page }) => {
    consoleErrors = [];
    consoleWarnings = [];
    unhandledRejections = [];
    failedRequests = [];

    page.on('console', (msg) => {
      const type = msg.type();
      const text = msg.text();
      // Filter out benign React dev warnings if any, or track strictly
      if (type === 'error') {
        consoleErrors.push(text);
      } else if (type === 'warning') {
        consoleWarnings.push(text);
      }
    });

    page.on('pageerror', (err) => {
      unhandledRejections.push(err.message || String(err));
    });

    page.on('response', (res) => {
      const status = res.status();
      const url = res.url();
      // Only track API requests from our app
      if (url.includes('/api/') && status >= 400) {
        failedRequests.push(`${res.request().method()} ${url} -> ${status}`);
      }
    });

    await resetDemoState(page);
  });

  test('Guest role screen walkthrough: all public screens have zero errors', async ({ page }) => {
    // 1. Switch to Guest View
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await switchPersona(page, 'Guest View');

    // 2. Visit Dashboard
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h1, h2').first()).toBeVisible();

    // 3. Visit Submit Grievance
    await page.goto('/submit');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('textarea')).toBeVisible();

    // 4. Visit Track Complaint
    await page.goto('/track');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('input[placeholder*="CMP-"]')).toBeVisible();

    // 5. Visit Demo Control
    await page.goto('/demo');
    await page.waitForLoadState('networkidle');

    // 6. Visit Login
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    expect(consoleErrors).toHaveLength(0);
    expect(unhandledRejections).toHaveLength(0);
    expect(failedRequests).toHaveLength(0);
  });

  test('Student role screen walkthrough: dashboard, submit, track, my-complaints, notifications', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await switchPersona(page, 'Student');

    // 1. Dashboard
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h1, h2').first()).toBeVisible();

    // 2. Submit Grievance
    await page.goto('/submit');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('textarea')).toBeVisible();

    // 3. Track
    await page.goto('/track');
    await page.waitForLoadState('networkidle');

    // 4. My Complaints
    await page.goto('/my-complaints');
    await page.waitForLoadState('networkidle');

    // 5. Notifications
    await page.goto('/notifications');
    await page.waitForLoadState('networkidle');

    expect(consoleErrors).toHaveLength(0);
    expect(unhandledRejections).toHaveLength(0);
    expect(failedRequests).toHaveLength(0);
  });

  test('Facility Handler role screen walkthrough: dashboard, incidents, deep link detail, suggestions', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await switchPersona(page, 'Facility Handler');

    // 1. Dashboard
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // 2. Incidents List
    await page.goto('/incidents');
    await page.waitForLoadState('networkidle');

    // 3. Incident Deep Link by Code (e.g. /incidents/INC-HIST-002)
    await page.goto('/incidents/INC-HIST-002');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('text=INC-HIST-002').first()).toBeVisible();

    // 4. Test Deep Link refresh
    await page.reload();
    await page.waitForLoadState('networkidle');
    await expect(page.locator('text=INC-HIST-002').first()).toBeVisible();

    // 5. AI Suggestions
    await page.goto('/suggestions');
    await page.waitForLoadState('networkidle');

    expect(consoleErrors).toHaveLength(0);
    expect(unhandledRejections).toHaveLength(0);
    expect(failedRequests).toHaveLength(0);
  });

  test('Chief Admin role screen walkthrough: full control access across all screens', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await switchPersona(page, 'Chief Admin');

    // 1. Dashboard with Recurring Issues Card
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('text=Recurring Campus Infrastructure Issues')).toBeVisible();

    // 2. AI Suggestions
    await page.goto('/suggestions');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('text=Incident Clustering Suggestions')).toBeVisible();

    // 3. Incidents List
    await page.goto('/incidents');
    await page.waitForLoadState('networkidle');

    // 4. Incident Detail by Code
    await page.goto('/incidents/INC-HIST-001');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('text=INC-HIST-001').first()).toBeVisible();

    // 5. Demo Control
    await page.goto('/demo');
    await page.waitForLoadState('networkidle');

    expect(consoleErrors).toHaveLength(0);
    expect(unhandledRejections).toHaveLength(0);
    expect(failedRequests).toHaveLength(0);
  });
});
