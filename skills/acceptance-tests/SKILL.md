---
name: acceptance-tests
description: "Tests d'acceptation tirés des scénarios Gherkin d'une fiche (boucle externe de l'ATDD) et revue d'acceptation d'une fonctionnalité livrée : un test par scénario, à son titre, qui exerce son « Quand » et vérifie chaque partie de son « Alors », au plus haut niveau qui évite l'interface (cas d'utilisation avec des doubles aux frontières, ou l'adapter) ; étapes minces sur une couche d'automatisation dans le vocabulaire du domaine ; Gherkin exécutable comme dépendance de build ; reprise d'un code écrit avant son test ; critères couvert, mal couvert, non couvert. À charger avant d'écrire le premier test d'acceptation d'une fiche, avant de reprendre du code de production écrit avant son test, ou pour relire une fonctionnalité livrée et dire si chaque scénario est couvert."
---

# Tests d'acceptation

Chaque scénario de la fiche a son test d'acceptation, écrit avant le code de production qu'il guide. Le même critère sert à celui qui l'écrit et à celui qui relit la fonctionnalité livrée : `references/revue-d-acceptation.md`.

## Un test par scénario

- **Il porte le titre du scénario** et suit son Étant donné / Quand / Alors : une recherche du titre trouve son test. Un plan du scénario donne un test par ligne d'exemples, sous le titre du plan.
- **Il exerce son « Quand »** : l'action du scénario est jouée par le test, pas seulement l'état qui la précède.
- **Il vérifie chaque partie de son « Alors »**, y compris la valeur qui distingue ce scénario des autres (une date limite, deux montants égaux).
- **Un « Et … n'est pas présenté » se vérifie sur la liste complète** de ce qui est présenté (« Alors le panier présente le stylo et le cahier Et la gomme, indisponible, n'y est pas présentée » : la liste est exactement le stylo et le cahier), jamais par un « ne contient pas » ni sur une liste filtrée, qui laisseraient passer un élément de trop. Ce « Et » remplace un « seulement », qui ne se vérifie pas tel quel.
- **Il se voit rouge pour la bonne raison** avant le code qui le fait passer. Seul un scénario que le code existant satisfait déjà (comportement hérité, scénario ajouté après coup) donne un test vert dès son écriture : le voir échouer en cassant exprès le code (une mutation à la main, aussitôt annulée en recopiant le fichier d'origine : `git checkout` effacerait ses changements non commités), et le dire dans le compte rendu.

## Son niveau

Il passe **au plus haut niveau qui évite l'interface** : les cas d'utilisation, avec des doubles aux frontières (test d'acceptation de domaine), ou l'adapter quand le scénario porte sur ce qu'il enregistre. Le bout en bout ne garde que ce qui demande la vraie application : parcours, persistance, présentation, câblage. Un scénario n'a pas à être rejoué de bout en bout : la règle se vérifie au plus près du code qui la porte.

## Sa forme

- **Les étapes restent minces** : elles traduisent le texte du scénario et appellent une couche d'automatisation écrite dans le vocabulaire du domaine (`uneBoutiqueEnMemoire().passerCommande({ … })`), qui monte les cas d'utilisation sur des adaptateurs en mémoire. Un libellé qui change ne se corrige qu'à un endroit.
- **Exécuter le texte Gherkin lui-même** (Cucumber, SpecFlow, jest-cucumber…) est une dépendance de build : la demander. Sans elle, le lien entre le scénario et son test se fait par le titre.
- **Le BDD se joue avant**, quand la fiche s'écrit : ne pas réécrire un scénario, signaler celui qu'on ne sait pas automatiser tel quel.
- **Ce qui dépend de la pile** (framework, emplacement, nommage) : la skill `test-conventions` si elle est installée, sinon les tests existants du dépôt.

## Reprendre un code écrit avant son test

Quand une reprise trouve du code de production qui précède son test d'acceptation (code non commité, ou écrit avant son test) : écrire le test, puis le lancer contre le code de production du dernier commit (`git stash push -- <fichiers de production>`, puis `git stash pop`). Il doit y être rouge pour la bonne raison. Seul un test encore vert à cet état passe par une mutation à la main. Le dire dans le compte rendu.
