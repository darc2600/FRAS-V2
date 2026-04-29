# FRAS Patch Roadmap

## Completed / prepared patches

```txt
Fix 1: Showcase README and docs cleanup
Fix 2: Docker and environment deployment cleanup
Fix 3: Panel feedback UI fixes
Fix 4: Duplicate room protection
Fix 5: Attendance Reports polish
Fix 6: Analytics charts and face registration insights
Fix 7: Repeatable demo data reset workflow
```

## Current patch: Fix 7

This patch adds a repeatable demo database reset script so the project can always be restored to a clean presentation-ready state.

## Next recommended patch

```txt
Fix 8: security cleanup for JWT secrets, password handling, debug logs, and environment validation
```

## Why Fix 8 matters

The project still contains development fallback secrets, password debug logging, and plaintext password fallback behavior in some paths. These should be cleaned before the final presentation or deployment.
