---
name: golden-master
description: "Pose un golden master (test de caractérisation, approval test) sur du code Java / Spring Boot existant pour figer son comportement actuel avant un refactoring. Utilise ApprovalTests.Java et une génération combinatoire des entrées (CombinationApprovals), puis prouve que le filet tient avec JaCoCo (couverture des branches) et PIT (tests de mutation). Couvre le code pur (mappers, utils, règles de calcul) comme les services à dépendances (mocks qui enregistrent les appels, horloge et aléatoire maîtrisés). Utiliser dès que l'utilisateur parle de golden master, de test de caractérisation, d'approval test, de snapshot test, de code legacy sans tests, de sécuriser ou blinder une classe avant de la refactorer, ou demande « comment toucher à ce code sans rien casser » — même sans dire « golden master ». Périmètre : un projet Maven. La skill s'arrête au filet de sécurité et propose un plan de refactoring, elle ne refactore pas."
---

# Golden master Java / Spring Boot

## Principe

Un golden master ne dit pas si le code est juste : il enregistre **ce qu'il fait aujourd'hui**, bugs compris, pour détecter le moindre changement de comportement pendant un refactoring.

1. On fait varier les entrées selon tous les **axes** qui influencent le code (null / non null, chaque valeur d'enum, chaque branche…), en **produit cartésien**.
2. Pour chaque combinaison, on imprime une ligne de texte **déterministe** : les entrées, puis la sortie, l'exception levée, et les effets de bord (appels aux dépendances).
3. ApprovalTests compare ce texte (`*.received.txt`) au fichier de référence versionné (`*.approved.txt`). Toute différence fait échouer le test.
4. On **prouve** que le filet est assez serré : JaCoCo montre que chaque branche est exécutée, PIT montre que chaque mutation du code fait échouer le test.

Un golden master sans couverture ni mutation est un faux sentiment de sécurité : une branche jamais exécutée ou un champ jamais imprimé peut changer sans que rien ne casse.

## Règles absolues

- **Ne pas modifier le code de production** pendant la construction du golden master. Seule exception : une couture minimale (injecter une `Clock`, extraire un appel statique) faite par un refactoring automatique de l'IDE, **après accord explicite de l'utilisateur**. Vérifier avec `git diff --stat -- src/main` qu'il n'y a rien d'autre.
- **Ne jamais corriger un comportement suspect** (NPE, valeur incohérente, commentaire contredit par le code) : le figer tel quel et le lister dans le rapport. Le corriger est une décision métier, prise plus tard, dans un commit à part.
- **Sortie déterministe** : pas de `Objet@1b6d3586`, pas de date du jour, pas d'UUID aléatoire, pas d'ordre de `HashMap` / `HashSet`. Le test doit donner exactement le même fichier deux fois de suite.
- **Relire avant d'approuver** le premier `received`. Ensuite, pendant le refactoring, un écart ne se résout **jamais** en ré-approuvant : c'est le code qui a tort.
- Travailler sur une branche dédiée avec un working tree propre.
- Le golden master est **temporaire** : il sera remplacé par de vrais tests unitaires métier une fois le code refactoré.

## Étape 1 — Cadrer

1. Identifier la **cible** : la classe, et ses méthodes publiques (ou appelées depuis l'extérieur). Choisir le **point d'appel le plus haut** qui reste rapide et isolable : une méthode publique couvre les méthodes privées qu'elle appelle. Si une méthode publique contient à elle seule une logique très combinatoire (ex. `extractPackSize` dans l'exemple), lui consacrer un test à part pour limiter l'explosion des combinaisons.
2. Classer la cible :
   - **code pur** (mapper, util statique, calcul) → section « Écrire le test » directement ;
   - **service à dépendances** (repositories, clients HTTP, Kafka, horloge, `@Value`) → lire aussi `references/services-et-dependances.md`.
3. Vérifier le build (`pom.xml`) :
   - JUnit 5 présent ; Mockito si la cible a des dépendances ;
   - ApprovalTests présent ? Sinon l'ajouter en scope `test` (voir `references/approvaltests.md`) ;
   - JaCoCo / PIT déjà configurés ? Sinon le profil Maven `golden-master` de `references/verification-maven.md` sera ajouté à l'étape 5.
4. `git status` propre, puis `git checkout -b test/golden-master-<cible-en-kebab>`.

## Étape 2 — Cartographier les axes de variation

Lire la cible **et toutes les méthodes qu'elle appelle sur ses entrées**, y compris les getters calculés du modèle (ex. `getCurrentActiveEdition()`, `getFirstSalePriceAsString()`) : ils cachent souvent des branches, des dates ou des formats.

Chaque point de décision devient un axe :

| Dans le code | Valeurs de l'axe |
|---|---|
| `x != null ? … : …`, `if (x == null)` | `null`, non null |
| `enum`, `switch`, `X.name().equals(key)` | `null`, **chaque** valeur de l'enum, une valeur inconnue (`"UNKNOWN"`) |
| comparaison numérique, seuil | juste en dessous, égal, juste au-dessus, `0`, négatif |
| chaîne | `null`, `""`, valeur nominale, casse différente si `equals`/`fromName` |
| collection, boucle | `null`, vide, un élément, plusieurs (dont doublons, ordre différent) |
| exception d'une dépendance | réponse nominale, vide, exception |

Le détail (choix des valeurs, objets imbriqués, maîtrise de l'explosion) est dans `references/axes-et-impression.md`.

Présenter la table des axes à l'utilisateur, avec le nombre de combinaisons, et lui demander s'il connaît **des cas métier réels** absents de la table (un format de données exotique, un produit particulier). Les ajouter comme valeurs d'axe.

Garder le total sous ~2 000 combinaisons par test. Au-delà : découper par sous-logique indépendante (un test par méthode publique, ou par axe qui ne se combine avec aucun autre).

## Étape 3 — Écrire le test

Créer `<Cible>GoldenMasterTest` dans le **même package** que la cible (accès aux méthodes package-private), sous `src/test/java`.

Structure type (code pur) :

```java
class PriceCalculatorGoldenMasterTest {

    private static final Options OPTIONS = new Options().withReporter(new QuietReporter());

    @Test
    void compute() {
        CombinationApprovals.verifyAllCombinations(
                (customer, quantity, promo) -> print(PriceCalculator.compute(fixture(customer), quantity, promo)),
                CustomerShape.values(),                 // axe 1 : forme de l'objet d'entrée
                new Integer[]{null, -1, 0, 1, 10, 11},  // axe 2 : bornes autour du seuil 10
                new String[]{null, "", "SUMMER", "summer", "UNKNOWN"},
                OPTIONS);
    }
}
```

Points clés :

- Chaque valeur d'axe doit avoir un **`toString()` lisible** : `CombinationApprovals` l'imprime en tête de ligne. Pour les objets complexes, utiliser un `enum` de « formes » (`CustomerShape.SANS_ADRESSE`) et une fonction `fixture(shape)` qui construit l'objet.
- Construire les entrées **comme en production** : builders, constructeurs ou désérialisation JSON du projet. Utiliser des **valeurs distinctes** pour chaque source possible d'une donnée (carton = 12, lot = 3, palette = 480) : la sortie révèle alors quelle branche a été prise.
- **Imprimer toute la sortie** : tous les champs du résultat, l'exception (classe + message), l'état modifié des arguments, les interactions avec les dépendances. Un champ non imprimé est un champ non protégé.
- Les exceptions levées par la cible sont capturées et imprimées par `CombinationApprovals` : ne pas les attraper soi-même.

Exemple complet : `references/exemple-book-dto-mapper.md`.

## Étape 4 — Générer, relire, approuver

1. Lancer le test seul :
   ```bash
   mvn -q test -Dtest='<Cible>GoldenMasterTest' -Dsurefire.failIfNoSpecifiedTests=false
   ```
   Le premier passage **échoue** (pas encore de fichier approuvé) et crée `<Cible>GoldenMasterTest.<methode>.received.txt` à côté de la classe de test.
2. **Relire** le fichier reçu (au moins un échantillon par axe) et vérifier :
   - aucune trace non déterministe (`@` suivi d'un hash, date du jour, UUID) → sinon corriger l'impression ou ajouter un scrubber ;
   - toutes les lignes ne donnent pas la même sortie → sinon un axe n'atteint pas le code (fixture mal construite) ;
   - les exceptions sont celles attendues du code, pas des erreurs de la fixture du test.
3. Vérifier le **déterminisme** : copier le `received`, relancer, comparer (`diff`). Aucune différence tolérée.
4. Approuver : `mv X.received.txt X.approved.txt`, relancer → vert.
5. Committer test + fichier approuvé : `git commit -m "test: golden master on <Cible>"`.

## Étape 5 — Prouver que le filet tient

Ajouter si besoin le profil Maven `golden-master` (`references/verification-maven.md`), puis boucler jusqu'à ce que les deux critères soient atteints.

`<dossier de cette skill>` est le dossier de ce fichier : par exemple `~/.claude/skills/golden-master` dans Claude Code, `~/.copilot/skills/golden-master` dans Copilot, `~/.config/opencode/skills/golden-master` dans opencode.

### 5a. Couverture (JaCoCo) — objectif : 100 % des branches de la cible

```bash
mvn -q -P golden-master test -Dtest='<Cible>GoldenMasterTest' -Dsurefire.failIfNoSpecifiedTests=false
python3 <dossier de cette skill>/scripts/coverage_report.py target/site/jacoco/jacoco.xml <fqn.Cible> --src src/main/java
```

Pour chaque ligne ou branche manquée : ajouter la valeur d'axe qui l'atteint, ou justifier dans le rapport (code mort, branche impossible à atteindre sans modifier le code).

### 5b. Mutation (PIT) — objectif : tous les mutants tués ou justifiés

```bash
mvn -q -P golden-master -Djacoco.skip=true test-compile org.pitest:pitest-maven:mutationCoverage \
    -DtargetClasses='<fqn.Cible>*' -DtargetTests='<fqn.Cible>GoldenMasterTest'
python3 <dossier de cette skill>/scripts/mutation_report.py target/pit-reports/mutations.xml <fqn.Cible> --src src/main/java
```

Pour chaque mutant non tué :

| Statut | Cause habituelle | Action |
|---|---|---|
| `NO_COVERAGE` | ligne jamais exécutée | revenir à 5a |
| `SURVIVED` sur une condition (`<` → `<=`, négation) | valeur limite absente | ajouter la borne exacte à l'axe |
| `SURVIVED` sur une valeur de retour ou un appel supprimé | sortie ou effet de bord non imprimé | compléter l'impression (champ, interaction, argument modifié) |
| `SURVIVED` sans effet observable possible | mutant équivalent | justifier dans le rapport |

À chaque ajout d'entrées, le fichier approuvé change : c'est autorisé **uniquement** si `git diff --stat -- src/main` est vide. Relire le nouveau `received`, ré-approuver, committer.

## Étape 6 — Rapport et proposition de refactoring

S'arrêter là et présenter à l'utilisateur :

```markdown
## Golden master — <Cible>
- Test : <Cible>GoldenMasterTest (N combinaisons, M méthodes de test) — branche test/golden-master-<cible>
- Couverture : lignes X/Y, branches X/Y (manques justifiés : …)
- Mutation : K/T mutants tués (survivants justifiés : …)

### Comportements suspects figés (non corrigés)
| Cas | Comportement actuel | Pourquoi suspect |
|---|---|---|
| bookKey null | NullPointerException | levée avant le contrôle métier NoActiveEdition |

### Proposition de refactoring (petits pas, golden master relancé après chacun)
1. …

### Après le refactoring
Écrire des tests unitaires métier lisibles (un comportement = un test nommé), corriger les comportements suspects validés,
puis supprimer le golden master, son fichier approuvé et le profil Maven `golden-master`.
```

Ne pas commencer le refactoring sans demande explicite de l'utilisateur.

## Ressources

| Fichier | Contenu |
|---|---|
| `references/approvaltests.md` | Dépendance, API (`verify`, `CombinationApprovals`, `Options`, reporters, scrubbers), emplacement des fichiers |
| `references/axes-et-impression.md` | Trouver les axes, choisir les valeurs, maîtriser l'explosion, écrire une impression déterministe |
| `references/services-et-dependances.md` | Services Spring : mocks enregistreurs, horloge, aléatoire, statiques, `@Value` |
| `references/verification-maven.md` | Profil Maven JaCoCo + PIT, commandes, multi-module, pièges |
| `references/exemple-book-dto-mapper.md` | Exemple complet sur `BookDtoMapperFromFeedUtils` |
| `scripts/coverage_report.py` | Extrait de `jacoco.xml` les lignes et branches manquées de la cible |
| `scripts/mutation_report.py` | Extrait de `mutations.xml` les mutants non tués de la cible |

Les scripts n'utilisent que la bibliothèque standard Python 3.8+. Après modification, lancer `python3 scripts/selftest.py`.
