# Exemple complet : `BookDtoMapperFromFeedUtils`

Classe utilitaire statique (code pur) qui transforme un `FeedBook` reçu du flux d'un éditeur en `BookDto`. Trois méthodes publiques :

- `mapToDto(FeedBook)` : point d'entrée principal ;
- `extractPackSize(Packaging, ShippingMode)` : appelée par `mapToDto`, mais publique et très combinatoire → **test dédié** ;
- `buildBook(String json)` : désérialisation Jackson avec un désérialiseur maison pour `ShippingMode` → test sur échantillons JSON.

> Les classes du modèle (`FeedBook`, `Edition`, `PurchaseCondition`, `Packaging`…) ne sont pas dans l'exemple : leur construction ci-dessous (builders Lombok) est **supposée**. Toujours lire les vraies classes et adapter les fixtures.

## 1. Axes trouvés

### `extractPackSize`

| # | Axe | Ligne | Valeurs |
|---|---|---|---|
| 1 | mode d'expédition | `WAREHOUSE.equals(shippingMode)` | `null`, `WAREHOUSE`, `STORE`, `PUBLISHER` |
| 2 | clé `outbound` (lue si `WAREHOUSE`) | `getOutbound()` | `null`, chaque nom de l'enum `Packaging`, `"UNKNOWN"`, `"carton"` |
| 3 | clé `inbound` (lue sinon) | `getInbound()` | idem |
| 4 | sous-objets présents | `getCarton() != null`, `getBundle() != null`, palettes | forme : `NULL`, `VIDE`, `CARTON_SANS_LOT`, `CARTON_AVEC_LOT`, `PALETTE_EXPEDIEE`, `PALETTE_LIVREE`, `COMPLETE` |

4 × 8 × 8 × 7 = **1 792** combinaisons. Valeurs distinctes : carton = 12, lot = 3, palette expédiée = 480, palette livrée = 960 (UNIT vaut toujours `"1"`).

À creuser en lisant le modèle : `getNbOfUnitAsString()` quand `nbOfUnit` est `null` (nouvel axe possible sur chaque sous-objet).

### `mapToDto`

| # | Axe | Ligne | Valeurs |
|---|---|---|---|
| 1 | édition active | `getCurrentActiveEdition()` | absente, active |
| 2 | condition d'achat courante | `getCurrentPurchaseCondition()` | `null`, vide, complète |
| 3 | mode d'expédition | `getShippingMode()` | `null`, `WAREHOUSE`, `STORE`, `PUBLISHER` |
| 4 | conditionnement | `extractPackSize(...)` | `null`, complète (`outbound = DELIVERED_PALLET`, `inbound = SHIPPED_PALLET`) |
| 5 | poids net | `getNetWeight() != null` | `null`, valeur |
| 6 | clé du livre | `getBookKey().toString()` | `null`, valeur |

2 × 3 × 4 × 2 × 2 × 2 = **192** combinaisons. L'axe 4 est réduit à deux formes : la logique fine est couverte par le test dédié ; ici on vérifie seulement que le bon mode est transmis (WAREHOUSE → 960, sinon → 480).

`getCurrentActiveEdition()` est un getter calculé : **lire son implémentation**. S'il dépend de la date du jour (dates de validité), l'axe 1 devient « dates de validité par rapport à une date fixée » (avant, pendant, après, sur chaque borne) et il faut maîtriser l'horloge (`services-et-dependances.md` §5). Même chose pour `getFirstSalePriceAsString()` et ses voisines (format des nombres, liste vide).

### `buildBook`

Échantillons JSON réels (demander à l'utilisateur, ou chercher dans `src/test/resources`), complétés par des variantes : `shippingMode` valide, en minuscules, inconnu, `null`, absent ; champ inconnu (l'`ObjectMapper` par défaut échoue sur les propriétés inconnues) ; JSON invalide.

## 2. Le test

