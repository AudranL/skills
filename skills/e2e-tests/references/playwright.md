# Playwright

## Viser, attendre, vérifier

- **Viser** : `page.getByRole('button', { name: 'Enregistrer' })`, `page.getByLabel('Adresse')`. `getByTestId` seulement quand aucun rôle ni nom ne convient, avec un attribut demandé au développeur.
- **Texte exact** : `page.getByText('à 16h', { exact: true })`, ou `page.getByText(/à 16h$/)`. Sans `exact`, `getByText` cherche une sous-chaîne, sans tenir compte de la casse.
- **Attendre un effet** : les assertions web attendent seules (`await expect(locator).toHaveText(…)`, `toBeVisible()`, `toHaveCount(0)`) ; pour une valeur hors de la page (un fichier écrit), `await expect.poll(() => lireLeFichier()).toEqual(…)`. Jamais `page.waitForTimeout()`.
- **Délais** : dans `playwright.config` (`timeout`, `expect: { timeout }`), pas dans chaque test.
- **Couche des gestes** : des fonctions (ou un objet) dans les mots du métier, qui seules connaissent les rôles et les libellés : `await reserverUnVelo(page, { station: 'Gare' })`.

## Isolation et captures

- **Un contexte neuf par test** : c'est le cas par défaut avec les fixtures de `@playwright/test` (`page`, `context`).
- **Réseau** (navigateur) : `await context.route('**/*', (route) => route.abort())`, puis n'autoriser que ce que le parcours appelle.
- **Captures** : vérifier d'abord un texte attendu, puis `await page.screenshot({ path, animations: 'disabled' })`, dans un dossier propre à la recette (par exemple `dist/captures-<fonctionnalité>/`), le nom du fichier tiré du scénario.

## Electron

- **Lancer le paquet**, pas les sources : `_electron.launch({ executablePath: <chemin de l'exécutable empaqueté>, args: ['--user-data-dir=<dossier temporaire>', <drapeau de fenêtre cachée de l'application>] })` (`import { _electron } from 'playwright'`).
- **Côté application**, le mode de test crée la fenêtre avec `show: false` (sans l'afficher à `ready-to-show`) et `webPreferences: { backgroundThrottling: false }`, pour que les clics et les captures marchent sur une fenêtre cachée (`page.screenshot`, ou `webContents.capturePage()` dans le processus principal). C'est au développeur de l'ajouter : le demander s'il manque.
- **Aucune fenêtre visible à la fin** : `await app.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows().some((w) => w.isVisible()))` doit rendre `false`.
- **Le réseau** se bloque côté application, en mode de test (par exemple par `session.webRequest`), puisque le parcours ne passe pas par un navigateur que Playwright contrôle entièrement.
- **Une fixture** lance l'application, crée et efface le dossier temporaire, vérifie qu'aucune fenêtre n'est visible et ferme l'application, pour chaque test.
