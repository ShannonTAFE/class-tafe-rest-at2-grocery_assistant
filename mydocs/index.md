# Version 1.1 Documentation Index

This folder contains the final documentation set for the Grocery Assistant MCP Version 1.1 stage.

Recommended placement:

```text
README.md
docs/project_roadmap.md
docs/version_1_1_completion_checklist.md
docs/mcp_testing_guide.md
docs/command_reference.md
docs/development_journal_v1_1.md
docs/future_version_plans.md
```

## Files

### README.md

Main project overview for Version 1.1. Explains the project purpose, current capabilities, data model, resources, tools, testing, and scope boundaries.

### project_roadmap.md

Longer-term staged roadmap from Version 1.0 to Version 1.5.

### version_1_1_completion_checklist.md

Definition of done for closing Version 1.1.

### mcp_testing_guide.md

Manual testing guide for MCP Inspector and curl.

### command_reference.md

Common PowerShell, pytest, server, MCP Inspector, curl, and git commands.

### development_journal_v1_1.md

Cleaned journal template and summary for the Version 1.1 development stage.

### future_version_plans.md

Deferred future ideas, including inventory consumption, batch meal logging, and waste pattern learning.

## Suggested Finalisation Flow

```text
1. Apply final code patch if not already applied.
2. Run pytest.
3. Run MCP Inspector checks.
4. Run a basic curl read/write/read test.
5. Copy the documentation files into the project.
6. Commit Version 1.1.
```
