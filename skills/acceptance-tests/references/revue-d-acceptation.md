# Revue d'acceptation

Relire une fonctionnalité livrée, par celui qui a écrit la fiche : comparer la fiche au diff et aux tests, sans modifier ni le code ni les tests.

1. **Pour chaque scénario**, dire s'il est couvert et par quel test, en vérifiant la table annoncée par celui qui a développé plutôt qu'en la croyant.
   - **Couvert** : chaque partie de son « Alors » est vérifiée par un test, à un niveau ou à un autre. Un scénario n'a pas à être rejoué de bout en bout : la règle se vérifie au plus près du code qui la porte, le parcours et la façon dont la règle apparaît à l'utilisateur (message, présentation) par un test de bout en bout.
   - **Mal couvert** : aucun test n'exerce son « Quand » (le test vérifie l'état avant l'action, pas son effet), ou la valeur qui le distingue des autres (une date limite, deux montants égaux) n'est vérifiée nulle part.
   - **Non couvert** : aucun test ne lui correspond.
2. **Les contraintes de la fiche** : plateformes, aucune requête réseau, besoins non fonctionnels touchés (le résultat de leur vérification à la recette).
3. **Un scénario de refus** : chercher chaque chemin par lequel l'utilisateur peut faire l'action refusée (bouton, raccourci, modification d'une donnée existante, import), pas seulement celui qu'exerce le test.
4. **Ce qui a été ajouté hors périmètre** : un comportement qu'aucun scénario ne demande.
5. **Ce que la fonctionnalité apprend** pour la suite : hypothèse confirmée ou non, nouvelles questions, idées pour une fonctionnalité suivante.
