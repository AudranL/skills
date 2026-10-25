---
name: architecture-styles
description: "Catalogue des styles d'architecture et de leurs compromis, et diagnostic d'une architecture existante : n-tiers, hexagonale selon Cockburn (port, adapter, côtés primaire et secondaire, divergence avec Vernon), onion, clean architecture, contextes bornés (langage publié entre deux contextes, lecture d'une frise d'événements, couche anticorruption), microservices et propriété des données ; questions à poser avant de choisir, dont la langue du code ; diagnostic d'un existant (constater, déduire et faire valider, consigner, réécrire ou faire évoluer). À charger avant de recommander, de comparer ou de faire évoluer un style, en cas de doute sur un terme (port, adapter, noyau partagé, contexte borné), pour proposer des contextes bornés et des agrégats à partir d'une frise d'événements, ou pour faire le diagnostic d'une architecture en place ou décider entre la réécrire et la faire évoluer."
---

# Styles d'architecture

Point commun (Martin, *Clean Architecture*, ch. 22) : séparer les règles métier des détails, et faire pointer les dépendances vers les règles métier. Les styles diffèrent surtout par le vocabulaire et le nombre de cercles. Dans un projet, on en choisit un, on le nomme dans un ADR, et on ne mélange pas les vocabulaires.

- **Les styles, un par un** : `references/styles.md` (n-tiers, hexagonale, onion, clean architecture, contextes bornés, microservices).
- **Le diagnostic d'un existant**, et le choix entre réécrire et faire évoluer : `references/diagnostic.md`.

## Choisir

Les questions à poser avant de recommander un style :

- Combien de règles métier, et vont-elles évoluer souvent ?
- Combien de systèmes externes, et risquent-ils d'être remplacés ?
- Qui pilote l'application : interface, API, batch, messages, autres applications ?
- Quelles qualités priment (testabilité, performance, disponibilité, sécurité, délai de livraison), avec quel seuil ?
- Quelles conventions existent déjà dans l'équipe ou l'entreprise, et que connaît l'équipe ?
- Dans quelle langue s'écrit le code (identifiants, fichiers, tests, commentaires, commits, messages) : quel est le public de l'application, et qui maintiendra le code ?

Toute recommandation se présente avec au moins deux options (souvent dont « ne rien changer »), les critères, les compromis de chacune et la recommandation : il n'y a pas de meilleure pratique, seulement la moins mauvaise combinaison de compromis (Ford, Richards et al., *Software Architecture: The Hard Parts*, ch. 1).

**Langue du code.** La faire décider explicitement au cadrage, ou à la première fonctionnalité d'un projet repris, sans la déduire de l'existant ni la supposer anglaise. Quand le métier et l'équipe parlent une autre langue que l'anglais, recommander par défaut d'écrire le code dans la langue du métier : traduire les termes du métier dans le code crée un second vocabulaire, et « translation blunts communication » (Evans, *Domain-Driven Design*, ch. 2 « Ubiquitous Language »). Un concept technique garde le nom usuel chez les développeurs (Martin, *Clean Code*, ch. 2 « Use Solution Domain Names »), et les termes imposés par le langage et les bibliothèques restent tels quels. La décision et ses conventions (périmètre, accents dans les identifiants et les noms de fichiers, termes imposés, coexistence avec le code existant) font l'objet d'un ADR.

## Vocabulaires qui divergent

- **Vernon** (*Implementing DDD*, ch. 4) appelle « port » le mécanisme technique (HTTP, AMQP) et « adapter » ce qui le traduit. On garde la définition de Cockburn : un port est une conversation qui a un but.
- **La skill `codebase-design`** (modules profonds) emploie « seam » au sens de Feathers (l'endroit où vit l'interface d'un module), « adapter » pour tout ce qui remplit une interface à une seam, et déconseille « boundary ». Ici, « frontière » désigne celle d'un contexte borné ou l'intérieur / extérieur de l'hexagone : préciser le sens quand les deux vocabulaires se croisent.

## Sources

L'article de Cockburn sur l'architecture hexagonale (https://alistair.cockburn.us/hexagonal-architecture), à relire en cas de doute plutôt que de se fier aux interprétations ; l'architecture onion de Jeffrey Palermo.
