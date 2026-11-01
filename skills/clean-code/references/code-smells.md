# Code smells and the refactoring that treats each

| Smell | Typical refactoring |
|---|---|
| Long method | Extract Method |
| Large class | Extract Class |
| Long parameter list | Introduce Parameter Object |
| Duplication | Extract Method, Pull Up Method, Form Template Method |
| Feature envy | Move Method |
| Data clumps | Extract Class, Introduce Parameter Object |
| Primitive obsession | Replace Primitive with Object (value object) |
| Repeated `switch` on the same type | Replace Conditional with Polymorphism |
| Divergent change | Extract Class (one reason to change each) |
| Shotgun surgery | Move Method / Inline Class (gather what changes together) |
| Dead code | Delete it |
| Speculative generality | Collapse Hierarchy, Inline Class, Remove Parameter |
| Comments compensating for obscure code | Extract Method, Rename |

Procedure: name the smell, name the refactoring, apply it in small steps, rerun the tests after each step. Prefer the IDE's automated refactorings.
