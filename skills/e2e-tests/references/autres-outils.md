# Autres outils

- **Cypress** : `cy.findByRole` (Testing Library pour Cypress) ou `cy.contains('button', 'Enregistrer')` ; texte exact par une expression ancrée (`cy.contains(/^à 16h$/)`) ; les commandes réessaient seules jusqu'au délai de `defaultCommandTimeout`, jamais `cy.wait(<durée>)` ; `cy.intercept` pour bloquer ou simuler le réseau ; `cy.screenshot()` après une assertion sur un texte attendu.
- **Selenium WebDriver** : attentes explicites (`WebDriverWait` et une condition), jamais `Thread.sleep` ni attente implicite globale mêlée aux explicites ; viser par un rôle ou un libellé accessible (XPath sur `@aria-label` ou le texte exact) plutôt que par une classe CSS ; un profil de navigateur temporaire par test ; navigateur sans interface (`--headless`).

Pour un autre outil : les mêmes principes (`SKILL.md`), traduits avec sa documentation, et la convention des parcours déjà présents dans le dépôt.
