# Events and Performance

## Event-first rule

Prefer events to unrestricted `OnUpdate` work. Events identify when a condition may have changed; the plugin can then update only its assigned output. Use `RegisterUnitEvent` when the event supports unit filtering.

An `OnUpdate` handler is appropriate only when a display consumer or animation genuinely needs time progression. Throttle it to the required resolution and keep its body allocation-free.

## Generated-code implications

Phantom generates all explicitly declared conditions in each selected rotation, including conditions not used by a rule. Generated Lua should:

1. load shared primitives first;
2. return early from each UUID rotation file when class or specialization does not match;
3. register only events required by the active rotation;
4. update only affected regions;
5. avoid unnecessary reconstruction of tables, curves, formatters or frames on frequent events; follow the explicit deferred-refresh contract for condition callbacks.

Static layout and plugin arguments are frozen during generation. Runtime code must not change output count or shift later regions.

## Useful lifecycle events

Choose the exact event from current source, but keep these lifecycle categories separate:

- addon initialization and saved state;
- player login or entering world;
- specialization or talent changes;
- combat lockdown transitions;
- unit-specific state changes;
- aura-container managed updates;
- post-combat work that was prohibited during combat.

Do not use event payloads as ordinary values when the current build marks them secret.

Phantom condition callback cadence is a project contract in [condition refresh rules](../../phantom-plugin-dev/references/conditions.md#刷新写法). Core runtime frame processing belongs to [architecture](../../phantom-code-dev/references/architecture.md#截图基础运行边界).
