# Full example: `BookDtoMapperFromFeedUtils`

A static utility class (pure code) that turns a `FeedBook` received from a publisher's feed into a `BookDto`. Three public methods:

- `mapToDto(FeedBook)`: the main entry point;
- `extractPackSize(Packaging, ShippingMode)`: called by `mapToDto`, but public and very combinatorial, so it gets a **test of its own**;
- `buildBook(String json)`: Jackson deserialization with a custom deserializer for `ShippingMode`, tested on JSON samples.

> The model classes (`FeedBook`, `Edition`, `PurchaseCondition`, `Packaging`…) are not part of the example: the way they are built below (Lombok builders) is **assumed**. Always read the real classes and adapt the fixtures.

## 1. Axes found

### `extractPackSize`

| # | Axis | Line | Values |
|---|---|---|---|
| 1 | shipping mode | `WAREHOUSE.equals(shippingMode)` | `null`, `WAREHOUSE`, `STORE`, `PUBLISHER` |
| 2 | `outbound` key (read for `WAREHOUSE`) | `getOutbound()` | `null`, each name of the `Packaging` enum, `"UNKNOWN"`, `"carton"` |
| 3 | `inbound` key (read otherwise) | `getInbound()` | same |
| 4 | parts present | `getCarton() != null`, `getBundle() != null`, pallets | shape: `NULL`, `EMPTY`, `CARTON_NO_BUNDLE`, `CARTON_WITH_BUNDLE`, `SHIPPED_PALLET_ONLY`, `DELIVERED_PALLET_ONLY`, `COMPLETE` |

4 × 8 × 8 × 7 = **1,792** combinations. Distinct values: carton = 12, bundle = 3, shipped pallet = 480, delivered pallet = 960 (UNIT is always `"1"`).

To dig into while reading the model: `getNbOfUnitAsString()` when `nbOfUnit` is `null` (a possible new axis on each part).

### `mapToDto`

| # | Axis | Line | Values |
|---|---|---|---|
| 1 | active edition | `getCurrentActiveEdition()` | absent, active |
| 2 | current purchase condition | `getCurrentPurchaseCondition()` | `null`, empty, complete |
| 3 | shipping mode | `getShippingMode()` | `null`, `WAREHOUSE`, `STORE`, `PUBLISHER` |
| 4 | packaging | `extractPackSize(...)` | `null`, complete (`outbound = DELIVERED_PALLET`, `inbound = SHIPPED_PALLET`) |
| 5 | net weight | `getNetWeight() != null` | `null`, value |
| 6 | book key | `getBookKey().toString()` | `null`, value |

2 × 3 × 4 × 2 × 2 × 2 = **192** combinations. Axis 4 is reduced to two shapes: its fine-grained logic is covered by the dedicated test; here the test only checks that the right mode is passed on (WAREHOUSE gives 960, anything else 480).

`getCurrentActiveEdition()` is a computed getter: **read its implementation**. If it depends on the current date (validity dates), axis 1 becomes "validity dates relative to a fixed date" (before, during, after, on each bound) and the clock must be controlled (`services-and-dependencies.md`, section 5). The same goes for `getFirstSalePriceAsString()` and its neighbors (number format, empty list).

### `buildBook`

Real JSON samples (ask the user, or look in `src/test/resources`), completed with variants: `shippingMode` valid, in lower case, unknown, `null`, missing; an unknown field (the default `ObjectMapper` fails on unknown properties); invalid JSON.

## 2. The test

