# Version 1.4 curl readable output update

Copy these files into your `version_1_4` folder:

```text
version_1_4/
  command_reference_v1_4.md
  curl_helpers_v1_4.ps1
```

From the folder that contains `version_1_4`, run:

```powershell
. .\version_1_4\curl_helpers_v1_4.ps1
Initialize-McpCurlSession
Send-McpInitializedNotification
Run-McpV14Workflow
```

Each request writes:

```text
*.response.txt
*.pretty.json
```

to:

```text
version_1_4/curl_responses/
```

Use the `.pretty.json` files for readable inspection.
