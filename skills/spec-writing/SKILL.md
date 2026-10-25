---
name: spec-writing
description: "Découpe une fonctionnalité en fonctionnalités livrables et rédige la fiche de spécification d'une fonctionnalité : carte de la fonctionnalité, INVEST, fonctionnalités verticales et fermées, walking skeleton, revue du découpage quand le périmètre change ; règles, exemples et questions (Example Mapping), système externe pris par son contrat, ce qui n'est pas spécifié ; scénarios Gherkin déclaratifs (un comportement par scénario, refus écrit par son effet, « seulement » écrit aussi en négatif, pas de plan pour gagner des lignes, langue des .feature) ; modèle de fiche et emplacement. À charger avant de proposer ou de revoir un découpage, et avant d'écrire, de compléter ou de corriger les scénarios ou la fiche d'une fonctionnalité ; à lire aussi pour proposer un scénario dans le style d'une fiche ou nommer le test d'un scénario."
---

# Découper et spécifier une fonctionnalité

Une fiche donne à celui qui développe le contexte précis dont il a besoin pour une fonctionnalité, et rien de plus. Elle se lit par un agent dont le contexte est limité : courte, sans répétition ni historique de la discussion, avec des scénarios qui disent tout ce que la fonctionnalité fait.

## Le déroulé

1. **Découper** avant de spécifier, quand la fonctionnalité demandera plusieurs fonctionnalités ou que le périmètre grossit : `references/decoupage.md`. Le découpage se fait valider par l'utilisateur ; seule la fonctionnalité suivante se spécifie.
2. **Règles, exemples, questions** pour la fonctionnalité retenue (ci-dessous).
3. **Les scénarios Gherkin** : `references/gherkin.md`.
4. **La fiche**, son modèle et son emplacement : `references/modele-de-fiche.md`. Elle renvoie aux besoins non fonctionnels qu'elle touche par leur identifiant (skill `spec-review`).

## Règles, exemples, questions

Pour la fonctionnalité retenue, travailler en trois listes (méthode dite *Example Mapping*, de Matt Wynne) :

- les **règles métier** (« un client fidèle a une remise de 10 % ») ;
- pour chaque règle, des **exemples concrets** avec des valeurs réelles, dont au moins un contre-exemple ou un cas limite ;
- les **questions** auxquelles personne ne sait répondre maintenant.

Signaux pour le découpage :

- beaucoup de règles (au-delà de quatre ou cinq) : la fonctionnalité est trop grosse, la redécouper ;
- beaucoup de questions : la fonctionnalité n'est pas prête, il faut d'abord trouver les réponses (ou une investigation).

**Système externe : partir de son contrat.** Les cas d'un système externe (réponses, erreurs) se spécifient à partir de son contrat documenté ; le demander à l'utilisateur s'il n'est pas dans le dépôt. Un code ou un cas que le contrat ne documente pas n'a pas de scénario dédié : demander quel traitement par défaut lui appliquer plutôt que d'en inventer un.

**Ce qui n'est pas spécifié est une autre fonctionnalité.** La fonctionnalité fait ce que disent ses scénarios, rien de plus. Quand un exemple fait surgir un cas que personne n'a demandé (un changement en cours de route, une variante, un « et si… »), poser la question à l'utilisateur avec une recommandation, sans écrire de scénario « au cas où ». S'il le priorise maintenant, le cas entre dans la fonctionnalité avec ses scénarios. Sinon, la fiche le range dans « Plus tard » ou « Hors sujet », sans rien construire pour lui, et la question et la réponse vont dans les notes du ticket de la fonctionnalité concernée (un nouveau ticket à cadrer s'il n'y en a pas). Ce qui sort ainsi, c'est un comportement nouveau, jamais le cas limite ou le refus d'une règle de la fonctionnalité. Une story n'est spécifiée que quand ses tests d'acceptation sont écrits (Martin, *Clean Agile*, ch. 3 « Acceptance Tests ») ; une bonne idée venue en cours de route se propose à celui qui priorise, pour une itération suivante (Cohn, *User Stories Applied*, ch. 14 « Goldplating »).

## Avant de remettre la fiche

- chaque règle a au moins un scénario nominal et un cas limite ou d'échec ;
- les termes sont ceux du métier, définis dans « Vocabulaire » s'ils sont ambigus, avec en regard le mot du code quand il diffère ;
- les questions ouvertes sont listées, avec l'hypothèse retenue en attendant ;
- une section vide est supprimée, pas remplie de « N/A » ;
- le bloc `gherkin` peut se copier tel quel dans un fichier `.feature`.