```java
package com.example.bookshop.mapper;

import com.example.bookshop.enums.ShippingMode;
import com.example.bookshop.model.Packaging;
import com.example.bookshop.model.FeedBook;
// + model imports (Carton, Bundle, Pallet, Edition, PurchaseCondition…)
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

    /** Every name of the enum com.example.bookshop.enums.Packaging, plus null, an unknown value and the wrong case. */
    private static final String[] KEYS =
            {null, "UNIT", "CARTON", "BUNDLE", "SHIPPED_PALLET", "DELIVERED_PALLET", "UNKNOWN", "carton"};

    // ---------------------------------------------------------------- extractPackSize

    @Test
    void extractPackSize() {
        CombinationApprovals.verifyAllCombinations(
                (mode, out, in, shape) -> BookDtoMapperFromFeedUtils.extractPackSize(packaging(shape, out, in), mode),
                MODES, KEYS, KEYS, Logistics.values(),
                OPTIONS);
    }

    // ---------------------------------------------------------------- mapToDto

    @Test
    void mapToDto() {
        CombinationApprovals.verifyAllCombinations(
                (version, purchase, mode, shape, weight, key) ->
                        BookDtoMapperFromFeedUtils.mapToDto(book(version, purchase, mode, shape, weight, key)),
                Version.values(), Purchase.values(), MODES,
                new Logistics[]{Logistics.NULL, Logistics.COMPLETE},
                Presence.values(), Presence.values(),
                OPTIONS);
    }

    // ---------------------------------------------------------------- buildBook (+ mapToDto)

    @Test
    void buildBookThenMapToDto() throws IOException {
        List<Path> files;
        try (Stream<Path> s = Files.list(Path.of("src/test/resources/golden-master/feed"))) {
            files = s.sorted().toList();                            // stable order
        }
        Approvals.verifyAll("json", files, f -> f.getFileName() + " => " + fromJson(f), OPTIONS);
    }

    private static String fromJson(Path file) {
        try {
            String json = Files.readString(file);
            return String.valueOf(BookDtoMapperFromFeedUtils.mapToDto(BookDtoMapperFromFeedUtils.buildBook(json)));
        } catch (IOException e) {
            throw new UncheckedIOException(e);                      // an error of the test, not of the code: let it propagate
        } catch (Exception e) {
            return e.getClass().getName() + ": " + e.getMessage();
        }
    }

    // ---------------------------------------------------------------- axes and fixtures

    enum Version { ABSENT, ACTIVE }
    enum Purchase { NULL, EMPTY, COMPLETE }
    enum Presence { WITHOUT, WITH }

    enum Logistics {
        NULL, EMPTY, CARTON_NO_BUNDLE, CARTON_WITH_BUNDLE, SHIPPED_PALLET_ONLY, DELIVERED_PALLET_ONLY, COMPLETE;

        boolean carton()          { return this == CARTON_NO_BUNDLE || this == CARTON_WITH_BUNDLE || this == COMPLETE; }
        boolean bundle()          { return this == CARTON_WITH_BUNDLE || this == COMPLETE; }
        boolean shippedPallet()   { return this == SHIPPED_PALLET_ONLY || this == COMPLETE; }
        boolean deliveredPallet() { return this == DELIVERED_PALLET_ONLY || this == COMPLETE; }
    }

    // ADAPT to the real model: builder names, type of nbOfUnit, etc.
    static Packaging packaging(Logistics shape, String out, String in) {
        if (shape == Logistics.NULL) {
            return null;
        }
        return Packaging.builder()
                .outbound(out)
                .inbound(in)
                .carton(shape.carton() ? Carton.builder().nbOfUnit(12).bundle(shape.bundle() ? Bundle.builder().nbOfUnit(3).build() : null).build() : null)
                .shippedPallet(shape.shippedPallet() ? Pallet.builder().nbOfUnit(480).build() : null)
                .deliveredPallet(shape.deliveredPallet() ? Pallet.builder().nbOfUnit(960).build() : null)
                .build();
    }

    // ADAPT: how an edition is made "active" depends on getCurrentActiveEdition().
    static FeedBook book(Version version, Purchase purchase, ShippingMode mode,
                         Logistics shape, Presence weight, Presence key) {
        Edition edition = version == Version.ABSENT ? null : Edition.builder()
                .publisher("PUB-001")
                .shippingMode(mode)
                .packaging(packaging(shape, "DELIVERED_PALLET", "SHIPPED_PALLET"))
                .purchaseConditions(purchaseConditions(purchase))
                .active(true)
                .build();
        return FeedBook.builder()
                .bookKey(key == Presence.WITH ? 1042L : null)
                .netWeight(weight == Presence.WITH ? new BigDecimal("0.450") : null)
                .editions(edition == null ? List.of() : List.of(edition))
                .build();
    }

    static List<PurchaseCondition> purchaseConditions(Purchase purchase) {
        return switch (purchase) {
            case NULL -> null;
            case EMPTY -> List.of(PurchaseCondition.builder().build());
            case COMPLETE -> List.of(PurchaseCondition.builder()
                    .salePrice(new BigDecimal("19.90"))
                    .minimumOrderQuantity(6)
                    .vatRate(new BigDecimal("5.5"))
                    .build());
        };
    }
}
```

