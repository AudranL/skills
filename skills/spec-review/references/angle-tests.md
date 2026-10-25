# Angle tests

L'analyste et le product owner décrivent le chemin heureux ; le testeur écrit les chemins qui échouent, bien plus nombreux, et y pense avant le développement plutôt que de les constater après (Martin, *Clean Agile*, ch. 3 « QA » ; Beck, *Extreme Programming Explained*, ch. 10 « Testers »).

Pour chaque règle de la fiche :

- **Les chemins qui échouent** : refus, valeurs limites (vide, zéro, maximum, doublon), ordre inattendu des gestes, retour en arrière.
- **Tous les chemins qui mènent à une action refusée** : bouton, double-clic, raccourci, modification d'une donnée existante, import, restauration. Un refus écrit « ne me le propose pas » n'est tenu que par un chemin ; écrit par son effet (« aucune commande n'est enregistrée »), il les couvre tous.
- **Une proposition par vrai risque** : le testeur apporte les cas limites que les autres n'ont pas vus, le product owner juge leur valeur ; quand les propositions deviennent évidentes, passer à la règle suivante plutôt que d'allonger la liste (Smart, *BDD in Action*, 4.5 « Three Amigos », 9.2).

Pour la fonctionnalité :

- **Les besoins non fonctionnels qu'elle touche** (temps de réponse d'un nouvel écran, données en plus dans la sauvegarde, plateformes), lus dans leur fichier, et ce que la recette vérifiera. Pour chacun, le valider ou le challenger (voir `besoins-non-fonctionnels.md`, « Challenger et valider ») ; proposer celui qui manque.
- **Le parcours principal** qui sera joué de bout en bout : celui qui joue le signal de réussite de la fiche (son « Pourquoi »). Un scénario de règle n'a pas de parcours de bout en bout s'il est déjà couvert au niveau des cas d'utilisation : le dire, plutôt que d'en ajouter un.

Les propositions de scénarios vont au product owner, dans la section « Pour le product-owner », chacune avec un exemple concret.
