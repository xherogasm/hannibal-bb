# Architecture technique — HannibalBB

## Schéma global
```
                       ┌─────────────────────────────────────────────┐
   operator (CLI)  ───▶│                 hannibal.py                  │
   "you ▸ ..."         │                   (REPL)                     │
                       │                                              │
                       │  build_system(msg)  ── assemble ──┐          │
                       │     ├─ core/identity/HANNIBAL.md   │          │
                       │     ├─ SKILLS[]                    │ system   │
                       │     ├─ knowledge index             │ prompt   │
                       │     ├─ long-term memory (JSON)     │          │
                       │     └─ RAG: retrieve_cards(msg) ◀── knowledge/*.md
                       │                                    │          │
                       │  agent_turn()  ──▶ call_llm() ─────┼───▶ PROVIDER (any OpenAI-compatible)
                       │     ▲   │                          │     claude / openai / deepseek / ...
                       │     │   ▼ tool_calls?              │        ▲
                       │     │  TOOL_FUNCS:                 │        │ /models (key + base_url + model)
                       │     │   analyze_auth_log           │        │
                       │     │   http_fingerprint ──────────┼──▶ target (authorized recon)
                       │     │   search_knowledge ──▶ knowledge/
                       │     │   query_arsenal  ──▶ arsenal/cards.json
                       │     └── remember ───────▶ memory/hannibal_memory.json
                       └─────────────────────────────────────────────┘
                                   ▲
   arsenal/learn_cve.py ──────────┘   (/learn : CVE feeds live ─▶ classify ─▶ cards.json + cards)
   connectors/notify.py           (Discord / Teams / GitHub webhooks)
```

## Flux d'un tour
1. L'opérateur tape un message.
2. `build_system()` construit un prompt système frais : identité + skills + mémoire LT +
   **cartes récupérées par RAG** selon le message.
3. `agent_turn()` appelle le provider actif (compatible OpenAI). Si le modèle demande des
   outils (`tool_calls`), l'agent les exécute et reboucle (max 6 itérations).
4. La réponse finale est affichée ; les faits importants peuvent être persistés en mémoire.

## Provider-agnostic
Un seul chemin de code (`call_llm`) parle le protocole **OpenAI chat/completions**. Claude
est joint via son endpoint compatible `https://api.anthropic.com/v1`. Si un provider ne
supporte pas les outils, l'agent réessaie automatiquement sans outils (dégradation propre).

## Dépendances
Python 3 **stdlib uniquement** (`urllib`, `json`, `threading`) — aucun paquet à installer,
portable partout.
