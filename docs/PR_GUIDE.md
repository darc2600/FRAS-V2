# Pull Request Guide

Use this guide when creating future FRAS pull requests.

## Recommended Branch Naming

```txt
fix/short-description
feat/short-description
docs/short-description
security/short-description
chore/short-description
```

Examples:

```txt
fix/prevent-duplicate-rooms
feat/analytics-charts
security/harden-password-reset
docs/update-demo-guide
```

## Recommended Commit Style

Use short conventional commit messages:

```txt
docs: update project setup guide
fix: prevent duplicate rooms in schedule editor
feat: add analytics charts
security: remove password debug logging
chore: archive old debug scripts
```

## PR Checklist

Before opening a PR, check:

- The app still starts locally.
- Frontend builds successfully.
- Backend starts successfully.
- No real passwords or secrets were committed.
- `.env` is not committed.
- Screenshots are added for UI changes when possible.
- Demo data still works after reset.
- Documentation is updated if behavior changed.

## Recommended PR Description Template

```md
## Summary

Briefly explain what changed.

## What changed

- Item 1
- Item 2
- Item 3

## Testing

- [ ] Backend starts
- [ ] Frontend builds
- [ ] Manual UI test completed
- [ ] Demo data reset tested

## Notes

Mention any known limitations or follow-up items.
```

## Safe PR Order

For remaining work, use this order:

1. Security hardening.
2. Debug/archive cleanup.
3. Smoke testing script.
4. Final UI polish.
5. Final deployment guide verification.
