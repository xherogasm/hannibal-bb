# MCP (Model Context Protocol) — HannibalBB

MCP est un protocole standard qui connecte un agent IA à des outils/sources externes de
façon uniforme et sécurisée. HannibalBB s'appuie sur **3 serveurs MCP réels** présents dans
l'environnement Claude Code qui l'opère :

| Serveur MCP | Rôle pour HannibalBB | Exemple d'usage |
|---|---|---|
| **Playwright MCP** | pilotage d'un navigateur headless | rejouer un PoC XSS, capturer une preuve, naviguer un flux OAuth |
| **BurpMCP** (:8181) | envoi de requêtes HTTP brutes via Burp | rejouer/modifier une requête signée, tester un IDOR en Repeater |
| **Claude Docs MCP** | création/édition de documents | générer le rapport de finding ou le livrable |

## Pourquoi MCP ici (vs. un simple appel HTTP)
- **Standardisé** : le même protocole expose des capacités hétérogènes (navigateur, proxy,
  docs) sans code d'intégration sur-mesure par outil.
- **Sécurisé** : chaque serveur MCP contrôle ses permissions ; l'agent ne reçoit que les
  capacités déclarées.
- **Découvrable** : l'agent liste dynamiquement les outils offerts par chaque serveur.

## Schéma
```
HannibalBB (agent)
   │  MCP (JSON-RPC)
   ├────────────▶ Playwright MCP  ──▶ Chromium headless ──▶ cible web
   ├────────────▶ BurpMCP         ──▶ Burp Suite proxy   ──▶ requêtes HTTP brutes
   └────────────▶ Claude Docs MCP ──▶ documents livrable
```

## Lien avec l'exercice
C'est le **bonus majeur** de la grille : l'agent est connecté « de manière standardisée et
sécurisée à des sources de données locales ou distantes » via MCP.

> Note : dans la version CLI standalone (`hannibal.py`), les équivalents sont fournis comme
> outils natifs (`http_fingerprint`, etc.) ; MCP est le mode d'intégration quand l'agent
> tourne sous Claude Code (démo de la vidéo/captures).
