# Besoins non fonctionnels

Un besoin non fonctionnel dit, de façon mesurable, comment le produit doit se comporter, et non ce qu'il fait : « la route `/commande` répond en moins de 100 ms, 95 fois sur 100 », plutôt que « l'API est rapide ». C'est un besoin comme les autres : le product owner le fixe, le testeur le vérifie.

## Qui fait quoi

- **Le product owner fixe les besoins non fonctionnels**, avec l'utilisateur, dans le fichier du projet. Il en est le seul rédacteur, comme de la fiche, et n'y écrit que les besoins que l'utilisateur a acceptés.
- **Tout le monde peut en proposer un** : l'utilisateur ; le product owner quand un besoin contient un mot vague (« rapide », « jamais ») ; l'architecte, pour une qualité implicite qui pilote l'architecture ; le testeur, pour un besoin qui manque ou qui ne tient pas avec les autres. La proposition va au product owner, au gabarit ci-dessous.
- **Le testeur les vérifie** : il les challenge et les valide à la relecture d'une fiche (voir « Challenger et valider »), puis les vérifie à chaque recette (voir « Vérifier »). Comment il les vérifie et ce que donne chaque vérification restent dans sa mémoire, pas dans le fichier du product owner.
- **L'architecte dit comment l'architecture tient un besoin** (un ADR), et garde le classement des qualités qui pilotent ses décisions ; il ne recopie pas les besoins.

## Le fichier

Lisible par toute l'équipe, à côté des fiches : la convention du projet, sinon `docs/specs/besoins-non-fonctionnels.md`. **Il ne contient que des besoins non fonctionnels** : ni règle métier (elles vont dans la fiche), ni solution (elle va dans un ADR), ni façon de les vérifier (elle va dans la mémoire du testeur). Une fiche y renvoie par l'identifiant des besoins qu'elle touche (« Contraintes connues : ENF-04, ENF-07 ») au lieu de les recopier : si un besoin change, la fiche reste juste.

```markdown
### ENF-04 · La route `/commande` répond en moins de 100 ms
- Situation : 50 commandes par seconde, catalogue de 10 000 articles
- Seuil : moins de 100 ms, 95 fois sur 100
- Source : notes de ABC-12 (AAAA-MM-JJ)
```

- **Pas de statut**, pas plus qu'une règle métier dans la fiche : le fichier ne contient que des besoins acceptés. Un besoin proposé, ou une valeur que l'utilisateur n'a pas donnée, reste une question à l'utilisateur, avec une valeur par défaut qu'il n'a qu'à confirmer ou corriger ; la question et sa réponse se rangent comme les autres (dans les notes du ticket, s'il y a un backlog). Un besoin refusé n'est pas gardé.
- **Ce qui vaut pour tous les besoins** (jeu de données de référence, machines, période sur laquelle valent les seuils) : en tête du fichier, une fois.

## Rendre un besoin mesurable

- **Un mot vague ou un « jamais »** devient une question à l'utilisateur, avec un seuil qui a un sens pour le métier et ce que coûte un dépassement : « en moins de 2 secondes dans 95 % des cas » ; « jamais » ne se démontre pas, « rarement » si (Cohn, *User Stories Applied*, ch. 2 « Testable » ; Smart, *BDD in Action*, 9.4).
- **Une qualité composite** (« évolutif », « fiable ») se décompose en besoins mesurables.
- **Un besoin dit quoi mesurer, pas comment le vérifier** : la façon de le vérifier ne va pas dans le fichier. Le testeur la choisit (une mesure à la recette, un test automatique) ; une règle d'architecture qui sert le besoin se vérifie par une fonction de conformité (*fitness function*), que l'architecte écrit.

## Challenger et valider

À la relecture d'une fiche, le testeur relit les besoins non fonctionnels que la fonctionnalité touche, et tout le fichier quand il le découvre :

- **deux besoins qui se contredisent** (un temps de réponse impossible avec la quantité de données promise ailleurs) ;
- **un seuil qu'on ne sait pas mesurer**, ou dans une situation que le projet ne peut pas reproduire ;
- **un besoin qui manque** pour ce que la fonctionnalité ajoute (une nouvelle route sans temps de réponse, des données en plus dans une sauvegarde) ;
- **un « jamais » ou un mot vague** resté dans un besoin.

Chaque remarque va au product owner, comme une proposition au gabarit ci-dessus. Un besoin mesurable tel quel, dans la situation qu'il fixe, est **validé** : le testeur le dit dans sa réponse et le note dans sa mémoire.

## Vérifier

À chaque recette, le testeur vérifie tous les besoins du fichier, sur l'application construite et dans la situation que chacun fixe :

- **un seuil de temps se mesure plusieurs fois** et se compare à sa proportion (« 95 fois sur 100 ») : une mesure unique ne prouve rien ;
- **les mesures de bas niveau** (processeur, mémoire, temps moyen) s'enregistrent pour expliquer un échec ; elles ne font échouer une recette que si un besoin les fixe (Smart, *BDD in Action*, 9.4 « Defining and testing nonfunctional requirements ») ;
- **chaque besoin a un résultat** : `tenu`, `en écart` (avec la mesure) ou `non vérifié` (et pourquoi).
