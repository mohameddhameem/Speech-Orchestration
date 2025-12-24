# Authentication & Storage Deep Dive

## Objectives
- Enforce OAuth2 Client Credentials for all API calls.
- Enforce BYOS with identity-based storage access (no SAS, no account keys).
- Provide verifiable guidance for customers and operators.

## API Authentication (OAuth2)
- Flow: Client Credentials against `https://auth.speechapi.dev/oauth/token`.
- Scopes (must match OpenAPI): `speech.transcribe speech.translate speech.detect speech.synthesize`.
- Required headers: `Authorization: Bearer <token>`, `Content-Type: application/json` (except multipart uploads).
- Token lifetime: configure 1h default; refresh 5m before expiry.

### Verification Steps
1) Request a token:
   - `curl -X POST https://auth.speechapi.dev/oauth/token -d "grant_type=client_credentials&client_id=...&client_secret=...&scope=speech.transcribe"`
2) Call a protected endpoint (e.g., `/health`) with the token; expect 200. Without token, expect 401.

## Storage Access (BYOS + Managed Identity)
- Principle: service reads customer blobs using its Managed Identity (MI); clients never send SAS or keys.
- Supported: System-assigned MI or user-assigned MI (UAMI) configured on the API service and workers.

### Customer Onboarding Checklist
1) Identify the service principal (Object ID) for the API MI (provided during onboarding).
2) In the customer storage account, assign **Storage Blob Data Reader** to that principal at the target container scope.
3) Optional: assign **Storage Blob Data Contributor** if results must be written back to customer storage.
4) No firewall exceptions needed if using private endpoints/PE; otherwise allow the service subnet.

### Backend Access Pattern (DefaultAzureCredential)
- Use `DefaultAzureCredential` in this order (Azure default):
  1. Environment (AZURE_CLIENT_ID/SECRET/TENANT for SP)
  2. Managed Identity (system or user-assigned)
  3. Developer tools (Visual Studio/CLI) for local debugging
- Blob access: build `account_url = https://{storage_account}.blob.core.windows.net` and call `BlobServiceClient(account_url, credential)`.
- Do **not** accept SAS URIs. Accept structured references only: `storage_account_name`, `container_name`, `blob_name`.

### RBAC Validation Playbook (Customer)
- After role assignment, run:
  - `az storage blob show --account-name <acct> --container-name <container> --name <blob> --auth-mode login`
- If this succeeds with the MI’s identity, the API will be able to read the blob.
- If access fails, expect API error `ACCESS_DENIED` with `details.container` in the response.

## Webhook Authentication (Job Completion)
- All webhooks MUST be signed; receivers must verify before accepting.
- Recommended scheme: HMAC-SHA256 signature header `X-Speech-Signature` over the raw body using a shared `WEBHOOK_SECRET`.
- Receiver must:
  1) Read body bytes and the signature header.
  2) Compute `hex(hmac_sha256(WEBHOOK_SECRET, body))`.
  3) Constant-time compare to header; reject mismatches.
- Include `timestamp` in payload and enforce a freshness window (e.g., 5 minutes) to mitigate replay.

## Secret & Identity Rotation
- Rotate OAuth2 client secrets every 90 days; overlap old/new for 24h.
- For UAMI rotation, deploy a new identity, grant roles, then switch the resource to the new client_id.
- Audit: enable Azure AD sign-in logs and Storage Data Plane logs; retain for 90 days.

## Local Development Notes
- For local runs, `DefaultAzureCredential` will fall back to `AZURE_CLIENT_ID/SECRET/TENANT_ID` or the Azure CLI login. Keep dev accounts scoped to non-prod storage with Reader-only rights.
- Never embed connection strings or SAS in configs, tests, or examples.
