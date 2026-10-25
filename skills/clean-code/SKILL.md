---
name: clean-code
description: "Règles pour écrire, refactorer et relire du code, de production comme de test, quelle que soit la pile : les quatre règles du Simple Design dans leur ordre (et quand extraire une constante ou une méthode), nommage (intention, un mot par concept, vocabulaire du métier, nom lu à l'endroit de l'appel), fonctions (petites, une seule chose, pas d'argument booléen, séparation commande-requête), commentaires (le pourquoi), erreurs (exceptions métier, pas de null), conception (SOLID, tell don't ask, dépendances explicites, objets valeur, modèle d'un système externe gardé à la frontière, adaptateur limité au contrat documenté), catalogue des code smells avec le refactoring qui traite chacun, et relecture de code (bloquant, important, suggestion). À charger au début de toute tâche qui écrit, modifie, nettoie ou relit du code : ses règles servent dès le premier test du cycle TDD, à chaque refactor et à chaque relecture."
---

# Clean Code

Du code qui marche, qui révèle son intention, et que le prochain développeur peut changer sans peur (Beck, les quatre règles du Simple Design ; Martin, *Clean Code*, ch. 2 « Meaningful Names », ch. 3 « Functions », ch. 4 « Comments » et ch. 7 « Error Handling » ; Fowler, *Refactoring*, ch. 3 « Bad Smells in Code »). Ces règles valent pour toutes les piles et pour le code de test comme pour le code de production.

## Quand s'en servir

| Moment | Ce qui s'applique |
|---|---|
| Au rouge du cycle TDD : le test invente l'interface du code qui n'existe pas encore | « Nommage » pour les classes et les méthodes qu'il appelle, « Conception » pour leurs dépendances et leurs types |
| Au vert : le moins de code qui fait passer le test, même imparfait (*fake it*) | Rien de plus : ce qu'il laisse de duplication ou de maladresse se traite au refactor, juste après |
| Au refactor, tests verts | « Simple Design » dans son ordre ; pour y arriver, toutes les autres sections, et les « Code smells » avec le refactoring qui traite chacun, à petits pas, tests relancés après chaque pas |
| Pour nettoyer ou restructurer du code hors d'un cycle TDD | La même chose, seulement sous des tests verts ; du code sans tests se sécurise d'abord (skill `legacy-code`, si elle est installée) |
| Pour relire du code | « Relecture de code » |

## Simple Design (Kent Beck), par ordre de priorité

1. Passe tous les tests.
2. Révèle l'intention.
3. Ne contient pas de duplication (de connaissance, pas seulement de lignes).
4. Contient le moins d'éléments possible.

La règle 4 passe en dernier : pas d'interface pour chaque classe, pas d'abstraction « au cas où ».

Une constante ou une méthode privée utilisée une seule fois n'est extraite que si son nom dit quelque chose que l'endroit de l'appel ne dit pas déjà. Sinon, la valeur reste en ligne (`formatPrice(total, "EUR")`) ou devient une variable locale bien nommée.

## Nommage

- Un nom révèle l'intention : pourquoi la chose existe, ce qu'elle fait, comment l'utiliser. Si un nom a besoin d'un commentaire, il est mauvais.
- Noms prononçables et cherchables, pas d'abréviations obscures, pas de bruit (`Data`, `Info`, `Manager`, `Impl`).
- Un mot par concept dans tout le code (pas de `fetch`, `get` et `retrieve` pour la même idée).
- Le vocabulaire du domaine métier dans le code (langage omniprésent). Un terme technique (`id`, `status`, `flag`) n'entre pas dans le domaine parce qu'une API externe l'emploie : on cherche le mot du métier (ex. l'*étape* d'une livraison, pas son `statusId`). En cas de doute, demander à l'utilisateur.
- Classes : des noms. Booléens : `is…`, `has…`, `can…`. Méthodes : des verbes par défaut, mais **un nom se lit à l'endroit de l'appel** : il complète la phrase commencée par le nom de la classe ou du champ, sans répéter ce qu'ils disent déjà (`getDeliveryStepService.forParcel(reference)`, `deliveryStepProvider.provideFor(reference)` plutôt que `getDeliveryStepService.getDeliveryStep(reference)`). Attention aux mots réservés du langage (`for`, `new`, `default`…).

