---
name: unit-tests
description: "Écrire, relire et améliorer des tests unitaires, quelle que soit la pile : ce qui fait un bon test (F.I.R.S.T., un concept par test, un comportement plutôt qu'une méthode, lisible comme une spécification, aussi propre que le code de production, message d'échec clair, texte attendu cherché exact), où tester une règle (triangulée là où elle vit, un seul cas passant dans la classe qui l'utilise, une classe qui transmet a son test, pas de test qui passe dès son écriture), anti-patterns à refuser (test couplé à l'implémentation, tautologique, fonctionnalités horizontales), doubles de test (objets réels par défaut, doubles aux frontières, ne mocker que ses propres types, mocks pour découvrir un rôle, écouter les tests, Test Data Builder). À charger au début de toute tâche qui écrit, modifie ou relit des tests unitaires, avant d'en dresser la liste, et pour améliorer une suite de tests. Ce qui dépend de la pile est dans la skill test-conventions."
---

# Tests unitaires

Un test unitaire écrit avant le code le guide, puis le protège : il doit pouvoir échouer, et dire pourquoi quand il échoue. Ces règles ne dépendent pas de la pile. Le cycle TDD est décrit par l'agent qui l'applique (ou la skill `tdd`) ; les tests d'acceptation ont leur skill (`acceptance-tests`).

## Quand s'en servir

| Moment | Ce qui s'applique |
|---|---|
| En dressant la liste de tests d'une tâche | « Où tester une règle » : chaque cas va dans le test de la classe où vit sa règle |
| Au rouge, en écrivant le test | « Ce qui fait un bon test » et « Doubles de test » ; un test qui tombe dans l'un des « Anti-patterns à refuser » ne s'écrit pas |
| Au refactor | Le code de test se nettoie comme le code de production (skill `clean-code`, si elle est installée), sans perdre ces règles |
| Pour relire ou améliorer une suite de tests | Chaque test passe par « Ce qui fait un bon test », « Où tester une règle » et « Anti-patterns à refuser » |

## Ce qui fait un bon test

- **F.I.R.S.T.** : rapide, indépendant (ordre libre, pas d'état partagé), reproductible (pas de réseau, pas d'horloge réelle, pas d'aléatoire non maîtrisé), auto-validant (vert ou rouge, rien à lire à la main), écrit au bon moment (juste avant le code).
- **Un concept par test.** Plusieurs assertions sont acceptables si elles vérifient le même concept.
- **Teste un comportement, pas une méthode.** Le nom du test décrit ce que le système fait dans une situation donnée, pas la méthode appelée.
- **Lisible comme une spécification.** Structure Given / When / Then (ou Arrange / Act / Assert) visible, données de test significatives, rien d'inutile dans le test.
- **Le code de test a la même exigence de propreté que le code de production.** Des tests sales finissent abandonnés, et le code pourrit avec eux.
- **Un message d'échec clair.** Lire l'échec avant de faire passer le test ; utiliser des assertions qui expliquent l'écart.
- **Un texte attendu qui peut en prolonger un autre se cherche exact** (« à 16h » trouve aussi « à 16h30 », et le test ne peut plus échouer) : formes par pile dans la skill `test-conventions`.

## Où tester une règle

- **Une règle se triangule là où elle vit**, et seulement là (Beck, *TDD by Example*, ch. 28 « Triangulate » : « Abstract only when you have two or more examples »). Exemple : la correspondance entre codes du transporteur et étapes de livraison est triangulée dans le test de `CarrierParcelStatus`, pas dans celui du provider qui l'utilise.
- **La forme des exemples est un choix de lisibilité**, pas une règle : autant de tests que de cas, ou un `@ParameterizedTest` (`it.each` côté TypeScript). Les deux sont valables.
- **Une classe qui utilise une règle déjà testée** a un seul cas passant pour cette règle, plus les cas qui lui sont propres (erreurs, absence, cas limites de sa propre responsabilité). Ne pas rejouer tous les exemples de la règle à chaque couche : si la règle change, un seul test doit casser.
- **Une classe qui ne fait que transmettre** (un service qui délègue à un port, par exemple) a quand même son test unitaire : il couvre la transmission, et uniquement elle. En TDD, c'est ce test qui justifie l'existence de la classe ; un test d'acceptance ne le remplace pas.
- **Pas de test qui passe dès son écriture.** Un test qui n'a jamais été rouge n'a guidé aucune ligne de code (ex. un deuxième cas pour une classe qui ne fait que transmettre). Ne pas l'ajouter ; s'il semble utile comme documentation, le signaler à l'utilisateur au lieu de l'ajouter en silence. Exception : le test d'acceptation d'un scénario de la fiche que le code satisfait déjà s'écrit quand même (skill `acceptance-tests`). Le voir échouer en cassant exprès le code (une mutation à la main, aussitôt annulée en recopiant le fichier d'origine : `git checkout` effacerait ses changements non commités), puis le dire dans le compte rendu : un test jamais vu rouge peut ne rien vérifier.

## Anti-patterns à refuser

- **Test couplé à l'implémentation** : il mocke des collaborateurs internes, teste une méthode privée, ou vérifie par un canal détourné (requête en base au lieu de passer par l'interface). Symptôme : il casse lors d'un refactoring alors que le comportement n'a pas changé.
- **Test tautologique** : la valeur attendue est recalculée comme le fait le code (`expect(add(a, b)).toBe(a + b)`), il ne peut donc jamais échouer. La valeur attendue vient d'une source indépendante : un littéral connu, un exemple travaillé à la main, la spécification.
- **Fonctionnalités horizontales** : écrire tous les tests puis tout le code. La liste de tests se *note* d'avance, mais s'*implémente* un test à la fois.

## Doubles de test

Approche pragmatique :

- **Par défaut, des objets réels.** Les objets valeur et le code métier pur ne sont jamais mockés : on les instancie.
- **Des doubles aux frontières** : base de données, HTTP, messagerie, système de fichiers, horloge, aléatoire.
- **Ne mocker que les types que tu possèdes.** Pour une librairie tierce, créer un adaptateur (une interface à toi, dans le vocabulaire du domaine) et mocker cet adaptateur ; l'adaptateur réel est couvert par un test d'intégration.
- **Mocks pour explorer des rôles.** En outside-in, un mock sert à découvrir l'interface d'un collaborateur qui n'existe pas encore. On vérifie les interactions seulement quand elles *sont* le comportement attendu (une commande envoyée à l'extérieur), pas pour les requêtes.
- **Écouter les tests.** Un test difficile à écrire (setup énorme, mocks de mocks, besoin de rendre une méthode publique, outils de manipulation de bytecode) signale un problème de conception : corriger la conception plutôt que compliquer le test.
- Pour construire des objets complexes, écrire un **Test Data Builder** plutôt que de mocker un objet valeur.

## Selon la pile

Ce qui change d'une pile à l'autre (framework de test, nommage, tests sans framework applicatif, asynchrone, exemples) est dans la skill `test-conventions`. La convention en place dans le dépôt prime.
