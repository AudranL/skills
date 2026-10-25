# ArchUnit (Java, Kotlin)

Guide utilisateur : https://www.archunit.org/userguide/html/000_Index.html

## Mise en place

- Dépendance `com.tngtech.archunit:archunit-junit5`, scope `test`. C'est une nouvelle dépendance de build : accord de l'utilisateur.
- Emplacement : la convention du projet ; sinon, proposer un package `architecture` sous la racine des tests.
- Modèles de référence, à adapter et non à copier : `HexagonalArchTest` de jhipster-lite (https://github.com/jhipster/jhipster-lite/blob/main/src/test/java/tech/jhipster/lite/HexagonalArchTest.java), et `AnnotationArchTest` pour les conventions de tests.

## Marquer l'architecture dans le code

Les tests s'appuient sur des **annotations de marquage** plutôt que sur des noms de packages ou de classes : un contexte, un port ou un adapter se déclare, il ne se devine pas. L'annotation documente aussi le rôle de la classe pour le lecteur. Deux options, à trancher dans un ADR :

1. **Annotations propres au projet** (par exemple dans un package `annotations` à la racine du code) : `@BoundedContext` et `@SharedKernel` sur `package-info.java`, `@PrimaryPort`, `@SecondaryPort`, `@PrimaryAdapter`, `@SecondaryAdapter` sur les types, plus des notions du domaine (`@DomainObject`, `@DomainService`, `@DomainEvent`, `@AntiCorruptionLayer`).
    - Pour : aucune dépendance externe, le vocabulaire de l'équipe, une Javadoc qui explique chaque notion. Les annotations peuvent aussi porter de la configuration (par exemple, méta-annoter `@SecondaryAdapter` avec `@ProductionScope` pour choisir l'implémentation selon l'environnement).
    - Contre : les règles ArchUnit sont à écrire et à maintenir soi-même.
2. **jMolecules** (https://github.com/xmolecules/jmolecules) : des annotations standard (`org.jmolecules.ddd.annotation.BoundedContext`, `org.jmolecules.architecture.hexagonal.PrimaryPort`, `SecondaryAdapter`…, et l'équivalent pour onion et couches), avec des règles ArchUnit toutes faites dans `org.jmolecules.integrations:jmolecules-archunit` : `JMoleculesArchitectureRules.ensureHexagonal()`, `ensureOnionSimple()`, `ensureOnionClassical()`, `ensureLayering()`, et `JMoleculesDddRules.all()`.
    - Pour : un vocabulaire partagé au-delà de l'équipe, des règles prêtes et maintenues, reconnues par d'autres outils (Spring Modulith, documentation générée).
    - Contre : une dépendance externe dans le domaine (des annotations seulement, sans dépendance transitive), pas d'équivalent direct au noyau partagé, des règles moins fines que celles écrites à la main.

Les deux se combinent : les annotations jMolecules pour les rôles standard, des règles du projet pour ce qu'elles ne couvrent pas (noyau partagé, communication entre contextes).

Règles qui en découlent : une annotation de marquage a une rétention `RUNTIME` si un test la lit par réflexion (comme `package-info.java`) ; une règle vérifie que chaque classe qui ressemble à un port ou un adapter (nom, package) porte bien l'annotation, sinon une classe non annotée échappe aux tests.

## Les règles habituelles en ArchUnit

- **Contextes bornés et noyaux partagés repérés par annotation** sur `package-info.java` (`@BoundedContext`, `@SharedKernel`) plutôt que listés en dur : un nouveau contexte est couvert sans toucher au test.
- **Par contexte**, une `layeredArchitecture().consideringOnlyDependenciesInAnyPackage(contexte + "..").withOptionalLayers(true)` : domaine, application, adapters primaires, adapters secondaires ; les adapters ne sont appelés par aucune couche (`mayNotBeAccessedByAnyLayer`).
- **Le domaine** ne dépend que de lui-même, de `java..`, des noyaux partagés et de la liste courte d'utilitaires décidée dans l'ADR.
- **Onion** : `Architectures.onionArchitecture()`.
- **Pas de cycle** : `slices().matching("<racine>.(*)..").should().beFreeOfCycles()`.

## Bonnes pratiques

- **Un seul mécanisme par classe de test** : soit des méthodes `@Test` qui appellent `.check(classes)`, soit `@AnalyzeClasses` avec des champs ou méthodes `@ArchTest`. Une méthode `@ArchTest` dans une classe sans `@AnalyzeClasses` n'est jamais exécutée, et le test passe en silence.
- **Import des classes une seule fois**, en champ statique, sans les tests (`ImportOption.Predefined.DO_NOT_INCLUDE_TESTS`).
- **`because(…)`** en langage clair, qui renvoie à la règle (`A-002`) ou à l'ADR.
- **Pas d'`allowEmptyShould(true)` par réflexe** : par défaut, ArchUnit échoue quand une règle ne s'applique à aucune classe, ce qui révèle un package mal nommé. Ne l'autoriser que pour une convention pas encore utilisée, et le dire.

## Geler les violations existantes

`FreezingArchRule.freeze(regle)` :

- Au premier passage, ArchUnit enregistre les violations actuelles dans un fichier, configuré dans `src/test/resources/archunit.properties` : `freeze.store.default.path`, et `freeze.store.default.allowStoreCreation=true` pour autoriser sa création.
- Ensuite, le test n'échoue que sur une violation **nouvelle**. Une violation corrigée sort du fichier et ne peut plus revenir : le nombre de violations ne peut que baisser.
- Le fichier se versionne. Le régénérer (`freeze.refreeze=true`) pour faire passer un test revient à affaiblir un test : jamais sans l'accord de l'utilisateur.
