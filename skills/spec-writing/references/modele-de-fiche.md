# Modèle de fiche

La fiche est lue par un agent dont le contexte est limité : **elle doit rester courte**, sans répétition entre les sections ni historique de la discussion. La concision porte sur la prose ; le Gherkin prend la place qu'il faut pour que chaque règle ait son cas nominal et ses cas limites. Le signal d'une fiche trop grosse est le nombre de règles (au-delà de quatre ou cinq), pas le nombre de lignes : redécouper la fonctionnalité. Une section vide est supprimée, pas remplie de « N/A ».

**Emplacement** : la convention du projet si elle existe (dossier `specs/`, `docs/specs/`…), sinon `docs/specs/<CLE-TICKET>-<slug>.md`, ou `docs/specs/<slug>.md` sans ticket. Hors d'un dépôt, demander où l'écrire.

**La fiche se lit seule** : celui qui développe ne lit ni la mémoire du product owner ni le backlog. Ce dont il a besoin pour la fonctionnalité est recopié dans la fiche (Vocabulaire, Contraintes connues). Elle peut renvoyer à un document que toute l'équipe lit (le fichier des besoins non fonctionnels, un contrat d'API du dépôt).

````markdown
# <CLE-TICKET> — <Titre de la fonctionnalité>

Ticket : <CLE-TICKET> · Jira : <CLE-JIRA ou « pas dans Jira »> · Fonctionnalité <n>/<total> · Statut : prête | questions ouvertes

## Pourquoi
<Le problème et l'objectif métier en 2 à 4 phrases. Le signal qui dira que c'est réussi.>

## Pour qui
<Rôle(s) concerné(s) et situation d'usage.>

## Périmètre
- Dans cette fonctionnalité : <…>
- Plus tard (fonctionnalités suivantes) : <…>
- Hors sujet : <…>

## Scénarios
```gherkin
# language: fr
Fonctionnalité: <titre>
  Pour <objectif métier>
  En tant que <rôle>
  Je veux <capacité>

  Règle: <règle métier 1>

    Scénario: <ce qui distingue ce cas>
      Étant donné <contexte métier>
      Quand <action>
      Alors <résultat observable>
```

## Vocabulaire
| Terme | Sens dans ce contexte |
|---|---|

## Questions ouvertes
- <Question> → <qui peut répondre, ou hypothèse retenue en attendant>

## Contraintes connues
<Seulement les contraintes réelles : système externe imposé, contrat existant, réglementation, et les besoins non fonctionnels que la fonctionnalité touche, par leur identifiant. Pas de conception.>
````

Le bloc `gherkin` doit pouvoir être copié tel quel dans un fichier `.feature`.
