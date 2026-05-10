import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright config for HelixNet / La Piazza E2E tests.
 *
 * Env model (decided 2026-05-10): 2-tier.
 *   - dev  = helix.local on this laptop
 *   - prod = lapiazza.app on Hetzner
 *   - staging = ephemeral (only spun up for big merges, opt-in via TEST_ENV=staging)
 *
 * Run:
 *   npm run test:e2e:dev       # against helix.local
 *   npm run test:e2e:prod      # against lapiazza.app  (READ-ONLY, smoke only)
 *   npm run test:e2e:staging   # against staging.lapiazza.app (when alive)
 */

const BASE_URLS = {
  dev: process.env.DEV_URL ?? 'https://helix.local',
  staging: process.env.STAGING_URL ?? 'https://staging.lapiazza.app',
  prod: process.env.PROD_URL ?? 'https://lapiazza.app',
};

export default defineConfig({
  testDir: '.',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
  ],

  use: {
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    // Self-signed certs on dev + Hetzner -- accept them
    ignoreHTTPSErrors: true,
    actionTimeout: 10_000,
    navigationTimeout: 20_000,
  },

  projects: [
    {
      name: 'dev',
      use: { ...devices['Desktop Chrome'], baseURL: BASE_URLS.dev },
    },
    {
      name: 'staging',
      use: { ...devices['Desktop Chrome'], baseURL: BASE_URLS.staging },
    },
    {
      name: 'prod',
      // Prod project ONLY runs tests tagged @smoke (read-only). Defends
      // against accidentally writing test data to lapiazza.app.
      grep: /@smoke/,
      use: { ...devices['Desktop Chrome'], baseURL: BASE_URLS.prod },
    },
  ],
});