```java
package com.example.bookshop.mapper;

import com.example.bookshop.enums.ShippingMode;
import com.example.bookshop.model.Packaging;
import com.example.bookshop.model.FeedBook;
// + imports du modèle (Carton, Bundle, Pallet, Edition, PurchaseCondition…)
import org.approvaltests.Approvals;
import org.approvaltests.combinations.CombinationApprovals;
import org.approvaltests.core.Options;
import org.approvaltests.reporters.QuietReporter;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigDecimal;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.stream.Stream;

class BookDtoMapperFromFeedUtilsGoldenMasterTest {

    private static final Options OPTIONS = new Options().withReporter(new QuietReporter());

    private static final ShippingMode[] MODES =
            {null, ShippingMode.WAREHOUSE, ShippingMode.STORE, ShippingMode.PUBLISHER};

    /** Chaque nom de l'enum com.example.bookshop.enums.Packaging + null, valeur inconnue, mauvaise casse. */
    private static final String[] CLES =
            {null, "UNIT", "CARTON", "BUNDLE", "SHIPPED_PALLET", "DELIVERED_PALLET", "UNKNOWN", "carton"};

    // ---------------------------------------------------------------- extractPackSize

    @Test
    void extractPackSize() {
        CombinationApprovals.verifyAllCombinations(
                (mode, out, in, forme) -> BookDtoMapperFromFeedUtils.extractPackSize(logistique(forme, out, in), mode),
                MODES, CLES, CLES, Logistique.values(),
                OPTIONS);
    }

    // ---------------------------------------------------------------- mapToDto

    @Test
    void mapToDto() {
        CombinationApprovals.verifyAllCombinations(
                (version, achat, mode, forme, poids, cle) ->
                        BookDtoMapperFromFeedUtils.mapToDto(livre(version, achat, mode, forme, poids, cle)),
                Version.values(), Achat.values(), MODES,
                new Logistique[]{Logistique.NULL, Logistique.COMPLETE},
                Presence.values(), Presence.values(),
                OPTIONS);
    }

    // ---------------------------------------------------------------- buildBook (+ mapToDto)

    @Test
    void buildBookPuisMapToDto() throws IOException {
        List<Path> fichiers;
        try (Stream<Path> s = Files.list(Path.of("src/test/resources/golden-master/flux"))) {
            fichiers = s.sorted().toList();                         // ordre stable
        }
        Approvals.verifyAll("json", fichiers, f -> f.getFileName() + " => " + depuisJson(f), OPTIONS);
    }

    private static String depuisJson(Path fichier) {
        try {
            String json = Files.readString(fichier);
            return String.valueOf(BookDtoMapperFromFeedUtils.mapToDto(BookDtoMapperFromFeedUtils.buildBook(json)));
        } catch (IOException e) {
            throw new UncheckedIOException(e);                      // erreur du test, pas du code : on la laisse remonter
        } catch (Exception e) {
            return e.getClass().getName() + ": " + e.getMessage();
        }
    }

    // ---------------------------------------------------------------- axes et fixtures

    enum Version { ABSENTE, ACTIVE }
    enum Achat { NULL, VIDE, COMPLETE }
    enum Presence { SANS, AVEC }

    enum Logistique {
        NULL, VIDE, CARTON_SANS_LOT, CARTON_AVEC_LOT, PALETTE_EXPEDIEE, PALETTE_LIVREE, COMPLETE;

        boolean carton()          { return this == CARTON_SANS_LOT || this == CARTON_AVEC_LOT || this == COMPLETE; }
        boolean lot()             { return this == CARTON_AVEC_LOT || this == COMPLETE; }
        boolean paletteExpediee() { return this == PALETTE_EXPEDIEE || this == COMPLETE; }
        boolean paletteLivree()   { return this == PALETTE_LIVREE || this == COMPLETE; }
    }

    // À ADAPTER au vrai modèle : noms des builders, types de nbOfUnit, etc.
    static Packaging logistique(Logistique forme, String out, String in) {
        if (forme == Logistique.NULL) {
            return null;
        }
        return Packaging.builder()
                .outbound(out)
                .inbound(in)
                .carton(forme.carton() ? Carton.builder().nbOfUnit(12).bundle(forme.lot() ? Bundle.builder().nbOfUnit(3).build() : null).build() : null)
                .shippedPallet(forme.paletteExpediee() ? Pallet.builder().nbOfUnit(480).build() : null)
                .deliveredPallet(forme.paletteLivree() ? Pallet.builder().nbOfUnit(960).build() : null)
                .build();
    }

    // À ADAPTER : la façon de rendre une édition « active » dépend de getCurrentActiveEdition().
    static FeedBook livre(Version version, Achat achat, ShippingMode mode,
                          Logistique forme, Presence poids, Presence cle) {
        Edition edition = version == Version.ABSENTE ? null : Edition.builder()
                .publisher("PUB-001")
                .shippingMode(mode)
                .packaging(logistique(forme, "DELIVERED_PALLET", "SHIPPED_PALLET"))
                .purchaseConditions(achats(achat))
                .active(true)
                .build();
        return FeedBook.builder()
                .bookKey(cle == Presence.AVEC ? 1042L : null)
                .netWeight(poids == Presence.AVEC ? new BigDecimal("0.450") : null)
                .editions(edition == null ? List.of() : List.of(edition))
                .build();
    }

    static List<PurchaseCondition> achats(Achat achat) {
        return switch (achat) {
            case NULL -> null;
            case VIDE -> List.of(PurchaseCondition.builder().build());
            case COMPLETE -> List.of(PurchaseCondition.builder()
                    .salePrice(new BigDecimal("19.90"))
                    .minimumOrderQuantity(6)
                    .vatRate(new BigDecimal("5.5"))
                    .build());
        };
    }
}
```

