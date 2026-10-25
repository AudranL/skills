# TypeScript (Vitest ou Jest, React, Node, Electron)

- **Framework** : celui du projet, Vitest ou Jest. Suivre le projet pour les imports explicites (`import { describe, expect, it } from 'vitest'`) ou les globales.
- **Emplacement** : celui du projet ; à défaut, le test à côté du fichier testé (`order.ts`, `order.test.ts`).
- **Noms** : `describe` nomme le concept ou la règle métier (« Remise de fidélité »), `it` est une phrase qui décrit le comportement, dans la langue du code du projet.
- **Exemples d'une règle** : autant de `it` que de cas, ou `it.each` avec des objets aux champs nommés plutôt que des tableaux de valeurs anonymes ; le titre reprend les valeurs.
- **Logique hors des composants** : les règles vivent dans des fonctions pures ou des cas d'utilisation, testés sans rendu ; un composant présente et transmet.
- **Composants React** : React Testing Library (`render`, `screen.getByRole`, `getByLabelText`) et `userEvent` plutôt que `fireEvent`, pour tester comme un utilisateur ; ni état interne ni classe CSS.
- **Un texte attendu qui peut en prolonger un autre se cherche exact.** Une recherche par sous-chaîne (`toContain`, `getByText` de Playwright par défaut) trouve « à 16h » dans « à 16h30 », et le test ne peut plus échouer quand l'ancienne valeur prolonge la nouvelle : chercher le texte exact (`{ exact: true }`, `toBe`) ou ancrer l'expression (`/… à 16h$/`).
- **Doubles** : un adaptateur en mémoire par port (`InMemoryOrderRepository`), écrit une fois et réutilisé par les tests des cas d'utilisation, plutôt que des `vi.fn()` recréés dans chaque test. `vi.fn()` / `jest.fn()` seulement pour vérifier une commande envoyée à l'extérieur.
- **Le temps** : une horloge injectée. À défaut, `vi.useFakeTimers()` et `vi.setSystemTime(…)` (Jest : `jest.useFakeTimers().setSystemTime(…)`), rétablis après chaque test.
- **Données de test** : un Test Data Builder qui rend un objet valide, à modifier (`anOrder({ total: 100 })`), plutôt que des `as any` ou des `!` pour faire compiler un test.
- **Tests d'acceptation** au niveau des cas d'utilisation : une couche d'automatisation écrite dans le vocabulaire de la fiche (`aShopInMemory().placeOrder({ … })`), qui monte les cas d'utilisation sur les adaptateurs en mémoire. Le titre du scénario se retrouve dans le `describe` ou le `it` : une recherche du titre trouve son test. Un plan du scénario devient un `describe` à son titre et un `it` par ligne d'exemples.
- **Forme négative** (« … n'est pas présenté ») : vérifier la liste complète (`expect(presented).toEqual([…])`), pas un `not.toContain` ni une liste filtrée.
- **Adaptateurs de persistance** (SQLite, fichiers) : un dossier temporaire par test (`mkdtempSync(join(tmpdir(), 'app-'))`), le vrai schéma, nettoyage en `afterEach`.
- **Asynchrone** : `async` / `await` ; `await expect(promise).rejects.toThrow(…)` pour une erreur attendue.
- **Electron** : les règles et les cas d'utilisation se testent dans le processus qui les exécute, sans lancer Electron ; seuls les tests de bout en bout lancent l'application (skill `e2e-tests`).

```ts
describe('Remise de fidélité', () => {
  it.each([
    { orders: 10, expectedTotal: 100 },
    { orders: 11, expectedTotal: 90 },
  ])('$orders commandes donnent un total de $expectedTotal €', ({ orders, expectedTotal }) => {
    const customer = aCustomer({ orders })

    expect(totalFor(aCart({ total: 100 }), customer)).toBe(expectedTotal)
  })
})
```
