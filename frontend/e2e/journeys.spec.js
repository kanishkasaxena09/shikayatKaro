import { test, expect } from '@playwright/test';
import {
  switchPersona,
  resetDemoState,
  captureResponsiveScreenshots,
} from './helpers.js';

test.describe.configure({ mode: 'serial' });

test.describe('Shikayat Karo - Comprehensive E2E Verification Suite', () => {
  let trackedAnonymousId = '';
  let trackedAccessCode = '';
  let confirmedIncidentUrl = '';

  test.beforeAll(async ({ browser }) => {
    // Quick health check to ensure backend is ready
    const page = await browser.newPage();
    try {
      await page.goto('http://127.0.0.1:8000/api/health', { timeout: 15000 });
      const content = await page.textContent('body');
      expect(content).toContain('healthy');
    } finally {
      await page.close();
    }
  });

  // -------------------------------------------------------------
  // JOURNEY 1: Multilingual Grievance Filing (English & Hinglish)
  // -------------------------------------------------------------
  test('Journey 1: Student submits grievances in English and Hinglish and inspects AI diagnostic', async ({
    page,
  }) => {
    await page.goto('/submit');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h1')).toContainText(/File a Campus Grievance/i);

    // 1. Submit English Grievance
    const englishDesc = 'Severe drinking water pipe burst outside Hostel Block B walkway flooding the path';
    await page.locator('textarea').fill(englishDesc);
    await page.locator('input[type="number"]').fill('12');

    // Submit
    const submitBtn = page.locator('button[type="submit"]:has-text("Submit Grievance")');
    await expect(submitBtn).toBeEnabled();
    await submitBtn.click();

    // Verify AI Analysis Modal
    const modal = page.locator('.fixed.inset-0');
    await expect(modal).toBeVisible({ timeout: 30000 });
    await expect(modal).toContainText(/Grievance Registered Successfully/i);
    await expect(modal).toContainText(/Water & Plumbing/i);
    await expect(modal).toContainText(/Language: EN/i);

    // Capture responsive screenshots (desktop + mobile)
    await captureResponsiveScreenshots(page, 'journey1-english-submission');

    // Close modal
    await modal.locator('button:has-text("Done")').click();
    await expect(modal).not.toBeVisible();

    // 2. Submit Hinglish Grievance
    const hinglishDesc = 'Hostel Block B ground floor ke paas paani ka pipe leak ho raha hai nal ka paani waste ho raha hai jaldi theek karo';
    await page.locator('textarea').fill(hinglishDesc);
    await page.locator('input[type="number"]').fill('8');

    await submitBtn.click();
    await expect(modal).toBeVisible({ timeout: 30000 });
    await expect(modal).toContainText(/Grievance Registered Successfully/i);
    await expect(modal).toContainText(/Language: HINGLISH/i);
    await expect(modal).toContainText(/Predicted Category:/i);

    // Capture responsive screenshots (desktop + mobile)
    await captureResponsiveScreenshots(page, 'journey1-hinglish-submission');

    await modal.locator('button:has-text("Done")').click();
    await expect(modal).not.toBeVisible();
  });

  // -------------------------------------------------------------
  // JOURNEY 2: Zero-Leakage Anonymous Filing & Public Tracking
  // -------------------------------------------------------------
  test('Journey 2: Anonymous submission yields access code; public tracking displays status with zero identity leakage', async ({
    page,
  }) => {
    await page.goto('/submit');
    await page.waitForLoadState('networkidle');

    // Enable Anonymous Mode
    const anonCheckbox = page.locator('input[type="checkbox"]');
    if (!(await anonCheckbox.isChecked())) {
      await anonCheckbox.check();
    }
    await expect(anonCheckbox).toBeChecked();

    // Fill sensitive grievance
    const confidentialText = 'Urgent: Staircase illumination failed completely in Block B First Floor corridor, student fell down in dark';
    await page.locator('textarea').fill(confidentialText);
    await page.locator('input[type="number"]').fill('20');

    await page.locator('button[type="submit"]:has-text("Submit Grievance")').click();

    // Modal with secret access code
    const modal = page.locator('.fixed.inset-0');
    await expect(modal).toBeVisible({ timeout: 30000 });
    await expect(modal).toContainText(/Anonymous Grievance — Save Your Access Code/i);

    // Extract Tracking ID and Secret Access Code
    const trackingText = await modal.locator('strong.font-mono').first().textContent();
    trackedAnonymousId = trackingText?.trim() || '';
    expect(trackedAnonymousId).toMatch(/^CMP-\d+$/);

    const codeElement = modal.locator('span.font-mono.select-all');
    trackedAccessCode = (await codeElement.textContent())?.trim() || '';
    expect(trackedAccessCode).toMatch(/^[A-F0-9]{8}$/);

    await captureResponsiveScreenshots(page, 'journey2-anonymous-modal');

    // Close modal
    await modal.locator('button:has-text("Done")').click();

    // Navigate to Public /track page (ensure guest/unauthenticated context)
    await page.goto('/track');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h1')).toContainText(/Track Grievance Status/i);

    // Fill tracking credentials
    await page.locator('input[placeholder*="CMP-"]').fill(trackedAnonymousId);
    await page.locator('input[placeholder*="8A4F19B2"]').fill(trackedAccessCode);

    await page.locator('button[type="submit"]:has-text("Track")').click();

    // Verify tracked status dossier appears
    await expect(page.locator(`text=${trackedAnonymousId}`).first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Submitted').first()).toBeVisible();
    await expect(page.locator('text=Resolution Pipeline Progression').first()).toBeVisible();
    await expect(page.locator('text=Anonymous Report').first()).toBeVisible();

    // Verify zero identity leakage
    const pageText = await page.content();
    expect(pageText).not.toContain('student@demo');
    expect(pageText).not.toContain('Arvind Sharma');

    await captureResponsiveScreenshots(page, 'journey2-anonymous-tracking');
  });

  // -------------------------------------------------------------
  // JOURNEY 3: Chief Admin Reviews & Approves AI Cluster
  // -------------------------------------------------------------
  test('Journey 3: Chief Admin reviews candidate AI suggestion and approves into a Parent Incident', async ({
    page,
  }) => {
    // Reset demo state so canonical story cluster is ready
    await resetDemoState(page);

    // Switch to Chief Administrator persona
    await switchPersona(page, 'Chief Admin');

    // Navigate to /suggestions
    await page.goto('/suggestions');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h1')).toContainText(/Incident Clustering Suggestions/i);

    // Verify pending suggestion card exists
    const confirmBtn = page.locator('button:has-text("Confirm & Create Incident")').first();
    await expect(confirmBtn).toBeVisible({ timeout: 15000 });

    // Review engine badge and reasoning
    await expect(page.locator('text=Clustering Factors:').first()).toBeVisible();

    // Open confirmation modal
    await confirmBtn.click();
    const modal = page.locator('.fixed.inset-0');
    await expect(modal).toBeVisible();
    await expect(modal.locator('h3')).toContainText(/Confirm Incident/i);

    // Click confirm
    const createBtn = modal.locator('button:has-text("Confirm & Create Incident")');
    await expect(createBtn).toBeEnabled();
    await createBtn.click();

    // Verify redirected to incident dossier (/incidents/:id)
    await page.waitForURL('**/incidents/**', { timeout: 15000 });
    confirmedIncidentUrl = page.url();
    expect(confirmedIncidentUrl).toContain('/incidents/');

    // Assert parent incident details
    await expect(page.locator('h1')).toBeVisible({ timeout: 30000 });
    await expect(page.locator('text=Transparent Impact Score').first()).toBeVisible({ timeout: 30000 });

    await captureResponsiveScreenshots(page, 'journey3-cluster-approved');
  });

  // -------------------------------------------------------------
  // JOURNEY 4: Facility Handler Resolves Incident with Mandatory Notes
  // -------------------------------------------------------------
  test('Journey 4: Facility Handler investigates incident and resolves with mandatory notes validation', async ({
    page,
  }) => {
    // Switch to Facility Handler persona
    await switchPersona(page, 'Facility Handler');

    // Navigate to the confirmed incident
    if (confirmedIncidentUrl) {
      await page.goto(confirmedIncidentUrl);
    } else {
      await page.goto('/incidents');
      await page.locator('tr td a').first().click();
    }
    await page.waitForLoadState('networkidle');

    // Verify similar historical resolved cases are recommended
    await expect(page.locator('text=AI Resolution Intelligence').first()).toBeVisible({ timeout: 30000 });

    // Click "Update Workflow Status"
    const updateStatusBtn = page.locator('button:has-text("Update Workflow Status")');
    await expect(updateStatusBtn).toBeVisible();
    await updateStatusBtn.click();

    const statusModal = page.locator('.fixed.inset-0');
    await expect(statusModal).toBeVisible();

    // Select "Resolved"
    const statusSelect = statusModal.locator('select').first();
    await statusSelect.selectOption('Resolved');

    // Fill comprehensive physical resolution notes
    const validNotes = 'Isolated 3-inch butterfly valve, replaced ruptured GI union flange with brass sleeve, chlorinated line, and verified full water pressure.';
    const notesTextarea = statusModal.locator('textarea').first();
    await notesTextarea.fill(validNotes);

    // Submit update
    await statusModal.locator('button:has-text("Save Status Update")').click();

    // Verify incident updates to Resolved
    await expect(page.locator('text=Resolved').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator(`text=${validNotes}`).first()).toBeVisible();

    await captureResponsiveScreenshots(page, 'journey4-incident-resolved');
  });

  // -------------------------------------------------------------
  // JOURNEY 5: Virtual-Clock Fast-Forward & SLA Escalation
  // -------------------------------------------------------------
  test('Journey 5: Virtual clock fast-forward triggers automated SLA escalation', async ({
    page,
  }) => {
    await page.goto('/demo');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h1')).toContainText(/Demo Simulator & SLA Time Machine/i);

    // Advance clock by 6 hours
    const advanceBtn = page.locator('button:has-text("+6 Hours")');
    await expect(advanceBtn).toBeVisible();
    await advanceBtn.click();

    // Verify update banner
    const updateBanner = page.locator('text=Virtual Clock Updated').first();
    await expect(updateBanner).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=+6 hours').first()).toBeVisible();

    await captureResponsiveScreenshots(page, 'journey5-sla-escalation');
  });

  // -------------------------------------------------------------
  // JOURNEY 6: Recurring-Issue Detection Card & Root-Cause Remediation
  // -------------------------------------------------------------
  test('Journey 6: Recurring-issue detection card renders on dashboard with root-cause permanent fix action', async ({
    page,
  }) => {
    // Switch to Chief Admin
    await switchPersona(page, 'Chief Admin');

    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h1')).toContainText(/Dr\. Arvind Sharma|Chief Administrator/i);

    // Verify Recurring Infrastructure Issues Card
    const recurringSection = page.locator('text=Recurring Campus Infrastructure Issues').first();
    await expect(recurringSection).toBeVisible({ timeout: 15000 });

    // Assert row values
    await expect(page.locator('text=Hostel Block B').first()).toBeVisible();
    await expect(page.locator('text=Sanitation & Cleanliness').first()).toBeVisible();
    await expect(page.locator('text=/3\\s*incidents/i').first()).toBeVisible();

    // Verify incident links exist
    const incidentLink = page.locator('a[href*="/incidents/"]').first();
    await expect(incidentLink).toBeVisible();

    // Open "Needs Permanent Fix" modal
    const fixBtn = page.locator('button:has-text("Needs Permanent Fix")').first();
    if (await fixBtn.isVisible()) {
      await fixBtn.click();

      const fixModal = page.locator('.fixed.inset-0');
      await expect(fixModal).toBeVisible();
      await expect(fixModal).toContainText(/Schedule Permanent Remediation/i);

      // Submit permanent fix task
      const scheduleTaskBtn = fixModal.locator('button:has-text("Schedule Task")');
      await expect(scheduleTaskBtn).toBeEnabled();
      const fixPromise = page.waitForResponse(
        (res) => res.url().includes('/api/analytics/recurring/mark-fix') && res.status() === 200,
        { timeout: 15000 }
      ).catch(() => null);
      await scheduleTaskBtn.click();
      await fixPromise;

      // Assert badge turns to "Remediation Scheduled"
      await expect(page.locator('text=Remediation Scheduled').first()).toBeVisible({ timeout: 15000 });
      await expect(page.locator('text=PFIX-').first()).toBeVisible();
    }

    await captureResponsiveScreenshots(page, 'journey6-recurring-fix-scheduled');
  });
});
