import { expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const SCREENSHOT_DIR = path.resolve('e2e/screenshots');

export function ensureScreenshotDir() {
  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }
}

/**
 * Captures responsive screenshots at desktop (1280x800) and mobile (393x851) resolutions.
 */
export async function captureResponsiveScreenshots(page, baseName) {
  ensureScreenshotDir();

  // Desktop (1280x800)
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.waitForTimeout(300);
  const desktopPath = path.join(SCREENSHOT_DIR, `${baseName}-desktop.png`);
  await page.screenshot({ path: desktopPath, fullPage: false });

  // Mobile (393x851 - Pixel 5 equivalent)
  await page.setViewportSize({ width: 393, height: 851 });
  await page.waitForTimeout(300);
  const mobilePath = path.join(SCREENSHOT_DIR, `${baseName}-mobile.png`);
  await page.screenshot({ path: mobilePath, fullPage: false });

  // Restore Desktop Viewport
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.waitForTimeout(200);
}

/**
 * Switches demo persona using the top interactive DemoBar or Login page.
 */
export async function switchPersona(page, personaLabel) {
  // Label can be: 'Chief Admin' | 'Facility Handler' | 'Student' | 'Guest View'
  if (personaLabel === 'Guest View') {
    const guestBtn = page.locator(`.bg-slate-900 button:has-text("Guest View")`).first();
    if (await guestBtn.isVisible()) {
      await guestBtn.click();
      await page.waitForTimeout(400);
    }
    return;
  }

  const demoBarBtn = page.locator(`.bg-slate-900 button:has-text("${personaLabel}")`).first();
  if (await demoBarBtn.isVisible()) {
    const loginPromise = page.waitForResponse(
      (res) => res.url().includes('/api/auth/login') && res.status() === 200,
      { timeout: 10000 }
    ).catch(() => null);
    await demoBarBtn.click();
    await loginPromise;
    await page.waitForTimeout(400);
    return;
  }

  // Fallback to /login page
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  const quickBtn = page.locator(`button:has-text("${personaLabel}")`).first();
  await expect(quickBtn).toBeVisible({ timeout: 5000 });
  const loginPromise = page.waitForResponse(
    (res) => res.url().includes('/api/auth/login') && res.status() === 200,
    { timeout: 10000 }
  ).catch(() => null);
  await quickBtn.click();
  await loginPromise;
  await page.waitForTimeout(400);
}

/**
 * Resets the demo story and virtual clock back to benchmark state.
 */
export async function resetDemoState(page) {
  // Reset via direct API call for complete determinism
  await page.request.post('http://127.0.0.1:8000/api/demo/reset');
  await page.waitForTimeout(500);
}