`BookDto` is assumed to have a Lombok `toString()` that prints all its fields. Otherwise, add a `print(BookDto)` that prints them in a fixed order.

## 3. Expected excerpt of the approved file (illustrative)

`BookDtoMapperFromFeedUtilsGoldenMasterTest.extractPackSize.approved.txt`:

```
[WAREHOUSE, DELIVERED_PALLET, CARTON, COMPLETE] => 960
[WAREHOUSE, BUNDLE, CARTON, CARTON_NO_BUNDLE] => null
[WAREHOUSE, CARTON, null, NULL] => java.lang.NullPointerException: Cannot invoke "...Packaging.getOutbound()" because "packaging" is null
[STORE, DELIVERED_PALLET, BUNDLE, COMPLETE] => 3
[null, null, CARTON, CARTON_NO_BUNDLE] => 12
[null, UNIT, UNKNOWN, EMPTY] => null
[PUBLISHER, null, UNIT, EMPTY] => 1
```

`…mapToDto.approved.txt`:

```
[ABSENT, NULL, null, NULL, WITHOUT, WITHOUT] => java.lang.NullPointerException: Cannot invoke "...toString()" because the return value of "...getBookKey()" is null
[ABSENT, NULL, null, NULL, WITHOUT, WITH] => com.example.bookshop.exception.NoActiveEdition: No active edition found for book :1042
[ACTIVE, COMPLETE, WAREHOUSE, COMPLETE, WITH, WITH] => BookDto(bookKey=1042, unitNetWeight=0.450, publisherId=PUB-001, salePrice=19.90, minimumOrder=6, shippingMode=WAREHOUSE, vatRate=5.5, packSize=960)
[ACTIVE, COMPLETE, STORE, NULL, WITH, WITH] => java.lang.NullPointerException: Cannot invoke "...Packaging.getInbound()" because "packaging" is null
```

## 4. Suspicious behaviors to freeze and report (without fixing them)

| Case | Current behavior | Why it is suspicious |
|---|---|---|
| `bookKey` `null` | `NullPointerException` | thrown before the business check `NoActiveEdition` |
| No active edition | every value is computed, then the exception is thrown | the check could come first |
| Active edition without packaging | `NullPointerException` in `extractPackSize` | no guard, unlike the other fields |
| Mode `null` | read as `STORE` / `PUBLISHER` (`inbound` key) | an implicit, undocumented choice |
| `STORE` with `inbound = BUNDLE` or `DELIVERED_PALLET` | returns the value | the Javadoc says `inbound` is only `UNIT`, `CARTON` or `SHIPPED_PALLET` |
| `UNIT` | `"1"` even with no part at all | intended according to the Javadoc, to be confirmed |
| Lower-case key (`"carton"`) | `null` | case-sensitive comparison |

## 5. Refactorings to propose

1. Throw `NoActiveEdition` at the very start of `mapToDto` (a guard clause). This changes the behavior when `bookKey` is `null`: to be validated with the user.
2. Replace the cascade of ternaries `activeEdition != null ? … : null` with a mapping from the active edition once the guard is in place.
3. Replace the chain of `if` in `extractPackSize` with a table from `Packaging` to an extractor (`Map<Packaging, Function<model.Packaging, String>>`) or a method on the enum.
4. Remove the name clash between `enums.Packaging` and `model.Packaging` (rename one of them).
5. Turn the static utility class into a component (`@Component`) if it needs to be injected, and move the custom `ObjectMapper` into a configuration.

Run the golden master again after **every** step; a difference means going back, not approving again (except for step 1, if the user validates the change of behavior: then approve again in a dedicated commit that says so).