## Fonctions

- Petites. Une seule chose. Un seul niveau d'abstraction par fonction.
- Un ou deux niveaux d'indentation au plus ; le corps d'un `if` ou d'une boucle est idéalement un appel de fonction bien nommé.
- Peu d'arguments ; pas d'argument booléen qui change le comportement (deux fonctions à la place).
- Séparation commande / requête : une fonction modifie un état **ou** renvoie une valeur, pas les deux.
- Pas d'effet de bord caché.

## Commentaires

- S'expliquer dans le code d'abord : extraire une méthode au nom explicite plutôt que commenter un bloc.
- Commentaires acceptés : le *pourquoi* d'une décision non évidente, un avertissement, une contrainte externe, la Javadoc / TSDoc d'une API publique.
- Pas de code commenté, pas de commentaire qui répète le code, pas de journal de modifications.

## Erreurs

- Exceptions plutôt que codes de retour ; exceptions métier nommées d'après le problème.
- Ne pas renvoyer `null` ni passer `null` : `Optional` en Java pour une absence attendue, objet vide ou exception sinon ; `strictNullChecks` côté TypeScript.
- La gestion d'erreur est une responsabilité : un `try` est la première instruction de sa fonction.

## Conception

- **SOLID.** En particulier SRP au sens « une seule raison de changer, un seul acteur », et DIP : le code métier ne dépend pas des détails techniques (base, HTTP, framework), ce sont les détails qui dépendent du métier.
- **Tell, don't ask.** Donner des ordres aux objets plutôt que tirer leurs données pour décider à leur place.
- **Dépendances explicites**, injectées par le constructeur. Pas de singleton ni d'état global caché. Le temps (`Clock`) et l'aléatoire sont des dépendances.
- **Objets valeur immuables** pour les concepts du domaine (montant, email, identifiant) plutôt que des types primitifs.
- **Le modèle d'un système externe reste à la frontière** (*anticorruption layer*, Evans, *Domain-Driven Design*, ch. 14). Ses champs, ses codes et ses valeurs (ex. les codes de statut de l'API d'un transporteur) vivent dans l'adaptateur d'infrastructure, avec leur propre type (ex. `CarrierParcelStatus`) et une traduction explicite vers le type du domaine (ex. `DeliveryStep`). Le type du domaine ne contient que ce qui a du sens pour le métier : il peut regrouper plusieurs valeurs externes en une seule (ex. les codes 20, 30, 40 et 50 → `IN_TRANSIT`). Face à une donnée externe, se demander, et demander à l'utilisateur si besoin : concept métier ou détail du fournisseur ?
- **Un adaptateur ne traite que le contrat documenté du système externe.** Chaque réponse documentée a sa branche et son test ; un code ou une forme de réponse non documentés n'ont ni branche, ni liste de codes, ni test : ils suivent le chemin par défaut le plus simple (en général l'erreur technique). Si le contrat manque, le demander plutôt que de deviner les cas.

## Code smells

Méthode longue, classe trop grosse, longue liste de paramètres, duplication, envie de fonctionnalité (feature envy), groupes de données qui voyagent ensemble (data clumps), obsession des primitifs, `switch` répétés sur le même type, changements divergents, chirurgie au fusil à pompe, code mort, généralité spéculative, commentaires qui compensent du code obscur.

Pour chaque smell trouvé : nommer le smell, nommer le refactoring (Extract Method, Introduce Parameter Object, Replace Conditional with Polymorphism, Move Method…), l'appliquer à petits pas, tests verts à chaque pas. Préférer les refactorings automatiques de l'IDE quand ils existent.

## Relecture de code

Quand on te demande une revue, classer les remarques par importance :

1. **Bloquant** : bug, comportement non couvert par un test, test qui ne peut pas échouer, faille de sécurité.
2. **Important** : conception (responsabilités mélangées, dépendance dans le mauvais sens, couplage), test fragile ou illisible.
3. **Suggestion** : nommage, petite duplication, style.

Pour chaque remarque : l'endroit (`fichier:ligne`), le problème, le principe ou le smell concerné, et une proposition concrète (extrait de code si utile). Signaler aussi ce qui est bien fait.

Des tests relus se jugent aussi avec la skill `unit-tests` (ce qui fait un bon test, anti-patterns à refuser), si elle est installée.
