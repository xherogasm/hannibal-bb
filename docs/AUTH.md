# Authentication — HannibalBB

HannibalBB supports three standard ways to authenticate to the AI backend and to external
services. No secret is ever hard-coded.

## 1. API keys (per provider) — default
Each configured AI has a key, stored in `config/providers.json` (git-ignored) or read from an
environment variable. It is sent as:
```
Authorization: Bearer <API_KEY>
```
Resolution order (`resolve_key()`): explicit value → environment variable
(`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`, …). Keys never live in source.

The default provider `claude-code` needs **no key** — it shells out to a locally installed
`claude` CLI. Add any OpenAI-compatible endpoint with `/models add`.

## 2. OAuth2 (connectors)
The connectors (`connectors/notify.py`) use OAuth2 / token auth, read from environment:
- **GitHub**: Personal Access Token (`GITHUB_TOKEN`) to open issues.
- **Discord / Teams**: signed webhook URL (`DISCORD_WEBHOOK` / `TEAMS_WEBHOOK`).

## 3. Enterprise SSO (optional)
When wiring HannibalBB-style agents into an enterprise stack, delegated OAuth2 / OIDC
tokens (e.g. Microsoft Entra ID, Okta) grant least-privilege, read-only access to internal
data sources. Scope tokens to exactly what the agent needs.

> Golden rule: keep every secret in an environment variable or a git-ignored config file —
> never commit keys, and rotate anything that leaks.
