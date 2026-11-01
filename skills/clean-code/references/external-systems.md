# External systems: model and contract

Detail for the "Design" section of `SKILL.md`.

## Keep the external model at the boundary

The fields, codes and values of an external system (e.g. the status codes of a carrier's API) live in the infrastructure adapter, with their own type (e.g. `CarrierParcelStatus`) and an explicit translation to the domain type (e.g. `DeliveryStep`).

The domain type holds only what makes sense to the business. It may group several external values into one (e.g. codes 20, 30, 40 and 50 → `IN_TRANSIT`).

Faced with a piece of external data, ask yourself, and ask the user if needed: business concept, or supplier detail?

## An adapter handles only the documented contract

Write one case and one test for each response the contract documents. A response the contract does not document gets no case of its own, no list of codes and no test: it falls through to a single default, usually a technical error. If the contract is missing, ask for it rather than guessing the cases.

## Wrap third-party code

- Few places in the code refer to a third-party API; wrap it or put an adapter in front. You can change library, mock it easily, and define the API you wish you had.
- A wrapper translates the vendor's exceptions into one exception type of your own.
- **Learning tests**: when the library's behavior is unclear, write tests that call it as production code will. They cost nothing, since you had to learn the API anyway, and rerun on each release to reveal behavior changes. For a documented external contract, they feed the adapter's tests.
