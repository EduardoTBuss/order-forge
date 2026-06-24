---
name: changelog-management
description: Update CHANGELOG.md and write entries in the correct Keep a Changelog format for every commit-worthy change.
---

# Changelog Management

Use this skill whenever a task changes code, documentation, configuration, CI,
or agent guidance and the repository history should reflect it.

This repository keeps a single changelog file: `CHANGELOG.md`.

## Rule Summary

1. Update `CHANGELOG.md` for every commit-worthy change.
2. Keep the changelog entry aligned with what the user asked for and why the
   change exists.

## `CHANGELOG.md` Format

### Required Structure

- Follow [Keep a Changelog](https://keepachangelog.com/) structure.
- By default, group entries under date headings (`## YYYY-MM-DD`), but it is also
  acceptable to group by version or release. If grouping by version, include an
  `[Unreleased]` section.
- Use categories such as `Added`, `Changed`, `Fixed`, `Removed`, and
  `Security` when appropriate.
- Write entries from the developer/user perspective, not implementation details.
- Every bullet must end with plain PR and/or author references in parentheses.
- Do not use commit hashes.

### Reference Rules

- Prefer plain PR numbers such as `#46` when a PR exists.
- Also include human authors such as `@your-handle`.
- If no PR exists, add the human author or authors only.
- Ignore Claude, Copilot, and generic agent authors unless they are the only
  authors attached to the change.
- Do not turn PRs or usernames into markdown links.
- Do not use reference-style link definitions at the bottom of the file.

### Example

```markdown
## [Unreleased]

### Added
- Added invoice approval reminders to the dashboard. (@your-handle)

### Fixed
- Fixed PDF import validation for multi-page uploads. (@your-handle)
```

## Checklist

- Updated `CHANGELOG.md`
- Included the user-request context in the wording
- Matched the required Keep a Changelog format
- Added plain `#pr` and `@user` references for every changelog bullet
