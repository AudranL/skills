# Services à dépendances

Pour un service Spring, la « sortie » n'est pas seulement la valeur retournée : ce sont aussi les appels faits aux dépendances (sauvegarde, message Kafka, appel HTTP) et leurs arguments. Le golden master doit les imprimer.

## 1. Pas de contexte Spring

Instancier la cible à la main, avec des mocks Mockito. Pas de `@SpringBootTest` : lent, et chaque mutant PIT relancerait le contexte.

```java
ProductRepository repository = mock(ProductRepository.class);
PricingClient pricing = mock(PricingClient.class);
Clock clock = Clock.fixed(Instant.parse("2026-01-15T10:00:00Z"), ZoneOffset.UTC);
ProductService service = new ProductService(repository, pricing, clock);
```

- Les champs `@Value` deviennent des axes : `ReflectionTestUtils.setField(service, "threshold", seuil)`.
- Un champ injecté par `@Autowired` sur un attribut : `ReflectionTestUtils.setField` aussi.

## 2. Les réponses des dépendances sont des axes

Chaque appel à une dépendance dont le résultat influence la suite est un axe : réponse nominale, vide (`Optional.empty()`, liste vide), `null` si le contrat le permet, exception.

```java
enum RepoResponse { TROUVE, ABSENT, ERREUR }

static void stub(ProductRepository repository, RepoResponse reponse) {
    switch (reponse) {
        case TROUVE -> when(repository.findById("P1")).thenReturn(Optional.of(produit()));
        case ABSENT -> when(repository.findById("P1")).thenReturn(Optional.empty());
        case ERREUR -> when(repository.findById("P1")).thenThrow(new DataAccessResourceFailureException("db down"));
    }
}
```

Préférer des matchers larges (`any()`) si l'argument exact n'est pas l'objet de l'axe : l'argument réellement passé sera de toute façon imprimé dans les interactions.

## 3. Des mocks neufs à chaque combinaison

Créer les mocks **dans la lambda** de `CombinationApprovals`, jamais en champ de classe : sinon les interactions s'accumulent d'une combinaison à l'autre.

```java
@Test
void process() {
    CombinationApprovals.verifyAllCombinations(
            (repoResponse, pricingResponse, quantite) -> {
                Deps d = new Deps();                       // mocks neufs
                stub(d.repository, repoResponse);
                stub(d.pricing, pricingResponse);
                String resultat;
                try {
                    resultat = String.valueOf(d.service().process("P1", quantite));
                } catch (Exception e) {
                    resultat = e.getClass().getName() + ": " + e.getMessage();
                }
                return resultat + "\n    " + interactions(d.repository, d.pricing);
            },
            RepoResponse.values(), PricingResponse.values(), new Integer[]{null, 0, 1, 100},
            OPTIONS);
}
```

Ici l'exception est attrapée explicitement pour pouvoir imprimer aussi les interactions faites **avant** l'erreur.

## 4. Enregistrer les interactions

Mockito garde toutes les invocations de chaque mock, avec un numéro de séquence global : on peut reconstituer l'ordre exact des appels, toutes dépendances confondues.

```java
import org.mockito.invocation.Invocation;

static String interactions(Object... mocks) {
    return Arrays.stream(mocks)
            .flatMap(m -> Mockito.mockingDetails(m).getInvocations().stream())
            .sorted(Comparator.comparingInt(Invocation::getSequenceNumber))
            .map(i -> Mockito.mockingDetails(i.getMock()).getMockCreationSettings().getTypeToMock().getSimpleName()
                    + "." + i.getMethod().getName()
                    + Arrays.stream(i.getArguments()).map(GoldenMasterTest::print).collect(Collectors.joining(", ", "(", ")")))
            .collect(Collectors.joining("\n    "));
}
```

- `print` est l'impression déterministe de `axes-et-impression.md` (JSON trié si l'argument n'a pas de `toString` utile).
- Les appels de lecture (`findById`) apparaissent aussi : c'est voulu, un refactoring qui double une requête doit se voir.

### Argument modifié après l'appel

Mockito garde une **référence** vers les arguments. Si la cible modifie l'entité après `repository.save(entity)`, l'impression montrera l'état final, pas l'état sauvegardé. Dans ce cas, photographier l'argument au moment de l'appel :

```java
List<String> sauvegardes = new ArrayList<>();
when(repository.save(any())).thenAnswer(inv -> {
    sauvegardes.add(print(inv.getArgument(0)));   // copie texte immédiate
    return inv.getArgument(0);
});
```

## 5. Horloge, aléatoire, statiques

Par ordre de préférence :

1. **La cible reçoit déjà une `Clock`, un `Supplier<UUID>`, un `Random`** : injecter une valeur fixe. Si la date compare à des données (validité d'une version, échéance), la date fixe devient un axe : avant, pendant, après, et pile sur chaque borne.
2. **Appel statique direct** (`LocalDate.now()`, `UUID.randomUUID()`) : le mocker le temps du test avec `mockStatic` (Mockito 5 l'active par défaut ; avec Mockito 4, il faut `mockito-inline`).

   ```java
   try (MockedStatic<LocalDate> now = mockStatic(LocalDate.class, CALLS_REAL_METHODS)) {
       now.when(LocalDate::now).thenReturn(LocalDate.of(2026, 1, 15));
       return appelerLaCible(...);
   }
   ```

   Ouvrir le `MockedStatic` **dans** la lambda (il est lié au thread et doit être fermé).
3. **Couture minimale** (remplacer `LocalDate.now()` par `LocalDate.now(clock)` avec une `Clock` injectée) : c'est une modification du code de production, donc **uniquement avec l'accord de l'utilisateur**, par refactoring automatique de l'IDE, dans un commit à part, avant le golden master.
4. **Scrubber** : seulement si la valeur apparaît dans la sortie sans influencer aucune branche.

## 6. Ce qui reste hors de portée

- Appels réseau ou base réels, threads, `@Async`, transactions : le golden master s'arrête à la frontière des mocks. Le signaler dans le rapport si une partie du comportement en dépend (ex. rollback transactionnel).
- Code dans des requêtes `@Query` / SQL : non couvert par ce test, à caractériser séparément avec une base de test si besoin.
