# HannibalBB — The 0 → Hero Methodology (target-agnostic)

A single, repeatable parcours HannibalBB runs on any authorized target. Non-linear: loop
back whenever a new fact changes the map.

---

## PHASE 0 — AUTHORIZATION & SCOPE  🚦
- Read the full program policy / scope. List in-scope assets, out-of-scope assets,
  allowed classes, and payout table.
- Confirm the operator picked this target and testing is authorized.
- Note the always-rejected classes for this program (to avoid wasted effort).
- **Gate:** no testing begins until this phase is green.

## PHASE 1 — RECON  🔭
- Passive: subdomain enum (subfinder, chaos, assetfinder), wayback/gau URLs, GitHub leaks.
- Active: live-host probe (httpx), tech fingerprint (wappalyzer/httpx), port/service map.
- Collect JS bundles → extract endpoints, secrets, API routes (LinkFinder/SecretFinder).
- Output: an **asset inventory** + **tech stack** + **version list** (feeds CVE arsenal).

## PHASE 2 — SURFACE MAP  🗺️
- Enumerate every entry point: params, headers, cookies, uploads, GraphQL/REST endpoints,
  websockets, OAuth flows, file paths, AI/LLM features.
- Classify each by the bug classes it could carry (cross-reference `knowledge/_TAXONOMY.md`).
- Build an attack-surface matrix: endpoint × candidate bug classes.

## PHASE 3 — UNDERSTAND (developer psychology)  🧠
- Ask: what did the dev assume? Where is auth enforced vs. assumed? What is validated on
  the client but trusted on the server? Which object IDs are sequential/guessable?
- Look for anomalies: inconsistent responses, verbose errors, debug flags, legacy routes.
- Form **What-If hypotheses** ("what if I swap this ID?", "what if I send this twice?").

## PHASE 4 — HUNT BY CLASS  🎯
- For each candidate class on the surface matrix, open its **Bug Knowledge Card**
  (`knowledge/<class>.md`) and run its SPOT → EXPLOIT tests.
- Breadth first (IDOR-first sweep — cheapest high-impact), then depth on promising leads.
- At every wall → run the deep-research bypass loop (see OPERATING-PROTOCOL). Never drop
  on first "defended".

## PHASE 5 — CHAIN TO THE CEILING  🧗
- Take each confirmed primitive and ask *what does it chain into?* Use each card's
  **Chain map**. Examples:
  - IDOR → mass-assignment → privilege escalation → full ATO
  - SSRF → cloud metadata → IAM creds → account takeover of the cloud tenant
  - Open redirect → OAuth token theft → ATO
  - XSS → session/token theft → ATO → admin → RCE via admin feature
- Re-score at the ceiling. Severity = the chain's impact, not the entry bug's.

## PHASE 6 — VALIDATE  ✅
- Run the **4 gates** (Scope, Impact, PoC, Defensibility).
- Check against the always-rejected list and conditional-chain table.
- Compute CVSS 3.1 (base vector). Assign severity emoji by score.
- Only all-green → ⭐ confirmed.

## PHASE 7 — REPORT  📝
- Impact-first title. Clear reproduction. Redact PII/cookies (evidence hygiene).
- Include CVSS vector, affected asset, fix recommendation.
- Hand to operator for confirmation. **Never auto-submit.**

---

### Loop discipline
- New subdomain / new JS / new version discovered → back to PHASE 1–2.
- New primitive confirmed → back to PHASE 5 (re-chain).
- Wall hit → deep-research loop, then resume the phase you were in.
