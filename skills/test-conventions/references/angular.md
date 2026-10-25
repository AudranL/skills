# Angular / TypeScript

- Le framework du projet (Jest ou Jasmine / Karma). Angular Testing Library si présent, pour tester comme un utilisateur (rôles, libellés) plutôt que via le DOM interne.
- `describe` imbriqués par situation, `it` qui se lit comme une phrase : `it('should disable the submit button when the form is invalid')`.
- Logique métier sortie des composants dans des services ou fonctions pures, testés sans `TestBed`.
- `TestBed` pour les composants ; doubles des services HTTP via `HttpTestingController` ou un fake du service, jamais d'appel réseau réel.
- Code asynchrone maîtrisé (`fakeAsync` / `tick`, ou `async` / `await`), pas de `setTimeout` dans les tests.
- `strictNullChecks` activé.

```ts
describe('CartTotalPipe', () => {
  describe('when the customer has more than ten orders', () => {
    it('should apply the loyalty discount', () => {
      const cart = aCart().withTotal(100).build();
      const loyalCustomer = aCustomer().withOrderCount(11).build();

      const total = new CartTotalPipe().transform(cart, loyalCustomer);

      expect(total).toBe(90);
    });
  });
});
```
