---
name: architecture-review
description: "Revue d'architecture d'un diff, d'une branche ou d'une fonctionnalité livrée : sens des dépendances, domaine libre de tout framework, modèle d'un système externe gardé dans son adapter, règles métier dans le domaine, ports qui sont des conversations, dépendances entre contextes, tests d'architecture non affaiblis et violations gelées qui n'ont pas grossi, nouvelle dépendance de build justifiée par un ADR ; classement des remarques (bloquant, important, suggestion) et leur forme ; dette hors périmètre ; dette proposée au product owner comme une fonctionnalité. À charger pour toute revue d'architecture d'un changement de code, ou pour transformer une dette d'architecture en fonctionnalité."
---

# Revue d'architecture

Relire un diff ou une branche sous l'angle de l'architecture, sans modifier le code : celui qui a développé corrige.

## Ce qu'on vérifie

- le sens des dépendances, et que le domaine reste libre de tout framework, annotation de persistance ou objet d'API externe ;
- que le modèle d'un système externe reste dans son adapter, avec une traduction explicite ;
- que chaque règle métier vit dans le domaine, pas dans un contrôleur ni un adapter ;
- que les ports correspondent à une conversation, dans le vocabulaire du domaine, pas à une table ou à une classe ;
- qu'aucune dépendance entre contextes ne passe hors du chemin prévu ;
- que les tests d'architecture sont verts, qu'aucune règle n'a été affaiblie et que le fichier des violations gelées n'a pas grossi ;
- qu'une nouvelle dépendance de build est justifiée par un ADR.

## Les remarques

Classer chaque remarque :

- **bloquant** : règle confirmée violée, test d'architecture affaibli ;
- **important** : dépendance dans le mauvais sens non encore couverte par un test, modèle externe qui fuit ;
- **suggestion** : le reste.

Pour chacune : l'endroit (`fichier:ligne`), la règle (son identifiant, l'ADR ou le principe), une proposition concrète. Signaler aussi ce qui est bien fait.

Une dette repérée hors du périmètre de la fonctionnalité se consigne comme dette, sans bloquer la fonctionnalité.

## De la dette à une fonctionnalité

Quand une dette coûte (bugs à répétition, fonctionnalités ralenties, tests impossibles à écrire), proposer au product owner une fonctionnalité formulée par ce qu'elle apporte (« livrer les évolutions du catalogue sans toucher à la facturation »), pas par la technique (« refactorer le module X »). Le product owner décide de sa place.
