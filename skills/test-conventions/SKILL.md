---
name: test-conventions
description: "Conventions de tests unitaires et d'acceptation propres à une pile technique : Java / Spring Boot (JUnit 5, AssertJ, Mockito, tests sans contexte Spring), Angular (Jest ou Jasmine, TestBed, Angular Testing Library) et TypeScript (Vitest ou Jest, React Testing Library, adaptateurs en mémoire, couche d'automatisation des tests d'acceptation). À utiliser avant d'écrire le premier test dans un dépôt, ou quand on se demande comment nommer, organiser ou outiller un test dans une pile donnée. Ne remplace pas les conventions déjà en place dans le dépôt."
---

# Conventions de test par pile

Ce qui ne dépend pas de la pile a sa place ailleurs : le cycle TDD dans l'agent qui écrit le code (ou la skill `tdd`) ; ce qui fait un bon test, où tester une règle et les doubles de test dans la skill `unit-tests` ; les tests d'acceptation et de bout en bout dans leurs skills (`acceptance-tests`, `e2e-tests`). Cette skill ne donne que ce qui change d'une pile à l'autre.

1. **Repérer la pile** : `pom.xml` ou `build.gradle` (Java), `angular.json` (Angular), `package.json` avec `vitest`, `jest` ou `react` (TypeScript).
2. **Lire la référence** qui correspond :

   | Pile | Référence |
   |---|---|
   | Java / Spring Boot | `references/java-spring.md` |
   | Angular / TypeScript | `references/angular.md` |
   | TypeScript (Vitest ou Jest, React, Node, Electron) | `references/typescript.md` |

3. **La convention du dépôt prime.** Regarder quelques tests représentatifs : quand le dépôt fait autrement que la référence (nommage, emplacement, framework), suivre le dépôt, et consigner ce qu'il fait dans la mémoire de l'agent qui écrit le test. Une pile absente de cette liste se traite de la même façon : les conventions du dépôt, puis celles de la communauté du langage.
