# Grocery Assistant MCP

## Current stable documentation set

This package is the consolidated Version 1.4 documentation set for the Grocery Assistant MCP project.

Version 1.4 moves the project from single-record write tools into safe batch meal workflows.

## Version 1.4 status

Version 1.4 is treated as the current closeout baseline.

Completed stages:

```text
Version 1.4A — Core service refactor
Version 1.4B — Intake-only batch meal logging
Version 1.4C — Inventory-linked batch meal logging
```

Current Version 1.4 batch tools:

```text
add_meal_with_items
add_meal_with_inventory_items
```

Core rule:

```text
Intake-only batch logging must not deduct inventory.
Inventory-linked batch logging deducts inventory only for explicitly selected inventory items.
```

## Active documentation

Use these files as the canonical documentation set:

```text
docs/README.md
docs/guides/command_reference_v1_4.md
docs/guides/mcp_testing_guide_v1_4.md
docs/checklists/version_1_4_closeout_checklist.md
docs/roadmap/project_roadmap.md
docs/planning/future_version_plans.md
docs/concepts/mcp_grocery_learning_concept.md
docs/journals/development_journal.md
DOCS_CLEANUP_PLAN.md
```

## Curl testing files

The final Version 1.4 curl request files are here:

```text
version_1_4/curl_requests/
```

Curl response output should be written here:

```text
version_1_4/curl_responses/
```

The command reference uses a PowerShell helper function that saves both:

```text
*.raw.txt
*.json
```

Use the `.json` files for normal inspection in VS Code.

## Archive

Older or superseded documentation has been preserved under:

```text
docs/archive/originals/
```

Do not use the archive as the active source of truth unless you need historical context.
