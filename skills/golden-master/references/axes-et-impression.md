# Axes de variation et impression déterministe

## 1. Trouver les axes

Parcourir la cible ligne par ligne, puis **chaque méthode appelée sur les entrées** (getters calculés, méthodes utilitaires du modèle, `fromName`, `toString` formatés). Noter chaque point de décision :

- conditions `if`, ternaires, `&&` / `||` (chaque opérande compte : `a != null && a.getB() != null` donne deux axes) ;
- `switch`, `equals` sur une constante, `X.name().equals(...)`, `fromName(...)` ;
- accès qui peuvent lever une exception : déréférencement (`x.getY().toString()`), `Integer.parseInt`, `get(0)`, `Optional.get()` ;
- boucles et streams (`filter`, `findFirst`, `max`) : contenu et **ordre** de la collection ;
- dépendances implicites : `LocalDate.now()`, `UUID.randomUUID()`, `Locale` par défaut, variables d'environnement, propriétés `@Value`.

Construire une table :

| # | Axe | Où | Valeurs |
|---|---|---|---|
| 1 | édition active | `getCurrentActiveEdition()` | absente, présente |
| 2 | mode d'expédition | `extractPackSize` l.93 | `null`, `WAREHOUSE`, `STORE`, `PUBLISHER` |
| … | | | |

## 2. Choisir les valeurs

- **Toutes** les valeurs d'un enum, plus `null`. Un enum qui gagne une valeur plus tard doit apparaître dans le fichier.
- Pour une clé comparée à des noms d'enum : chaque nom, `null`, une valeur inconnue, une variante de casse.
- Pour un nombre : les bornes exactes de chaque comparaison (`< 10` → 9, 10, 11), `0`, négatif, `null` si objet.
- Pour un objet imbriqué : `null`, « vide » (tous les champs `null`), « complet ».
- Pour une collection : `null`, vide, 1 élément, plusieurs éléments dont un qui gagne le tri, puis l'ordre inversé.
- **Valeurs distinctes** pour chaque source possible d'une donnée de sortie (carton = 12, lot = 3, palette expédiée = 480, palette livrée = 960). Si deux branches renvoient la même valeur de test, PIT ne verra pas la différence.
- Ajouter les **cas réels** fournis par l'utilisateur ou trouvés dans les ressources de test existantes (`src/test/resources/*.json`).

## 3. Objets complexes : des « formes » plutôt que des champs

Quand un objet d'entrée a beaucoup de sous-éléments optionnels, ne pas créer un axe par champ : définir un `enum` de formes significatives, avec un `toString` parlant, et une fonction de construction.

```java
enum Logistique {
    NULL, VIDE, CARTON_SANS_LOT, CARTON_AVEC_LOT, PALETTE_EXPEDIEE, PALETTE_LIVREE, COMPLETE
}

static Packaging fixture(Logistique forme, String out, String in) { … }
```

Le choix des formes vient de la table des axes : une forme par combinaison de sous-éléments qui change une branche.

## 4. Maîtriser l'explosion

Nombre de lignes = produit des tailles des axes. Cibles : < 2 000 par méthode de test, < 10 s d'exécution (PIT relance le test pour chaque mutant).

Leviers, dans l'ordre :

1. **Découper** : tester directement une méthode publique très combinatoire (ex. `extractPackSize`), et ne garder qu'une ou deux formes de cet axe dans le test de la méthode appelante.
2. **Séparer les axes indépendants** : si l'axe X n'influence qu'une partie du résultat qui ne dépend d'aucun autre axe, le tester dans une méthode à part avec les autres axes figés.
3. **Regrouper** des champs liés en formes (section 3).
4. En dernier recours seulement, retirer des valeurs « intermédiaires » (jamais les bornes, jamais `null`, jamais une valeur d'enum).

Chaque réduction doit être vérifiée a posteriori par la couverture et la mutation (étape 5).

## 5. Impression

### Ce qu'il faut imprimer

- **Tous les champs** du résultat, y compris ceux qui paraissent sans intérêt.
- L'**exception** : classe et message (fait automatiquement par `CombinationApprovals`).
- L'**état des arguments** après l'appel si la cible peut les modifier.
- Les **interactions** avec les dépendances, dans l'ordre (voir `services-et-dependances.md`).
- Pour une méthode `void` : uniquement les effets de bord, mais tous.

### Comment

1. Si le type de sortie a un `toString()` généré (Lombok `@Data` / `@Value` / `@ToString`, record) qui inclut tous les champs, l'utiliser tel quel.
2. Sinon, écrire un `print(...)` dans le test : champs dans un **ordre fixe**, `null` explicite.
3. Pour un graphe d'objets profond, sérialiser en JSON avec un `ObjectMapper` configuré pour être stable :

```java
private static final ObjectMapper PRINTER = JsonMapper.builder()
        .enable(MapperFeature.SORT_PROPERTIES_ALPHABETICALLY)
        .enable(SerializationFeature.ORDER_MAP_ENTRIES_BY_KEYS)
        .addModule(new JavaTimeModule())
        .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS)
        .build();

static String print(Object o) {
    try { return PRINTER.writeValueAsString(o); }
    catch (JsonProcessingException e) { throw new UncheckedIOException(e); }
}
```

Ne pas utiliser l'`ObjectMapper` de production pour imprimer : s'il change pendant le refactoring, l'impression changerait avec lui.

### Déterminisme

| Source de bruit | Remède |
|---|---|
| `Objet@1b6d3586` (pas de `toString`) | imprimer les champs ou sérialiser en JSON |
| `HashMap` / `HashSet` dans la sortie | trier à l'impression (`new TreeMap<>(map)`, `ORDER_MAP_ENTRIES_BY_KEYS`) |
| Date / heure du jour | `Clock` fixe (voir `services-et-dependances.md`), scrubber en dernier recours |
| UUID, aléatoire | générateur injecté ou statique mocké, scrubber en dernier recours |
| `Locale` / fuseau par défaut (formats de nombres, dates) | fixer `Locale.setDefault` et `TimeZone.setDefault` dans un `@BeforeAll` et restaurer dans `@AfterAll` |
| `BigDecimal` `1.0` vs `1.00` | imprimer tel quel : l'échelle fait partie du comportement |
| Ordre d'itération d'un `Set` en **entrée** | utiliser `LinkedHashSet` dans les fixtures |
