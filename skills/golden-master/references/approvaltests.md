# ApprovalTests.Java — l'essentiel pour un golden master

## Dépendance

```xml
<dependency>
    <groupId>com.approvaltests</groupId>
    <artifactId>approvaltests</artifactId>
    <version>31.0.0</version> <!-- ou plus récent : vérifier sur Maven Central -->
    <scope>test</scope>
</dependency>
```

Si le projet a déjà ApprovalTests, garder sa version. Si un BOM d'entreprise gère les versions, vérifier qu'il ne l'impose pas déjà.

## Imports utiles

```java
import org.approvaltests.Approvals;
import org.approvaltests.combinations.CombinationApprovals;
import org.approvaltests.core.Options;
import org.approvaltests.reporters.QuietReporter;
import org.approvaltests.scrubbers.RegExScrubber;
```

## Fichiers produits

- `<ClasseDeTest>.<methode>.received.txt` : sortie du dernier passage, créée **seulement** si elle diffère de l'approuvé.
- `<ClasseDeTest>.<methode>.approved.txt` : référence, **à versionner**.
- Les deux sont écrits **à côté du fichier source du test** (`src/test/java/<package>/`). Si le projet veut les ranger ailleurs, une classe `PackageSettings` dans le package du test peut définir `public static String ApprovalBaseDirectory = "../resources";`.
- Approuver = renommer : `mv X.received.txt X.approved.txt`.
- Ajouter `*.received.*` au `.gitignore` du projet s'il n'y est pas.

## Reporter

Par défaut, ApprovalTests tente d'ouvrir un outil de diff graphique. Pour un agent ou une CI, utiliser `QuietReporter`, qui se contente d'afficher la commande `mv` dans la console :

```java
private static final Options OPTIONS = new Options().withReporter(new QuietReporter());
```

Passer `OPTIONS` en dernier argument de chaque `verify…`.

## API

### Un seul résultat

```java
Approvals.verify(texte, OPTIONS);
```

### Une liste d'entrées (échantillons réels, fichiers JSON)

```java
Approvals.verifyAll("Produit", echantillons, e -> e.nom() + " => " + imprimer(mapper.apply(e)), OPTIONS);
```

### Produit cartésien — l'outil principal du golden master

```java
CombinationApprovals.verifyAllCombinations(
        (a, b, c) -> appelerLaCible(a, b, c),   // lambda qui retourne l'objet à imprimer
        valeursA, valeursB, valeursC,          // un tableau par axe (jusqu'à 9 axes)
        OPTIONS);
```

- Chaque ligne du fichier a la forme `[valeurA, valeurB, valeurC] => résultat.toString()`.
- Si la lambda lève une exception, elle est capturée et imprimée à la place du résultat : ne pas l'attraper soi-même, sauf pour ajouter des informations (ex. état d'un mock).
- Les tableaux doivent être typés (`new Integer[]{null, 0, 1}`, `ShippingMode.values()`). Pour ajouter `null` aux valeurs d'un enum, construire le tableau à la main ou avec un petit utilitaire :

```java
@SafeVarargs
static <T> T[] avecNull(T... valeurs) {
    T[] resultat = Arrays.copyOf(valeurs, valeurs.length + 1);
    System.arraycopy(resultat, 0, resultat, 1, valeurs.length);
    resultat[0] = null;
    return resultat;
}
// avecNull(ShippingMode.values()) -> [null, WAREHOUSE, STORE, PUBLISHER]
```

- Plus de 9 axes : regrouper des axes liés dans un `enum` de « formes » (voir `axes-et-impression.md`), ou découper en plusieurs tests.

## Scrubbers : masquer ce qui ne peut pas être rendu déterministe

À utiliser en dernier recours, quand la valeur n'influence aucune branche (sinon, la maîtriser en amont : horloge fixe, générateur figé).

```java
Options options = new Options()
        .withReporter(new QuietReporter())
        .withScrubber(new RegExScrubber("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "[uuid]"));
```

## Plusieurs vérifications dans une même méthode

Une méthode de test = un fichier approuvé. Plutôt que plusieurs `verify` dans la même méthode, créer une méthode de test par sous-logique (`mapToDto`, `extractPackSize`, `buildBook`…).

## Pièges fréquents

| Symptôme | Cause | Correction |
|---|---|---|
| Le test est vert dès le premier lancement | Un ancien `.approved.txt` existe déjà | Vérifier `git status` et le contenu du fichier |
| Diff à chaque passage | Sortie non déterministe | Voir `axes-et-impression.md` § Déterminisme |
| `received` vide ou une seule ligne | Un tableau d'axe est vide | Vérifier chaque tableau |
| Fins de ligne différentes Windows / Mac | `core.autocrlf` | `.gitattributes` : `*.approved.txt text eol=lf` |
