---
name: e2e-tests
description: "Écrire, lancer et maintenir des tests de bout en bout (parcours joués sur l'application construite, de l'extérieur) qui ne dérangent personne et ne mentent pas : peu de parcours, chacun lisible comme son scénario (scénario, gestes dans les mots du métier, détails d'écran rangés à un seul endroit) ; viser par rôle et nom accessible ; texte exact quand un autre peut le prolonger ; attendre un effet, jamais une durée ; isolation (dossier de données temporaire, contexte neuf, réseau bloqué) ; sans fenêtre visible ni prise de focus ; parcours vu rouge ; captures vérifiées puis regardées ; parcours instable à comprendre plutôt qu'à relancer. Détails pour Playwright (navigateur et Electron), et une ligne pour Cypress et Selenium. À charger avant d'écrire le premier parcours de bout en bout d'un dépôt, avant d'en ajouter ou d'en réparer un, ou pour prendre des captures d'écran d'une application."
---

# Tests de bout en bout

Un test de bout en bout joue un parcours sur l'application telle qu'elle sera remise, de l'extérieur. Il coûte cher à écrire, il est lent et plus fragile que les autres : il vérifie les parcours principaux et le câblage, pas les règles, qui se vérifient plus bas (Smart, *BDD in Action*, ch. 9 ; Freeman & Pryce, *GOOS*, ch. 1 « Testing End-to-End » : des tests d'acceptation qui appelaient le code interne passaient alors que l'application ne faisait rien).

Les détails d'un outil : `references/playwright.md` (navigateur et Electron) ; pour les autres, `references/autres-outils.md`. La convention du dépôt prime : partir des parcours existants, puis de la documentation de l'outil.

## Un parcours se lit comme son scénario

- **Trois couches** : le scénario (son titre et ses étapes, ceux de la fiche) ; les gestes de l'utilisateur dans les mots du métier (« réserver un vélo ») ; les détails d'écran (rôles, libellés, sélecteurs), rangés à un seul endroit. Un libellé qui change ne se corrige qu'à cet endroit (Smart, *BDD in Action*, 7.3 « Separating the what from the how »).
- **Le titre du parcours est celui du scénario qu'il joue** : une recherche du titre trouve le parcours.

## Viser et vérifier

- **Viser un élément par son rôle et son nom accessible** (un bouton « Enregistrer », un champ « Adresse »), pas par une classe CSS, une position ou un identifiant technique. S'il manque un repère, le demander à celui qui écrit le code de production plutôt que de l'ajouter soi-même.
- **Un texte attendu se cherche exact quand un autre peut le prolonger** : « à 16h » se trouve aussi dans « à 16h30 », et le parcours ne peut plus échouer. Recherche exacte de l'outil ou expression ancrée (`/à 16h$/`).
- **Attendre un effet, jamais une durée.** Un parcours attend un changement visible (un texte, un état de l'écran, un fichier écrit) avec un délai maximal réglé à un seul endroit, jamais une pause fixe. Si l'état attendu est celui de départ (une liste vidée, un compteur revenu à zéro), attendre d'abord un signe que l'action a eu lieu : sinon le parcours passe avant que l'application ait agi (Freeman & Pryce, *GOOS*, ch. 27 « Testing Asynchronous Code » : « Wait for Success », « Runaway Tests »).
- **Un parcours qui échoue de temps en temps est à comprendre, pas à relancer** : il peut cacher un vrai défaut (*GOOS*, ch. 27 « Beware of Flickering Tests »).

## Ne déranger personne

- **Sans fenêtre visible, sans prise de focus** : l'application se lance dans le mode prévu pour les tests (fenêtre cachée), jamais de façon à recevoir les frappes de l'utilisateur. Le parcours échoue si une fenêtre de l'application reste visible à la fin. Si l'application n'a pas ce mode, le demander avant le premier parcours.
- **Jamais les données de l'utilisateur** : un dossier de données temporaire par test, créé puis effacé ; un contexte neuf par test (pas de session ni de stockage partagés) ; le réseau bloqué, sauf ce que le parcours doit appeler.
- **Sur l'application construite** comme elle sera remise (installateur, paquet, image), pas sur le serveur de développement.

## Pas de faux vert

- **Voir rouge** : un parcours écrit sur un comportement déjà livré se voit échouer, sur le build d'avant ou par une mutation à la main faite dans une copie temporaire du dépôt (`git worktree add`, retirée ensuite), et on le dit. Pas dans la copie de travail : d'autres y écrivent, et un `git checkout` pour annuler y effacerait les changements non commités.
- **Une capture vérifie d'abord ce qu'elle montre** (un texte attendu), animations désactivées, puis elle est regardée avant d'être remise : une capture que personne n'a regardée peut mentir. Son nom dit le scénario qu'elle montre.
