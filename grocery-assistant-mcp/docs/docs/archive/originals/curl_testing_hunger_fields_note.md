# Curl Testing Note — Hunger Fields

## Issue Encountered

During Version 1.1 curl testing, this request shape failed for `add_intake_entry`:

```json
"hunger_before": 7,
"hunger_after": 3
```

The MCP tool argument layer returned a validation error because the current Version 1.1 tool schema expects these fields as strings.

## Correct Version 1.1 Usage

Use string values:

```json
"hunger_before": "7",
"hunger_after": "3"
```

## Reason

In Version 1.1, `hunger_before` and `hunger_after` are flexible text fields.

This allows values such as:

```text
"7"
"3"
"high"
"low"
"unknown"
""
```

## Future Consideration

A later version may convert these into structured numeric ratings, such as integers from 0 to 10, if hunger ratings become part of analysis or recommendations.

For Version 1.1, no code change is required. The curl request body should send hunger values as strings.
