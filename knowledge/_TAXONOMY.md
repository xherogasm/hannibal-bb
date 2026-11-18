# HannibalBB — Bug Class Taxonomy (knowledge base index)

Every Bug Knowledge Card follows the SAME schema so the agent can read, retrieve and extend
them uniformly. The dynamic arsenal maps each new CVE into one of these classes.

## Card schema (every `knowledge/<class>.md`)
```
# <CLASS> — Bug Knowledge Card
Classe / sous-classe:
Severity ceiling (CVSS): <max realistic> — why
🔭 SPOT TESTS:       signals/probes that reveal the bug MAY exist
🧨 EXPLOIT TESTS:    steps to confirm it
🧗 BYPASS TABLE:     WAF/filter bypasses specific to the class
🔗 CHAIN MAP:        what it chains FROM and INTO (A→B)
🧪 POC SKELETON:     minimal reproducible proof
📚 REFS:             sources, dated
```

## The classes (OWASP + custom)
| Group | Classes (cards) |
|---|---|
| Injection | sqli, nosqli, ssti, xxe, ldap, command-injection, crlf, host-header |
| Client-side | xss, dom-xss, html-injection, clickjacking, csrf, cors |
| Access control | idor, auth-bypass, privilege-escalation, mass-assignment, shadow-api |
| SSRF family | ssrf, cloud-metadata, dns-rebinding |
| Auth / session | oauth, oidc, saml, jwt-crypto, session, mfa-bypass, forgot-password, ato |
| Logic | business-logic, race-condition, exceptional-conditions |
| Serialization | deserialization, prototype-pollution |
| Infra / cloud | cloud-misconfig, iam-escalation, k8s, cicd, subdomain-takeover |
| Protocol | http-smuggling, cache-poisoning, websocket, grpc, graphql |
| AI / LLM | prompt-injection, indirect-injection, llm-exfil, agentic-ai, rag-poisoning |
| Native / files | file-upload, lfi, path-traversal, rce, deserialization |

## Retrieval
The CLI retrieves the most relevant cards for each operator question by keyword match over
these files + the arsenal DB, and injects them into the model context (RAG).