`BookDto` est supposé avoir un `toString()` Lombok qui imprime tous ses champs. Sinon, ajouter un `print(BookDto)` qui les imprime dans un ordre fixe.

## 3. Extrait attendu du fichier approuvé (illustratif)

`BookDtoMapperFromFeedUtilsGoldenMasterTest.extractPackSize.approved.txt` :

```
[WAREHOUSE, DELIVERED_PALLET, CARTON, COMPLETE] => 960
[WAREHOUSE, BUNDLE, CARTON, CARTON_SANS_LOT] => null
[WAREHOUSE, CARTON, null, NULL] => java.lang.NullPointerException: Cannot invoke "...Packaging.getOutbound()" because "packaging" is null
[STORE, DELIVERED_PALLET, BUNDLE, COMPLETE] => 3
[null, null, CARTON, CARTON_SANS_LOT] => 12
[null, UNIT, UNKNOWN, VIDE] => null
[PUBLISHER, null, UNIT, VIDE] => 1
```

`…mapToDto.approved.txt` :

```
[ABSENTE, NULL, null, NULL, SANS, SANS] => java.lang.NullPointerException: Cannot invoke "...toString()" because the return value of "...getBookKey()" is null
[ABSENTE, NULL, null, NULL, SANS, AVEC] => com.example.bookshop.exception.NoActiveEdition: No active edition found for book :1042
[ACTIVE, COMPLETE, WAREHOUSE, COMPLETE, AVEC, AVEC] => BookDto(bookKey=1042, unitNetWeight=0.450, publisherId=PUB-001, salePrice=19.90, minimumOrder=6, shippingMode=WAREHOUSE, vatRate=5.5, packSize=960)
[ACTIVE, COMPLETE, STORE, NULL, AVEC, AVEC] => java.lang.NullPointerException: Cannot invoke "...Packaging.getInbound()" because "packaging" is null
```

## 4. Comportements suspects à figer et à signaler (sans les corriger)

| Cas | Comportement actuel | Pourquoi suspect |
|---|---|---|
| `bookKey` `null` | `NullPointerException` | levée avant le contrôle métier `NoActiveEdition` |
| Pas d'édition active | toutes les valeurs sont calculées, puis l'exception est levée | le contrôle pourrait être fait en premier |
| Édition active sans conditionnement | `NullPointerException` dans `extractPackSize` | aucune protection, contrairement aux autres champs |
| Mode `null` | lu comme `STORE` / `PUBLISHER` (clé `inbound`) | choix implicite, non documenté |
| `STORE` avec `inbound = BUNDLE` ou `DELIVERED_PALLET` | renvoie la valeur | la Javadoc dit que `inbound` ne vaut que `UNIT`, `CARTON` ou `SHIPPED_PALLET` |
| `UNIT` | `"1"` même sans aucun sous-objet | voulu d'après la Javadoc, à confirmer |
| Clé en minuscules (`"carton"`) | `null` | comparaison sensible à la casse |

## 5. Refactorings à proposer

1. Lever `NoActiveEdition` en tout début de `mapToDto` (garde) — change le comportement si `bookKey` est `null` : à valider avec l'utilisateur.
2. Remplacer la cascade de ternaires `activeEdition != null ? … : null` par un mapping depuis l'édition active une fois la garde posée.
3. Remplacer la chaîne de `if` d'`extractPackSize` par une table `Packaging` → extracteur (`Map<Packaging, Function<model.Packaging, String>>`) ou une méthode sur l'enum.
4. Lever l'ambiguïté de nom entre `enums.Packaging` et `model.Packaging` (renommer l'un des deux).
5. Transformer la classe utilitaire statique en composant (`@Component`) si elle doit être injectée, et sortir l'`ObjectMapper` maison dans une configuration.

Relancer le golden master après **chaque** pas ; un écart = revenir en arrière, pas ré-approuver (sauf pour le pas 1, si l'utilisateur valide le changement de comportement : alors ré-approuver dans un commit dédié qui le dit).
