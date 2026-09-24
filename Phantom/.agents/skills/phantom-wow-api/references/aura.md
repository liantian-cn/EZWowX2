# Aura Display in WoW 12.1

## Default architecture

Use the managed AuraContainer model for aura display in 12.1. The container tracks aura state, selects frames, updates display bindings, and performs layout. Addon code declares filters and static presentation; it must not reconstruct a secret aura list for combat decisions.

Current implementation evidence is under `@wow-ui-source/Interface/AddOns/Blizzard_AuraContainer/`.

## Groups and slots

Choose the shape by business need:

- An Aura group is dynamic. It filters and orders a changing set of auras and lets the container allocate visible buttons.
- An Aura slot is fixed. It represents a configured position or spell selection and is better when Phantom needs deterministic screen coordinates.

The exact `AddAuraGroup`, `AddAuraSlot`, filter, sort, layout, duration, application, dispel, and tooltip options must be read from the pinned implementation and generated documentation. The 12.1 PTR renamed several layout and styling fields.

## Initialization boundary

Use the button initialization callback only for static setup that the contract allows, such as creating and registering supported display regions. The callback is not permission to inspect `AuraData`, observe allocation counts, attach side-channel scripts, or infer state from later access restrictions.

Let the managed container own anchors for dynamically laid-out group buttons. Do not add custom anchors that compete with the container.

## Forbidden and secret behavior

- Aura buttons and inbound regions may carry forbidden aspects or access restrictions.
- A button becoming forbidden or accessible is not a combat-data signal.
- Visibility, `OnShow`, `IsShown`, layout callbacks, and button allocation must not be used to reconstruct aura state.
- NeverSecret spell filters are narrow exemptions; other aura data remains subject to the active restriction.

## Phantom patterns

For a deterministic condition plugin:

1. Choose a managed group or fixed slot only after checking the target source revision.
2. Allocate a stable pixel region before runtime.
3. Connect supported Aura display properties to that region without Lua-side inspection.
4. Decode the rendered Cell, Value Bar, or Icon Tile on the Python side.
5. Document empty output, fallback behavior, and version-specific assumptions.

Fixed slots are generally easier to map to stable pixel coordinates. Dynamic groups require a fixed maximum frame count and a documented ordering contract.

## Do not revive old list loops

Patterns that call unit-aura list APIs, take `#` of a returned collection, iterate instance IDs, or fetch aura records for Lua comparisons are not safe defaults in 12.1. Use them only after the exact API, context, and secrecy level are verified as non-secret.
