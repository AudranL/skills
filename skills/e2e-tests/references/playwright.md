# Playwright

## Targeting, waiting, checking

- **Target**: `page.getByRole('button', { name: 'Save' })`, `page.getByLabel('Address')`. `getByTestId` only when no role or name fits, with an attribute asked of the developer.
- **Narrow rather than pick**: a locator that matches two elements makes the action fail (locators are strict). Do not silence it with `.first()` or `.nth()`: narrow it to a region (`page.getByRole('row', { name: 'Central Station' }).getByRole('button', { name: 'Book' })`) or filter it (`locator.filter({ hasText: … })`).
- **Exact text**: `page.getByText('Gate 4', { exact: true })`, or `page.getByText(/Gate 4$/)`. Without `exact`, `getByText` looks for a substring, ignoring case.
- **Wait for an effect**: web assertions wait on their own (`await expect(locator).toHaveText(…)`, `toBeVisible()`, `toHaveCount(0)`); for a value outside the page (a file written), `await expect.poll(() => readTheFile()).toEqual(…)`. Never `page.waitForTimeout()`. Never read a value and then compare it (`expect(await locator.textContent()).toBe(…)`): the reading does not wait, and the journey fails or passes by chance.
- **Delays**: in `playwright.config` (`timeout`, `expect: { timeout }`), not in each test.
- **Actions layer**: functions (or an object per screen) in business words, which alone know the roles and labels: `await bookABike(page, { station: 'Central Station' })`.

## Configuration

- **`retries: 0`**: a retry turns a flaky journey green. If the project keeps retries in CI, the report's "flaky" list is read after each run and each journey in it is investigated.
- **`forbidOnly: !!process.env.CI`**: a `test.only` forgotten in a commit fails the run instead of skipping all the other journeys.
- **On failure only**: `use: { trace: 'retain-on-failure', screenshot: 'only-on-failure' }`; the trace (`npx playwright show-trace`) replays each action with the page's state.
- **Parallel runs** (`fullyParallel`, `workers`) are only safe once each journey is isolated: they also reveal the journeys that are not.

## Isolation, time and screenshots

- **A fresh context per test**: that is the default with the `@playwright/test` fixtures (`page`, `context`).
- **Network** (browser): `await context.route('**/*', (route) => route.abort())`, then allow only what the journey calls.
- **Time** (browser): `await page.clock.setFixedTime(new Date('2026-03-02T09:00:00'))`, or `page.clock.install({ time })` when the page's timers must run, before the navigation.
- **Screenshots**: first check an expected text, then `await page.screenshot({ path, animations: 'disabled' })`, into a folder of the acceptance check's own (for instance `dist/screenshots-<slice>/`), the file name taken from the scenario.

## Electron

- **Launch the package**, not the sources: `_electron.launch({ executablePath: <path to the packaged executable>, args: ['--user-data-dir=<temporary folder>', <the application's hidden-window flag>] })` (`import { _electron } from 'playwright'`).
- **On the application's side**, the test mode creates the window with `show: false` (without showing it on `ready-to-show`) and `webPreferences: { backgroundThrottling: false }`, so that clicks and screenshots work on a hidden window (`page.screenshot`, or `webContents.capturePage()` in the main process). It is the developer's to add, as test configuration: ask for it if it is missing.
- **No visible window at the end**: `await app.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows().some((w) => w.isVisible()))` must return `false`.
- **The network** is blocked on the application's side, in test mode (for instance through `session.webRequest`), since the journey does not go through a browser Playwright fully controls.
- **A fixture** launches the application, creates and deletes the temporary folder, checks that no window is visible and closes the application, for each test.
