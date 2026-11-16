# Other tools

- **Cypress**: `cy.findByRole` (Testing Library for Cypress, `@testing-library/cypress`) or `cy.contains('button', 'Save')`; exact text through an anchored expression (`cy.contains(/^Gate 4$/)`); commands retry on their own until `defaultCommandTimeout`, never `cy.wait(<duration>)`; `cy.intercept` to block or simulate the network; `cy.clock` to fix the date; `cy.screenshot()` after an assertion on an expected text; `retries` left at 0, for the same reason as in Playwright.
- **Selenium WebDriver**: explicit waits (`WebDriverWait` and a condition), never `Thread.sleep` nor a global implicit wait mixed with explicit ones; target by an accessible role or label (XPath on `@aria-label` or the exact text) rather than a CSS class; screen details in one object per screen; a temporary browser profile per test; a browser without interface (`--headless`).

For another tool: the same principles (`SKILL.md`), translated with its documentation, and the convention of the journeys already in the repository.
