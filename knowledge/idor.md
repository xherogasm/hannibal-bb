# IDOR — Bug Knowledge Card
Classe / sous-classe: Access Control / Insecure Direct Object Reference (BOLA)

Severity ceiling (CVSS): up to 9.8 — a cross-tenant IDOR on a write/admin object = full
account/tenant takeover. Read-only PII IDOR typically 6.5–7.5; mass-assignment/privesc 8–9.8.

🔭 SPOT TESTS
- Any request with an object identifier: `id=`, `uuid=`, `/users/123`, `account_id`,
  `orderId`, `fileId`, `?user=`, GraphQL node IDs, JWT `sub` echoed into queries.
- Two accounts (A, B) available → the fastest tell. Note A's object IDs, replay as B.
- Sequential / predictable IDs, or UUIDs leaked in other responses (listing endpoints).
- Endpoints that return more data than the UI shows (over-fetching APIs).

🧨 EXPLOIT TESTS
1. Capture a request as user A that reads/writes an object A owns.
2. Replay it as user B (swap session only, keep the object ID) → does B get A's data?
3. Vary the method: GET→POST→PUT→PATCH→DELETE on the same object.
4. Try ID in body vs. query vs. header vs. path — auth often checked on one location only.
5. Mass-assignment: add `role`, `is_admin`, `owner_id`, `tenant_id` to the body.
6. Blind IDOR: compare status/length/timing when the object exists vs. not.

🧗 BYPASS TABLE
- Wrap ID: `123` → `[123]`, `{"id":123}`, `123.json`, `123/`, `%31%32%33`.
- Parameter pollution: `id=self&id=123`.
- Path tricks: `/users/me/../123`, encoded slashes `%2e%2e`.
- Change content-type JSON↔form to dodge a type-specific check.
- GraphQL: query by `node(id:)` / aliases to batch many IDs in one request.

🔗 CHAIN MAP
- IDOR(read) → leak other users' tokens/emails → **ATO** / password-reset chain.
- IDOR(write) + mass-assignment → **privilege escalation** → admin → RCE via admin feature.
- IDOR on tenant_id → **cross-tenant** data breach (highest severity in SaaS).
- IDOR exposing internal URLs → **SSRF** pivot.

🧪 POC SKELETON
```
# As user B's session, request user A's object:
GET /api/v1/users/A_ID/profile  (Cookie: B_session)
→ 200 with A's PII  == confirmed cross-account IDOR
```
Capture both accounts' IDs; screenshot B reading A's data with B's session highlighted.

📚 REFS: OWASP API1:2023 BOLA; PortSwigger Access Control labs; H1 hacktivity IDOR reports.
