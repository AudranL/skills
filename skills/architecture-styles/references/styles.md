# Les styles

## N-tiers (couches)

Présentation → métier → accès aux données. Simple et connu de tous. Risques : le métier dépend de la base, les couches sont contournées (un contrôleur qui appelle directement un repository : « relaxed layered architecture », Simon Brown, *Clean Architecture*, ch. 34), la logique fuit vers l'interface. Convient à une application surtout CRUD, avec peu de règles et peu d'intégrations.

## Hexagonale (ports & adapters)

La référence est l'article d'Alistair Cockburn : https://alistair.cockburn.us/hexagonal-architecture. En cas de doute sur un point, le relire plutôt que se fier aux interprétations.

- **Intention** : l'application peut être pilotée aussi bien par des utilisateurs que par des programmes, des tests automatisés ou des scripts, et se développe et se teste isolée de ses bases de données et équipements. « Create your application to work without either a UI or a database. »
- **La frontière qui compte est intérieur / extérieur**, pas gauche / droite ni haut / bas.
- **Port** : une conversation qui a un but, définie par une API dans les termes de l'application. **Adapter** : traduit une technologie (UI, HTTP, SQL, test, mémoire) vers ce port.
- **Côté primaire** (*driving*) : les acteurs qui pilotent l'application (utilisateur, API, batch, test). **Côté secondaire** (*driven*) : ce que l'application pilote (base, service externe, messagerie).
- **Nombre de ports** : une affaire de jugement, souvent deux à quatre. Pas un port par classe ni par table ; le chiffre six n'a rien d'important.
- **Tests** : un test remplace un acteur primaire ; un adapter en mémoire remplace un acteur secondaire. Cockburn décrit une progression : d'abord des tests avec des valeurs en dur, puis l'interface, puis un adapter en mémoire, remplacé ensuite par la vraie base.
- **Les cas d'utilisation s'écrivent à la frontière de l'application**, sans détail de technologie.
- Vernon emploie « port » et « adapter » autrement : voir « Vocabulaires qui divergent » dans `SKILL.md`.

## Onion

Jeffrey Palermo : des anneaux concentriques, avec le modèle du domaine au centre, puis les services du domaine, les services applicatifs, et à l'extérieur l'UI, l'infrastructure et les tests. Toutes les dépendances vont vers le centre. Plus prescriptif que l'hexagonale sur l'intérieur.

## Clean Architecture

Martin, ch. 22 : entités, cas d'utilisation, adaptateurs d'interface, frameworks et pilotes. La règle de dépendance : aucun nom d'un cercle extérieur n'apparaît dans un cercle intérieur. Pour franchir une frontière à contre-courant du flux de contrôle, inversion de dépendance : le cas d'utilisation appelle une interface qu'il possède (port de sortie), implémentée à l'extérieur. Ce qui traverse une frontière, ce sont des structures de données simples, pas des entités ni des objets de framework.

## Contextes bornés

Evans (*Domain-Driven Design*, ch. 14), Vernon (*Implementing DDD*, ch. 2 et 3). C'est un découpage **vertical** par modèle métier, indépendant du style : chaque contexte a sa propre architecture interne (son hexagone).

- Pas de dépendance entre les domaines de deux contextes.
- Le noyau partagé (*shared kernel*) reste petit et explicite ; un package `common` ou `shared` qui grossit est un signal d'alerte.
- Deux contextes se parlent par leurs adapters, pas par leurs domaines (l'adapter secondaire de A appelle un adapter primaire de B), à travers un contrat déclaré : un langage publié (types, schéma, messages), stable et distinct du modèle interne de chacun, que chaque côté traduit (Evans, *Domain-Driven Design*, ch. 14 « Published Language » : « do not equate the interchange language and the model of the host »).
- **Lire une frise d'événements** : une frontière de contexte se cherche aux événements charnières entre deux phases du métier, entre des couloirs parallèles, là où un mot change de sens et là où les experts changent ; un agrégat, autour d'une règle qui doit être vraie à l'instant (Brandolini, *Introducing EventStorming*, « Discovering Bounded Contexts with EventStorming »). Ce qu'on en tire reste une hypothèse à faire valider.
- Le modèle d'un système externe s'arrête à la frontière : couche anticorruption (Evans, ch. 14) avec une traduction explicite vers le modèle du domaine.

## Microservices

Ce n'est pas un style de code mais une décision de déploiement et d'organisation (*Microservice Architecture*, Nadareishvili et al. ; *The Hard Parts*). À ne proposer que pour un besoin réel : déploiement indépendant, montée en charge différenciée, équipes autonomes. Le risque principal est le monolithe distribué : la complexité des services distribués sans leur indépendance.

- **Chaque service a sa propre base, qu'il est seul à lire et à écrire.** Cela vaut entre services déployés séparément (microservices) ; partager un même serveur de base reste possible si chaque service a son propre schéma. Le propriétaire d'une donnée est le service qui l'écrit. Pour la modifier, un autre service le demande au propriétaire : appel à son API s'il attend une réponse, message sinon. Pour la lire : appeler l'API du propriétaire, ou tenir sa propre copie (colonnes ou cache répliqués) que le propriétaire met à jour par événements, réservée aux données stables et peu volumineuses. Deux services qui écrivent la même table : un seul en devient propriétaire, l'autre lui délègue ses écritures. Seule exception, consignée dans un ADR : un schéma partagé par plusieurs services (domaine de données), quand la cohérence ou le volume l'imposent ; le schéma devient alors le contrat, et chaque changement touche tous ces services (Ford et al., *Software Architecture: The Hard Parts*, ch. 9 « Data Ownership and Distributed Transactions » et ch. 10 « Distributed Data Access » ; Nadareishvili et al., *Microservice Architecture*, ch. 5).
