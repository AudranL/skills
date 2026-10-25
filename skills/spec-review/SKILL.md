---
name: spec-review
description: "Relecture d'une fiche de spécification avant le développement, à trois (les « trois amigos » : product owner, architecte, testeur) : angle architecture (qualités implicites rendues mesurables, systèmes externes, ce que l'existant porte déjà, contextes bornés, incertitude technique, versions livrées et migrations, découpage, walking skeleton), angle tests (chemins qui échouent, tous les chemins vers une action refusée, besoins non fonctionnels touchés, parcours principal), besoins non fonctionnels (gabarit mesurable, qui les propose, qui les fixe, qui les challenge, les valide et les vérifie) et, côté product owner, l'intégration ou l'écart de chaque remarque. À charger pour relire une fiche sous l'angle de l'architecture ou des tests, pour intégrer les remarques des relecteurs, ou pour proposer, challenger, valider, vérifier ou ranger un besoin non fonctionnel."
---

# Relire une fiche à trois

Avant le développement, la fiche est relue par ceux qui la construiront et la vérifieront. Chacun cherche ce qui manque de son point de vue ; le product owner, seul rédacteur, décide de ce qu'il en reprend. La relecture vise les questions qui coûteraient cher une fois le code écrit : un chemin d'échec oublié, une qualité sans seuil, une frontière franchie sans le savoir.

## Qui fait quoi

| Rôle | Ce qu'il apporte | Référence |
|---|---|---|
| Product owner | Seul rédacteur de la fiche et des besoins non fonctionnels, qu'il fixe avec l'utilisateur. Il juge la pertinence et la valeur de chaque scénario proposé (Smart, *BDD in Action*, ch. 4.5 : « the business analyst or product owner will be able to judge the relevance and relative value of the different scenarios ») | « Côté product owner » ci-dessous |
| Architecte | Ce qu'il faut pour que l'architecture tienne : qualités implicites, systèmes externes, frontières, incertitude technique | `references/angle-architecture.md` |
| Testeur (`quality-analyst`) | Les chemins qui échouent, les autres chemins vers une action refusée, le parcours principal ; il challenge, valide et vérifie les besoins non fonctionnels | `references/angle-tests.md` |

Les besoins non fonctionnels ont leur propre référence : `references/besoins-non-fonctionnels.md`.

## Ce que rend un relecteur

- **Il lit la fiche sans la modifier.**
- **Ses remarques vont au product owner**, dans une section « Pour le product-owner », formulées comme des besoins ou des questions, jamais comme une solution à écrire dans la fiche. Chaque scénario proposé vient avec un exemple concret, dans les mots du métier.
- **Ce que personne ne sait** devient une question pour l'utilisateur, avec les options, un exemple pour chacune et une recommandation.
- **Ce qui relève de son propre travail** (les consignes de l'architecte, les parcours que jouera le testeur) ne va pas dans la fiche : il le garde pour la suite.

## Côté product owner

À la réception des remarques d'un relecteur :

- **Chaque remarque ou scénario proposé s'intègre ou s'écarte en disant pourquoi.** Un scénario retenu rejoint sa règle, avec son exemple ; une contrainte rejoint « Contraintes connues » ; une incertitude, « Questions ouvertes » ou le découpage. Ce qui demande une décision devient une question pour l'utilisateur.
- **Une question d'un relecteur reçoit une réponse sourcée**, dans une section « Pour le <relecteur> » (par exemple « Pour le software-architect ») : l'entrée confirmée de la mémoire, la fiche validée ou le ticket d'où vient la réponse. Ce que le product owner ne sait pas devient une question pour l'utilisateur : il ne devine pas.
- **Un besoin non fonctionnel proposé** se range dans leur fichier, au gabarit de `references/besoins-non-fonctionnels.md`, et la fiche y renvoie par son identifiant.
- **Pas de solution technique dans la fiche** : ni table, ni endpoint, ni classe, ni écran précis, sauf contrainte réelle (système externe imposé, contrat existant).
